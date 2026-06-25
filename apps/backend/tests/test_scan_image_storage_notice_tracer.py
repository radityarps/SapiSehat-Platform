"""Scan image storage notice gate tracer tests."""

from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from api.farmer_accounts import farmer_account_store
from api.media_governance import media_store

client = TestClient(app)


def create_farmer(consent_state="research_and_monitoring"):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08777{suffix[:5]}",
            "name": "Notice Farmer",
            "jurisdiction_id": "tembalang",
            "consent_state": consent_state,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def media_payload(farmer_id: str):
    return {
        "farmer_id": farmer_id,
        "cattle_id": None,
        "detection_id": "detection-notice-1",
        "checksum": f"sha256-{uuid4().hex}",
        "consent_scope": "research_and_monitoring",
        "storage_reference": f"s3://sapisehat-dev/{uuid4().hex}.jpg",
    }


def test_media_storage_requires_first_scan_notice_acceptance():
    media_store.clear()
    farmer = create_farmer()

    rejected = client.post("/api/media", json=media_payload(farmer["id"]))

    assert rejected.status_code == 403
    assert rejected.json()["message"] == "Scan image storage notice must be accepted before storing media"

    accepted = client.post(f"/api/farmers/{farmer['id']}/scan-image-storage-notice", json={"accepted": True})

    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["scan_image_storage_notice_accepted"] is True

    stored = client.post("/api/media", json=media_payload(farmer["id"]))

    assert stored.status_code == 200, stored.text
    assert stored.json()["farmer_id"] == farmer["id"]


def test_notice_acceptance_persists_for_existing_farmer_account():
    farmer_account_store.clear()
    farmer = create_farmer()

    client.post(f"/api/farmers/{farmer['id']}/scan-image-storage-notice", json={"accepted": True})

    loaded = client.get(f"/api/farmers/{farmer['id']}/scan-image-storage-notice")

    assert loaded.status_code == 200, loaded.text
    assert loaded.json() == {"farmer_id": farmer["id"], "scan_image_storage_notice_accepted": True}
