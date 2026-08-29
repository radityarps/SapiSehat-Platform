"""Example-based integration tests for the backend prediction contract.

Uses pytest + httpx.AsyncClient against the actual FastAPI app.
"""

import asyncio
import io
from unittest.mock import MagicMock, patch

import httpx  # type: ignore[import-not-found]
import pytest  # type: ignore[import-not-found]
from PIL import Image

from api.schemas import PredictResponse
from config import settings
from main import app


def _create_test_jpeg() -> bytes:
    """Create a small valid JPEG image (224x224) in memory."""
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.getvalue()


MOCK_SUCCESS_RESULT = {
    "status": "success",
    "prediction": {
        "disease_class": "FMD",
        "display_label_key": "disease.fmd",
        "confidence": 0.944,
        "is_reliable": True,
        "scores": {
            "FMD": 0.944,
            "healthy": 0.056,
        },
    },
    "model_info": {"version": "1.0.0"},
    "processing_time_ms": 2340,
    "preprocessing_time_ms": 120,
    "inference_time_ms": 2180,
}


# --- Task 8.1: Error condition tests ---


def test_invalid_content_type_returns_422():
    """Test invalid content type returns HTTP 422 + INVALID_IMAGE.

    Validates: Requirements 3.3
    """

    async def _run():
        with patch("api.routes.is_model_ready", return_value=True):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    "/api/predict",
                    files={"image": ("test.txt", b"not an image", "text/plain")},
                )

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "INVALID_IMAGE"
        assert "message" in body
        assert len(body["message"]) <= 256

    asyncio.run(_run())


def test_empty_image_returns_422():
    """Test empty image file returns HTTP 422 + INVALID_IMAGE.

    Validates: Requirements 3.4
    """

    async def _run():
        with patch("api.routes.is_model_ready", return_value=True):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    "/api/predict",
                    files={"image": ("empty.jpg", b"", "image/jpeg")},
                )

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "INVALID_IMAGE"
        assert "message" in body

    asyncio.run(_run())


def test_corrupted_image_returns_422():
    """Test corrupted image (random bytes) returns HTTP 422 + INVALID_IMAGE.

    Validates: Requirements 3.4
    """

    async def _run():
        with patch("api.routes.is_model_ready", return_value=True):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    "/api/predict",
                    files={
                        "image": (
                            "corrupt.jpg",
                            b"\x00\x01\x02\x03\xff\xfe",
                            "image/jpeg",
                        )
                    },
                )

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "INVALID_IMAGE"
        assert "message" in body

    asyncio.run(_run())


def test_model_not_ready_returns_503():
    """Test model not ready returns HTTP 503 + MODEL_NOT_READY.

    Validates: Requirements 3.5
    """

    async def _run():
        with patch("api.routes.is_model_ready", return_value=False):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                jpeg_bytes = _create_test_jpeg()
                response = await client.post(
                    "/api/predict",
                    files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
                )

        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "MODEL_NOT_READY"
        assert "message" in body

    asyncio.run(_run())


def test_inference_exception_returns_500():
    """Test inference exception returns HTTP 500 + INFERENCE_FAILED.

    Validates: Requirements 3.6
    """

    async def _run():
        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.get_inference_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.predict.return_value = {
                "status": "error",
                "message": "Model inference failed unexpectedly",
                "processing_time_ms": 100,
            }
            mock_get_service.return_value = mock_service

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                jpeg_bytes = _create_test_jpeg()
                response = await client.post(
                    "/api/predict",
                    files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
                )

        assert response.status_code == 500
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "INFERENCE_FAILED"
        assert "message" in body

    asyncio.run(_run())


def test_timeout_returns_408():
    """Test timeout returns HTTP 408 + TIMEOUT.

    Validates: Requirements 3.7
    """

    async def _run():
        # Mock asyncio.wait_for to raise TimeoutError directly
        # This avoids actually waiting for a real timeout
        async def mock_wait_for(coro, timeout):
            # Cancel the coroutine to clean up
            coro.close()
            raise asyncio.TimeoutError()

        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.get_inference_service") as mock_get_service,
            patch("api.routes.asyncio.wait_for", side_effect=mock_wait_for),
        ):
            mock_service = MagicMock()
            mock_service.predict.return_value = MOCK_SUCCESS_RESULT
            mock_get_service.return_value = mock_service

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                jpeg_bytes = _create_test_jpeg()
                response = await client.post(
                    "/api/predict",
                    files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
                )

        assert response.status_code == 408
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "TIMEOUT"
        assert "message" in body

    asyncio.run(_run())


