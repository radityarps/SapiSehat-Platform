"""Verified active model artifact policy tests."""

import pytest  # type: ignore[import-not-found]

from model.loader import ModelLoader
from utils.errors import ModelLoadError


def reset_loader():
    ModelLoader._instance = None
    ModelLoader._initialized = False


def test_active_model_requires_verified_artifact_in_test_environment(tmp_path):
    reset_loader()

    with pytest.raises(ModelLoadError, match="Verified model artifact not found"):
        ModelLoader(str(tmp_path / "missing.keras"))

    reset_loader()


def test_active_model_requires_real_artifact_in_production(monkeypatch, tmp_path):
    reset_loader()
    monkeypatch.setattr("model.loader.settings.fastapi_env", "production")

    with pytest.raises(ModelLoadError, match="Verified model artifact not found"):
        ModelLoader(str(tmp_path / "missing.keras"))

    reset_loader()
