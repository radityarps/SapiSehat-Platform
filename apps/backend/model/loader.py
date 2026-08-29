"""Verified three-output model loading and inference boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional

import numpy as np  # type: ignore[import-not-found]

try:  # Keep the API bootable in degraded mode when ML dependencies are absent.
    import tensorflow as tf
except ImportError:  # pragma: no cover - exercised only in minimal deployments
    tf = None

from config import MODEL_CLASS_ORDER, settings
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

    _instance: Optional["ModelLoader"] = None
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
            raise ModelLoadError("TensorFlow is required for the verified model artifact")

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
            raise ModelLoadError(
                f"Verified model metadata not found: {metadata_path}"
            )
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
        if metadata.get("model_version") != settings.model_version:
            raise ModelLoadError("Model metadata version does not match MODEL_VERSION")
        if settings.model_version.endswith("-pending"):
            raise ModelLoadError("MODEL_VERSION is pending verified artifact rollout")
        if metadata.get("artifact_status") not in {None, "verified"}:
            raise ModelLoadError("Model artifact is not marked verified")

        class_order = metadata.get("class_order")
        if tuple(class_order or ()) != tuple(MODEL_CLASS_ORDER):
            raise ModelLoadError("Model class_order must match the active output contract")
        indices = metadata.get("class_indices")
        if indices is not None:
            expected_indices = {str(i): label for i, label in enumerate(MODEL_CLASS_ORDER)}
            if indices != expected_indices:
                raise ModelLoadError("Model class_indices do not match the active order")

        preprocessing = metadata.get("preprocessing")
        if not isinstance(preprocessing, dict):
            raise ModelLoadError("Model preprocessing metadata is required")
        if _normalise_shape(preprocessing.get("input_size")) != (224, 224):
            raise ModelLoadError("Model input_size must be [224, 224]")
        if preprocessing.get("resize_method") != "bilinear":
            raise ModelLoadError("Model preprocessing resize_method must be bilinear")
        if preprocessing.get("channels") != 3 or preprocessing.get("color_mode") != "RGB":
            raise ModelLoadError("Model preprocessing must be RGB with three channels")
        pixel_range = preprocessing.get("input_range", preprocessing.get("value_range"))
        if _normalise_shape(pixel_range) != (0, 255):
            raise ModelLoadError("Model preprocessing input range must be [0, 255]")
        internal_rescaling = preprocessing.get("internal_rescaling")
        rescale_description = str(preprocessing.get("rescale", "")).lower()
        if (
            not isinstance(internal_rescaling, bool)
            or not internal_rescaling
        ) and "internal" not in rescale_description:
            raise ModelLoadError("Model must perform its own 1/255 internal rescaling")

        output_shape = _normalise_shape(
            metadata.get("output_shape", metadata.get("output", {}).get("shape"))
            if isinstance(metadata.get("output", {}), dict)
            else metadata.get("output_shape")
        )
        if output_shape not in {(None, 3), ("None", 3), (1, 3)}:
            raise ModelLoadError("Model output_shape must contain exactly three outputs")
        output_dtype = str(
            metadata.get("output_dtype", metadata.get("output", {}).get("dtype", ""))
        ).lower()
        if output_dtype not in {"float32", "<f4", "numpy.float32"}:
            raise ModelLoadError("Model output dtype must be float32")

        if not artifact.is_file() and not artifact.is_dir():
            raise ModelLoadError("Keras artifact must be a file or directory")
        declared_hash = metadata.get("keras_sha256")
        if not isinstance(declared_hash, str) or _sha256(artifact) != declared_hash:
            raise ModelLoadError("Keras artifact checksum does not match metadata")

        verification = metadata.get("verification") or metadata.get("parity")
        if (
            not isinstance(verification, dict)
            or not isinstance(verification.get("overall_pass"), bool)
            or not verification["overall_pass"]
        ):
            raise ModelLoadError("Authoritative model verification has not passed")
        verification_classes = verification.get("classes") or verification.get("class_order")
        if verification_classes is not None and tuple(verification_classes) != tuple(MODEL_CLASS_ORDER):
            raise ModelLoadError("Verification set classes do not match the active order")

    def _validate_loaded_model(self) -> None:
        inputs = getattr(self.model, "inputs", None)
        outputs = getattr(self.model, "outputs", None)
        if not isinstance(inputs, (list, tuple)) or len(inputs) != 1:
            raise ModelLoadError("Loaded model must have exactly one input tensor")
        if not isinstance(outputs, (list, tuple)) or len(outputs) != 1:
            raise ModelLoadError("Loaded model must have exactly one output tensor")

        input_tensor = inputs[0]
        input_shape = _normalise_shape(getattr(input_tensor, "shape", None))
        if input_shape not in {(None, *EXPECTED_INPUT_SHAPE), (1, *EXPECTED_INPUT_SHAPE)}:
            raise ModelLoadError("Loaded model input shape must be [None, 224, 224, 3]")
        input_dtype = str(getattr(input_tensor, "dtype", "")).lower()
        if input_dtype and input_dtype not in {EXPECTED_INPUT_DTYPE, "<f4", "numpy.float32"}:
            raise ModelLoadError("Loaded model input dtype must be float32")

        output_tensor = outputs[0]
        output_shape = _normalise_shape(getattr(output_tensor, "shape", None))
        if output_shape not in {(None, 3), (1, 3)}:
            raise ModelLoadError("Loaded model output shape must be [None, 3]")
        output_dtype = str(getattr(output_tensor, "dtype", "")).lower()
        if output_dtype and output_dtype not in {EXPECTED_OUTPUT_DTYPE, "<f4", "numpy.float32"}:
            raise ModelLoadError("Loaded model output dtype must be float32")

    def _compatible_load_path(self, path: Path) -> str:
        """Return a loadable path, patching newer Keras config keys if needed."""
        if not (path.is_dir() and str(path).endswith(".keras")):
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
            return array
        except ModelLoadError:
            raise
        except Exception as exc:
            raise ModelLoadError(f"Model inference failed: {exc}") from exc
