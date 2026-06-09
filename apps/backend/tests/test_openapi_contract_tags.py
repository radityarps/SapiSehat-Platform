"""OpenAPI surface tag contract tests."""

from main import app


def operation_tags(path: str, method: str) -> list[str]:
    schema = app.openapi()
    return schema["paths"][path][method]["tags"]


def test_openapi_groups_auth_farmer_agency_and_media_surfaces():
    assert operation_tags("/api/auth/farmer/login", "post") == ["auth"]
    assert operation_tags("/api/farmers/{farmer_id}/cattle", "post") == ["farmer"]
    assert operation_tags("/api/agency/detection-monitoring", "get") == ["agency"]
    assert operation_tags("/api/media", "post") == ["media"]
