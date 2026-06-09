"""Surface-specific account auth behavior."""

from fastapi.testclient import TestClient
import pytest

from main import app
from api.surface_auth import surface_account_store
from api import surface_auth


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
    assert current.json() == {
        "account_type": "farmer",
        "email": "farmer@example.com",
        "id": register.json()["account"]["id"],
    }


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

def test_farmer_google_login_creates_farmer_account_but_agency_google_rejected():
    client = TestClient(app)

    farmer = client.post(
        "/api/auth/farmer/google",
        json={"id_token": "google:google-farmer@example.com:Google Farmer", "jurisdiction_id": "tembalang"},
    )
    agency = client.post(
        "/api/auth/agency/google",
        json={"id_token": "google:officer@example.com:Officer"},
    )

    assert farmer.status_code == 200
    assert farmer.json()["account"]["account_type"] == "farmer"
    assert farmer.json()["account"]["email"] == "google-farmer@example.com"
    assert agency.status_code == 404

def test_farmer_google_login_verifies_real_google_claims_when_enabled(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(surface_auth.settings, "fastapi_env", "production")
    monkeypatch.setattr(surface_auth.settings, "google_auth_enabled", True)
    monkeypatch.setattr(surface_auth.settings, "google_client_id", "sapisehat-client-id")
    monkeypatch.setattr(
        surface_auth.settings,
        "google_id_token_issuers",
        "https://accounts.google.com,accounts.google.com",
    )

    def fake_verify_google_id_token_claims(token):
        assert token == "signed-google-id-token"
        return {
            "iss": "https://accounts.google.com",
            "aud": "sapisehat-client-id",
            "email": "Verified-Farmer@Example.COM",
            "email_verified": True,
            "name": "Verified Farmer",
            "sub": "google-subject-1",
        }

    monkeypatch.setattr(surface_auth, "verify_google_id_token_claims", fake_verify_google_id_token_claims)

    response = client.post(
        "/api/auth/farmer/google",
        json={"id_token": "signed-google-id-token", "jurisdiction_id": "tembalang"},
    )

    assert response.status_code == 200
    assert response.json()["account"]["account_type"] == "farmer"
    assert response.json()["account"]["email"] == "verified-farmer@example.com"

def test_farmer_google_login_rejects_unverified_google_email(monkeypatch):
    monkeypatch.setattr(surface_auth.settings, "fastapi_env", "production")
    monkeypatch.setattr(surface_auth.settings, "google_auth_enabled", True)
    monkeypatch.setattr(surface_auth.settings, "google_client_id", "sapisehat-client-id")

    monkeypatch.setattr(surface_auth, "verify_google_id_token_claims", lambda token: {
        "iss": "https://accounts.google.com",
        "aud": "sapisehat-client-id",
        "email": "unverified@example.com",
        "email_verified": False,
        "sub": "google-subject-2",
    })

    with pytest.raises(ValueError, match="not verified"):
        surface_auth.parse_google_id_token("signed-google-id-token")
