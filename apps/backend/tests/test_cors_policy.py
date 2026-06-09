"""CORS production policy tests."""

import pytest

from config import resolve_cors_origins


def test_development_cors_allows_local_wildcard_default():
    assert resolve_cors_origins(fastapi_env="development", cors_origins="") == ["*"]


def test_production_cors_rejects_wildcard():
    with pytest.raises(ValueError, match="CORS_ORIGINS must not contain wildcard in production"):
        resolve_cors_origins(fastapi_env="production", cors_origins="*")


def test_production_cors_uses_explicit_origins():
    assert resolve_cors_origins(
        fastapi_env="production",
        cors_origins="https://dashboard.sapisehat.id,https://api.sapisehat.id",
    ) == ["https://dashboard.sapisehat.id", "https://api.sapisehat.id"]
