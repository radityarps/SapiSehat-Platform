"""Agency jurisdiction scope audit tests."""

from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from api.farmer_accounts import farmer_account_store
from api.cattle_profiles import cattle_profile_store
from api.follow_ups import follow_up_store
from api.surface_auth import DEFAULT_AGENCY_OFFICER_ID

client = TestClient(app)


def setup_function():
    follow_up_store.clear()
    cattle_profile_store.clear()
    farmer_account_store.clear()


def farmer(jurisdiction_id: str):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={
            "phone_number": f"08888{suffix[:5]}",
            "name": "Scoped Farmer",
            "jurisdiction_id": jurisdiction_id,
            "consent_state": "agency_monitoring",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def cattle(farmer_id: str, jurisdiction_id: str):
    response = client.post(
        f"/api/farmers/{farmer_id}/cattle",
        json={"tag": f"SCOPE-{uuid4().hex[:6]}", "sex": "female", "breed": "sapi bali", "age_months": 24, "jurisdiction_id": jurisdiction_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_agency_follow_up_rejects_farmer_outside_jurisdiction():
    outside = farmer("west-java")
    outside_cattle = cattle(outside["id"], "west-java")

    response = client.post(
        "/api/agency/follow-ups",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
        json={
            "farmer_id": outside["id"],
            "cattle_id": outside_cattle["id"],
            "status": "review_needed",
            "public_message": "Please wait for agency review.",
            "internal_notes": "outside scope",
        },
    )

    assert response.status_code == 403
    assert "visible" in response.text


def test_agency_cattle_detail_rejects_cattle_outside_jurisdiction():
    outside = farmer("west-java")
    outside_cattle = cattle(outside["id"], "west-java")

    response = client.get(
        f"/api/agency/cattle/{outside_cattle['id']}",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
    )

    assert response.status_code == 404
    assert "not visible" in response.text
