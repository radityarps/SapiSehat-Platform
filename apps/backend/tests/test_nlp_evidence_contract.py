"""Team 2 NLP evidence contract tracer tests."""

from pydantic import ValidationError
from fastapi.testclient import TestClient

from main import app
from api.schemas import NlpEvidenceRequest


def valid_payload(**overrides):
    payload = {
        "source": "nlp",
        "model_version": "nlp-model-1.0.0",
        "inference_mode": "online",
        "questionnaire_answers": {"mouth_lesion": True, "skin_nodule": False},
        "notes_present": True,
        "disease_scores": {"healthy": 0.1, "FMD": 0.75, "LSD": 0.15},
        "top_class": "FMD",
        "confidence": 0.75,
        "evidence_terms": ["mouth_lesion", "fever"],
        "debug": {"token_count": 12},
    }
    payload.update(overrides)
    return payload


def test_valid_nlp_evidence_contract_accepts_questionnaire_notes_and_metadata():
    evidence = NlpEvidenceRequest(**valid_payload())

    assert evidence.source == "nlp"
    assert evidence.model_version == "nlp-model-1.0.0"
    assert evidence.inference_mode == "online"
    assert evidence.questionnaire_answers["mouth_lesion"] is True
    assert evidence.notes_present is True
    assert evidence.disease_scores == {"healthy": 0.1, "FMD": 0.75, "LSD": 0.15}
    assert evidence.top_class == "FMD"
    assert evidence.evidence_terms == ["mouth_lesion", "fever"]


def test_nlp_evidence_rejects_missing_disease_score_key():
    payload = valid_payload(disease_scores={"healthy": 0.2, "FMD": 0.8})

    try:
        NlpEvidenceRequest(**payload)
    except ValidationError as exc:
        assert "disease_scores must contain exactly healthy, FMD, and LSD" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_nlp_evidence_rejects_top_class_mismatch():
    payload = valid_payload(top_class="LSD")

    try:
        NlpEvidenceRequest(**payload)
    except ValidationError as exc:
        assert "top_class must match highest disease score" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_nlp_evidence_requires_questionnaire_or_notes():
    payload = valid_payload(questionnaire_answers={}, notes_present=False)

    try:
        NlpEvidenceRequest(**payload)
    except ValidationError as exc:
        assert "questionnaire_answers or notes_present is required" in str(exc)
    else:
        raise AssertionError("Expected ValidationError")


def test_nlp_evidence_endpoint_accepts_offline_mode_for_mobile_fusion():
    client = TestClient(app)
    payload = valid_payload(inference_mode="offline", notes_present=False)

    response = client.post("/api/evidence/nlp", json=payload)

    assert response.status_code == 200
    assert response.json()["inference_mode"] == "offline"
    assert response.json()["accepted_for_fusion"] is True


def test_nlp_evidence_endpoint_accepts_notes_only_input():
    client = TestClient(app)
    payload = valid_payload(questionnaire_answers={}, notes_present=True)

    response = client.post("/api/evidence/nlp", json=payload)

    assert response.status_code == 200
    assert response.json()["questionnaire_answers"] == {}
    assert response.json()["notes_present"] is True
