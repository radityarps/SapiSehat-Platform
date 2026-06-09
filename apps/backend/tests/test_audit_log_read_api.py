"""Admin audit-log read API."""

from fastapi.testclient import TestClient

from main import app
from api.audit_logs import audit_log_store

client = TestClient(app)

def setup_function():
    audit_log_store.clear()

def test_admin_can_read_recent_audit_logs_with_filters():
    audit_log_store.record(
        actor_type="farmer",
        actor_id="farmer-1",
        action="media.uploaded",
        resource_type="media",
        resource_id="media-1",
        metadata_json={"content_type": "image/jpeg"},
    )
    audit_log_store.record(
        actor_type="agency",
        actor_id="semarang-officer",
        action="follow_up.created",
        resource_type="follow_up",
        resource_id="follow-up-1",
    )

    response = client.get(
        "/api/agency/audit-logs?action=media.uploaded&limit=10",
        headers={"X-Agency-User-Id": "central-java-admin"},
    )

    assert response.status_code == 200, response.text
    body = response.json()["audit_logs"]
    assert len(body) == 1
    assert body[0]["action"] == "media.uploaded"
    assert body[0]["resource_id"] == "media-1"
    assert body[0]["metadata_json"] == {"content_type": "image/jpeg"}

def test_non_admin_agency_cannot_read_audit_logs():
    audit_log_store.record(
        actor_type="farmer",
        actor_id="farmer-1",
        action="media.uploaded",
        resource_type="media",
        resource_id="media-1",
    )

    response = client.get(
        "/api/agency/audit-logs",
        headers={"X-Agency-User-Id": "semarang-officer"},
    )

    assert response.status_code == 403
    assert "admin" in response.text
