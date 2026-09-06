"""Verified three-output model loading and inference boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import numpy as np  # type: ignore[import-not-found]

try:  # Keep the API bootable in degraded mode when ML dependencies are absent.
    import tensorflow as tf
except (ImportError, OSError):  # pragma: no cover - minimal deployments
    tf = None

from config import MODEL_CLASS_ORDER, MODEL_LABEL_MAPPING, settings
from model.verification.verify_model_pair import REQUIRED_VERIFICATION_GATES
from utils.errors import ModelLoadError
from utils.logger import get_logger

logger = get_logger(__name__)

EXPECTED_INPUT_SHAPE = (224, 224, 3)
EXPECTED_OUTPUT_SHAPE = (1, 3)
EXPECTED_INPUT_DTYPE = "float32"
EXPECTED_OUTPUT_DTYPE = "float32"


def _sha256(path: Path) -> str:
    """Hash a file or directory deterministically."""
    digest = hashlib.sha256()
    if path.is_file():
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with child.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _normalise_shape(value: Any) -> tuple[Any, ...] | None:
    if not isinstance(value, (list, tuple)):
        return None
    return tuple(value)


class ModelLoader:
    """Load exactly one verified Keras artifact for the active contract."""

    _instance: ModelLoader | None = None
    _initialized = False

    def __new__(cls, model_path: str | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        if not cls._instance._initialized:
            cls._instance._load_model(model_path or settings.model_path)
            cls._instance._initialized = True
        return cls._instance

    def _load_model(self, model_path: str) -> None:
        """Load and validate the artifact pair before making inference available."""
        path = Path(model_path)
        if not path.exists():
            raise ModelLoadError(
                f"Verified model artifact not found: {model_path}. "
                "Supply the matching three-output artifact and metadata."
            )
        if tf is None:
            raise ModelLoadError(
                "TensorFlow is required for the verified model artifact"
            )

        try:
            metadata = self._load_metadata()
            self._validate_metadata(metadata, path)
            logger.info("Loading verified model from %s", model_path)
            load_path = self._compatible_load_path(path)
            self.model = tf.keras.models.load_model(load_path, compile=False)
            self._validate_loaded_model()
            self.class_names = list(MODEL_CLASS_ORDER)
            self.metadata = metadata
            logger.info(
                "Verified model loaded successfully. Parameters: %s",
                f"{self.model.count_params():,}",
            )
        except ModelLoadError:
            raise
        except Exception as exc:
            raise ModelLoadError(f"Failed to load verified model: {exc}") from exc

    def _load_metadata(self) -> dict[str, Any]:
        metadata_path = Path(settings.model_metadata_path)
        if not metadata_path.is_file():
            raise ModelLoadError(f"Verified model metadata not found: {metadata_path}")
        try:
            with metadata_path.open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelLoadError(f"Invalid model metadata: {metadata_path}") from exc
        if not isinstance(metadata, dict):
            raise ModelLoadError("Model metadata must be a JSON object")
        return metadata

    def _validate_metadata(self, metadata: dict[str, Any], artifact: Path) -> None:
        """Reject missing, legacy, or unverified model contracts."""
        metadata_version = metadata.get("model_version")
        if (
            not isinstance(metadata_version, str)
            or not metadata_version.strip()
            or metadata_version != settings.model_version
        ):
            raise ModelLoadError("Model metadata version does not match MODEL_VERSION")
        if settings.model_version.endswith("-pending"):
            raise ModelLoadError("MODEL_VERSION is pending verified artifact rollout")
        if metadata.get("artifact_status") != "verified":
            raise ModelLoadError("Model artifact is not marked verified")

        class_order = metadata.get("class_order")
        if tuple(class_order or ()) != tuple(MODEL_CLASS_ORDER):
            raise ModelLoadError(
                "Model class_order must match the active output contract"
            )
        indices = metadata.get("class_indices")
        expected_indices = {str(i): label for i, label in enumerate(MODEL_CLASS_ORDER)}
        if indices != expected_indices:
            raise ModelLoadError(
                "Model class_indices do not match the raw output order"
            )
        if metadata.get("label_mapping") != MODEL_LABEL_MAPPING:
            raise ModelLoadError("Model canonical label mapping is invalid")

        preprocessing = metadata.get("preprocessing")
        if not isinstance(preprocessing, dict):
            raise ModelLoadError("Model preprocessing metadata is required")
        if _normalise_shape(preprocessing.get("input_size")) != (224, 224):
            raise ModelLoadError("Model input_size must be [224, 224]")
        if preprocessing.get("resize_method") != "bilinear":
            raise ModelLoadError("Model preprocessing resize_method must be bilinear")
        if (
            preprocessing.get("channels") != 3
            or preprocessing.get("color_mode") != "RGB"
        ):
            raise ModelLoadError("Model preprocessing must be RGB with three channels")
        pixel_range = preprocessing.get("input_range", preprocessing.get("value_range"))
        if _normalise_shape(pixel_range) != (0, 255):
            raise ModelLoadError("Model preprocessing input range must be [0, 255]")
        internal_rescaling = preprocessing.get("internal_rescaling")
        if (
            not isinstance(internal_rescaling, bool)
            or not internal_rescaling
            or preprocessing.get("internal_rescaling_scale") != 1 / 127.5
            or preprocessing.get("internal_rescaling_offset") != -1.0
        ):
            raise ModelLoadError(
                "Model must perform the declared 1/127.5 internal rescaling"
            )

        tensor_contract = metadata.get("tensor_contract")
        if not isinstance(tensor_contract, dict):
            raise ModelLoadError("Model tensor contract is required")
        expected_tensor_contract = {
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
        }
        if any(
            tensor_contract.get(key) != value
            for key, value in expected_tensor_contract.items()
        ):
            raise ModelLoadError(
                "Model tensor contract does not match the active contract"
            )

        if not artifact.is_file() and not artifact.is_dir():
            raise ModelLoadError("Keras artifact must be a file or directory")
        declared_hash = metadata.get("keras_sha256")
        if not isinstance(declared_hash, str) or _sha256(artifact) != declared_hash:
            raise ModelLoadError("Keras artifact checksum does not match metadata")

        verification = metadata.get("verification")
        if (
            not isinstance(verification, dict)
            or not isinstance(verification.get("overall_pass"), bool)
            or not verification.get("overall_pass")
        ):
            raise ModelLoadError("Authoritative model verification has not passed")
        report_reference = verification.get("report")
        if not isinstance(report_reference, str) or not report_reference.strip():
            raise ModelLoadError("Authoritative model verification report is missing")
        report_path = self._resolve_metadata_reference(report_reference)
        if not report_path.is_file():
            raise ModelLoadError("Authoritative model verification report is missing")
        try:
            with report_path.open("r", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelLoadError(
                "Invalid authoritative model verification report"
            ) from exc
        if (
            not isinstance(report, dict)
            or not isinstance(report.get("activation_ready"), bool)
            or not report.get("activation_ready")
            or not isinstance(report.get("overall_pass"), bool)
            or not report.get("overall_pass")
            or report.get("artifact_status") != "verified"
        ):
            raise ModelLoadError("Authoritative model verification has not passed")
        if report.get("model_version") != metadata.get("model_version"):
            raise ModelLoadError(
                "Verification report model version does not match metadata"
            )
        report_gates = report.get("gates")
        required_gates = report.get("required_gates")
        if (
            required_gates != list(REQUIRED_VERIFICATION_GATES)
            or not isinstance(report_gates, dict)
            or any(
                not isinstance(report_gates.get(name), bool)
                or not report_gates.get(name)
                for name in REQUIRED_VERIFICATION_GATES
            )
        ):
            raise ModelLoadError("Verification report contains blocked gates")
        report_artifacts = report.get("artifacts")
        if not isinstance(report_artifacts, dict):
            raise ModelLoadError("Verification report artifact checks are missing")
        for name, metadata_key in (
            ("keras", "keras_sha256"),
            ("tflite", "tflite_sha256"),
        ):
            expected_hash = metadata.get(metadata_key)
            entry = report_artifacts.get(name)
            if (
                not isinstance(expected_hash, str)
                or not isinstance(entry, dict)
                or entry.get("sha256") != expected_hash
                or entry.get("expected_sha256") != expected_hash
                or not isinstance(entry.get("matches"), bool)
                or not entry.get("matches")
            ):
                raise ModelLoadError(
                    f"Verification report {name} checksum does not match metadata"
                )

    def _resolve_metadata_reference(self, reference: str) -> Path:
        """Resolve a metadata reference relative to the repository or backend."""
        metadata_path = Path(settings.model_metadata_path).resolve()
        candidate = Path(reference)
        if candidate.is_absolute():
            return candidate
        if candidate.parts[:2] == ("apps", "backend"):
            candidate = Path(*candidate.parts[2:])
            return (metadata_path.parent.parent / candidate).resolve()
        return (metadata_path.parent / candidate).resolve()

    def _validate_loaded_model(self) -> None:
        inputs = getattr(self.model, "inputs", None)
        outputs = getattr(self.model, "outputs", None)
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 1:
            raise ModelLoadError("Loaded model must have exactly one input tensor")
        if not isinstance(outputs, (list, tuple)) or len(outputs) != 1:
            raise ModelLoadError("Loaded model must have exactly one output tensor")

        input_tensor = inputs[0]
        input_shape = _normalise_shape(getattr(input_tensor, "shape", None))
        if input_shape not in {
            (None, *EXPECTED_INPUT_SHAPE),
            (1, *EXPECTED_INPUT_SHAPE),
        }:
            raise ModelLoadError("Loaded model input shape must be [None, 224, 224, 3]")
        input_dtype = str(getattr(input_tensor, "dtype", "")).lower()
        if input_dtype not in {
            EXPECTED_INPUT_DTYPE,
            "<f4",
            "numpy.float32",
        }:
            raise ModelLoadError("Loaded model input dtype must be float32")

        output_tensor = outputs[0]
        output_shape = _normalise_shape(getattr(output_tensor, "shape", None))
        if output_shape not in {(None, 3), (1, 3)}:
            raise ModelLoadError("Loaded model output shape must be [None, 3]")
        output_dtype = str(getattr(output_tensor, "dtype", "")).lower()
        if output_dtype not in {
            EXPECTED_OUTPUT_DTYPE,
            "<f4",
            "numpy.float32",
        }:
            raise ModelLoadError("Loaded model output dtype must be float32")

    def _compatible_load_path(self, path: Path) -> str:
        """Return a loadable path, patching newer Keras config keys if needed."""
        if not (path.is_dir() and str(path).endswith(".keras")):
            if path.is_file() and path.suffix == ".keras":
                return self._compatible_file_load_path(path)
            return str(path)
        config_path = path / "config.json"
        if not config_path.exists():
            return f"{path}/"
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                config = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelLoadError(f"Invalid Keras model config: {config_path}") from exc
        if not self._remove_key(config, "quantization_config"):
            return f"{path}/"
        temp_dir = Path(tempfile.mkdtemp(prefix="sapisehat_keras_compat_")) / path.name
        shutil.copytree(path, temp_dir)
        with (temp_dir / "config.json").open("w", encoding="utf-8") as handle:
            json.dump(config, handle)
        return f"{temp_dir}/"

    def _compatible_file_load_path(self, path: Path) -> str:
        """Return a temporary Keras archive without unsupported config keys."""
        if not zipfile.is_zipfile(path):
            return str(path)
        try:
            with zipfile.ZipFile(path) as archive:
                config = json.loads(archive.read("config.json"))
                if not self._remove_key(config, "quantization_config"):
                    return str(path)
                output = Path(tempfile.mkdtemp(prefix="sapisehat_keras_")) / path.name
                with zipfile.ZipFile(output, "w") as patched:
                    for info in archive.infolist():
                        data = (
                            json.dumps(config).encode()
                            if info.filename == "config.json"
                            else archive.read(info)
                        )
                        patched.writestr(info, data)
            return str(output)
        except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            raise ModelLoadError(f"Invalid Keras model archive: {path}") from exc

    def _remove_key(self, value: Any, key: str) -> bool:
        changed = False
        if isinstance(value, dict):
            if key in value:
                value.pop(key)
                changed = True
            for nested in value.values():
                changed = self._remove_key(nested, key) or changed
        elif isinstance(value, list):
            for nested in value:
                changed = self._remove_key(nested, key) or changed
        return changed

    def predict(self, image_array: np.ndarray) -> np.ndarray:
        """Run inference and enforce the one-tensor, three-probability contract."""
        try:
            output = self.model.predict(image_array, verbose=0)
            if isinstance(output, (list, tuple)):
                if len(output) != 1:
                    raise ModelLoadError("Model must return exactly one output tensor")
                output = output[0]
            array = np.asarray(output)
            if array.shape != EXPECTED_OUTPUT_SHAPE:
                raise ModelLoadError("Model output must have shape [1, 3]")
            if array.dtype != np.float32:
                raise ModelLoadError("Model output tensor must be float32")
            if not np.all(np.isfinite(array)):
                raise ModelLoadError("Model output contains non-finite probabilities")
            if np.any(array < 0.0) or np.any(array > 1.0):
                raise ModelLoadError("Model output probabilities must be in [0, 1]")
            if not np.isclose(float(array.sum()), 1.0, atol=1e-3):
                raise ModelLoadError("Model output probabilities must sum to 1")
            return array
        except ModelLoadError:
            raise
        except Exception as exc:
            raise ModelLoadError(f"Model inference failed: {exc}") from exc
