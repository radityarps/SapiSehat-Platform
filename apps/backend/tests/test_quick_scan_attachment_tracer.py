"""Quick-scan detection attachment tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.cattle_profiles import cattle_profile_store
from api.detection_events import detection_event_store
from api.farmer_accounts import FarmerConsentState, farmer_account_store
from api.surface_auth import DEFAULT_AGENCY_OFFICER_ID


def setup_function():
    farmer_account_store.clear()
    cattle_profile_store.clear()
    detection_event_store.clear()


def create_farmer_and_cattle(client, phone="081234567890", consent_state=FarmerConsentState.PRIVATE, jurisdiction="tembalang"):
    farmer, _ = farmer_account_store.upsert_by_phone(
        phone_number=phone,
        name="Pak Tono",
        jurisdiction_id=jurisdiction,
        consent_state=consent_state,
    )
    cattle_response = client.post(
        f"/api/farmers/{farmer.id}/cattle",
        json={
            "tag": f"SAPI-{farmer.id}",
            "sex": "female",
            "breed": "unknown",
            "age_months": 24,
            "status": "active",
            "jurisdiction_id": jurisdiction,
        },
    )
    assert cattle_response.status_code == 200
    return farmer, cattle_response.json()


def create_quick_scan(client, farmer_id):
    response = client.post(
        "/api/detections/quick-scan",
        json={
            "farmer_id": farmer_id,
            "result_label": "FMD",
            "confidence": 0.82,
            "source": "quick_scan",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_quick_scan_detection_created_unattached():
    client = TestClient(app)
    farmer, _ = create_farmer_and_cattle(client)

    detection = create_quick_scan(client, farmer.id)

    assert detection["id"] == "detection-1"
    assert detection["farmer_id"] == farmer.id
    assert detection["cattle_id"] is None
    assert detection["attached"] is False
    assert detection["result_label"] == "FMD"
    assert detection["confidence"] == 0.82


def test_farmer_can_attach_unattached_detection_to_owned_cattle():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client)
    detection = create_quick_scan(client, farmer.id)

    response = client.post(
        f"/api/farmers/{farmer.id}/detections/{detection['id']}/attach",
        json={"cattle_id": cattle["id"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == detection["id"]
    assert body["cattle_id"] == cattle["id"]
    assert body["attached"] is True


def test_farmer_cannot_attach_detection_to_other_farmer_cattle():
    client = TestClient(app)
    farmer_one, _ = create_farmer_and_cattle(client, phone="081111111111")
    farmer_two, cattle_two = create_farmer_and_cattle(client, phone="082222222222")
    detection = create_quick_scan(client, farmer_one.id)

    response = client.post(
        f"/api/farmers/{farmer_one.id}/detections/{detection['id']}/attach",
        json={"cattle_id": cattle_two["id"]},
    )

    assert response.status_code == 404


def test_agency_dashboard_sees_detection_after_attachment_when_authorized():
    client = TestClient(app)
    farmer, cattle = create_farmer_and_cattle(client, consent_state=FarmerConsentState.AGENCY_MONITORING)
    detection = create_quick_scan(client, farmer.id)
    attach_response = client.post(
        f"/api/farmers/{farmer.id}/detections/{detection['id']}/attach",
        json={"cattle_id": cattle["id"]},
    )
    assert attach_response.status_code == 200

    response = client.get("/api/agency/detections", headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID})

    assert response.status_code == 200
    detections = response.json()["detections"]
    assert [item["id"] for item in detections] == [detection["id"]]
    assert detections[0]["attached"] is True


def test_agency_dashboard_does_not_see_unattached_or_unauthorized_detection():
    client = TestClient(app)
    private_farmer, private_cattle = create_farmer_and_cattle(client, consent_state=FarmerConsentState.PRIVATE)
    authorized_farmer, _ = create_farmer_and_cattle(client, phone="082222222222", consent_state=FarmerConsentState.AGENCY_MONITORING)
    private_detection = create_quick_scan(client, private_farmer.id)
    unattached_detection = create_quick_scan(client, authorized_farmer.id)
    client.post(
        f"/api/farmers/{private_farmer.id}/detections/{private_detection['id']}/attach",
        json={"cattle_id": private_cattle["id"]},
    )

    response = client.get("/api/agency/detections", headers={"X-Agency-User-Id": DEFAULT_AGENCY_OFFICER_ID})

    assert response.status_code == 200
    assert response.json()["detections"] == []
