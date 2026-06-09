"""Stored media governance tracer tests."""

from uuid import uuid4
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def farmer(consent="research_and_monitoring", jurisdiction_id="tembalang"):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": f"08333{suffix[:5]}", "name": "Media Farmer", "jurisdiction_id": jurisdiction_id, "consent_state": consent},
    )
    assert response.status_code == 200, response.text
    return response.json()


def cattle(farmer_id):
    response = client.post(
        f"/api/farmers/{farmer_id}/cattle",
        json={"tag": f"MEDIA-{uuid4().hex[:6]}", "sex": "female", "breed": "sapi bali", "age_months": 30, "jurisdiction_id": "tembalang"},
    )
    assert response.status_code == 200, response.text
    return response.json()

def accept_notice(farmer_id):
    response = client.post(f"/api/farmers/{farmer_id}/scan-image-storage-notice", json={"accepted": True})
    assert response.status_code == 200, response.text


def media_payload(farmer_id, cattle_id=None):
    return {
        "farmer_id": farmer_id,
        "cattle_id": cattle_id,
        "detection_id": "detection-local-1",
        "checksum": "sha256:abcdef1234567890",
        "consent_scope": "research_and_monitoring",
        "storage_reference": "media://bucket/object.jpg",
        "content_type": "image/jpeg",
        "byte_size": 128000,
        "retention_policy": "first_release_monitoring",
    }


def test_allowed_media_access_for_authorized_agency():
    f = farmer()
    c = cattle(f["id"])
    accept_notice(f["id"])
    create = client.post("/api/media", json=media_payload(f["id"], c["id"]))
    assert create.status_code == 200, create.text

    response = client.get(f"/api/agency/media/{create.json()['id']}", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["farmer_id"] == f["id"]
    assert body["cattle_id"] == c["id"]
    assert body["checksum"] == "sha256:abcdef1234567890"
    assert body["consent_scope"] == "research_and_monitoring"
    assert body["storage_reference"] == "media://bucket/object.jpg"
    assert body["content_type"] == "image/jpeg"
    assert body["byte_size"] == 128000
    assert body["retention_policy"] == "first_release_monitoring"
    assert "created_at" in body


def test_denied_media_access_for_wrong_jurisdiction():
    f = farmer(jurisdiction_id="west-java")
    accept_notice(f["id"])
    create = client.post("/api/media", json=media_payload(f["id"]))
    assert create.status_code == 200, create.text

    response = client.get(f"/api/agency/media/{create.json()['id']}", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 403


def test_denied_media_storage_without_required_consent():
    f = farmer(consent="agency_monitoring")
    accept_notice(f["id"])

    response = client.post("/api/media", json=media_payload(f["id"]))

    assert response.status_code == 403
    assert "research_and_monitoring" in response.text


def test_missing_media_returns_404():
    response = client.get("/api/agency/media/media-missing", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 404

def test_media_storage_rejects_non_image_content_type():
    f = farmer()
    accept_notice(f["id"])
    payload = media_payload(f["id"])
    payload["content_type"] = "application/pdf"

    response = client.post("/api/media", json=payload)

    assert response.status_code == 422
    assert "content_type" in response.text
