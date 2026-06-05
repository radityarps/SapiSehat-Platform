"""Tests for selected model metadata and issue #23 traceability."""

import hashlib
import json
from pathlib import Path

from config import settings

ROOT = Path(__file__).resolve().parents[3]
BACKEND_MODEL_DIR = ROOT / "apps" / "backend" / "model"
MOBILE_ASSETS_DIR = ROOT / "apps" / "mobile" / "app" / "src" / "main" / "assets"

EXPECTED_BASE_VERSION = "cattle-disease-mobilenetv2-v20260601-s42"
EXPECTED_TFLITE_VERSION = f"{EXPECTED_BASE_VERSION}-dynamic-range"
EXPECTED_CLASS_ORDER = ["FMD", "LSD", "healthy"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_backend_metadata_matches_selected_model_contract():
    metadata = json.loads((BACKEND_MODEL_DIR / "metadata.json").read_text())

    assert metadata["model_version"] == EXPECTED_BASE_VERSION
    assert metadata["architecture"] == "mobilenetv2"
    assert metadata["class_order"] == EXPECTED_CLASS_ORDER
    assert metadata["class_indices"] == {"0": "FMD", "1": "LSD", "2": "healthy"}
    assert metadata["supported_disease_classes"] == EXPECTED_CLASS_ORDER
    assert metadata["preprocessing"]["input_size"] == [224, 224]
    assert metadata["preprocessing"]["color_mode"] == "RGB"
    assert metadata["preprocessing"]["rescale"] == "1/255"
    assert metadata["test_split_metrics"]["evaluated_on_split"] == "test"
    assert metadata["tflite_dynamic_range"]["overall_pass"] is True


def test_backend_settings_advertise_selected_model_version_and_class_order():
    assert settings.model_version == EXPECTED_BASE_VERSION
    assert settings.labels == EXPECTED_CLASS_ORDER
    assert settings.input_size == 224


def test_backend_keras_artifact_checksum_matches_metadata():
    metadata = json.loads((BACKEND_MODEL_DIR / "metadata.json").read_text())
    artifact = BACKEND_MODEL_DIR / metadata["keras_artifact"]

    assert artifact.exists()
    assert _sha256(artifact) == metadata["keras_sha256"]


def test_android_metadata_matches_backend_class_order_and_preprocessing():
    backend = json.loads((BACKEND_MODEL_DIR / "metadata.json").read_text())
    android = json.loads((MOBILE_ASSETS_DIR / "model_metadata.json").read_text())

    assert android["model_version"] == EXPECTED_TFLITE_VERSION
    assert android["base_model_version"] == backend["model_version"]
    assert android["class_order"] == backend["class_order"]
    assert android["class_indices"] == backend["class_indices"]
    assert (
        android["preprocessing"]["input_size"] == backend["preprocessing"]["input_size"]
    )
    assert (
        android["preprocessing"]["color_mode"] == backend["preprocessing"]["color_mode"]
    )
    assert android["preprocessing"]["rescale"] == backend["preprocessing"]["rescale"]
    assert android["parity"]["overall_pass"] is True


def test_android_tflite_artifact_checksum_matches_metadata():
    android = json.loads((MOBILE_ASSETS_DIR / "model_metadata.json").read_text())
    artifact = MOBILE_ASSETS_DIR / android["asset"]

    assert artifact.exists()
    assert _sha256(artifact) == android["sha256"]


def test_user_facing_metadata_uses_early_detection_warning_not_diagnosis_claim():
    backend = json.loads((BACKEND_MODEL_DIR / "metadata.json").read_text())
    android = json.loads((MOBILE_ASSETS_DIR / "model_metadata.json").read_text())

    for warning in (backend["warning"], android["warning"]):
        lower = warning.lower()
        assert "early detection" in lower
        assert "not a final clinical diagnosis" in lower
        assert "not" in lower and "veterinarian replacement" in lower
