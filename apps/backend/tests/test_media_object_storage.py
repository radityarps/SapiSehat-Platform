"""MinIO/S3-compatible media object storage tests."""

import hashlib
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from api.farmer_accounts import farmer_account_store
from api.media_governance import media_store
import api.routes as routes

client = TestClient(app)


class FakeObjectStorage:
    backend = "s3-compatible"

    def __init__(self):
        self.objects = {}

    def put_object(self, *, object_key, content, content_type):
        self.objects[object_key] = {"content": content, "content_type": content_type}
        return object_key

    def presigned_get_url(self, *, object_key, expires_seconds=900):
        return f"https://minio.local/{object_key}?expires={expires_seconds}"


def setup_function():
    media_store.clear()
    farmer_account_store.clear()


def create_farmer():
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08777{suffix[:5]}",
            "name": "Upload Farmer",
            "jurisdiction_id": "semarang-city",
            "consent_state": "research_and_monitoring",
        },
    )
    assert response.status_code == 200, response.text
    farmer = response.json()
    notice = client.post(
        f"/api/farmers/{farmer['id']}/scan-image-storage-notice",
        json={"accepted": True},
    )
    assert notice.status_code == 200, notice.text
    return farmer


def test_media_upload_stores_image_bytes_in_s3_compatible_storage(monkeypatch):
    fake = FakeObjectStorage()
    monkeypatch.setattr(routes, "media_storage_client", fake)
    farmer = create_farmer()
    content = b"fake-jpeg-bytes"

    response = client.post(
        "/api/media/uploads",
        data={"farmer_id": farmer["id"]},
        files={"file": ("scan.jpg", content, "image/jpeg")},
    )

    assert response.status_code == 200, response.text
    media = response.json()
    assert media["storage_backend"] == "s3-compatible"
    assert media["object_key"].startswith(f"scan-images/{farmer['id']}/")
    assert media["checksum"] == hashlib.sha256(content).hexdigest()
    assert media["byte_size"] == len(content)
    assert fake.objects[media["object_key"]]["content"] == content


def test_media_presigned_url_requires_agency_scope(monkeypatch):
    fake = FakeObjectStorage()
    monkeypatch.setattr(routes, "media_storage_client", fake)
    farmer = create_farmer()
    upload = client.post(
        "/api/media/uploads",
        data={"farmer_id": farmer["id"]},
        files={"file": ("scan.png", b"png-bytes", "image/png")},
    )
    assert upload.status_code == 200, upload.text

    response = client.get(
        f"/api/agency/media/{upload.json()['id']}/download-url",
        headers={"X-Agency-User-Id": "semarang-officer"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["url"].startswith("https://minio.local/")
    assert response.json()["expires_seconds"] == 900


def test_media_upload_rejects_files_over_configured_limit(monkeypatch):
    monkeypatch.setattr(routes.settings, "media_max_upload_bytes", 4)
    monkeypatch.setattr(routes, "media_storage_client", FakeObjectStorage())
    farmer = create_farmer()

    response = client.post(
        "/api/media/uploads",
        data={"farmer_id": farmer["id"]},
        files={"file": ("scan.webp", b"12345", "image/webp")},
    )

    assert response.status_code == 413
    assert "too large" in response.text
