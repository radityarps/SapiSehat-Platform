"""Property-based tests for the backend prediction contract.

Uses Hypothesis to verify universal invariants across randomized inputs.
"""

import pytest  # type: ignore[import-not-found]
from hypothesis import HealthCheck, given, settings as hypothesis_settings  # type: ignore[import-not-found]
from hypothesis import strategies as st  # type: ignore[import-not-found]

from api.schemas import (
    PredictResponse,
    PredictionResult,
    ModelInfo,
    DiseaseClass,
    ErrorResponse,
)
from utils.errors import ErrorCode
from inference_server import DISPLAY_LABEL_KEY_MAP
from config import settings as app_settings


# --- Strategies ---

DISEASE_CLASSES = [DiseaseClass.FMD.value, DiseaseClass.HEALTHY.value]

disease_classes_st = st.sampled_from(DISEASE_CLASSES)

# Generate a valid probability distribution across the accepted classes.
# Raw non_cattle probability is intentionally excluded from accepted results.
probability_distributions = st.tuples(
    st.integers(min_value=1, max_value=10_000),
    st.integers(min_value=1, max_value=10_000),
).map(
    lambda xs: [x / sum(xs) for x in xs]
)

# Generate valid timing values (non-negative integers)
timing_values = st.integers(min_value=0, max_value=100000)

