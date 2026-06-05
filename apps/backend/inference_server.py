"""Core inference service - NO FastAPI/HTTP coupling."""

import numpy as np
import time
from typing import Dict, Any, Optional
from PIL import Image
from config import settings
from model.loader import ModelLoader
from preprocessing.model_preprocessor import ModelPreprocessor
from utils.errors import InferenceError
from utils.logger import get_logger

logger = get_logger(__name__)

DISPLAY_LABEL_KEY_MAP = {
    "FMD": "disease.fmd",
    "LSD": "disease.lsd",
    "healthy": "disease.healthy",
    "INSUFFICIENT_VISUAL_EVIDENCE": "disease.insufficient_visual_evidence",
}

INSUFFICIENT_VISUAL_EVIDENCE = "INSUFFICIENT_VISUAL_EVIDENCE"


class InferenceService:
    """
    Pure inference logic with NO HTTP/FastAPI coupling.
    Can be called from FastAPI, Go, or any other framework.
    
    Designed for easy migration to Go + Python microservice architecture.
    """
    
    # Labels from config
    LABELS = settings.labels  # ["FMD", "LSD", "healthy"]
    CONFIDENCE_THRESHOLD = settings.confidence_threshold  # 0.60
    FIELD_CONFIDENCE_THRESHOLD = settings.field_confidence_threshold
    FIELD_MARGIN_THRESHOLD = settings.field_margin_threshold
    
    def __init__(self):
        """Initialize inference service with singleton model loader."""
        self.model_loader = ModelLoader(settings.model_path)
        self.preprocessor = ModelPreprocessor()
        logger.info("InferenceService initialized")

    def _top_margin(self, scores: Dict[str, float]) -> float:
        values = sorted(scores.values(), reverse=True)
        if len(values) < 2:
            return 0.0
        return float(values[0] - values[1])

    def _build_prediction(
        self,
        probs: np.ndarray,
        *,
        symptom_regions_debug: Optional[list[Dict[str, Any]]] = None,
        needs_review: bool = False,
        apply_field_policy: bool = False,
    ) -> Dict[str, Any]:
        pred_idx = int(np.argmax(probs))
        pred_label = self.LABELS[pred_idx]
        pred_confidence = float(probs[pred_idx])
        scores = {
            self.LABELS[i]: round(float(probs[i]), 4)
            for i in range(len(self.LABELS))
        }
        margin = self._top_margin(scores)
        is_insufficient = (
            apply_field_policy
            and (
                pred_confidence < self.FIELD_CONFIDENCE_THRESHOLD
                or margin < self.FIELD_MARGIN_THRESHOLD
            )
        )
        final_label = INSUFFICIENT_VISUAL_EVIDENCE if is_insufficient else pred_label
        prediction = {
            "disease_class": final_label,
            "display_label_key": DISPLAY_LABEL_KEY_MAP[final_label],
            "confidence": round(pred_confidence, 4),
            "is_reliable": (not is_insufficient) and (not needs_review),
            "scores": scores,
            "outcome": "INSUFFICIENT_VISUAL_EVIDENCE" if is_insufficient else "DISEASE_CLASS",
            "needs_review": needs_review,
        }
        if symptom_regions_debug is not None:
            prediction["symptom_regions_debug"] = symptom_regions_debug
        return prediction
    
    def predict(self, image: Image.Image) -> Dict[str, Any]:
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
            
            preprocessing_ms = int((time.time() - start_time) * 1000)
            infer_start = time.time()
            
            # Inference (TensorFlow/Keras)
            output = self.model_loader.predict(image_array)
            # Softmax with numpy
            exp = np.exp(output[0] - np.max(output[0]))
            probs = exp / exp.sum()
            
            inference_ms = int((time.time() - infer_start) * 1000)
            total_ms = int((time.time() - start_time) * 1000)
            
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
                "prediction": {
                    **prediction
                },
                "model_info": {
                    "version": settings.model_version
                },
                "processing_time_ms": total_ms,
                "preprocessing_time_ms": preprocessing_ms,
                "inference_time_ms": inference_ms,
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }

    def predict_two_stage_prototype(self, image: Image.Image, *, include_debug_regions: bool = False) -> Dict[str, Any]:
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
        symptom_regions_debug: Optional[list[Dict[str, Any]]] = None,
        needs_review: bool = False,
    ) -> Dict[str, Any]:
        """Build two-stage prototype prediction from fused scores."""
        return self._build_prediction(
            probs,
            symptom_regions_debug=symptom_regions_debug,
            needs_review=needs_review,
            apply_field_policy=True,
        )
    

_service_init_error: Optional[str] = None

# Singleton instance - try to load model once on module import.
# If model is missing, keep app bootable in degraded mode.
try:
    inference_service: Optional[InferenceService] = InferenceService()
except Exception as e:
    inference_service = None
    _service_init_error = str(e)
    logger.warning(
        "Inference service unavailable at startup. "
        "API will run in degraded mode until model is provided.",
        extra={"model_path": settings.model_path, "error": _service_init_error}
    )


def is_model_ready() -> bool:
    """Return True when inference model is loaded and ready."""
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


def get_model_status() -> Dict[str, Any]:
    """Expose model readiness details for health endpoint."""
    return {
        "model_loaded": inference_service is not None,
        "model_path": settings.model_path,
        "error": _service_init_error,
    }
