"""Tests for the verified model contract and legacy model traceability."""

import hashlib
import json
from pathlib import Path

from config import ACTIVE_DETECTION_CLASSES, settings

from tests.conftest import BACKEND_ROOT, REPO_ROOT, repo_file

ROOT = REPO_ROOT
BACKEND_MODEL_DIR = BACKEND_ROOT / "model"
MOBILE_MODEL_DIR = ROOT / "apps" / "mobile" / "assets" / "model"
LEGACY_ASSETS_DIR = (
    ROOT / "apps" / "mobile-android-legacy" / "app" / "src" / "main" / "assets"
)
EXPECTED_MODEL_VERSION = "cattle-disease-mobilenetv3large-v20260902-pmk-fp32"
EXPECTED_BASE_VERSION = "cattle-disease-mobilenetv3large-v20260902-pmk"
EXPECTED_ARCHITECTURE = "MobileNetV3Large"
EXPECTED_CLASS_ORDER = ["non_sapi", "pmk", "sehat"]
EXPECTED_LABEL_MAPPING = {
    "non_sapi": "non_cattle",
    "pmk": "FMD",
    "sehat": "healthy",
}
EXPECTED_ACTIVE_CLASSES = list(ACTIVE_DETECTION_CLASSES)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(child.read_bytes())
    return digest.hexdigest()


def _read_json(relative_path: str) -> dict:
    return json.loads(repo_file(relative_path).read_text(encoding="utf-8"))


def test_backend_metadata_matches_verified_contract():
    metadata = _read_json("apps/backend/model/metadata.json")

    assert metadata["model_version"] == EXPECTED_MODEL_VERSION
    assert metadata["base_model_version"] == EXPECTED_BASE_VERSION
    assert metadata["architecture"] == EXPECTED_ARCHITECTURE
    assert metadata["artifact_status"] == "verified"
    assert metadata["class_order"] == EXPECTED_CLASS_ORDER
    assert metadata["class_indices"] == {
        str(index): label for index, label in enumerate(EXPECTED_CLASS_ORDER)
    }
    assert metadata["label_mapping"] == EXPECTED_LABEL_MAPPING
    assert set(EXPECTED_ACTIVE_CLASSES) == {"FMD", "healthy"}
    assert metadata["tensor_contract"]["keras_output_shape"] == [None, 3]
    assert metadata["tensor_contract"]["tflite_output_shape"] == [1, 3]
    assert metadata["preprocessing"] == {
        **metadata["preprocessing"],
        "resize_method": "bilinear",
        "input_range": [0, 255],
        "internal_rescaling": True,
    }
    assert metadata["verification"]["overall_pass"] is True


def test_backend_settings_use_verified_candidate():
    assert settings.model_version == EXPECTED_MODEL_VERSION
    assert settings.model_path.endswith("pmkbest.keras")
    assert settings.labels == EXPECTED_CLASS_ORDER
    assert tuple(EXPECTED_ACTIVE_CLASSES) == ACTIVE_DETECTION_CLASSES
    assert settings.input_size == 224


def test_backend_keras_artifact_checksum_matches_metadata():
    metadata = _read_json("apps/backend/model/metadata.json")
    artifact = BACKEND_MODEL_DIR / metadata["keras_artifact"]

    assert artifact.exists()
    assert _sha256(artifact) == metadata["keras_sha256"]


def test_flutter_metadata_and_asset_match_verified_backend_pair():
    backend = _read_json("apps/backend/model/metadata.json")
    mobile = _read_json("apps/mobile/assets/model/model_metadata.json")
    asset = MOBILE_MODEL_DIR / mobile["asset"]

    assert mobile["model_version"] == backend["model_version"]
    assert mobile["base_model_version"] == backend["base_model_version"]
    assert mobile["architecture"] == backend["architecture"]
    assert mobile["artifact_status"] == "verified"
    assert mobile["class_order"] == backend["class_order"]
    assert mobile["class_indices"] == backend["class_indices"]
    assert mobile["label_mapping"] == backend["label_mapping"]
    assert mobile["tensor_contract"]["input_shape"] == [1, 224, 224, 3]
    assert mobile["tensor_contract"]["output_shape"] == [1, 3]
    assert mobile["preprocessing"]["resize_method"] == "bilinear"
    assert mobile["preprocessing"]["input_range"] == [0, 255]
    assert mobile["verification"]["overall_pass"] is True
    assert asset.is_file()
    assert _sha256(asset) == mobile["sha256"]


def test_legacy_android_metadata_and_asset_remain_unchanged():
    metadata = _read_json(
        "apps/mobile-android-legacy/app/src/main/assets/model_metadata.json"
    )
    asset = LEGACY_ASSETS_DIR / metadata["asset"]

    assert metadata["class_order"] == ["FMD", "LSD", "healthy"]
    assert metadata["class_indices"] == {"0": "FMD", "1": "LSD", "2": "healthy"}
    assert metadata["asset"] == "cattle_disease.tflite"
    assert asset.is_file()
    assert _sha256(asset) == metadata["sha256"]


def test_verified_candidate_report_activates_inference():
    backend = _read_json("apps/backend/model/metadata.json")
    report = _read_json("apps/backend/model/verification/verification_report.json")

    assert backend["verification"]["report"] == (
        "apps/backend/model/verification/verification_report.json"
    )
    assert report["artifact_status"] == "verified"
    assert report["activation_ready"] is True
    assert report["overall_pass"] is True
    assert report["gates"]["metadata_pair_contract"] is True
    assert report["gates"]["artifact_checksums"] is True
    assert report["gates"]["metadata_activation_status"] is True
    assert report["gates"]["physical_android_offline_smoke"] is True


def test_user_facing_metadata_uses_early_detection_warning_not_diagnosis_claim():
    for relative_path in (
        "apps/backend/model/metadata.json",
        "apps/mobile/assets/model/model_metadata.json",
    ):
        warning = _read_json(relative_path)["warning"].lower()
        assert "early detection" in warning
        assert "not a final clinical diagnosis" in warning
        assert "veterinarian replacement" in warning
