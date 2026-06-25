"""Production model artifact policy tests."""

import pytest

from model.loader import ModelLoader
from utils.errors import ModelLoadError


def reset_loader():
    ModelLoader._instance = None
    ModelLoader._initialized = False


def test_dev_test_environment_may_use_deterministic_fallback(monkeypatch, tmp_path):
    reset_loader()
    monkeypatch.setattr("model.loader.settings.fastapi_env", "test")

    loader = ModelLoader(str(tmp_path / "missing.keras"))

    assert loader.model.count_params() == 0
    reset_loader()


def test_production_requires_real_model_artifact(monkeypatch, tmp_path):
    reset_loader()
    monkeypatch.setattr("model.loader.settings.fastapi_env", "production")

    with pytest.raises(ModelLoadError, match="Model file not found"):
        ModelLoader(str(tmp_path / "missing.keras"))

    reset_loader()
