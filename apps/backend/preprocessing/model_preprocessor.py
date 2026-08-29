"""Image preprocessing module - Tahap 2 (Model preprocessing)."""

import numpy as np  # type: ignore[import-not-found]
from PIL import Image, ImageOps
from typing import Union
from utils.errors import PreprocessingError
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelPreprocessor:
    """
    Tahap 2 Preprocessing: Convert image to model-ready numpy array.

    Steps:
    1. Correct EXIF orientation and convert to RGB.
    2. Resize to 224x224 with bilinear interpolation (verified contract).
    3. Convert to float32 pixels in [0, 255]; the model rescales internally.
    """

    # Constants
    INPUT_SIZE = 224

    @staticmethod
    def process(image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """
        Process image to model-ready numpy array.

        Args:
            image: PIL Image or numpy array (must be RGB)

        Returns:
            numpy array of shape (1, 224, 224, 3), dtype float32, values in [0, 255]

        Raises:
            PreprocessingError: If image processing fails
        """
        try:
            # Ensure PIL Image
            if isinstance(image, np.ndarray):
                pil_image = Image.fromarray(np.asarray(image, dtype=np.uint8), 'RGB')
            elif isinstance(image, Image.Image):
                pil_image = image
            else:
                raise PreprocessingError(f"Unsupported image type: {type(image)}")

            # Correct camera EXIF orientation before RGB conversion and resize.
            image = ImageOps.exif_transpose(pil_image).convert('RGB')

            image = image.resize(
                (ModelPreprocessor.INPUT_SIZE, ModelPreprocessor.INPUT_SIZE),
                Image.Resampling.BILINEAR,
            )

            # Keep the raw pixel range; the verified model rescales internally.
            array = np.array(image, dtype=np.float32)

            # Add batch dimension: (224, 224, 3) -> (1, 224, 224, 3)
            array = np.expand_dims(array, axis=0)

            logger.debug(f"Preprocessed image array shape: {array.shape}")

            return array

        except Exception as e:
            raise PreprocessingError(f"Image preprocessing failed: {str(e)}") from e
