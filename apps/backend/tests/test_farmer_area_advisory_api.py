"""Farmer area advisory must expose safe district-level signal only."""

from uuid import uuid4
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from main import app
from api.risk_signals import cluster_risk_signal_store
from api.surface_auth import DEFAULT_AGENCY_OFFICER_ID

client = TestClient(app)


def farmer_cattle(jurisdiction_id="tembalang", tag="ADV"):
    suffix = uuid4().hex[:8]
    farmer = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08888{suffix[:5]}",
            "name": "Advisory Farmer",
            "jurisdiction_id": jurisdiction_id,
            "consent_state": "agency_monitoring",
        },
    ).json()
    cattle = client.post(
        f"/api/farmers/{farmer['id']}/cattle",
        json={
            "tag": f"{tag}-{suffix}",
            "sex": "female",
            "breed": "sapi bali",
            "age_months": 18,
            "jurisdiction_id": jurisdiction_id,
        },
    )
    assert cattle.status_code == 200, cattle.text
    return farmer["id"], cattle.json()["id"]


def evidence(kind="image", disease="FMD", confidence=0.8):
    scores = {"FMD": confidence, "healthy": 1 - confidence}
    if disease == "healthy":
        scores = {"FMD": 1 - confidence, "healthy": confidence}
    if kind == "image":
        return {"source": "image", "model_version": "image-advisory", "inference_mode": "online", "disease_scores": scores, "top_class": disease, "confidence": confidence, "quality_status": "accepted", "rejection_reasons": []}
    return {"source": "nlp", "model_version": "nlp-advisory", "inference_mode": "online", "questionnaire_answers": {"mouth_lesion": True}, "notes_present": False, "disease_scores": scores, "top_class": disease, "confidence": confidence, "evidence_terms": ["mouth_lesion"]}


def create_signal(jurisdiction_id="tembalang", disease="FMD"):
    farmer_id, cattle_id = farmer_cattle(jurisdiction_id=jurisdiction_id)
    response = client.post("/api/fusion/results", json={"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": evidence("image", disease), "nlp_evidence": evidence("nlp", disease)})
    assert response.status_code == 200, response.text
    return farmer_id


def test_farmer_area_advisory_activates_for_farmer_district_cluster_without_identity_leakage():
    cluster_risk_signal_store.clear()
    farmer_id = create_signal()
    create_signal()
    create_signal()
    agency = client.get("/api/agency/risk-signals", headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID})
    assert agency.status_code == 200, agency.text

    response = client.get(f"/api/farmers/{farmer_id}/area-advisory")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["advisory_active"] is True
    assert body["jurisdiction_id"] == "tembalang"
    assert "Increased disease-risk reports in your district" in body["message"]
    assert body["signals"][0]["risk_level"] == "possible_increased_risk"
    serialized = str(body).lower()
    assert "advisory farmer" not in serialized
    assert "confirmed outbreak" not in serialized.replace("not confirmed outbreak", "")
    assert "confirmed diagnosis" not in serialized.replace("not confirmed diagnosis", "")


def test_farmer_area_advisory_inactive_without_cluster():
    cluster_risk_signal_store.clear()
    farmer_id, _ = farmer_cattle(jurisdiction_id="banyumanik")

    response = client.get(f"/api/farmers/{farmer_id}/area-advisory")

    assert response.status_code == 200, response.text
    assert response.json()["advisory_active"] is False
    assert response.json()["signals"] == []
