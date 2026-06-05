"""Team 1 image evidence contract tracer tests."""

from pydantic import ValidationError
from fastapi.testclient import TestClient

from main import app
from api.schemas import ImageEvidenceRequest


def valid_payload(**overrides):
    payload = {
        "source": "image",
        "model_version": "image-model-1.0.0",
        "inference_mode": "online",
        "disease_scores": {"healthy": 0.1, "FMD": 0.8, "LSD": 0.1},
        "top_class": "FMD",
        "confidence": 0.8,
        "quality_status": "accepted",
        "rejection_reasons": [],
        "debug": {"preprocessing": "center_crop"},
    }
    payload.update(overrides)
    return payload


def test_valid_image_evidence_contract_accepts_required_scores_and_metadata():
    evidence = ImageEvidenceRequest(**valid_payload())

    assert evidence.source == "image"
    assert evidence.model_version == "image-model-1.0.0"
    assert evidence.inference_mode == "online"
    assert evidence.disease_scores == {"healthy": 0.1, "FMD": 0.8, "LSD": 0.1}
    assert evidence.top_class == "FMD"
    assert evidence.confidence == 0.8
    assert evidence.quality_status == "accepted"


def test_image_evidence_rejects_missing_disease_score_key():
    payload = valid_payload(disease_scores={"healthy": 0.2, "FMD": 0.8})

    try:
        ImageEvidenceRequest(**payload)
    except ValidationError as exc:
        assert "disease_scores must contain exactly healthy, FMD, and LSD" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_image_evidence_rejects_top_class_mismatch():
    payload = valid_payload(top_class="LSD")

    try:
        ImageEvidenceRequest(**payload)
    except ValidationError as exc:
        assert "top_class must match highest disease score" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_rejected_image_evidence_requires_rejection_reason_and_marks_not_for_fusion():
    client = TestClient(app)
    payload = valid_payload(
        disease_scores={"healthy": 0.34, "FMD": 0.33, "LSD": 0.33},
        top_class="healthy",
        confidence=0.34,
        quality_status="rejected",
        rejection_reasons=["too_blurry"],
    )

    response = client.post("/api/evidence/image", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["quality_status"] == "rejected"
    assert body["rejection_reasons"] == ["too_blurry"]
    assert body["accepted_for_fusion"] is False


def test_rejected_image_evidence_without_reason_is_invalid():
    payload = valid_payload(quality_status="rejected", rejection_reasons=[])

    try:
        ImageEvidenceRequest(**payload)
    except ValidationError as exc:
        assert "rejected image evidence requires rejection_reasons" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_image_evidence_endpoint_accepts_offline_mode_for_mobile_fusion():
    client = TestClient(app)
    payload = valid_payload(inference_mode="offline")

    response = client.post("/api/evidence/image", json=payload)

    assert response.status_code == 200
    assert response.json()["inference_mode"] == "offline"
    assert response.json()["accepted_for_fusion"] is True
