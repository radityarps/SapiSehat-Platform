"""Agency follow-up status tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.farmer_accounts import farmer_account_store
from api.cattle_profiles import cattle_profile_store


def setup_function():
    farmer_account_store.clear()
    cattle_profile_store.clear()


def test_agency_internal_notes_hidden_from_farmer_follow_up_status():
    client = TestClient(app)
    farmer = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "08777123456", "name": "Pak Follow", "jurisdiction_id": "tembalang", "consent_state": "agency_monitoring"},
    ).json()
    cattle = client.post(
        f"/api/farmers/{farmer['id']}/cattle",
        json={"tag": "FOLLOW-1", "sex": "female", "breed": "sapi bali", "age_months": 24, "jurisdiction_id": "tembalang"},
    ).json()

    created = client.post(
        "/api/agency/follow-ups",
        headers={"X-Agency-User-Id": "semarang-officer"},
        json={
            "farmer_id": farmer["id"],
            "cattle_id": cattle["id"],
            "status": "scheduled",
            "public_message": "Petugas dijadwalkan menindaklanjuti.",
            "internal_notes": "Prioritize visit; possible cluster edge.",
        },
    )
    farmer_view = client.get(f"/api/farmers/{farmer['id']}/follow-ups")

    assert created.status_code == 200, created.text
    assert created.json()["internal_notes"] == "Prioritize visit; possible cluster edge."
    assert farmer_view.status_code == 200
    body = farmer_view.json()["follow_ups"][0]
    assert body["status"] == "scheduled"
    assert body["public_message"] == "Petugas dijadwalkan menindaklanjuti."
    assert "internal_notes" not in body
