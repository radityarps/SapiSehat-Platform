"""Agency detection monitoring dashboard tracer tests."""

from uuid import uuid4
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from main import app
from tests.conftest import repo_text

client = TestClient(app)


def farmer_cattle(consent="agency_monitoring", jurisdiction_id="tembalang", tag="MON"):
    suffix = uuid4().hex[:8]
    farmer = client.post("/api/farmers/accounts", json={"phone_number": f"08555{suffix[:5]}", "name": "Monitor Farmer", "jurisdiction_id": jurisdiction_id, "consent_state": consent}).json()
    cattle_response = client.post(f"/api/farmers/{farmer['id']}/cattle", json={"tag": f"{tag}-{suffix}", "sex": "female", "breed": "sapi bali", "age_months": 20, "jurisdiction_id": jurisdiction_id})
    assert cattle_response.status_code == 200, cattle_response.text
    return farmer["id"], cattle_response.json()["id"]


def image(top_class="FMD", confidence=0.8):
    scores = {"FMD": confidence, "healthy": 1 - confidence}
    if top_class == "healthy":
        scores = {"FMD": 1 - confidence, "healthy": confidence}
    return {"source": "image", "model_version": "image-1", "inference_mode": "online", "disease_scores": scores, "top_class": top_class, "confidence": confidence, "quality_status": "accepted", "rejection_reasons": []}


def nlp(top_class="FMD", confidence=0.78):
    scores = {"FMD": confidence, "healthy": 1 - confidence}
    if top_class == "healthy":
        scores = {"FMD": 1 - confidence, "healthy": confidence}
    return {"source": "nlp", "model_version": "nlp-1", "inference_mode": "online", "questionnaire_answers": {"mouth_lesion": True}, "notes_present": False, "disease_scores": scores, "top_class": top_class, "confidence": confidence, "evidence_terms": ["mouth_lesion"]}


def create_fusion(farmer_id, cattle_id, image_top="FMD", nlp_top="FMD"):
    response = client.post("/api/fusion/results", json={"farmer_id": farmer_id, "cattle_id": cattle_id, "image_evidence": image(image_top), "nlp_evidence": nlp(nlp_top)})
    assert response.status_code == 200, response.text
    return response.json()


def test_detection_monitoring_lists_only_authorized_scope():
    allowed_farmer, allowed_cattle = farmer_cattle()
    outside_farmer, outside_cattle = farmer_cattle(jurisdiction_id="west-java", tag="OUT")
    allowed_result = create_fusion(allowed_farmer, allowed_cattle)
    outside_result = create_fusion(outside_farmer, outside_cattle)

    response = client.get("/api/agency/detection-monitoring", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200, response.text
    ids = {item["id"] for item in response.json()["detections"]}
    assert allowed_result["id"] in ids
    assert outside_result["id"] not in ids


def test_detection_monitoring_shows_conflict_and_evidence_breakdown():
    farmer_id, cattle_id = farmer_cattle(tag="CONFLICT")
    conflict = create_fusion(farmer_id, cattle_id, image_top="FMD", nlp_top="healthy")

    response = client.get("/api/agency/detection-monitoring", headers={"X-Agency-User-Id": "semarang-officer"})
    row = next(item for item in response.json()["detections"] if item["id"] == conflict["id"])

    assert row["conflict_status"] == "image_nlp_conflict"
    assert row["reliability"] == "needs_review"
    assert row["evidence_breakdown"]["image"]["source"] == "image"
    assert row["evidence_breakdown"]["nlp"]["source"] == "nlp"


def test_detection_monitoring_ui_uses_safe_language():
    source = repo_text("apps/dashboard/app/agency/detections/page.tsx")

    assert "Disease risk signals" in source
    assert "Risk signal" in source
    assert "Image/NLP breakdown" in source
    assert "confirmed diagnosis" not in source.lower().replace("not confirmed diagnosis", "")
    assert "confirmed outbreak" not in source.lower().replace("outbreak declaration", "")
    assert "diagnosis" not in source.lower().replace("not confirmed diagnosis", "")
