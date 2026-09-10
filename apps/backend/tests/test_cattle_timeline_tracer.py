"""Livestock profile event timeline tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.database import SessionLocal
from api.db_models import CattleTimelineEventModel
from api.cattle_profiles import cattle_profile_store
from api.farmer_accounts import FarmerConsentState, farmer_account_store
from api.surface_auth import DEFAULT_AGENCY_OFFICER_ID


def setup_function():
    farmer_account_store.clear()
    cattle_profile_store.clear()


def create_farmer_and_cattle(client, consent_state=FarmerConsentState.PRIVATE, jurisdiction="tembalang"):
    farmer, _ = farmer_account_store.upsert_by_phone(
        phone_number="081234567890",
        name="Pak Tono",
        jurisdiction_id=jurisdiction,
        consent_state=consent_state,
    )
    cattle_response = client.post(
        f"/api/farmers/{farmer.id}/cattle",
        json={
            "tag": "SAPI-001",
            "sex": "female",
            "breed": "unknown",
            "age_months": 24,
            "status": "active",
            "jurisdiction_id": jurisdiction,
        },
    )
    assert cattle_response.status_code == 200
    return farmer, cattle_response.json()


def add_vaccination(client, farmer_id, cattle_id, event_date, title="FMD vaccination"):
    response = client.post(
        f"/api/farmers/{farmer_id}/cattle/{cattle_id}/timeline",
        json={
            "event_type": "vaccination",
            "event_date": event_date,
            "title": title,
            "description": "Dose 1 complete",
            "payload": {"vaccine": "FMD", "dose": 1},
            "creator_id": farmer_id,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_farmer_can_create_vaccination_timeline_event():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client)

    event = add_vaccination(client, farmer.id, cattle["id"], "2026-06-01")

    assert event["id"] == "event-1"
    assert event["cattle_id"] == cattle["id"]
    assert event["event_type"] == "vaccination"
    assert event["event_date"] == "2026-06-01"
    assert event["title"] == "FMD vaccination"
    assert event["description"] == "Dose 1 complete"
    assert event["payload"] == {"vaccine": "FMD", "dose": 1}
    assert event["creator_id"] == farmer.id
    with SessionLocal() as session:
        assert session.query(CattleTimelineEventModel).count() == 1


def test_cattle_detail_includes_timeline_ordered_newest_first():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client)
    add_vaccination(client, farmer.id, cattle["id"], "2026-05-01", "Older vaccination")
    add_vaccination(client, farmer.id, cattle["id"], "2026-06-01", "Newer vaccination")

    response = client.get(f"/api/farmers/{farmer.id}/cattle/{cattle['id']}")

    assert response.status_code == 200
    timeline = response.json()["timeline"]
    assert [event["title"] for event in timeline] == ["Newer vaccination", "Older vaccination"]


def test_farmer_cannot_add_event_to_other_farmer_cattle():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client)
    other_farmer, _ = farmer_account_store.upsert_by_phone(
        phone_number="082222222222",
        name="Pak Dua",
        jurisdiction_id="tembalang",
    )

    response = client.post(
        f"/api/farmers/{other_farmer.id}/cattle/{cattle['id']}/timeline",
        json={
            "event_type": "vaccination",
            "event_date": "2026-06-01",
            "title": "Blocked vaccination",
            "description": "Should fail",
            "payload": {"vaccine": "FMD"},
            "creator_id": other_farmer.id,
        },
    )

    assert response.status_code == 404


def test_authorized_agency_can_read_cattle_timeline():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client, consent_state=FarmerConsentState.AGENCY_MONITORING)
    add_vaccination(client, farmer.id, cattle["id"], "2026-06-01")

    response = client.get(
        f"/api/agency/cattle/{cattle['id']}",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
    )

    assert response.status_code == 200
    assert response.json()["timeline"][0]["event_type"] == "vaccination"


def test_unauthorized_agency_cannot_read_cattle_timeline():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client, consent_state=FarmerConsentState.PRIVATE)
    add_vaccination(client, farmer.id, cattle["id"], "2026-06-01")

    response = client.get(
        f"/api/agency/cattle/{cattle['id']}",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID},
    )

    assert response.status_code == 404
