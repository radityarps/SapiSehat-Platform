"""Surface-specific account auth behavior."""

from fastapi.testclient import TestClient

from main import app
from api.surface_auth import surface_account_store


def setup_function():
    surface_account_store.clear()


def test_farmer_registers_with_email_password_and_reads_current_account():
    client = TestClient(app)

    register = client.post(
        "/api/auth/farmer/register",
        json={
            "email": "farmer@example.com",
            "password": "strong-password",
            "name": "Pak Tono",
            "jurisdiction_id": "tembalang",
        },
    )

    assert register.status_code == 200
    token = register.json()["access_token"]

    current = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert current.status_code == 200
    assert current.json()["account_type"] == "farmer"
    assert current.json()["email"] == "farmer@example.com"
    assert current.json()["id"] == register.json()["account"]["id"]
    assert current.json()["name"] == "Pak Tono"
    assert current.json()["jurisdiction_id"] == "tembalang"
    assert current.json()["is_active"] is True


def test_farmer_logs_in_with_email_password_after_registration():
    client = TestClient(app)
    client.post(
        "/api/auth/farmer/register",
        json={
            "email": "login-farmer@example.com",
            "password": "strong-password",
            "name": "Bu Sari",
            "jurisdiction_id": "banyumanik",
        },
    )

    login = client.post(
        "/api/auth/farmer/login",
        json={"email": "login-farmer@example.com", "password": "strong-password"},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]
    current = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert current.status_code == 200
    assert current.json()["account_type"] == "farmer"
    assert current.json()["email"] == "login-farmer@example.com"



def test_default_farmer_seeded_account_logs_in_with_email_password():
    client = TestClient(app)

    login = client.post(
        "/api/auth/farmer/login",
        json={"email": "farmer@example.com", "password": "strong-password"},
    )

    assert login.status_code == 200
    body = login.json()
    assert body["account"]["account_type"] == "farmer"
    assert body["account"]["email"] == "farmer@example.com"
    seeded = surface_account_store.get(account_type="farmer", email="farmer@example.com")
    assert seeded is not None
    assert seeded.name == "Demo Farmer"
    assert seeded.jurisdiction_id == "tembalang"

def test_agency_seeded_account_logs_in_with_email_password():
    client = TestClient(app)

    login = client.post(
        "/api/auth/agency/login",
        json={"email": "semarang-officer@sapisehat.test", "password": "agency-password"},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]
    current = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert current.status_code == 200
    assert current.json()["account_type"] == "agency"
    assert current.json()["email"] == "semarang-officer@sapisehat.test"

def test_same_email_can_exist_as_farmer_and_agency_surface_accounts():
    client = TestClient(app)
    surface_account_store.seed_agency(
        email="shared@example.com",
        password="agency-password",
        name="Shared Agency Officer",
        jurisdiction_id="semarang-city",
    )

    register = client.post(
        "/api/auth/farmer/register",
        json={
            "email": "shared@example.com",
            "password": "farmer-password",
            "name": "Shared Farmer",
            "jurisdiction_id": "tembalang",
        },
    )
    agency_login = client.post(
        "/api/auth/agency/login",
        json={"email": "shared@example.com", "password": "agency-password"},
    )

    assert register.status_code == 200
    assert agency_login.status_code == 200
    assert register.json()["account"]["account_type"] == "farmer"
    assert agency_login.json()["account"]["account_type"] == "agency"
    assert register.json()["account"]["id"] != agency_login.json()["account"]["id"]

def test_auth_uses_jwt_and_non_plain_sha256_password_hash():
    client = TestClient(app)

    register = client.post(
        "/api/auth/farmer/register",
        json={
            "email": "hardened@example.com",
            "password": "strong-password",
            "name": "Pak Hardened",
            "jurisdiction_id": "tembalang",
        },
    )

    assert register.status_code == 200
    assert len(register.json()["access_token"].split(".")) == 3
    account = surface_account_store.get(account_type="farmer", email="hardened@example.com")
    assert account is not None
    assert account.password_hash.startswith("$pbkdf2-sha256$")
    assert account.password_hash != "strong-password"

def test_google_login_routes_removed():
    client = TestClient(app)

    farmer = client.post(
        "/api/auth/farmer/google",
        json={"id_token": "google:farmer@example.com:Farmer", "jurisdiction_id": "tembalang"},
    )
    agency = client.post(
        "/api/auth/agency/google",
        json={"id_token": "google:officer@example.com:Officer"},
    )

    assert farmer.status_code == 404
    assert agency.status_code == 404

def test_farmer_updates_profile_and_jurisdiction_with_same_account_token():
    client = TestClient(app)
    register = client.post(
        "/api/auth/farmer/register",
        json={"email": "profile@example.com", "password": "strong-password", "name": "Old Name", "jurisdiction_id": "tembalang"},
    )
    token = register.json()["access_token"]
    farmer_id = register.json()["account"]["id"]

    update = client.put(
        f"/api/farmers/{farmer_id}/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name", "jurisdiction_id": "banyumanik"},
    )

    assert update.status_code == 200
    assert update.json()["name"] == "New Name"
    assert update.json()["jurisdiction_id"] == "banyumanik"


def test_farmer_preferences_are_backend_backed():
    client = TestClient(app)
    register = client.post(
        "/api/auth/farmer/register",
        json={"email": "prefs@example.com", "password": "strong-password", "name": "Prefs Farmer", "jurisdiction_id": "tembalang"},
    )
    token = register.json()["access_token"]
    farmer_id = register.json()["account"]["id"]

    initial = client.get(f"/api/farmers/{farmer_id}/preferences", headers={"Authorization": f"Bearer {token}"})
    assert initial.status_code == 200
    assert initial.json()["scan_result_notifications"] is True

    updated = client.put(
        f"/api/farmers/{farmer_id}/preferences",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scan_result_notifications": False,
            "sync_notifications": True,
            "area_risk_advisory_notifications": True,
            "follow_up_status_notifications": False,
            "quiet_hours_enabled": True,
            "quiet_hours_start": "20:00",
            "quiet_hours_end": "05:30",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["scan_result_notifications"] is False
    assert updated.json()["area_risk_advisory_notifications"] is True
    assert updated.json()["quiet_hours_enabled"] is True
    assert updated.json()["quiet_hours_start"] == "20:00"


def test_farmer_archive_requires_password_and_disables_future_login():
    client = TestClient(app)
    register = client.post(
        "/api/auth/farmer/register",
        json={"email": "archive@example.com", "password": "strong-password", "name": "Archive Farmer", "jurisdiction_id": "tembalang"},
    )
    token = register.json()["access_token"]
    farmer_id = register.json()["account"]["id"]

    wrong = client.post(
        f"/api/farmers/{farmer_id}/account/archive",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "wrong-password"},
    )
    assert wrong.status_code == 403

    archive = client.post(
        f"/api/farmers/{farmer_id}/account/archive",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "strong-password"},
    )
    assert archive.status_code == 200
    assert archive.json()["is_active"] is False

    login = client.post("/api/auth/farmer/login", json={"email": "archive@example.com", "password": "strong-password"})
    assert login.status_code == 403
    assert "archived" in str(login.json()).lower()
