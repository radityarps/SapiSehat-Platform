"""Offline detection sync tracer tests."""

from uuid import uuid4
from fastapi.testclient import TestClient  # type: ignore[import-not-found]

from main import app
from api.database import SessionLocal
from api.db_models import OfflineSyncedDetectionModel, FusionResultModel
from api.cattle_profiles import cattle_profile_store
from api.farmer_accounts import farmer_account_store
from api.fusion_results import fusion_result_store
from api.offline_sync import offline_detection_sync_store

client = TestClient(app)

def setup_function():
    offline_detection_sync_store.clear()
    fusion_result_store.clear()
    cattle_profile_store.clear()
    farmer_account_store.clear()


def farmer_cattle():
    suffix = uuid4().hex[:8]
    farmer_response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": f"08222{suffix[:5]}", "name": "Offline Farmer", "jurisdiction_id": "district-bandung-1"},
    )
    assert farmer_response.status_code == 200, farmer_response.text
    farmer = farmer_response.json()
    cattle_response = client.post(
        f"/api/farmers/{farmer['id']}/cattle",
        json={"tag": f"OFF-{suffix}", "sex": "female", "breed": "sapi bali", "age_months": 24, "jurisdiction_id": "district-bandung-1"},
    )
    assert cattle_response.status_code == 200, cattle_response.text
    return farmer["id"], cattle_response.json()["id"]


def image():
    return {
        "source": "image",
        "model_version": "image-offline-1.0.0",
        "inference_mode": "offline",
        "disease_scores": {"healthy": 0.18, "FMD": 0.82},
        "top_class": "FMD",
        "confidence": 0.82,
        "quality_status": "accepted",
        "rejection_reasons": [],
    }



def sync_payload(local_id, farmer_id, cattle_id):
    return {
        "local_detection_id": local_id,
        "farmer_id": farmer_id,
        "cattle_id": cattle_id,
        "local_created_at": "2026-06-05T08:30:00+07:00",
        "image_evidence": image(),
        "nlp_evidence": None,
        "offline_fused_result": {"disease_class": "FMD", "confidence": 0.8},
    }


def test_first_sync_preserves_local_id_versions_and_timestamp():
    farmer_id, cattle_id = farmer_cattle()
    local_id = f"local-{uuid4().hex}"

    response = client.post("/api/offline/detections/sync", json=sync_payload(local_id, farmer_id, cattle_id))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["local_detection_id"] == local_id
    assert body["sync_status"] == "synced"
    assert body["local_created_at"] == "2026-06-05T08:30:00+07:00"
    assert body["fusion_result"]["inference_mode"] == "synced_offline"
    assert body["fusion_result"]["model_versions"] == {"image": "image-offline-1.0.0", "nlp": "missing"}
    assert body["fusion_result"]["evidence_breakdown"]["image"]["inference_mode"] == "offline"
    with SessionLocal() as session:
        assert session.query(OfflineSyncedDetectionModel).count() == 1
        assert session.query(FusionResultModel).count() == 1


def test_duplicate_sync_is_idempotent_for_stable_local_identifier():
    farmer_id, cattle_id = farmer_cattle()
    local_id = f"local-{uuid4().hex}"
    payload = sync_payload(local_id, farmer_id, cattle_id)

    first = client.post("/api/offline/detections/sync", json=payload).json()
    second = client.post("/api/offline/detections/sync", json=payload).json()

    assert second["local_detection_id"] == first["local_detection_id"]
    assert second["fusion_result"]["id"] == first["fusion_result"]["id"]
    assert second["synced_at"] == first["synced_at"]


def test_malformed_offline_evidence_is_rejected():
    farmer_id, cattle_id = farmer_cattle()
    payload = sync_payload(f"local-{uuid4().hex}", farmer_id, cattle_id)
    payload["image_evidence"]["disease_scores"]["LSD"] = 0.0

    response = client.post("/api/offline/detections/sync", json=payload)

    assert response.status_code == 422
    assert "disease_scores" in response.text