def test_rate_limit_returns_429_with_retry_after():
    """Test rate limit exceeded returns HTTP 429 + RATE_LIMITED with Retry-After.

    Validates: Requirements 3.8
    """
    from api.rate_limiter import RateLimiterMiddleware
    from fastapi import FastAPI  # type: ignore[import-not-found]
    from starlette.requests import Request  # type: ignore[import-not-found]
    from starlette.responses import JSONResponse  # type: ignore[import-not-found]

    async def _run():
        # Create a fresh app with a very low rate limit
        test_app = FastAPI()
        test_app.add_middleware(
            RateLimiterMiddleware,
            max_requests=2,
            window_seconds=60,
        )

        @test_app.post("/api/predict")
        async def mock_predict(request: Request):
            return JSONResponse(
                status_code=200,
                content={"status": "success", "prediction": "mock"},
            )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=test_app),
            base_url="http://testserver",
        ) as client:
            # Use up the rate limit
            for _ in range(2):
                await client.post("/api/predict")

            # This request should be rate-limited
            response = await client.post("/api/predict")

        assert response.status_code == 429
        body = response.json()
        assert body["status"] == "error"
        assert body["error_code"] == "RATE_LIMITED"
        assert "message" in body

        # Verify Retry-After header
        retry_after = response.headers.get("retry-after")
        assert retry_after is not None, "Missing Retry-After header"
        assert int(retry_after) > 0

    asyncio.run(_run())


# --- Task 8.2: Health endpoint contract tests ---
# Requirements: 6.1, 6.2, 6.3, 6.4, 4.6


def test_health_ok_state():
    """Test health endpoint returns OK state when model is loaded.

    Validates: Requirements 6.1, 6.2, 6.4
    - status: "ok"
    - model_loaded: true
    - model_version: semantic version string
    - HTTP 200
    - Content-Type is application/json
    - Response contains exactly {status, model_loaded, model_version} fields
    """

    async def _run():
        with patch("api.routes.is_model_ready", return_value=True):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                response = await client.get("/api/health")

        # Assert HTTP 200
        assert response.status_code == 200

        # Assert Content-Type is application/json
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Expected Content-Type 'application/json', got '{content_type}'"
        )

        body = response.json()

        # Assert exactly the required fields are present
        assert set(body.keys()) == {"status", "model_loaded", "model_version"}

        # Assert correct values for OK state
        assert body["status"] == "ok"
        assert body["model_loaded"] is True
        assert body["model_version"] == settings.model_version

    asyncio.run(_run())


def test_health_degraded_state():
    """Test health endpoint returns degraded state when model is not loaded.

    Validates: Requirements 6.1, 6.3, 6.4
    - status: "degraded"
    - model_loaded: false
    - model_version: still present as a string
    - HTTP 200
    - Content-Type is application/json
    - Response contains exactly {status, model_loaded, model_version} fields
    """

    async def _run():
        with patch("api.routes.is_model_ready", return_value=False):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                response = await client.get("/api/health")

        # Assert HTTP 200
        assert response.status_code == 200

        # Assert Content-Type is application/json
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, (
            f"Expected Content-Type 'application/json', got '{content_type}'"
        )

        body = response.json()

        # Assert exactly the required fields are present
        assert set(body.keys()) == {"status", "model_loaded", "model_version"}

        # Assert correct values for degraded state
        assert body["status"] == "degraded"
        assert body["model_loaded"] is False
        assert isinstance(body["model_version"], str)
        assert len(body["model_version"]) > 0

    asyncio.run(_run())


