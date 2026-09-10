"""Audit logs for sensitive backend actions."""

import io
from uuid import uuid4

from fastapi.testclient import TestClient  # type: ignore[import-not-found]
from PIL import Image

from main import app
from api.audit_logs import audit_log_store
from api.farmer_accounts import farmer_account_store
from api.follow_ups import follow_up_store
from api.media_governance import media_store
from api.surface_auth import DEFAULT_AGENCY_OFFICER_ID
import api.routes as routes
from utils.errors import NonCattleImageError

client = TestClient(app)

class FakeObjectStorage:
    backend = "s3-compatible"

    def put_object(self, *, object_key, content, content_type):
        return object_key

    def presigned_get_url(self, *, object_key, expires_seconds=900):
        return f"https://minio.local/{object_key}?expires={expires_seconds}"

class NonCattleInferenceService:
    def predict(self, image):
        raise NonCattleImageError("Image was rejected because it is not a cattle image")

class FakeInferenceService:
    def predict(self, image):
        return {
            "status": "success",
            "prediction": {
                "disease_class": "healthy",
                "display_label_key": "disease.healthy",
                "confidence": 0.91,
                "is_reliable": True,
                "scores": {"FMD": 0.09, "healthy": 0.91},
                "outcome": "DISEASE_CLASS",
                "needs_review": False,
            },
            "model_info": {"version": "test"},
            "processing_time_ms": 1,
            "preprocessing_time_ms": 1,
            "inference_time_ms": 1,
        }

def setup_function():
    audit_log_store.clear()
    media_store.clear()
    farmer_account_store.clear()
    follow_up_store.clear()

def create_farmer():
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08888{suffix[:5]}",
            "name": "Audit Farmer",
            "jurisdiction_id": "semarang-city",
            "consent_state": "research_and_monitoring",
        },
    )
    assert response.status_code == 200, response.text
    farmer = response.json()
    notice = client.post(f"/api/farmers/{farmer['id']}/scan-image-storage-notice", json={"accepted": True})
    assert notice.status_code == 200, notice.text
    return farmer

def test_media_upload_and_signed_url_write_audit_logs(monkeypatch):
    monkeypatch.setattr(routes, "media_storage_client", FakeObjectStorage())
    farmer = create_farmer()

    upload = client.post(
        "/api/media/uploads",
        data={"farmer_id": farmer["id"]},
        files={"file": ("scan.jpg", b"jpeg-bytes", "image/jpeg")},
    )
    assert upload.status_code == 200, upload.text
    media_id = upload.json()["id"]

    signed_url = client.get(f"/api/agency/media/{media_id}/download-url", headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID})
    assert signed_url.status_code == 200, signed_url.text

    upload_events = audit_log_store.list_by_action("media.uploaded")
    url_events = audit_log_store.list_by_action("media.download_url_issued")
    assert upload_events[0].actor_type == "farmer"
    assert upload_events[0].actor_id == farmer["id"]
    assert upload_events[0].resource_id == media_id
    assert url_events[0].actor_type == "agency"
    assert url_events[0].actor_id == DEFAULT_AGENCY_OFFICER_ID
    assert url_events[0].resource_id == media_id

def test_non_cattle_prediction_is_rejected_without_audit_event(monkeypatch):
    monkeypatch.setattr(routes, "is_model_ready", lambda: True)
    monkeypatch.setattr(routes, "get_inference_service", lambda: NonCattleInferenceService())
    image = Image.new("RGB", (1, 1), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    prediction = client.post(
        "/api/predict",
        files={"image": ("scan.png", buffer.getvalue(), "image/png")},
    )

    assert prediction.status_code == 422, prediction.text
    assert prediction.json()["error_code"] == "NON_CATTLE_IMAGE"
    assert audit_log_store.list_by_action("prediction.created") == []


def test_prediction_and_follow_up_write_audit_logs(monkeypatch):
    monkeypatch.setattr(routes, "is_model_ready", lambda: True)
    monkeypatch.setattr(routes, "get_inference_service", lambda: FakeInferenceService())
    image = Image.new("RGB", (1, 1), color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    prediction = client.post("/api/predict", files={"image": ("scan.png", buffer.getvalue(), "image/png")})
    assert prediction.status_code == 200, prediction.text

    farmer = create_farmer()
    follow_up = client.post(
        "/api/agency/follow-ups",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
        json={
            "farmer_id": farmer["id"],
            "status": "in_progress",
            "public_message": "Officer reviewing possible risk.",
            "internal_notes": "Audit test.",
        },
    )
    assert follow_up.status_code == 200, follow_up.text

    prediction_events = audit_log_store.list_by_action("prediction.created")
    follow_up_events = audit_log_store.list_by_action("follow_up.created")
    assert prediction_events[0].resource_type == "prediction"
    assert prediction_events[0].resource_id == "healthy"
    assert follow_up_events[0].actor_type == "agency"
    assert follow_up_events[0].actor_id == DEFAULT_AGENCY_OFFICER_ID
    assert follow_up_events[0].resource_id == follow_up.json()["id"]
