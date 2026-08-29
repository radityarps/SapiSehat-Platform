"""CORS production policy tests."""

import pytest

from config import resolve_cors_origins


def test_development_cors_defaults_to_local_origins():
    assert resolve_cors_origins(fastapi_env="development", cors_origins="") == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://10.0.2.2:3000",
    ]


def test_production_cors_rejects_wildcard():
    with pytest.raises(ValueError, match="CORS_ORIGINS must not contain wildcard origins"):
        resolve_cors_origins(fastapi_env="production", cors_origins="*")


def test_production_cors_uses_explicit_origins():
    assert resolve_cors_origins(
        fastapi_env="production",
        cors_origins="https://dashboard.sapisehat.id,https://api.sapisehat.id",
    ) == ["https://dashboard.sapisehat.id", "https://api.sapisehat.id"]
