import asyncio
import io
from unittest.mock import MagicMock, patch

import httpx
from PIL import Image

from inference_server import InferenceService
from main import app


def _jpeg() -> bytes:
    image = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _result(label="FMD", confidence=0.91, reliable=True, debug=None, needs_review=False):
    prediction = {
        "disease_class": label,
        "display_label_key": "disease.fmd" if label == "FMD" else "disease.insufficient_visual_evidence",
        "confidence": confidence,
        "is_reliable": reliable,
        "scores": {"FMD": confidence, "LSD": 0.05, "healthy": 0.04},
        "outcome": "INSUFFICIENT_VISUAL_EVIDENCE" if label == "INSUFFICIENT_VISUAL_EVIDENCE" else "DISEASE_CLASS",
        "needs_review": needs_review,
    }
    if debug is not None:
        prediction["symptom_regions_debug"] = debug
    return {
        "status": "success",
        "prediction": prediction,
        "model_info": {"version": "test", "inference_pipeline": "two_stage_prototype"},
        "processing_time_ms": 10,
        "preprocessing_time_ms": 2,
        "inference_time_ms": 8,
    }


def test_two_stage_route_can_return_debug_regions_when_enabled():
    async def _run():
        debug = [{"x_min": 0.1, "y_min": 0.2, "x_max": 0.4, "y_max": 0.5, "confidence": 0.8, "symptom_region_type": "fmd_mouth_lesion"}]
        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.settings.two_stage_enabled", True),
            patch("api.routes.settings.two_stage_debug_regions_enabled", True),
            patch("api.routes.get_inference_service") as mock_get_service,
        ):
            service = MagicMock()
            service.predict_two_stage_prototype.return_value = _result(debug=debug)
            mock_get_service.return_value = service
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.post("/api/predict?two_stage=true&debug_regions=true", files={"image": ("a.jpg", _jpeg(), "image/jpeg")})
        assert response.status_code == 200
        data = response.json()
        assert data["model_info"]["inference_pipeline"] == "two_stage_prototype"
        assert data["prediction"]["symptom_regions_debug"][0]["symptom_region_type"] == "fmd_mouth_lesion"

    asyncio.run(_run())


def test_two_stage_contract_allows_insufficient_visual_evidence():
    async def _run():
        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.settings.two_stage_enabled", True),
            patch("api.routes.get_inference_service") as mock_get_service,
        ):
            service = MagicMock()
            service.predict_two_stage_prototype.return_value = _result(label="INSUFFICIENT_VISUAL_EVIDENCE", confidence=0.62, reliable=False)
            mock_get_service.return_value = service
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.post("/api/predict?two_stage=true", files={"image": ("a.jpg", _jpeg(), "image/jpeg")})
        assert response.status_code == 200
        prediction = response.json()["prediction"]
        assert prediction["disease_class"] == "INSUFFICIENT_VISUAL_EVIDENCE"
        assert prediction["is_reliable"] is False
        assert prediction["outcome"] == "INSUFFICIENT_VISUAL_EVIDENCE"

    asyncio.run(_run())


def test_two_stage_contract_allows_lowered_reliability_needs_review():
    async def _run():
        with (
            patch("api.routes.is_model_ready", return_value=True),
            patch("api.routes.settings.two_stage_enabled", True),
            patch("api.routes.get_inference_service") as mock_get_service,
        ):
            service = MagicMock()
            service.predict_two_stage_prototype.return_value = _result(reliable=False, needs_review=True)
            mock_get_service.return_value = service
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
                response = await client.post("/api/predict?two_stage=true", files={"image": ("a.jpg", _jpeg(), "image/jpeg")})
        assert response.status_code == 200
        prediction = response.json()["prediction"]
        assert prediction["disease_class"] == "FMD"
        assert prediction["needs_review"] is True
        assert prediction["is_reliable"] is False

    asyncio.run(_run())


def test_two_stage_prediction_policy_can_return_insufficient_evidence():
    service = InferenceService.__new__(InferenceService)
    service.LABELS = ["FMD", "LSD", "healthy"]
    service.FIELD_CONFIDENCE_THRESHOLD = 0.70
    service.FIELD_MARGIN_THRESHOLD = 0.15

    prediction = service.predict_two_stage_scores(__import__("numpy").array([0.62, 0.28, 0.10]))

    assert prediction["disease_class"] == "INSUFFICIENT_VISUAL_EVIDENCE"
    assert prediction["is_reliable"] is False