def test_health_endpoint_not_rate_limited():
    """Test that the health endpoint is NOT subject to rate limiting.

    Validates: Requirements 4.6, 6.4
    - Send more requests than the rate limit allows
    - None should receive HTTP 429
    - All should return HTTP 200
    """

    async def _run():
        # Send more requests than the rate limit allows
        num_requests = settings.rate_limit_max_requests + 20

        with patch("api.routes.is_model_ready", return_value=True):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://testserver"
            ) as client:
                for i in range(num_requests):
                    response = await client.get("/api/health")
                    assert response.status_code == 200, (
                        f"Health request {i + 1} got status {response.status_code}, "
                        f"expected 200 (health should not be rate limited)"
                    )
                    body = response.json()
                    assert body["status"] == "ok"

    asyncio.run(_run())


# --- Task 8.3: Success response and no-localized-text tests ---


@pytest.mark.parametrize(
    ("disease_class", "scores"),
    [
        ("FMD", {"FMD": 0.944, "healthy": 0.056}),
        ("healthy", {"FMD": 0.056, "healthy": 0.944}),
    ],
)
def test_success_response_contains_all_required_fields(disease_class, scores):
    """Test both accepted classes return schema-valid HTTP 200 responses.

    Validates: Requirements 1.1, 7.1
    """

    async def _run():
        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.get_inference_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.predict.return_value = {
                **MOCK_SUCCESS_RESULT,
                "prediction": {
                    **MOCK_SUCCESS_RESULT["prediction"],
                    "disease_class": disease_class,
                    "display_label_key": f"disease.{disease_class.lower()}",
                    "scores": scores,
                },
            }
            mock_get_service.return_value = mock_service

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                jpeg_bytes = _create_test_jpeg()
                response = await client.post(
                    "/api/predict",
                    files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
                )

        assert response.status_code == 200
        data = response.json()
        validated = PredictResponse.model_validate(data)
        assert validated.prediction.disease_class.value == disease_class
        assert set(validated.prediction.scores) == {"FMD", "healthy"}
        assert "non_cattle" not in validated.prediction.scores

        # Verify all required top-level fields exist
        required_top_level = [
            "status",
            "prediction",
            "model_info",
            "processing_time_ms",
            "preprocessing_time_ms",
            "inference_time_ms",
        ]
        for field in required_top_level:
            assert field in data, f"Missing required top-level field: {field}"

        # Verify status is "success"
        assert data["status"] == "success"

        # Verify prediction object has all required sub-fields
        prediction = data["prediction"]
        required_prediction_fields = [
            "disease_class",
            "display_label_key",
            "confidence",
            "is_reliable",
            "scores",
        ]
        for field in required_prediction_fields:
            assert field in prediction, f"Missing prediction field: {field}"

        # Verify types
        assert isinstance(prediction["disease_class"], str)
        assert prediction["disease_class"] in ["FMD", "healthy"]
        assert isinstance(prediction["display_label_key"], str)
        assert isinstance(prediction["confidence"], float)
        assert 0.0 <= prediction["confidence"] <= 1.0
        assert isinstance(prediction["is_reliable"], bool)
        assert isinstance(prediction["scores"], dict)
        assert len(prediction["scores"]) == 2

        # Verify model_info
        assert "version" in data["model_info"]
        assert isinstance(data["model_info"]["version"], str)

        # Verify timing fields are non-negative integers
        assert isinstance(data["processing_time_ms"], int)
        assert isinstance(data["preprocessing_time_ms"], int)
        assert isinstance(data["inference_time_ms"], int)
        assert data["processing_time_ms"] >= 0
        assert data["preprocessing_time_ms"] >= 0
        assert data["inference_time_ms"] >= 0

    asyncio.run(_run())


