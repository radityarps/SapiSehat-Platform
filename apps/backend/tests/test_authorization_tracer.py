"""Role-jurisdiction-consent authorization tracer tests."""

from fastapi.testclient import TestClient

from main import app
from api.database import SessionLocal
from api.db_models import AgencyJurisdictionModel, AgencyUserModel
from api.authorization import (
    AgencyRole,
    AgencyUser,
    ConsentTier,
    FarmerRecord,
    DEMO_JURISDICTIONS,
    can_agency_access_farmer,
    filter_visible_farmers,
)


def test_authorization_allows_same_jurisdiction_with_monitoring_consent():
    with SessionLocal() as session:
        assert session.query(AgencyJurisdictionModel).count() >= 5
        assert session.query(AgencyUserModel).count() >= 3
    agency = AgencyUser("officer", AgencyRole.DISTRICT_OFFICER, "semarang-city")
    farmer = FarmerRecord("farmer", "Pak Tono", "tembalang", ConsentTier.AGENCY_MONITORING)
    assert can_agency_access_farmer(agency, farmer, DEMO_JURISDICTIONS) is True


def test_authorization_rejects_wrong_jurisdiction():
    agency = AgencyUser("officer", AgencyRole.DISTRICT_OFFICER, "semarang-city")
    farmer = FarmerRecord("farmer", "Pak Asep", "west-java", ConsentTier.AGENCY_MONITORING)
    assert can_agency_access_farmer(agency, farmer, DEMO_JURISDICTIONS) is False


def test_authorization_rejects_private_consent():
    agency = AgencyUser("officer", AgencyRole.DISTRICT_OFFICER, "semarang-city")
    farmer = FarmerRecord("farmer", "Bu Sari", "banyumanik", ConsentTier.PRIVATE)
    assert can_agency_access_farmer(agency, farmer, DEMO_JURISDICTIONS) is False


def test_authorization_rejects_insufficient_role():
    agency = AgencyUser("viewer", AgencyRole.VIEWER, "tembalang")
    farmer = FarmerRecord("farmer", "Pak Asep", "west-java", ConsentTier.AGENCY_MONITORING)
    assert can_agency_access_farmer(agency, farmer, DEMO_JURISDICTIONS) is False


def test_filter_visible_farmers_excludes_unauthorized_records():
    agency = AgencyUser("officer", AgencyRole.DISTRICT_OFFICER, "semarang-city")
    farmers = [
        FarmerRecord("allowed", "Pak Tono", "tembalang", ConsentTier.AGENCY_MONITORING),
        FarmerRecord("private", "Bu Sari", "banyumanik", ConsentTier.PRIVATE),
        FarmerRecord("outside", "Pak Asep", "west-java", ConsentTier.AGENCY_MONITORING),
    ]
    visible = filter_visible_farmers(agency, farmers, DEMO_JURISDICTIONS)
    assert [farmer.id for farmer in visible] == ["allowed"]


def test_agency_farmers_endpoint_filters_by_role_jurisdiction_and_consent():
    client = TestClient(app)
    response = client.get("/api/agency/farmers", headers={"X-Agency-User-Id": "semarang-officer"})
    assert response.status_code == 200
    body = response.json()
    assert body["agency_user_id"] == "semarang-officer"
    assert [farmer["id"] for farmer in body["farmers"]] == ["farmer-1"]


def test_agency_farmers_endpoint_rejects_unknown_agency_user():
    client = TestClient(app)
    response = client.get("/api/agency/farmers", headers={"X-Agency-User-Id": "unknown"})
    assert response.status_code == 403
