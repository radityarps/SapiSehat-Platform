"""Optional real MinIO smoke for media upload and signed URL."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app
from api.farmer_accounts import farmer_account_store
from api.media_governance import media_store
from api.surface_auth import DEFAULT_AGENCY_OFFICER_ID

client = TestClient(app)

def setup_function():
    media_store.clear()
    farmer_account_store.clear()

def minio_client():
    boto3 = pytest.importorskip("boto3")
    botocore_client = pytest.importorskip("botocore.client")
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=botocore_client.Config(s3={"addressing_style": "path"}),
    )

def create_farmer():
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08999{suffix[:5]}",
            "name": "MinIO Farmer",
            "jurisdiction_id": "semarang-city",
            "consent_state": "research_and_monitoring",
        },
    )
    assert response.status_code == 200, response.text
    farmer = response.json()
    notice = client.post(f"/api/farmers/{farmer['id']}/scan-image-storage-notice", json={"accepted": True})
    assert notice.status_code == 200, notice.text
    return farmer

def ensure_bucket(s3):
    try:
        s3.create_bucket(Bucket=settings.s3_bucket)
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise

@pytest.mark.skipif(os.getenv("RUN_MINIO_SMOKE") != "1", reason="requires local MinIO")
def test_real_minio_upload_and_signed_url_smoke():
    s3 = minio_client()
    ensure_bucket(s3)
    farmer = create_farmer()
    content = b"real-minio-smoke-image-bytes"

    upload = client.post(
        "/api/media/uploads",
        data={"farmer_id": farmer["id"]},
        files={"file": ("scan.jpg", content, "image/jpeg")},
    )
    assert upload.status_code == 200, upload.text
    media = upload.json()

    stored = s3.get_object(Bucket=settings.s3_bucket, Key=media["object_key"])["Body"].read()
    signed_url = client.get(
        f"/api/agency/media/{media['id']}/download-url",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
    )

    assert stored == content
    assert signed_url.status_code == 200, signed_url.text
    assert media["object_key"] in signed_url.json()["url"]
