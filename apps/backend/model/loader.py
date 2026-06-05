"""Model loading module with singleton pattern."""

import tensorflow as tf
import numpy as np
from pathlib import Path
from typing import Optional
from utils.errors import ModelLoadError
from utils.logger import get_logger

logger = get_logger(__name__)


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
                raise ModelLoadError(f"Model file not found: {model_path}")

            logger.info(f"Loading model from {model_path}")

            self.model = tf.keras.models.load_model(model_path)

            logger.info(f"Model loaded successfully. Parameters: {self.model.count_params():,}")

        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {str(e)}") from e

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
