"""Tests for agency user management API endpoints."""

import uuid
from fastapi.testclient import TestClient

from api.authorization import refresh_agency_users
from api.surface_auth import DEFAULT_AGENCY_VIEWER_ID, seed_default_agency_accounts
from main import app


def _get_admin_token(client: TestClient) -> tuple[str, str]:
    seed_default_agency_accounts()
    refresh_agency_users()
    login = client.post(
        "/api/auth/agency/login",
        json={"email": "admin@sapisehat.id", "password": "admin123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    user_id = login.json()["account"]["id"]
    return token, user_id


def test_list_agency_users_requires_admin():
    client = TestClient(app)
    res = client.get(
        "/api/agency/users",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_VIEWER_ID},
    )
    assert res.status_code == 403


def test_create_agency_user_without_manual_id_and_login():
    client = TestClient(app)
    token, admin_id = _get_admin_token(client)

    # 1. Create a new agency user without providing manual ID
    res = client.post(
        "/api/agency/users",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
        json={
            "name": "Dokter Hewan Budi",
            "email": "drh.budi@sapisehat.id",
            "role": "district_officer",
            "jurisdiction_id": "semarang-city",
        },
    )
    assert res.status_code == 201
    created = res.json()
    assert str(uuid.UUID(created["id"])) == created["id"]
    assert created["name"] == "Dokter Hewan Budi"
    assert created["email"] == "drh.budi@sapisehat.id"
    assert created["role"] == "district_officer"
    assert created["jurisdiction_id"] == "semarang-city"

    # 2. Verify the new user can log in with default password
    login_new = client.post(
        "/api/auth/agency/login",
        json={"email": "drh.budi@sapisehat.id", "password": "agency-password"},
    )
    assert login_new.status_code == 200
    assert login_new.json()["account"]["name"] == "Dokter Hewan Budi"
    assert login_new.json()["account"]["role"] == "district_officer"

    # 3. Verify user appears in list_agency_users
    list_res = client.get(
        "/api/agency/users",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
    )
    assert list_res.status_code == 200
    all_users = list_res.json()["users"]
    found = [u for u in all_users if u["id"] == created["id"]]
    assert len(found) == 1
    assert found[0]["name"] == "Dokter Hewan Budi"
    assert found[0]["email"] == "drh.budi@sapisehat.id"

    # 4. Duplicate email returns 409
    dup = client.post(
        "/api/agency/users",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
        json={
            "name": "Budi Clone",
            "email": "drh.budi@sapisehat.id",
            "role": "village_officer",
            "jurisdiction_id": "tembalang",
        },
    )
    assert dup.status_code == 409

    # 5. Update user name and role
    upd = client.put(
        f"/api/agency/users/{created['id']}",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
        json={
            "name": "Drh. Budi Santoso",
            "role": "province_officer",
            "jurisdiction_id": "central-java",
        },
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Drh. Budi Santoso"
    assert upd.json()["role"] == "province_officer"
    assert upd.json()["jurisdiction_id"] == "central-java"

    # 6. Delete user and verify access is revoked
    delete_res = client.delete(
        f"/api/agency/users/{created['id']}",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["deleted"] is True

    login_after_del = client.post(
        "/api/auth/agency/login",
        json={"email": "drh.budi@sapisehat.id", "password": "agency-password"},
    )
    assert login_after_del.status_code == 401


def test_reset_agency_user_password_by_admin():
    client = TestClient(app)
    token, admin_id = _get_admin_token(client)

    # 1. Create a user with a custom password
    res = client.post(
        "/api/agency/users",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
        json={
            "name": "Drh. Siti",
            "email": "drh.siti@sapisehat.id",
            "role": "district_officer",
            "jurisdiction_id": "semarang-city",
            "password": "custom-password-123",
        },
    )
    assert res.status_code == 201
    user_id = res.json()["id"]

    # 2. Login with custom password works
    login_custom = client.post(
        "/api/auth/agency/login",
        json={"email": "drh.siti@sapisehat.id", "password": "custom-password-123"},
    )
    assert login_custom.status_code == 200

    # 3. Non-admin reset fails with 403
    res_non_admin = client.post(
        f"/api/agency/users/{user_id}/reset-password",
        headers={"X-Agency-User-Id": DEFAULT_AGENCY_VIEWER_ID},
    )
    assert res_non_admin.status_code == 403

    # 4. Admin resets password
    res_reset = client.post(
        f"/api/agency/users/{user_id}/reset-password",
        headers={"Authorization": f"Bearer {token}", "X-Agency-User-Id": admin_id},
    )
    assert res_reset.status_code == 200
    assert res_reset.json()["success"] is True
    assert res_reset.json()["default_password"] == "agency-password"

    # 5. Old password no longer works
    login_old = client.post(
        "/api/auth/agency/login",
        json={"email": "drh.siti@sapisehat.id", "password": "custom-password-123"},
    )
    assert login_old.status_code == 401

    # 6. Default password now works
    login_reset = client.post(
        "/api/auth/agency/login",
        json={"email": "drh.siti@sapisehat.id", "password": "agency-password"},
    )
    assert login_reset.status_code == 200