# Generate valid model version strings
model_versions = st.from_regex(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", fullmatch=True)


# --- Property 1: Prediction response contains all required fields with correct types ---


@given(
    probs=probability_distributions,
    preprocessing_ms=timing_values,
    inference_ms=timing_values,
    model_version=model_versions,
)
@hypothesis_settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_success_response_shape(probs, preprocessing_ms, inference_ms, model_version):
    """
    Property 1: Prediction response contains all required fields with correct types.

    For any valid inference result (random disease class, random confidence scores
    that sum to ~1.0), the PredictResponse schema always produces a response with
    all required fields and correct types.

    **Validates: Requirements 1.1, 1.4, 1.6**
    """
    labels = ["FMD", "healthy"]

    # Determine predicted class from max probability
    pred_idx = probs.index(max(probs))
    pred_label = labels[pred_idx]
    pred_confidence = round(probs[pred_idx], 4)
    is_reliable = pred_confidence >= app_settings.confidence_threshold

    # Build scores dict
    scores = {labels[i]: round(probs[i], 4) for i in range(2)}

    # Total processing time must be >= sum of parts
    total_ms = preprocessing_ms + inference_ms + 1  # +1 for overhead

    # Construct the result dict as InferenceService.predict() would return
    result_dict = {
        "status": "success",
        "prediction": {
            "disease_class": pred_label,
            "display_label_key": DISPLAY_LABEL_KEY_MAP[pred_label],
            "confidence": pred_confidence,
            "is_reliable": is_reliable,
            "scores": scores,
        },
        "model_info": {"version": model_version},
        "processing_time_ms": total_ms,
        "preprocessing_time_ms": preprocessing_ms,
        "inference_time_ms": inference_ms,
    }

    # Validate against PredictResponse schema (Pydantic validation)
    response = PredictResponse(**result_dict)

    # Assert all required top-level fields exist with correct types
    assert response.status == "success"
    assert isinstance(response.prediction, PredictionResult)
    assert isinstance(response.model_info, ModelInfo)
    assert isinstance(response.processing_time_ms, int)
    assert isinstance(response.preprocessing_time_ms, int)
    assert isinstance(response.inference_time_ms, int)

    # Assert timing fields are non-negative
    assert response.processing_time_ms >= 0
    assert response.preprocessing_time_ms >= 0
    assert response.inference_time_ms >= 0

    # Assert nested prediction fields exist with correct types
    prediction = response.prediction
    assert isinstance(prediction.disease_class, DiseaseClass)
    assert prediction.disease_class.value in labels
    assert isinstance(prediction.display_label_key, str)
    assert isinstance(prediction.confidence, float)
    assert 0.0 <= prediction.confidence <= 1.0
    assert isinstance(prediction.is_reliable, bool)
    assert isinstance(prediction.scores, dict)

    # Assert accepted scores contain exactly the two active classes.
    assert set(prediction.scores) == {"FMD", "healthy"}
    for label in labels:
        assert label in prediction.scores
        assert isinstance(prediction.scores[label], float)

    # Assert model_info has version field
    assert isinstance(response.model_info.version, str)
    assert len(response.model_info.version) > 0

    # Verify serialized dict contains all required fields
    serialized = response.model_dump()
    required_top_level = [
        "status", "prediction", "model_info",
        "processing_time_ms", "preprocessing_time_ms", "inference_time_ms",
    ]
    for field in required_top_level:
        assert field in serialized, f"Missing top-level field: {field}"

    required_prediction_fields = [
        "disease_class", "display_label_key", "confidence", "is_reliable", "scores",
    ]
    for field in required_prediction_fields:
        assert field in serialized["prediction"], f"Missing prediction field: {field}"

    assert "version" in serialized["model_info"], "Missing model_info.version field"



# --- Property 3: Timing fields satisfy ordering invariant ---
# **Validates: Requirements 1.5**


@given(
    preprocessing_ms=st.integers(min_value=0, max_value=100_000),
    inference_ms=st.integers(min_value=0, max_value=100_000),
    overhead_ms=st.integers(min_value=0, max_value=10_000),
)
@hypothesis_settings(max_examples=100)
def test_timing_ordering_invariant(
    preprocessing_ms: int, inference_ms: int, overhead_ms: int
):
    """Property 3: Timing fields satisfy ordering invariant.

    For any successful prediction, the timing fields SHALL satisfy:
    - processing_time_ms >= 0
    - preprocessing_time_ms >= 0
    - inference_time_ms >= 0
    - processing_time_ms >= preprocessing_time_ms + inference_time_ms

    **Validates: Requirements 1.5**
    """
    # Compute total as sum of parts plus some non-negative overhead
    # (simulating real behavior where total >= preprocessing + inference)
    total_ms = preprocessing_ms + inference_ms + overhead_ms

    # Construct a PredictResponse with these timing values
    response = PredictResponse(
        status="success",
        prediction=PredictionResult(
            disease_class=DiseaseClass.FMD,
            display_label_key="disease.fmd",
            confidence=0.85,
            is_reliable=True,
            scores={"FMD": 0.85, "healthy": 0.15},
        ),
        model_info=ModelInfo(version="1.0.0"),
        processing_time_ms=total_ms,
        preprocessing_time_ms=preprocessing_ms,
        inference_time_ms=inference_ms,
    )

    # Assert all timing fields are non-negative
    assert response.processing_time_ms >= 0
    assert response.preprocessing_time_ms >= 0
    assert response.inference_time_ms >= 0

    # Assert ordering invariant: total >= preprocessing + inference
    assert (
        response.processing_time_ms
        >= response.preprocessing_time_ms + response.inference_time_ms
    )


# --- Property 2: Prediction object satisfies structural invariants ---
# **Validates: Requirements 1.2, 1.5**


@given(
    s1=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
    s2=st.floats(min_value=0.01, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@hypothesis_settings(max_examples=100)
def test_prediction_structural_invariants(s1: float, s2: float):
    """Property 2: Prediction object satisfies structural invariants.

    For any probability distribution across the two accepted classes, the constructed
    prediction object SHALL have:
    - disease_class equal to the class with the maximum score
    - confidence equal to that maximum score (in range 0.0-1.0)
    - is_reliable equal to confidence >= 0.60
    - scores containing exactly two entries (one per active class)
      that sum to approximately 1.0

    **Validates: Requirements 1.2, 1.5**
    """
    labels = ["FMD", "healthy"]
    confidence_threshold = app_settings.confidence_threshold  # 0.60

    # Normalize to create a valid probability distribution
    probs = [s1 / (s1 + s2), s2 / (s1 + s2)]

    # Simulate what InferenceService.predict() does:
    # Pick argmax as disease_class, confidence = max score, is_reliable = confidence >= threshold
    pred_idx = probs.index(max(probs))
    pred_label = labels[pred_idx]
    pred_confidence = round(probs[pred_idx], 4)
    is_reliable = pred_confidence >= confidence_threshold

    # Build scores dict (same rounding as inference_server.py)
    scores = {labels[i]: round(probs[i], 4) for i in range(2)}

    # Build prediction object (same as inference_server.py)
    prediction = PredictionResult(
        disease_class=pred_label,
        display_label_key=DISPLAY_LABEL_KEY_MAP[pred_label],
        confidence=pred_confidence,
        is_reliable=is_reliable,
        scores=scores,
    )

    # Assert: disease_class matches the class with highest score
    max_score_class = max(scores, key=lambda key: scores[key])
    assert prediction.disease_class.value == max_score_class, (
        f"disease_class '{prediction.disease_class.value}' does not match "
        f"class with max score '{max_score_class}' (scores: {scores})"
    )

    # Assert: confidence equals the max score
    assert prediction.confidence == max(scores.values()), (
        f"confidence {prediction.confidence} does not equal "
        f"max score {max(scores.values())} (scores: {scores})"
    )

    # Assert: confidence is in valid range [0.0, 1.0]
    assert 0.0 <= prediction.confidence <= 1.0, (
        f"confidence {prediction.confidence} is out of range [0.0, 1.0]"
    )

    # Assert: is_reliable matches threshold comparison
    expected_reliable = prediction.confidence >= confidence_threshold
    assert prediction.is_reliable == expected_reliable, (
        f"is_reliable is {prediction.is_reliable} but confidence "
        f"{prediction.confidence} vs threshold {confidence_threshold} "
        f"should give {expected_reliable}"
    )

    # Assert: accepted scores have exactly two entries (one per active class)
    assert len(prediction.scores) == 2, (
        f"scores has {len(prediction.scores)} entries, expected 2"
    )

    # Assert: scores contains one entry per active class
    for label in labels:
        assert label in prediction.scores, (
            f"scores missing entry for '{label}'"
        )

    # Assert: accepted scores sum to approximately 1.0 (allowing for rounding)
    score_sum = sum(prediction.scores.values())
    assert abs(score_sum - 1.0) < 0.01, (
        f"scores sum to {score_sum}, expected approximately 1.0"
    )


# --- Property 5: Error responses have exactly the standardized shape ---
# **Validates: Requirements 3.1, 3.10, 2.4**

VALID_ERROR_CODES = [
    ErrorCode.INVALID_IMAGE,
    ErrorCode.MODEL_NOT_READY,
    ErrorCode.INFERENCE_FAILED,
    ErrorCode.TIMEOUT,
    ErrorCode.RATE_LIMITED,
]


@given(
    error_code=st.sampled_from(VALID_ERROR_CODES),
    message=st.text(min_size=0, max_size=256),
)
@hypothesis_settings(max_examples=100)
def test_error_response_shape(error_code: ErrorCode, message: str):
    """Property 5: Error responses have exactly the standardized shape.

    For any error condition, the response body SHALL contain exactly three
    fields: `status` (equal to "error"), `error_code` (one of the 5 defined
    values), and `message` (string of at most 256 characters).

    **Validates: Requirements 3.1, 3.10, 2.4**
    """
    # Construct an ErrorResponse with the generated error code and message
    response = ErrorResponse(
        status="error",
        error_code=error_code.value,
        message=message,
    )

    # Serialize to dict (simulates JSON serialization)
    response_dict = response.model_dump()

    # Assert exactly 3 fields exist
    assert set(response_dict.keys()) == {"status", "error_code", "message"}, (
        f"Expected exactly 3 fields (status, error_code, message), "
        f"got: {set(response_dict.keys())}"
    )

    # Assert status == "error"
    assert response_dict["status"] == "error", (
        f"Expected status='error', got '{response_dict['status']}'"
    )

    # Assert error_code is one of the 5 defined values
    valid_codes = {code.value for code in VALID_ERROR_CODES}
    assert response_dict["error_code"] in valid_codes, (
        f"Expected error_code to be one of {valid_codes}, "
        f"got '{response_dict['error_code']}'"
    )

    # Assert message length <= 256
    assert len(response_dict["message"]) <= 256, (
        f"Expected message length <= 256, got {len(response_dict['message'])}"
    )


# --- Property 4: No localized text and correct display_label_key mapping ---
# **Validates: Requirements 2.1, 2.2**


@given(disease_class=st.sampled_from(DISEASE_CLASSES))
@hypothesis_settings(max_examples=100)
def test_no_localized_text_and_correct_display_label_key(disease_class: str):
    """Property 4: No localized text and correct display_label_key mapping.

    For any disease class value, the serialized prediction result SHALL NOT
    contain a 'display_label' field, and SHALL contain a 'display_label_key'
    field whose value matches the defined mapping:
    - FMD → disease.fmd
    - healthy → disease.healthy

    **Validates: Requirements 2.1, 2.2**
    """
    # Construct a prediction result for this disease class
    display_label_key = DISPLAY_LABEL_KEY_MAP[disease_class]

    prediction = PredictionResult(
        disease_class=disease_class,
        display_label_key=display_label_key,
        confidence=0.85,
        is_reliable=True,
        scores={"FMD": 0.10, "healthy": 0.90},
    )

    # Serialize to dict (simulates JSON serialization)
    result_dict = prediction.model_dump()

    # Property 4a: No 'display_label' field exists (no localized text)
    assert "display_label" not in result_dict, (
        f"Found forbidden 'display_label' field in prediction result "
        f"for disease_class '{disease_class}'"
    )

    # Property 4b: 'display_label_key' matches the defined mapping
    assert result_dict["display_label_key"] == DISPLAY_LABEL_KEY_MAP[disease_class], (
        f"Expected display_label_key '{DISPLAY_LABEL_KEY_MAP[disease_class]}' "
        f"for disease_class '{disease_class}', "
        f"got '{result_dict['display_label_key']}'"
    )

    # Property 4c: display_label_key follows pattern "disease.<lowercase>"
    expected_pattern = f"disease.{disease_class.lower()}"
    assert result_dict["display_label_key"] == expected_pattern, (
        f"display_label_key '{result_dict['display_label_key']}' does not match "
        f"expected pattern 'disease.<lowercase>' = '{expected_pattern}'"
    )


@given(disease_class=st.sampled_from(DISEASE_CLASSES))
@hypothesis_settings(max_examples=100)
def test_full_response_no_display_label(disease_class: str):
    """Property 4 (extended): Full PredictResponse has no display_label anywhere.

    Verifies that the complete response object, when serialized, does not
    contain a 'display_label' field at any level.

    **Validates: Requirements 2.1, 2.2**
    """
    display_label_key = DISPLAY_LABEL_KEY_MAP[disease_class]

    prediction = PredictionResult(
        disease_class=disease_class,
        display_label_key=display_label_key,
        confidence=0.9,
        is_reliable=True,
        scores={"FMD": 0.05, "healthy": 0.95},
    )

    response = PredictResponse(
        status="success",
        prediction=prediction,
        model_info=ModelInfo(version="1.0.0"),
        processing_time_ms=100,
        preprocessing_time_ms=30,
        inference_time_ms=70,
    )

    response_dict = response.model_dump()

    # No 'display_label' at top level
    assert "display_label" not in response_dict, (
        "Found 'display_label' at top level of response"
    )

    # No 'display_label' in prediction object
    assert "display_label" not in response_dict["prediction"], (
        "Found 'display_label' in prediction object"
    )

    # Verify display_label_key is present and correct in prediction
    assert response_dict["prediction"]["display_label_key"] == DISPLAY_LABEL_KEY_MAP[disease_class], (
        f"Expected display_label_key '{DISPLAY_LABEL_KEY_MAP[disease_class]}' "
        f"for disease_class '{disease_class}', "
        f"got '{response_dict['prediction']['display_label_key']}'"
    )


# --- Property 6: Rate limiter enforces per-IP request ceiling ---
# **Validates: Requirements 4.1, 4.3**

import httpx  # type: ignore[import-not-found]
from fastapi import FastAPI, Request  # type: ignore[import-not-found]
from fastapi.responses import JSONResponse  # type: ignore[import-not-found]
from api.rate_limiter import RateLimiterMiddleware


def _create_rate_limited_app(max_requests: int, window_seconds: int = 60) -> FastAPI:
    """Create a minimal FastAPI app with rate limiter middleware for testing."""
    app = FastAPI()

    # Add rate limiter middleware
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests=max_requests,
        window_seconds=window_seconds,
    )

    @app.post("/api/predict")
    async def mock_predict(request: Request):
        """Mock predict endpoint that always succeeds."""
        return JSONResponse(
            status_code=200,
            content={"status": "success", "prediction": "mock"},
        )

    return app


@given(max_requests=st.integers(min_value=1, max_value=20))
@hypothesis_settings(max_examples=100, deadline=None)
def test_rate_limiter_enforcement(max_requests: int):
    """Property 6: Rate limiter enforces per-IP request ceiling.

    For any sequence of N requests from the same client IP to the prediction
    endpoint within a time window, where N > max_requests: the first
    max_requests requests SHALL be allowed through, and request number
    max_requests + 1 SHALL be rejected with HTTP 429, error_code RATE_LIMITED,
    and a Retry-After header containing a positive integer.

    **Validates: Requirements 4.1, 4.3**
    """
    import asyncio

    async def _run_test():
        # Create a fresh app with the generated max_requests
        app = _create_rate_limited_app(max_requests=max_requests, window_seconds=60)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            # Send max_requests requests - all should be allowed
            for i in range(max_requests):
                response = await client.post("/api/predict")
                assert response.status_code != 429, (
                    f"Request {i + 1} of {max_requests} was rate-limited "
                    f"(expected to be allowed)"
                )

            # Send the (max_requests + 1)th request - should be rejected
            response = await client.post("/api/predict")

            # Assert HTTP 429
            assert response.status_code == 429, (
                f"Request {max_requests + 1} should be rate-limited with 429, "
                f"got {response.status_code}"
            )

            # Assert error_code is RATE_LIMITED
            body = response.json()
            assert body["error_code"] == "RATE_LIMITED", (
                f"Expected error_code='RATE_LIMITED', got '{body.get('error_code')}'"
            )

            # Assert Retry-After header exists with a positive integer value
            retry_after = response.headers.get("retry-after")
            assert retry_after is not None, (
                "Expected 'Retry-After' header in 429 response, but it was missing"
            )
            retry_after_int = int(retry_after)
            assert retry_after_int > 0, (
                f"Expected Retry-After to be a positive integer, got {retry_after_int}"
            )

    asyncio.run(_run_test())
