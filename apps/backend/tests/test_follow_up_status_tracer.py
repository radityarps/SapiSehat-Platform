"""Agency follow-up status tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.farmer_accounts import farmer_account_store
from api.cattle_profiles import cattle_profile_store
from api.follow_ups import follow_up_store


def setup_function():
    farmer_account_store.clear()
    cattle_profile_store.clear()
    follow_up_store.clear()


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

def test_agency_follow_up_list_returns_agency_rows_with_internal_notes():
    client = TestClient(app)
    farmer = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "08777123457", "name": "Pak Agency Follow", "jurisdiction_id": "tembalang", "consent_state": "agency_monitoring"},
    ).json()
    created = client.post(
        "/api/agency/follow-ups",
        headers={"X-Agency-User-Id": "semarang-officer"},
        json={
            "farmer_id": farmer["id"],
            "cattle_id": None,
            "status": "in_progress",
            "public_message": "Petugas sedang meninjau laporan.",
            "internal_notes": "Coordinate district visit.",
        },
    )

    listed = client.get("/api/agency/follow-ups", headers={"X-Agency-User-Id": "semarang-officer"})

    assert created.status_code == 200, created.text
    assert listed.status_code == 200, listed.text
    assert listed.json() == [created.json()]


def test_agency_follow_up_list_is_jurisdiction_scoped():
    client = TestClient(app)
    allowed = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "08777123458", "name": "Pak Local Follow", "jurisdiction_id": "tembalang", "consent_state": "agency_monitoring"},
    ).json()
    outside = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "08777123459", "name": "Pak Outside Follow", "jurisdiction_id": "west-java", "consent_state": "agency_monitoring"},
    ).json()
    allowed_created = client.post(
        "/api/agency/follow-ups",
        headers={"X-Agency-User-Id": "semarang-officer"},
        json={"farmer_id": allowed["id"], "cattle_id": None, "status": "scheduled", "public_message": "Petugas meninjau sinyal risiko.", "internal_notes": "visible local row"},
    )
    assert allowed_created.status_code == 200, allowed_created.text
    follow_up_store.create(
        farmer_id=outside["id"],
        cattle_id=None,
        status="scheduled",
        public_message="Outside agency row.",
        internal_notes="must not leak to semarang officer",
    )

    listed = client.get("/api/agency/follow-ups", headers={"X-Agency-User-Id": "semarang-officer"})

    assert listed.status_code == 200, listed.text
    rows = listed.json()
    assert allowed_created.json()["id"] in {row["id"] for row in rows}
    assert all(row["farmer_id"] != outside["id"] for row in rows)
