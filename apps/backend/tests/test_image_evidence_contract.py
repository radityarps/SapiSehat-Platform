"""Team 1 image evidence contract tracer tests."""

import pytest  # type: ignore[import-not-found]
from pydantic import ValidationError  # type: ignore[import-not-found]
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from main import app
from api.schemas import ImageEvidenceRequest


def valid_payload(**overrides):
    payload = {
        "source": "image",
        "model_version": "image-model-1.0.0",
        "inference_mode": "online",
        "disease_scores": {"healthy": 0.1, "FMD": 0.9},
        "top_class": "FMD",
        "confidence": 0.9,
        "quality_status": "accepted",
        "rejection_reasons": [],
        "debug": {"preprocessing": "rgb_224_bilinear"},
    }
    payload.update(overrides)
    return payload


def test_valid_image_evidence_contract_accepts_only_active_scores():
    evidence = ImageEvidenceRequest(**valid_payload())

    assert evidence.source == "image"
    assert evidence.model_version == "image-model-1.0.0"
    assert evidence.inference_mode == "online"
    assert evidence.disease_scores == {"healthy": 0.1, "FMD": 0.9}
    assert evidence.top_class == "FMD"
    assert evidence.confidence == 0.9
    assert evidence.quality_status == "accepted"


def test_image_evidence_rejects_missing_or_retired_score_key():
    for scores in ({"healthy": 0.1}, {"healthy": 0.1, "FMD": 0.8, "LSD": 0.1}):
        try:
            ImageEvidenceRequest(**valid_payload(disease_scores=scores))
        except ValidationError as exc:
            assert "disease_scores must contain exactly healthy and FMD" in str(exc)
        else:
            raise AssertionError("Expected ValidationError")


def test_image_evidence_rejects_non_cattle_top_class():
    with pytest.raises(ValidationError):
        ImageEvidenceRequest(
            **valid_payload(
                disease_scores={"healthy": 0.1, "FMD": 0.1, "non_cattle": 0.8},
                top_class="non_cattle",
                confidence=0.8,
            )
        )


def test_image_evidence_rejects_confidence_not_matching_top_score():
    with pytest.raises(ValidationError, match="confidence must match"):
        ImageEvidenceRequest(**valid_payload(confidence=0.8))


def test_rejected_image_evidence_requires_reason_and_marks_not_for_fusion():
    client = TestClient(app)
    payload = valid_payload(
        disease_scores={"healthy": 0.34, "FMD": 0.66},
        top_class="FMD",
        confidence=0.66,
        quality_status="rejected",
        rejection_reasons=["too_blurry"],
    )

    response = client.post("/api/evidence/image", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["quality_status"] == "rejected"
    assert body["accepted_for_fusion"] is False


def test_rejected_image_evidence_without_reason_is_invalid():
    try:
        ImageEvidenceRequest(**valid_payload(quality_status="rejected"))
    except ValidationError as exc:
        assert "rejected image evidence requires rejection_reasons" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_image_evidence_endpoint_accepts_offline_mode_for_mobile_fusion():
    client = TestClient(app)
    response = client.post(
        "/api/evidence/image", json=valid_payload(inference_mode="offline")
    )

    assert response.status_code == 200
    assert response.json()["inference_mode"] == "offline"
    assert response.json()["accepted_for_fusion"] is True
