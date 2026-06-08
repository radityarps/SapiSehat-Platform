"""Cattle-first profile tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.cattle_profiles import cattle_profile_store
from api.farmer_accounts import FarmerConsentState, farmer_account_store


def setup_function():
    farmer_account_store.clear()
    cattle_profile_store.clear()


def create_farmer(client, phone="081234567890", name="Pak Tono", jurisdiction="tembalang"):
    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": phone, "name": name, "jurisdiction_id": jurisdiction},
    )
    assert response.status_code == 200
    return response.json()


def create_cattle(client, farmer_id, tag="SAPI-001", jurisdiction="tembalang"):
    response = client.post(
        f"/api/farmers/{farmer_id}/cattle",
        json={
            "tag": tag,
            "sex": "female",
            "breed": "unknown",
            "age_months": 24,
            "status": "active",
            "jurisdiction_id": jurisdiction,
        },
    )
    assert response.status_code == 200
    return response.json()


def test_farmer_can_create_cattle_profile_linked_to_account():
    client = TestClient(app)
    farmer = create_farmer(client)

    cattle = create_cattle(client, farmer["id"])

    assert cattle["id"] == "cattle-1"
    assert cattle["farmer_id"] == farmer["id"]
    assert cattle["tag"] == "SAPI-001"
    assert cattle["sex"] == "female"
    assert cattle["breed"] == "unknown"
    assert cattle["age_months"] == 24
    assert cattle["status"] == "active"
    assert cattle["jurisdiction_id"] == "tembalang"


def test_farmer_can_list_and_select_owned_cattle_for_detection():
    client = TestClient(app)
    farmer = create_farmer(client)
    cattle = create_cattle(client, farmer["id"])

    list_response = client.get(f"/api/farmers/{farmer['id']}/cattle")
    select_response = client.get(f"/api/farmers/{farmer['id']}/cattle/{cattle['id']}")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["cattle"]] == [cattle["id"]]
    assert select_response.status_code == 200
    assert select_response.json()["id"] == cattle["id"]


def test_farmer_cannot_select_other_farmer_cattle():
    client = TestClient(app)
    farmer_one = create_farmer(client, phone="081111111111", name="Pak Satu")
    farmer_two = create_farmer(client, phone="082222222222", name="Pak Dua")
    cattle = create_cattle(client, farmer_one["id"])

    response = client.get(f"/api/farmers/{farmer_two['id']}/cattle/{cattle['id']}")

    assert response.status_code == 404


def test_cattle_creation_requires_existing_farmer():
    client = TestClient(app)

    response = client.post(
        "/api/farmers/missing/cattle",
        json={
            "tag": "SAPI-404",
            "sex": "male",
            "breed": "unknown",
            "age_months": 12,
            "status": "active",
            "jurisdiction_id": "tembalang",
        },
    )

    assert response.status_code == 404

def test_farmer_archive_action_hides_cattle_without_backend_delete():
    client = TestClient(app)
    farmer = create_farmer(client)
    cattle = create_cattle(client, farmer["id"])

    archive = client.delete(f"/api/farmers/{farmer['id']}/cattle/{cattle['id']}")
    list_response = client.get(f"/api/farmers/{farmer['id']}/cattle")
    direct_response = client.get(f"/api/farmers/{farmer['id']}/cattle/{cattle['id']}")

    assert archive.status_code == 200
    assert archive.json()["id"] == cattle["id"]
    assert archive.json()["status"] == "archived"
    assert list_response.status_code == 200
    assert list_response.json()["cattle"] == []
    assert direct_response.status_code == 200
    assert direct_response.json()["status"] == "archived"


def test_agency_can_see_cattle_when_role_jurisdiction_and_consent_allow():
    client = TestClient(app)
    account, _ = farmer_account_store.upsert_by_phone(
        phone_number="081234567890",
        name="Pak Tono",
        jurisdiction_id="tembalang",
        consent_state=FarmerConsentState.AGENCY_MONITORING,
    )
    create_cattle(client, account.id, jurisdiction="tembalang")

    response = client.get("/api/agency/cattle", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["cattle"]] == ["cattle-1"]


def test_agency_cannot_see_cattle_without_consent_or_jurisdiction():
    client = TestClient(app)
    private_farmer, _ = farmer_account_store.upsert_by_phone(
        phone_number="081234567890",
        name="Bu Sari",
        jurisdiction_id="tembalang",
    )
    outside_farmer, _ = farmer_account_store.upsert_by_phone(
        phone_number="082222222222",
        name="Pak Asep",
        jurisdiction_id="west-java",
        consent_state=FarmerConsentState.AGENCY_MONITORING,
    )
    create_cattle(client, private_farmer.id, tag="PRIVATE", jurisdiction="tembalang")
    create_cattle(client, outside_farmer.id, tag="OUTSIDE", jurisdiction="west-java")

    response = client.get("/api/agency/cattle", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200
    assert response.json()["cattle"] == []
