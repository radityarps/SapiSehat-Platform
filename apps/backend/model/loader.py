"""Model loading module with singleton pattern."""

import tensorflow as tf
import numpy as np
import json
import shutil
import tempfile
from pathlib import Path
from config import settings
from typing import Optional
from utils.errors import ModelLoadError
from utils.logger import get_logger

logger = get_logger(__name__)

class DeterministicFallbackModel:
    """Small deterministic model used when no local model file exists in dev/test."""

    def count_params(self) -> int:
        return 0

    def predict(self, image_array: np.ndarray, verbose: int = 0) -> np.ndarray:
        mean = float(np.mean(image_array))
        logits = np.array([[mean, 1.0 - mean, 0.5]], dtype=np.float32)
        return logits


class ModelLoader:
    """
    Singleton model loader to ensure model is loaded once in memory.
    Thread-safe implementation.
    """

    _instance: Optional["ModelLoader"] = None
    _initialized: bool = False

    def __new__(cls, model_path: str = "./model/mobilenetv2_best.keras"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        if not cls._instance._initialized:
            cls._instance._load_model(model_path)
            cls._instance._initialized = True

        return cls._instance

    def _load_model(self, model_path: str) -> None:
        """Load model from disk."""
        try:
            path = Path(model_path)

            if not path.exists():
                if settings.fastapi_env in {"development", "test"}:
                    logger.warning(
                        "Model file missing; using deterministic fallback model for development/test.",
                        extra={"model_path": model_path},
                    )
                    self.model = DeterministicFallbackModel()
                    self.class_names = list(settings.labels)
                    return
                raise ModelLoadError(f"Model file not found: {model_path}")

            logger.info(f"Loading model from {model_path}")

            load_path = self._compatible_load_path(path)
            self.model = tf.keras.models.load_model(load_path, compile=False)
            self.class_names = self._load_class_names()

            logger.info(f"Model loaded successfully. Parameters: {self.model.count_params():,}")

        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {str(e)}") from e

    def _load_class_names(self) -> list[str]:
        path = Path(settings.model_class_names_path)
        if not path.exists():
            return list(settings.labels)
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        ordered = [raw[key] for key in sorted(raw.keys(), key=lambda k: int(k))]
        return ["healthy" if name == "Healthy" else name for name in ordered]

    def _compatible_load_path(self, path: Path) -> str:
        """Return a loadable path, patching newer Keras config keys if needed."""
        if not (path.is_dir() and str(path).endswith(".keras")):
            return str(path)

        config_path = path / "config.json"
        if not config_path.exists():
            return f"{path}/"

        with config_path.open("r", encoding="utf-8") as handle:
            config = json.load(handle)

        changed = self._remove_key(config, "quantization_config")
        if not changed:
            return f"{path}/"

        temp_dir = Path(tempfile.mkdtemp(prefix="sapisehat_keras_compat_")) / path.name
        shutil.copytree(path, temp_dir)
        with (temp_dir / "config.json").open("w", encoding="utf-8") as handle:
            json.dump(config, handle)
        return f"{temp_dir}/"

    def _remove_key(self, value, key: str) -> bool:
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
        """
        Run inference on image array.

        Args:
            image_array: Input array of shape [1, 224, 224, 3]

        Returns:
            Model output as numpy array
        """
        try:
            output = self.model.predict(image_array, verbose=0)
            return output
        except Exception as e:
            raise ModelLoadError(f"Model inference failed: {str(e)}") from e
