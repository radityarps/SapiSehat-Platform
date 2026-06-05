"""Phone-number farmer account tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.farmer_accounts import farmer_account_store


def setup_function():
    farmer_account_store.clear()


def test_farmer_can_register_with_phone_number_identity():
    client = TestClient(app)

    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "081234567890", "name": "Pak Tono", "jurisdiction_id": "tembalang"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "farmer-1"
    assert body["phone_number"] == "+6281234567890"
    assert body["name"] == "Pak Tono"
    assert body["jurisdiction_id"] == "tembalang"
    assert body["created"] is True


def test_duplicate_phone_signs_in_existing_farmer_account():
    client = TestClient(app)

    first = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "081234567890", "name": "Pak Tono", "jurisdiction_id": "tembalang"},
    )
    second = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "+62 812-3456-7890", "name": "Different Name", "jurisdiction_id": "banyumanik"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert second.json()["created"] is False
    assert second.json()["name"] == "Pak Tono"
    assert second.json()["jurisdiction_id"] == "tembalang"


def test_consent_initializes_private_for_new_farmer_account():
    client = TestClient(app)

    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "81234567890", "name": "Bu Sari", "jurisdiction_id": "banyumanik"},
    )

    assert response.status_code == 200
    assert response.json()["consent_state"] == "private"


def test_farmer_identity_available_for_downstream_cattle_and_detection_links():
    client = TestClient(app)

    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "6281234567890", "name": "Pak Tono", "jurisdiction_id": "tembalang"},
    )

    farmer_id = response.json()["id"]
    assert farmer_account_store.get_by_id(farmer_id) is not None


def test_invalid_phone_number_rejected():
    client = TestClient(app)

    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": "12345", "name": "Pak Tono", "jurisdiction_id": "tembalang"},
    )

    assert response.status_code == 422
