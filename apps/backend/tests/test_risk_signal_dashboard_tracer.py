"""Disease risk signal dashboard tracer tests."""

from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from tests.conftest import repo_text

client = TestClient(app)


def farmer_cattle(jurisdiction_id="tembalang", tag="RISK"):
    suffix = uuid4().hex[:8]
    farmer = client.post("/api/farmers/accounts", json={"phone_number": f"08666{suffix[:5]}", "name": "Risk Farmer", "jurisdiction_id": jurisdiction_id, "consent_state": "agency_monitoring"}).json()
    cattle_response = client.post(f"/api/farmers/{farmer['id']}/cattle", json={"tag": f"{tag}-{suffix}", "sex": "female", "breed": "sapi bali", "age_months": 22, "jurisdiction_id": jurisdiction_id})
    assert cattle_response.status_code == 200, cattle_response.text
    return farmer["id"], cattle_response.json()["id"]


def evidence(kind="image", disease="FMD", confidence=0.8):
    scores = {"healthy": 0.1, "FMD": confidence if disease == "FMD" else 0.1, "LSD": confidence if disease == "LSD" else 0.1}
    if kind == "image":
        return {"source": "image", "model_version": "image-risk", "inference_mode": "online", "disease_scores": scores, "top_class": disease, "confidence": confidence, "quality_status": "accepted", "rejection_reasons": []}
    return {"source": "nlp", "model_version": "nlp-risk", "inference_mode": "online", "questionnaire_answers": {"mouth_lesion": True}, "notes_present": False, "disease_scores": scores, "top_class": disease, "confidence": confidence, "evidence_terms": ["mouth_lesion"]}


def create_signal(jurisdiction_id="tembalang", disease="FMD"):
    farmer_id, cattle_id = farmer_cattle(jurisdiction_id=jurisdiction_id)
    response = client.post("/api/fusion/results", json={"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": evidence("image", disease), "nlp_evidence": evidence("nlp", disease)})
    assert response.status_code == 200, response.text
    return response.json()


def test_three_signal_threshold_marks_possible_increased_risk():
    create_signal()
    create_signal()
    create_signal()

    response = client.get("/api/agency/risk-signals", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200, response.text
    body = response.json()
    signal = next(item for item in body["signals"] if item["jurisdiction_id"] == "tembalang" and item["disease_class"] == "FMD")
    assert signal["signal_count"] >= 3
    assert signal["risk_level"] == "possible_increased_risk"
    assert signal["priority"] == "follow_up_priority"
    assert signal["id"].startswith("cluster-risk-")
    assert len(signal["source_result_ids"]) >= 3
    assert body["rule"]["threshold_count"] == 3
    assert body["rule"]["window_days"] == 7


def test_risk_signal_summary_filters_out_unauthorized_jurisdiction():
    create_signal(jurisdiction_id="west-java", disease="LSD")

    response = client.get("/api/agency/risk-signals", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200, response.text
    assert all(item["jurisdiction_id"] != "west-java" for item in response.json()["signals"])


def test_risk_signal_dashboard_uses_safe_wording():
    source = repo_text("apps/dashboard/app/agency/risk-signals/page.tsx").lower()

    assert "possible increased risk" in source
    assert "follow-up priority" in source
    assert "not confirmed outbreak" in source
    assert "not veterinary diagnosis" in source
