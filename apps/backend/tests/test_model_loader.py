"""Fail-closed readiness checks for the verified model loader."""

import hashlib
import json
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np  # type: ignore[import-not-found]
import pytest  # type: ignore[import-not-found]

import model.loader as loader_module
from config import MODEL_CLASS_ORDER, MODEL_LABEL_MAPPING, settings
from model.loader import ModelLoader
from model.verification.verify_model_pair import REQUIRED_VERIFICATION_GATES
from utils.errors import ModelLoadError


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_fixture(tmp_path, *, metadata_status="verified", report=None):
    keras = tmp_path / "candidate.keras"
    keras.write_bytes(b"controlled keras artifact")
    tflite = tmp_path / "candidate.tflite"
    tflite.write_bytes(b"controlled tflite artifact")
    keras_hash = _sha256(keras)
    tflite_hash = _sha256(tflite)
    version = "controlled-model-v1"
    metadata = {
        "model_version": version,
        "base_model_version": "controlled-model",
        "architecture": "ControlledModel",
        "artifact_status": metadata_status,
        "keras_artifact": keras.name,
        "tflite_artifact": tflite.name,
        "keras_sha256": keras_hash,
        "tflite_sha256": tflite_hash,
        "class_order": list(MODEL_CLASS_ORDER),
        "class_indices": {
            str(index): label for index, label in enumerate(MODEL_CLASS_ORDER)
        },
        "label_mapping": dict(MODEL_LABEL_MAPPING),
        "preprocessing": {
            "input_size": [224, 224],
            "channels": 3,
            "color_mode": "RGB",
            "resize_method": "bilinear",
            "input_range": [0, 255],
            "internal_rescaling": True,
            "internal_rescaling_scale": 1 / 127.5,
            "internal_rescaling_offset": -1.0,
        },
        "tensor_contract": {
            "keras_input_tensor_count": 1,
            "keras_output_tensor_count": 1,
            "keras_input_shape": [None, 224, 224, 3],
            "keras_output_shape": [None, 3],
            "keras_input_dtype": "float32",
            "keras_output_dtype": "float32",
            "tflite_input_tensor_count": 1,
            "tflite_output_tensor_count": 1,
            "tflite_input_shape": [1, 224, 224, 3],
            "tflite_output_shape": [1, 3],
            "tflite_input_dtype": "float32",
            "tflite_output_dtype": "float32",
        },
        "verification": {
            "overall_pass": True,
            "report": "verification/verification_report.json",
        },
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    report = report or {
        "model_version": version,
        "activation_ready": True,
        "overall_pass": True,
        "artifact_status": "verified",
        "required_gates": list(REQUIRED_VERIFICATION_GATES),
        "gates": dict.fromkeys(REQUIRED_VERIFICATION_GATES, True),
        "artifacts": {
            "keras": {
                "sha256": keras_hash,
                "expected_sha256": keras_hash,
                "matches": True,
            },
            "tflite": {
                "sha256": tflite_hash,
                "expected_sha256": tflite_hash,
                "matches": True,
            },
        },
    }
    report_path = tmp_path / "verification_report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return keras, metadata_path, report_path, report


class _FakeTensor:
    shape = (None, 224, 224, 3)
    dtype = "float32"


class _FakeOutputTensor:
    shape = (None, 3)
    dtype = "float32"


class _FakeModel:
    def __init__(self):
        self.inputs = [_FakeTensor()]
        self.outputs = [_FakeOutputTensor()]

    def count_params(self):
        return 3

    def predict(self, image_array, verbose=0):
        return np.array([[0.8, 0.1, 0.1]], dtype=np.float32)


@pytest.fixture(autouse=True)
def reset_loader(monkeypatch):
    ModelLoader._instance = None
    ModelLoader._initialized = False
    monkeypatch.setattr(settings, "model_version", "controlled-model-v1")
    yield
    ModelLoader._instance = None
    ModelLoader._initialized = False


def _use_fake_tensorflow(monkeypatch, loaded=None):
    loaded = loaded or _FakeModel()
    load_model = Mock(return_value=loaded)

    fake_tf = SimpleNamespace(
        keras=SimpleNamespace(models=SimpleNamespace(load_model=load_model))
    )
    monkeypatch.setattr(loader_module, "tf", fake_tf)
    return load_model


def _use_report_path(monkeypatch, metadata_path, report_path):
    monkeypatch.setattr(settings, "model_metadata_path", str(metadata_path))
    report_target = metadata_path.parent / "verification" / "verification_report.json"
    report_target.parent.mkdir()
    report_target.write_bytes(report_path.read_bytes())


def test_pending_metadata_never_loads_candidate(tmp_path, monkeypatch):
    keras, metadata_path, report_path, _ = _write_fixture(
        tmp_path, metadata_status="pending"
    )
    _use_report_path(monkeypatch, metadata_path, report_path)
    load_model = _use_fake_tensorflow(monkeypatch)

    with pytest.raises(ModelLoadError, match="not marked verified"):
        ModelLoader(str(keras))

    load_model.assert_not_called()


def test_pending_report_never_loads_candidate(tmp_path, monkeypatch):
    keras, metadata_path, report_path, report = _write_fixture(tmp_path)
    report.update(
        activation_ready=False,
        overall_pass=False,
        artifact_status="pending",
    )
    report_path.write_text(json.dumps(report), encoding="utf-8")
    _use_report_path(monkeypatch, metadata_path, report_path)
    load_model = _use_fake_tensorflow(monkeypatch)

    with pytest.raises(ModelLoadError, match="Authoritative model verification"):
        ModelLoader(str(keras))

    load_model.assert_not_called()


def test_report_must_have_all_required_gates_true(tmp_path, monkeypatch):
    keras, metadata_path, report_path, report = _write_fixture(tmp_path)
    report["gates"][REQUIRED_VERIFICATION_GATES[0]] = False
    report_path.write_text(json.dumps(report), encoding="utf-8")
    _use_report_path(monkeypatch, metadata_path, report_path)
    _use_fake_tensorflow(monkeypatch)

    with pytest.raises(ModelLoadError, match="blocked gates"):
        ModelLoader(str(keras))


def test_malformed_report_fails_closed(tmp_path, monkeypatch):
    keras, metadata_path, report_path, _ = _write_fixture(tmp_path)
    report_path.write_text("not json", encoding="utf-8")
    _use_report_path(monkeypatch, metadata_path, report_path)
    _use_fake_tensorflow(monkeypatch)

    with pytest.raises(ModelLoadError, match="Invalid authoritative"):
        ModelLoader(str(keras))


def test_report_artifact_checksums_must_match_metadata(tmp_path, monkeypatch):
    keras, metadata_path, report_path, report = _write_fixture(tmp_path)
    report["artifacts"]["tflite"]["sha256"] = "0" * 64
    report_path.write_text(json.dumps(report), encoding="utf-8")
    _use_report_path(monkeypatch, metadata_path, report_path)
    _use_fake_tensorflow(monkeypatch)

    with pytest.raises(ModelLoadError, match="tflite checksum"):
        ModelLoader(str(keras))


def test_controlled_verified_fixture_loads_and_predicts(tmp_path, monkeypatch):
    keras, metadata_path, report_path, _ = _write_fixture(tmp_path)
    _use_report_path(monkeypatch, metadata_path, report_path)
    load_model = _use_fake_tensorflow(monkeypatch)

    loader = ModelLoader(str(keras))
    load_model.assert_called_once_with(str(keras), compile=False)
    result = loader.predict(np.zeros((1, 224, 224, 3), dtype=np.float32))

    assert loader.class_names == list(MODEL_CLASS_ORDER)
    assert result.dtype == np.float32
    assert result.shape == (1, 3)
    np.testing.assert_allclose(result, [[0.8, 0.1, 0.1]])
