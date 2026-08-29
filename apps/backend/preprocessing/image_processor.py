"""Image preprocessing module - Tahap 1 (Client preprocessing)."""

import io
from PIL import Image, ExifTags
from typing import Union
from utils.errors import PreprocessingError
from utils.logger import get_logger

logger = get_logger(__name__)


class ClientPreprocessor:
    """
    Tahap 1 Preprocessing: Prepare image for upload/offline processing.
    
    Steps:
    1. Correct EXIF orientation
    2. Resize max dimension to 800px
    3. Compress as JPEG 85% quality
    4. Remove EXIF metadata (privacy)
    
    This preprocessing is done BEFORE uploading to server or before offline inference.
    Output: ~100-300KB JPEG ready for efficient transfer or processing.
    """
    
    MAX_DIMENSION = 800
    JPEG_QUALITY = 85
    
    @staticmethod
    def correct_orientation(image: Image.Image) -> Image.Image:
        """
        Correct image orientation based on EXIF data.
        
        Args:
            image: PIL Image
        
        Returns:
            Corrected PIL Image
        """
        try:
            # Try to get EXIF data
            exif_data = getattr(image, "_getexif", lambda: None)()
            
            if exif_data is None:
                return image
            
            # Find orientation tag
            for tag_id, tag_value in exif_data.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                
                if tag == "Orientation":
                    # Apply rotation based on orientation value
                    orientation = tag_value
                    
                    if orientation == 2:
                        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    elif orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 4:
                        image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    elif orientation == 5:
                        image = image.rotate(90, expand=True).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 7:
                        image = image.rotate(270, expand=True).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
                    
                    break
            
            return image
            
        except Exception as e:
            logger.warning(f"Failed to correct EXIF orientation: {e}")
            return image
    
    @staticmethod
    def resize_max(image: Image.Image, max_dimension: int = MAX_DIMENSION) -> Image.Image:
        """
        Resize image so max dimension doesn't exceed max_dimension.
        
        Args:
            image: PIL Image
            max_dimension: Maximum width or height in pixels
        
        Returns:
            Resized PIL Image
        """
        try:
            width, height = image.size
            if width <= max_dimension and height <= max_dimension:
                return image
            ratio = min(max_dimension / width, max_dimension / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except (TypeError, ValueError, ZeroDivisionError, OSError) as exc:
            raise PreprocessingError("Image resize failed") from exc
    
    @staticmethod
    def compress_jpeg(image: Image.Image, quality: int = JPEG_QUALITY) -> bytes:
        """
        Compress image as JPEG.
        
        Note: JPEG compression removes EXIF metadata automatically.
        
        Args:
            image: PIL Image
            quality: JPEG quality 1-100 (85 = good balance)
        
        Returns:
            JPEG bytes
        """
        output = io.BytesIO()
        
        # Ensure RGB (JPEG doesn't support RGBA)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    
    @staticmethod
    def process(image_input: Union[bytes, Image.Image]) -> bytes:
        """
        Process image through Tahap 1 pipeline.
        
        Args:
            image_input: Raw JPEG/PNG bytes or PIL Image
        
        Returns:
            Processed JPEG bytes (~100-300KB)
        
        Raises:
            PreprocessingError: If processing fails
        """
        try:
            # Load image if bytes
            if isinstance(image_input, bytes):
                image = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                raise PreprocessingError(f"Unsupported input type: {type(image_input)}")
            
            # Step 1: Correct EXIF orientation
            image = ClientPreprocessor.correct_orientation(image)
            logger.debug("EXIF orientation corrected")
            
            # Step 2: Resize max dimension to 800px
            image = ClientPreprocessor.resize_max(image, ClientPreprocessor.MAX_DIMENSION)
            logger.debug(f"Image resized to {image.size}")
            
            # Step 3: Compress JPEG (removes EXIF metadata)
            jpeg_bytes = ClientPreprocessor.compress_jpeg(image, ClientPreprocessor.JPEG_QUALITY)
            logger.info(f"Image preprocessed: {len(jpeg_bytes) / 1024:.1f}KB")
            
            return jpeg_bytes
            
        except PreprocessingError:
            raise
        except Exception as e:
            raise PreprocessingError(f"Client preprocessing failed: {str(e)}") from e
