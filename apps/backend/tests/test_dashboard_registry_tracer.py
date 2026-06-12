"""Agency dashboard registry tracer tests."""

from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from tests.conftest import repo_text

client = TestClient(app)


def create_farmer(consent, jurisdiction_id):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/farmers/accounts",
        json={"phone_number": f"08444{suffix[:5]}", "name": f"Registry {suffix}", "jurisdiction_id": jurisdiction_id, "consent_state": consent},
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_cattle(farmer_id, tag, jurisdiction_id="tembalang"):
    response = client.post(
        f"/api/farmers/{farmer_id}/cattle",
        json={"tag": tag, "sex": "female", "breed": "sapi bali", "age_months": 18, "jurisdiction_id": jurisdiction_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_registry_api_filters_farmers_and_cattle_by_authorization_scope():
    allowed = create_farmer("agency_monitoring", "tembalang")
    private = create_farmer("private", "tembalang")
    outside = create_farmer("agency_monitoring", "west-java")
    allowed_cattle = create_cattle(allowed["id"], "REG-ALLOWED")
    create_cattle(private["id"], "REG-PRIVATE")
    create_cattle(outside["id"], "REG-OUTSIDE", "west-java")

    response = client.get("/api/agency/registry", headers={"X-Agency-User-Id": "semarang-officer"})

    assert response.status_code == 200, response.text
    body = response.json()
    cattle_tags = {item["tag"] for item in body["cattle"]}
    cattle_ids = {item["id"] for item in body["cattle"]}
    assert allowed_cattle["id"] in cattle_ids
    assert "REG-ALLOWED" in cattle_tags
    assert "REG-PRIVATE" not in cattle_tags
    assert "REG-OUTSIDE" not in cattle_tags
    assert body["filters"]["table_pattern"] == "TanStack Table compatible columns"


def test_dashboard_registry_component_contains_table_filter_and_permitted_sections():
    source = repo_text("apps/dashboard/src/features/agency/registry/registry-client.tsx")
    page = repo_text("apps/dashboard/app/agency/registry/page.tsx")

    assert "@tanstack/react-table" in source
    assert "getAgencyRegistry" in source
    assert "X-Agency-User-Id" in repo_text("apps/dashboard/src/shared/api/client.ts")
    assert "Search name, tag, district, consent" in source
    assert "Farmers" in source
    assert "Cattle" in source
    assert "DataTable" in source
