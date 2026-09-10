"""Core inference service - NO FastAPI/HTTP coupling."""

import time
from typing import Any

import numpy as np  # type: ignore[import-not-found]
from PIL import Image

from config import (
    ACTIVE_DETECTION_CLASSES,
    MODEL_CLASS_ORDER,
    MODEL_LABEL_MAPPING,
    settings,
)
from model.loader import ModelLoader
from preprocessing.model_preprocessor import ModelPreprocessor
from utils.errors import InferenceError, NonCattleImageError
from utils.logger import get_logger

logger = get_logger(__name__)

DISPLAY_LABEL_KEY_MAP = {
    "FMD": "disease.fmd",
    "healthy": "disease.healthy",
    "non_cattle": "rejection.non_cattle",
    "INSUFFICIENT_VISUAL_EVIDENCE": "disease.insufficient_visual_evidence",
}

INSUFFICIENT_VISUAL_EVIDENCE = "INSUFFICIENT_VISUAL_EVIDENCE"


class InferenceService:
    """
    Pure inference logic with NO HTTP/FastAPI coupling.
    Can be called from FastAPI, Go, or any other framework.

    Designed for easy migration to Go + Python microservice architecture.
    """

    CONFIDENCE_THRESHOLD = settings.confidence_threshold  # 0.60
    FIELD_CONFIDENCE_THRESHOLD = settings.field_confidence_threshold
    FIELD_MARGIN_THRESHOLD = settings.field_margin_threshold

    def __init__(self):
        """Initialize inference service with singleton model loader."""
        self.model_loader = ModelLoader(settings.model_path)
        # Labels come from the verified raw artifact contract.
        self.LABELS = list(self.model_loader.class_names)
        if tuple(self.LABELS) != tuple(settings.labels):
            raise InferenceError(
                "Loaded model class order does not match active settings"
            )
        self.preprocessor = ModelPreprocessor()
        logger.info("InferenceService initialized")

    def _as_probabilities(self, output: np.ndarray) -> np.ndarray:
        try:
            values = np.asarray(output)
            if values.dtype != np.dtype(np.float32):
                raise InferenceError("Model output tensor must be float32")
            if values.shape != (1, 3):
                raise InferenceError(
                    "Model output must be one float32 tensor with shape [1, 3]"
                )
            values = values[0]
            if not np.all(np.isfinite(values)):
                raise InferenceError("Model output contains non-finite probabilities")
            if np.any(values < 0.0) or np.any(values > 1.0):
                raise InferenceError("Model output probabilities must be in [0, 1]")
            if not np.isclose(float(values.sum()), 1.0, atol=1e-3):
                raise InferenceError("Model output probabilities must sum to 1")
            return values
        except InferenceError:
            raise
        except (TypeError, ValueError, OverflowError) as exc:
            raise InferenceError("Model output could not be validated") from exc

    def _top_margin(self, scores: dict[str, float]) -> float:
        try:
            values = sorted(scores.values(), reverse=True)
            if len(values) < 2:
                return 0.0
            return float(values[0] - values[1])
        except (TypeError, ValueError, OverflowError) as exc:
            raise InferenceError("Prediction scores could not be ranked") from exc

    def _build_prediction(
        self,
        probs: np.ndarray,
        *,
        symptom_regions_debug: list[dict[str, Any]] | None = None,
        needs_review: bool = False,
        apply_field_policy: bool = False,
    ) -> dict[str, Any]:
        try:
            if tuple(self.LABELS) != tuple(MODEL_CLASS_ORDER):
                raise InferenceError("Active model class order is invalid")
            pred_idx = int(np.argmax(probs))
            raw_label = self.LABELS[pred_idx]
            pred_label = MODEL_LABEL_MAPPING[raw_label]
            if pred_label == "non_cattle":
                raise NonCattleImageError(
                    "Image was rejected because it is not a cattle image"
                )
            raw_scores = dict(zip(self.LABELS, probs, strict=True))
            canonical_scores = {
                MODEL_LABEL_MAPPING[label]: float(score)
                for label, score in raw_scores.items()
            }
            active_total = sum(
                canonical_scores[label] for label in ACTIVE_DETECTION_CLASSES
            )
            if active_total <= 0:
                raise InferenceError(
                    "Active model probabilities must have positive mass"
                )
            scores = {
                label: canonical_scores[label] / active_total
                for label in ACTIVE_DETECTION_CLASSES
            }
            pred_confidence = scores[pred_label]
            margin = self._top_margin(scores)
            is_insufficient = apply_field_policy and (
                pred_confidence < self.FIELD_CONFIDENCE_THRESHOLD
                or margin < self.FIELD_MARGIN_THRESHOLD
            )
            final_label = (
                INSUFFICIENT_VISUAL_EVIDENCE if is_insufficient else pred_label
            )
            prediction = {
                "disease_class": final_label,
                "display_label_key": DISPLAY_LABEL_KEY_MAP[final_label],
                "confidence": round(pred_confidence, 4),
                "is_reliable": (not is_insufficient) and (not needs_review),
                "scores": scores,
                "outcome": "INSUFFICIENT_VISUAL_EVIDENCE"
                if is_insufficient
                else "DISEASE_CLASS",
                "needs_review": needs_review,
            }
            if symptom_regions_debug is not None:
                prediction["symptom_regions_debug"] = symptom_regions_debug
            return prediction
        except (InferenceError, NonCattleImageError):
            raise
        except (TypeError, ValueError, IndexError, OverflowError) as exc:
            raise InferenceError("Prediction output could not be mapped") from exc

    def predict(self, image: Image.Image) -> dict[str, Any]:
        """
        Pure inference - NO HTTP logic.

        Args:
            image: PIL Image in RGB format

        Returns:
            Dict with prediction results
        """
        start_time = time.time()

        try:
            # Preprocessing: Convert image to numpy array
            image_array = self.preprocessor.process(image)

            preprocessing_ms = max(1, int((time.time() - start_time) * 1000))
            infer_start = time.time()

            # Inference (TensorFlow/Keras)
            output = self.model_loader.predict(image_array)
            probs = self._as_probabilities(output)

            inference_ms = max(1, int((time.time() - infer_start) * 1000))
            total_ms = max(1, int((time.time() - start_time) * 1000))

            prediction = self._build_prediction(probs)
            pred_label = prediction["disease_class"]
            pred_confidence = prediction["confidence"]

            # Log inference
            logger.info(
                f"Inference: {pred_label} ({pred_confidence:.2%}) "
                f"preprocessing={preprocessing_ms}ms, "
                f"inference={inference_ms}ms, "
                f"total={total_ms}ms"
            )

            # Build response
            result = {
                "status": "success",
                "prediction": {**prediction},
                "model_info": {"version": settings.model_version},
                "processing_time_ms": total_ms,
                "preprocessing_time_ms": preprocessing_ms,
                "inference_time_ms": inference_ms,
            }

            return result

        except NonCattleImageError:
            raise
        except Exception as e:
            logger.exception("Inference failed: %s", e)
            return {
                "status": "error",
                "message": str(e),
                "processing_time_ms": max(1, int((time.time() - start_time) * 1000)),
            }

    def predict_two_stage_prototype(
        self, image: Image.Image, *, include_debug_regions: bool = False
    ) -> dict[str, Any]:
        """Server-only two-stage prototype boundary.

        Current implementation preserves single-stage classifier behavior while
        exposing optional developer-only symptom-region debug structure for
        configured experiments. Android TFLite fallback remains unchanged.
        """
        result = self.predict(image)
        if result.get("status") != "success":
            return result
        result["model_info"]["inference_pipeline"] = "two_stage_prototype"
        if include_debug_regions:
            result["prediction"]["symptom_regions_debug"] = []
        return result

    def predict_two_stage_scores(
        self,
        probs: np.ndarray,
        *,
        symptom_regions_debug: list[dict[str, Any]] | None = None,
        needs_review: bool = False,
    ) -> dict[str, Any]:
        """Build two-stage prototype prediction from fused scores."""
        return self._build_prediction(
            probs,
            symptom_regions_debug=symptom_regions_debug,
            needs_review=needs_review,
            apply_field_policy=True,
        )


_service_init_error: str | None = None

# Singleton instance - try to load model once on module import.
# If model is missing, keep app bootable in degraded mode.
try:
    inference_service: InferenceService | None = InferenceService()
except Exception as e:  # noqa: BLE001 - startup must degrade on any model failure.
    inference_service = None
    _service_init_error = str(e)
    logger.warning(
        "Inference service unavailable at startup. "
        "API will run in degraded mode until model is provided.",
        extra={"model_path": settings.model_path, "error": _service_init_error},
    )


def is_model_ready() -> bool:
    """Return True only when the verified inference service is loaded."""
    return inference_service is not None


def get_inference_service() -> InferenceService:
    """Return active inference service or raise a clear error when unavailable."""
    if inference_service is None:
        error_message = _service_init_error or "Model service not initialized"
        raise InferenceError(
            f"Model not loaded. Expected file at '{settings.model_path}'. "
            f"Startup error: {error_message}"
        )
    return inference_service


def get_model_status() -> dict[str, Any]:
    """Expose model readiness details for health endpoint."""
    return {
        "model_loaded": inference_service is not None,
        "model_path": settings.model_path,
        "model_version": settings.model_version,
        "class_order": list(settings.labels),
        "error": _service_init_error,
    }