def test_no_display_label_field_in_success_response():
    """Test no `display_label` field in any success response.

    The server must return only machine-readable keys (display_label_key),
    not localized display text (display_label).

    Validates: Requirements 2.1, 7.3
    """

    async def _run():
        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.get_inference_service") as mock_get_service,
        ):
            mock_service = MagicMock()
            mock_service.predict.return_value = MOCK_SUCCESS_RESULT
            mock_get_service.return_value = mock_service

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                jpeg_bytes = _create_test_jpeg()
                response = await client.post(
                    "/api/predict",
                    files={"image": ("test.jpg", jpeg_bytes, "image/jpeg")},
                )

        assert response.status_code == 200
        data = response.json()

        # Verify no display_label at top level
        assert "display_label" not in data, (
            "Found forbidden 'display_label' field at top level of response"
        )

        # Verify no display_label in prediction object
        assert "display_label" not in data["prediction"], (
            "Found forbidden 'display_label' field in prediction object"
        )

        # Verify display_label_key IS present (the correct field)
        assert "display_label_key" in data["prediction"], (
            "Missing required 'display_label_key' field in prediction"
        )

        # Recursively check no display_label anywhere in the response
        def _check_no_display_label(obj, path=""):
            if isinstance(obj, dict):
                assert "display_label" not in obj, (
                    f"Found 'display_label' at path: {path}"
                )
                for key, value in obj.items():
                    _check_no_display_label(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    _check_no_display_label(item, f"{path}[{i}]")

        _check_no_display_label(data, "response")

    asyncio.run(_run())


def test_rate_limit_configurable_via_env_vars():
    """Test rate limit is configurable via env vars.

    Setting RATE_LIMIT_MAX_REQUESTS and RATE_LIMIT_WINDOW_SECONDS
    environment variables should override the default rate limiter values.

    Validates: Requirements 4.4, 4.5
    """
    from api.rate_limiter import RateLimiterMiddleware
    from fastapi import FastAPI  # type: ignore[import-not-found]
    from starlette.requests import Request  # type: ignore[import-not-found]
    from starlette.responses import JSONResponse  # type: ignore[import-not-found]

    custom_max_requests = 3
    custom_window_seconds = 30

    async def _run():
        # Create a fresh app with custom rate limit values
        # (simulating what happens when env vars are set)
        test_app = FastAPI()
        test_app.add_middleware(
            RateLimiterMiddleware,
            max_requests=custom_max_requests,
            window_seconds=custom_window_seconds,
        )

        @test_app.post("/api/predict")
        async def mock_predict(request: Request):
            return JSONResponse(
                status_code=200,
                content={"status": "success", "prediction": "mock"},
            )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=test_app),
            base_url="http://testserver",
        ) as client:
            # Send custom_max_requests requests - all should succeed
            for i in range(custom_max_requests):
                response = await client.post("/api/predict")
                assert response.status_code == 200, (
                    f"Request {i + 1} of {custom_max_requests} was unexpectedly "
                    f"rejected with status {response.status_code}"
                )

            # The next request should be rate-limited
            response = await client.post("/api/predict")
            assert response.status_code == 429, (
                f"Request {custom_max_requests + 1} should be rate-limited "
                f"(429), got {response.status_code}"
            )

            body = response.json()
            assert body["error_code"] == "RATE_LIMITED"
            assert body["status"] == "error"

            # Verify Retry-After header is present
            retry_after = response.headers.get("retry-after")
            assert retry_after is not None, (
                "Expected 'Retry-After' header in 429 response"
            )
            retry_after_int = int(retry_after)
            assert retry_after_int > 0
            # Retry-After should be <= window_seconds
            assert retry_after_int <= custom_window_seconds, (
                f"Retry-After ({retry_after_int}) should not exceed "
                f"window_seconds ({custom_window_seconds})"
            )

    asyncio.run(_run())


def test_rate_limit_env_vars_loaded_in_config():
    """Test that config.py reads RATE_LIMIT_MAX_REQUESTS and
    RATE_LIMIT_WINDOW_SECONDS from environment variables.

    Validates: Requirements 4.4, 4.5
    """
    import os

    custom_max = "5"
    custom_window = "120"

    with patch.dict(
        os.environ,
        {
            "RATE_LIMIT_MAX_REQUESTS": custom_max,
            "RATE_LIMIT_WINDOW_SECONDS": custom_window,
        },
    ):
        # Re-import to pick up new env vars
        from config import Settings

        test_settings = Settings()

        assert test_settings.rate_limit_max_requests == int(custom_max), (
            f"Expected rate_limit_max_requests={custom_max}, "
            f"got {test_settings.rate_limit_max_requests}"
        )
        assert test_settings.rate_limit_window_seconds == int(custom_window), (
            f"Expected rate_limit_window_seconds={custom_window}, "
            f"got {test_settings.rate_limit_window_seconds}"
        )
