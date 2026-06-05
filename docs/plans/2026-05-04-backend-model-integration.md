# Backend Model Integration — PyTorch → TensorFlow/Keras

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task via Pi Agent.

**Goal:** Migrate the SapiSehat backend from PyTorch (`.pth`) to TensorFlow/Keras (`.keras`) to support the partner's trained `mobilenetv2_best.keras` model, including corrected preprocessing and class labels.

**Architecture:** Replace PyTorch inference stack with TensorFlow/Keras while preserving the existing clean separation: HTTP layer (FastAPI) → pure inference logic (InferenceService) → model loading (TensorFlow singleton). Preprocessing changes from ImageNet normalization to simple rescale (÷255) to match training.

**Tech Stack:** Python 3.10+, FastAPI, TensorFlow 2.19+, Keras 3.13+, NumPy, Pillow

**Key decisions from user:**
- Labels: `PMK`, `LATO_LATO`, `HEALTHY` (not FMD/LSD/healthy — those are English equivalents)
- Preprocessing: Simple rescale `/255.0` only, NO ImageNet normalization
- Backend stays Python/FastAPI (no Go migration yet)
- Model path: `apps/backend/model/` — files already present: `config.json`, `model.weights.h5`, `metadata.json`, `class_names.json`
- Partner handles TFLite conversion for mobile

---

## Pre-flight Checklist

Before any code changes, verify the model loads correctly:

```bash
cd "/mnt/d/Files/Documents/Kuliah/Tugas Akhir/apps/backend"
python3 -c "
import tensorflow as tf
model = tf.keras.models.load_model('./model/mobilenetv2_best.keras')
print('Model loaded. Input shape:', model.input_shape)
print('Output shape:', model.output_shape)
print('Layers:', len(model.layers))
"
```

**Expected:** Input (None, 224, 224, 3), Output (None, 3), no errors.

Then verify preprocessing with a test image:

```bash
python3 -c "
import numpy as np
from PIL import Image
import tensorflow as tf
import json

model = tf.keras.models.load_model('./model/mobilenetv2_best.keras')
with open('./model/class_names.json') as f:
    class_names = json.load(f)

# Create test image
img = Image.new('RGB', (224, 224), color=(128, 128, 128))
img_array = np.array(img, dtype=np.float32) / 255.0
img_array = np.expand_dims(img_array, axis=0)

preds = model.predict(img_array, verbose=0)
pred_idx = int(np.argmax(preds[0]))
print(f'Predicted: {class_names[str(pred_idx)]}, confidence: {float(preds[0][pred_idx]):.4f}')
print(f'All scores: {preds[0].tolist()}')
"
```

**Expected:** No errors, valid prediction with 3 probability scores.

---

### Task 1: Update `requirements.txt`

**Objective:** Replace PyTorch dependencies with TensorFlow

**Files:**
- Modify: `apps/backend/requirements.txt`

**Step 1: Write content**

```txt
tensorflow>=2.19.0
fastapi>=0.115.0
uvicorn>=0.30.0
gunicorn>=23.0.0
pillow>=10.4.0
pydantic>=2.9.0
pydantic-settings>=2.6.0
python-multipart>=0.0.9
python-dotenv>=1.0.1
numpy>=2.0.0
```

Removed: `torch==2.6.0`, `torchvision==0.21.0` (no longer needed).
No new deps beyond tensorflow — keras comes bundled with tf 2.19.

**Step 2: Install and verify**

```bash
cd apps/backend
pip install -r requirements.txt
python3 -c "import tensorflow; print('TF', tensorflow.__version__)"
```

**Expected:** TF version printed, no import errors.

**Step 3: Commit**

```bash
git add apps/backend/requirements.txt
git commit -m "deps: replace PyTorch with TensorFlow for Keras model support"
```

---

### Task 2: Update `config.py` — Labels and Model Settings

**Objective:** Change class labels and remove PyTorch-specific settings

**Files:**
- Modify: `apps/backend/config.py`

**Step 1: Replace labels and model settings**

Current (lines 28-31):
```python
    model_version: str = "1.0.0"
    labels: list = ["SEHAT", "PMK", "LATO_LATO"]
    confidence_threshold: float = 0.60
    input_size: int = 224
```

Replace with:
```python
    model_version: str = "1.0.0"
    labels: list = ["PMK", "LATO_LATO", "HEALTHY"]
    confidence_threshold: float = 0.60
    input_size: int = 224
    
    # Model file settings (Keras format)
    model_format: str = os.getenv("MODEL_FORMAT", "keras")  # "keras" or "tflite"
    model_config_path: str = os.getenv("MODEL_CONFIG_PATH", "./model/config.json")
    model_weights_path: str = os.getenv("MODEL_WEIGHTS_PATH", "./model/model.weights.h5")
    class_names_path: str = os.getenv("CLASS_NAMES_PATH", "./model/class_names.json")
```

Also update `model_path` default (line 14):
```python
    model_path: str = os.getenv("MODEL_PATH", "./model/mobilenetv2_best.keras")
```

Remove `device` setting (line 15) — TensorFlow handles device placement automatically:
```python
    # REMOVE: device: str = os.getenv("DEVICE", "cpu")
```

**Step 2: Update display label mapping location**

Note: `_get_display_label` in `inference_server.py` must be updated separately. This task only handles config. The display mapping:
- `PMK` → "Penyakit Mulut & Kuku (PMK)"
- `LATO_LATO` → "Penyakit Lato-Lato (LSD)"
- `HEALTHY` → "Sapi Sehat"

**Step 3: Verify**

```bash
cd apps/backend
python3 -c "from config import settings; print(settings.labels); print(settings.model_path)"
```

**Expected:** `['PMK', 'LATO_LATO', 'HEALTHY']` and `./model/mobilenetv2_best.keras`

**Step 4: Commit**

```bash
git add apps/backend/config.py
git commit -m "feat: update labels to PMK/LATO_LATO/HEALTHY, add Keras model paths"
```

---

### Task 3: Rewrite `model/loader.py` — TensorFlow Model Loader

**Objective:** Replace PyTorch singleton loader with TensorFlow/Keras singleton

**Files:**
- Modify: `apps/backend/model/loader.py`

**Step 1: Write new loader.py**

```python
"""Model loading module with singleton pattern (TensorFlow/Keras)."""

import tensorflow as tf
import threading
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from utils.errors import ModelLoadError
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelLoader:
    """
    Singleton model loader for TensorFlow/Keras models.
    Thread-safe implementation.
    Supports .keras format (native Keras 3) and .h5 format.
    """
    
    _instance: Optional["ModelLoader"] = None
    _lock = threading.Lock()
    
    def __new__(
        cls,
        model_path: str = "./model/mobilenetv2_best.keras",
        config_path: Optional[str] = None,
        weights_path: Optional[str] = None,
    ):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        
        if not cls._instance._initialized:
            cls._instance._load_model(model_path, config_path, weights_path)
            cls._instance._initialized = True
        
        return cls._instance
    
    def _load_model(
        self,
        model_path: str,
        config_path: Optional[str] = None,
        weights_path: Optional[str] = None,
    ) -> None:
        """Load Keras model from disk."""
        try:
            path = Path(model_path)
            
            if path.suffix == '.keras' and path.exists():
                # Native Keras format — load directly
                logger.info(f"Loading Keras model from {model_path}")
                self.model = tf.keras.models.load_model(str(path))
                logger.info(
                    f"Model loaded. Input shape: {self.model.input_shape}, "
                    f"Output shape: {self.model.output_shape}"
                )
            elif config_path and weights_path:
                # Separate config + weights
                cfg = Path(config_path)
                wts = Path(weights_path)
                if not cfg.exists():
                    raise ModelLoadError(f"Model config not found: {config_path}")
                if not wts.exists():
                    raise ModelLoadError(f"Model weights not found: {weights_path}")
                
                logger.info(f"Loading model from config={config_path}, weights={weights_path}")
                with open(str(cfg), 'r') as f:
                    model_json = f.read()
                self.model = tf.keras.models.model_from_json(model_json)
                self.model.load_weights(str(wts))
            else:
                raise ModelLoadError(
                    f"Model file not found: {model_path}. "
                    f"Expected .keras file or provide config_path + weights_path."
                )
            
            logger.info(
                f"Model ready. Parameters: {self.model.count_params():,}"
            )
            
        except ModelLoadError:
            raise
        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {str(e)}") from e
    
    def predict(self, image_batch) -> Any:
        """
        Run inference on preprocessed image batch.
        
        Args:
            image_batch: NumPy array of shape [batch, 224, 224, 3], float32, values in [0, 1]
        
        Returns:
            Model predictions — NumPy array of shape [batch, num_classes]
        """
        try:
            predictions = self.model.predict(image_batch, verbose=0)
            return predictions
        except Exception as e:
            raise ModelLoadError(f"Model inference failed: {str(e)}") from e
    
    @property
    def input_shape(self):
        """Return the model's expected input shape."""
        return self.model.input_shape
    
    @property
    def output_shape(self):
        """Return the model's output shape."""
        return self.model.output_shape
```

**Step 2: Verify model loads**

```bash
cd apps/backend
python3 -c "
from model.loader import ModelLoader
loader = ModelLoader('./model/mobilenetv2_best.keras')
print('Input:', loader.input_shape)
print('Params:', loader.model.count_params())
"
```

**Expected:** Input (None, 224, 224, 3), parameter count printed.

**Step 3: Commit**

```bash
git add apps/backend/model/loader.py
git commit -m "feat: rewrite model loader for TensorFlow/Keras (singleton)"
```

---

### Task 4: Rewrite `preprocessing/model_preprocessor.py` — Simple Rescale

**Objective:** Replace ImageNet normalization with simple rescale (÷255)

**Files:**
- Modify: `apps/backend/preprocessing/model_preprocessor.py`

**Step 1: Write new preprocessor**

```python
"""Image preprocessing module — Tahap 2 (Model preprocessing, TensorFlow)."""

import numpy as np
from PIL import Image
from typing import Union
from utils.errors import PreprocessingError
from utils.logger import get_logger

logger = get_logger(__name__)


class ModelPreprocessor:
    """
    Tahap 2 Preprocessing: Convert image to model-ready numpy array.
    
    Steps (MATCHES training pipeline exactly):
    1. Resize to 224x224 (MobileNetV2 input size)
    2. Convert to float32 numpy array
    3. Rescale pixel values: divide by 255.0 → [0.0, 1.0]
    
    IMPORTANT: This does NOT apply ImageNet normalization (mean/std).
    The partner's model was trained with simple rescale (1./255) only.
    Applying ImageNet normalization here would produce WRONG predictions.
    
    This preprocessing MUST BE IDENTICAL to Kotlin implementation
    (ModelPreprocessor.kt) to ensure consistent online/offline predictions.
    """
    
    INPUT_SIZE = 224
    
    @staticmethod
    def process(image: Union[Image.Image, np.ndarray]) -> np.ndarray:
        """
        Process image to model-ready numpy array.
        
        Args:
            image: PIL Image or numpy array (must be RGB)
        
        Returns:
            NumPy array of shape [1, 224, 224, 3], float32, values in [0.0, 1.0]
        
        Raises:
            PreprocessingError: If image processing fails
        """
        try:
            # Convert numpy array to PIL if needed
            if isinstance(image, np.ndarray):
                image = Image.fromarray(image.astype('uint8'), 'RGB')
            elif not isinstance(image, Image.Image):
                raise PreprocessingError(f"Unsupported image type: {type(image)}")
            
            # Ensure RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Step 1: Resize to 224x224
            image = image.resize(
                (ModelPreprocessor.INPUT_SIZE, ModelPreprocessor.INPUT_SIZE),
                Image.Resampling.LANCZOS
            )
            
            # Step 2+3: Convert to float32 numpy and rescale
            img_array = np.array(image, dtype=np.float32) / 255.0
            
            # Add batch dimension: [224, 224, 3] → [1, 224, 224, 3]
            img_array = np.expand_dims(img_array, axis=0)
            
            logger.debug(f"Preprocessed image shape: {img_array.shape}, range: [{img_array.min():.3f}, {img_array.max():.3f}]")
            
            return img_array
            
        except Exception as e:
            raise PreprocessingError(f"Image preprocessing failed: {str(e)}") from e
```

**Step 2: Verify preprocessing**

```bash
cd apps/backend
python3 -c "
from PIL import Image
from preprocessing.model_preprocessor import ModelPreprocessor
import numpy as np

img = Image.new('RGB', (800, 600), color=(128, 128, 128))
result = ModelPreprocessor.process(img)
print('Shape:', result.shape)
print('Dtype:', result.dtype)
print('Min:', result.min(), 'Max:', result.max())
# Should be [1, 224, 224, 3], float32, range ~[0.5, 0.5]
assert result.shape == (1, 224, 224, 3)
assert result.dtype == np.float32
assert 0.0 <= result.min() <= result.max() <= 1.0
print('ALL CHECKS PASSED')
"
```

**Step 3: Commit**

```bash
git add apps/backend/preprocessing/model_preprocessor.py
git commit -m "feat: replace ImageNet normalization with simple rescale (/255)"
```

---

### Task 5: Rewrite `inference_server.py` — TensorFlow Inference

**Objective:** Replace PyTorch inference with TensorFlow/numpy inference

**Files:**
- Modify: `apps/backend/inference_server.py`

**Step 1: Write new inference_server.py**

```python
"""Core inference service — NO FastAPI/HTTP coupling (TensorFlow/Keras)."""

import time
import numpy as np
from typing import Dict, Any, Optional
from PIL import Image
from config import settings
from model.loader import ModelLoader
from preprocessing.model_preprocessor import ModelPreprocessor
from utils.errors import InferenceError
from utils.logger import get_logger

logger = get_logger(__name__)


class InferenceService:
    """
    Pure inference logic with NO HTTP/FastAPI coupling.
    Can be called from FastAPI, Go, or any other framework.
    
    Uses TensorFlow/Keras model loaded via singleton ModelLoader.
    Preprocessing matches partner's training: resize 224×224 + rescale /255.
    """
    
    LABELS = settings.labels  # ["PMK", "LATO_LATO", "HEALTHY"]
    CONFIDENCE_THRESHOLD = settings.confidence_threshold  # 0.60
    
    def __init__(self):
        """Initialize inference service with singleton model loader."""
        self.model_loader = ModelLoader(
            model_path=settings.model_path,
            config_path=getattr(settings, 'model_config_path', None),
            weights_path=getattr(settings, 'model_weights_path', None),
        )
        self.preprocessor = ModelPreprocessor()
        logger.info("InferenceService initialized (TensorFlow/Keras backend)")
    
    def predict(self, image: Image.Image) -> Dict[str, Any]:
        """
        Pure inference — NO HTTP logic.
        
        Args:
            image: PIL Image in RGB format
        
        Returns:
            Dict with prediction results matching existing API schema
        """
        start_time = time.time()
        
        try:
            # Preprocessing: resize + rescale (NO ImageNet normalization)
            image_array = self.preprocessor.process(image)
            
            preprocessing_ms = int((time.time() - start_time) * 1000)
            infer_start = time.time()
            
            # Inference
            predictions = self.model_loader.predict(image_array)
            probs = predictions[0]  # Shape: (num_classes,)
            
            inference_ms = int((time.time() - infer_start) * 1000)
            total_ms = int((time.time() - start_time) * 1000)
            
            # Get prediction
            pred_idx = int(np.argmax(probs))
            pred_label = self.LABELS[pred_idx]
            pred_confidence = float(probs[pred_idx])
            is_reliable = pred_confidence >= self.CONFIDENCE_THRESHOLD
            
            # Log inference
            logger.info(
                f"Inference: {pred_label} ({pred_confidence:.2%}) "
                f"preprocessing={preprocessing_ms}ms, "
                f"inference={inference_ms}ms, "
                f"total={total_ms}ms"
            )
            
            # Build response (preserving existing API contract)
            result = {
                "status": "success",
                "prediction": {
                    "label": pred_label,
                    "display_label": self._get_display_label(pred_label),
                    "confidence": round(pred_confidence, 4),
                    "is_reliable": is_reliable,
                    "scores": {
                        self.LABELS[i]: round(float(probs[i]), 4)
                        for i in range(len(self.LABELS))
                    }
                },
                "model_info": {
                    "version": settings.model_version
                },
                "processing_time_ms": total_ms,
                "preprocessing_time_ms": preprocessing_ms,
                "inference_time_ms": inference_ms
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Inference failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            }
    
    @staticmethod
    def _get_display_label(label: str) -> str:
        """Get Indonesian display label for prediction."""
        display_map = {
            "PMK": "Penyakit Mulut & Kuku (PMK)",
            "LATO_LATO": "Penyakit Lato-Lato (LSD)",
            "HEALTHY": "Sapi Sehat"
        }
        return display_map.get(label, label)


_service_init_error: Optional[str] = None

# Singleton instance — try to load model once on module import.
# If model is missing, keep app bootable in degraded mode.
try:
    inference_service: Optional[InferenceService] = InferenceService()
except Exception as e:
    inference_service = None
    _service_init_error = str(e)
    logger.warning(
        "Inference service unavailable at startup. "
        "API will run in degraded mode until model is provided.",
        extra={"model_path": settings.model_path, "error": _service_init_error}
    )


def is_model_ready() -> bool:
    """Return True when inference model is loaded and ready."""
    return inference_service is not None


def get_inference_service() -> InferenceService:
    """Return active inference service or raise a clear error when unavailable."""
    if inference_service is None:
        error_message = _service_init_error or "Model service not initialized"
        raise InferenceError(
            f"Model not loaded. Expected file at '{settings.model_path}'. "
            f"Startup error: {error_message}"
        )
    return inference_service


def get_model_status() -> Dict[str, Any]:
    """Expose model readiness details for health endpoint."""
    return {
        "model_loaded": inference_service is not None,
        "model_path": settings.model_path,
        "error": _service_init_error,
    }
```

**Step 2: Verify inference service works**

```bash
cd apps/backend
python3 -c "
from PIL import Image
from inference_server import get_inference_service, is_model_ready

print('Model ready:', is_model_ready())
if is_model_ready():
    svc = get_inference_service()
    img = Image.new('RGB', (224, 224), color=(128, 128, 128))
    result = svc.predict(img)
    print('Status:', result['status'])
    print('Prediction:', result['prediction']['label'])
    print('Confidence:', result['prediction']['confidence'])
    print('Scores:', result['prediction']['scores'])
"
```

**Expected:** Model ready: True, valid prediction with 3 scores.

**Step 3: Commit**

```bash
git add apps/backend/inference_server.py
git commit -m "feat: rewrite inference service for TensorFlow/Keras backend"
```

---

### Task 6: Update `api/schemas.py` — No schema changes needed

**Objective:** Verify schemas are compatible with new labels

**Files:**
- Review: `apps/backend/api/schemas.py`

**Step 1: Review — no changes required**

The existing Pydantic schemas (`PredictResponse`, `PredictionResult`, `HealthResponse`) are label-agnostic — they accept any string labels via `Dict[str, float]` for scores and `str` for label. No schema changes needed. The display_label mapping is handled in `inference_server.py` (Task 5).

**Step 2: Skip commit** (no changes)

---

### Task 7: Update `api/routes.py` — Verify compatibility

**Objective:** Ensure routes work with TensorFlow inference service

**Files:**
- Review: `apps/backend/api/routes.py`

**Step 1: Review — minor updates only**

The current routes call `get_inference_service()` which returns `InferenceService`. The interface hasn't changed — `service.predict(img_pil)` still returns the same Dict structure. One update needed: Pix2Pix validation message mentions "JPEG, PNG, WebP" — this is fine as-is. No functional changes required.

However, let's add a small improvement: the content_type check can be broadened slightly:

Current (line 52):
```python
if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
```

Update to also accept `image/jpg`:
```python
if image.content_type not in ["image/jpeg", "image/jpg", "image/png", "image/webp"]:
```

**Step 2: Commit**

```bash
git add apps/backend/api/routes.py
git commit -m "fix: accept image/jpg content type in predict endpoint"
```

---

### Task 8: Rewrite `tests/test_inference.py` — TensorFlow Tests

**Objective:** Rewrite all tests for TensorFlow backend

**Files:**
- Modify: `apps/backend/tests/test_inference.py`

**Step 1: Write new test file**

```python
"""Unit tests for inference service (TensorFlow/Keras backend)."""

import unittest
import numpy as np
from PIL import Image
from inference_server import inference_service
from preprocessing.model_preprocessor import ModelPreprocessor
from utils.errors import PreprocessingError


class TestModelPreprocessor(unittest.TestCase):
    """Test Tahap 2 preprocessing (simple rescale, no ImageNet norm)."""
    
    def test_preprocessing_returns_correct_shape(self):
        """Test that preprocessing returns correct array shape."""
        img = Image.new('RGB', (800, 600), color='red')
        result = ModelPreprocessor.process(img)
        self.assertEqual(result.shape, (1, 224, 224, 3))
        self.assertEqual(result.dtype, np.float32)
    
    def test_preprocessing_values_in_range(self):
        """Test that preprocessed values are in [0, 1] range (rescale only)."""
        # Pure white (255, 255, 255) → ~1.0 after rescale
        img_white = Image.new('RGB', (224, 224), color=(255, 255, 255))
        result_white = ModelPreprocessor.process(img_white)
        self.assertAlmostEqual(float(result_white.max()), 1.0, places=1)
        
        # Pure black (0, 0, 0) → ~0.0 after rescale
        img_black = Image.new('RGB', (224, 224), color=(0, 0, 0))
        result_black = ModelPreprocessor.process(img_black)
        self.assertAlmostEqual(float(result_black.min()), 0.0, places=1)
    
    def test_preprocessing_is_deterministic(self):
        """Test that preprocessing produces deterministic output."""
        img1 = Image.new('RGB', (256, 256), color=(100, 150, 200))
        img2 = Image.new('RGB', (256, 256), color=(100, 150, 200))
        result1 = ModelPreprocessor.process(img1)
        result2 = ModelPreprocessor.process(img2)
        self.assertTrue(np.allclose(result1, result2))
    
    def test_preprocessing_handles_different_formats(self):
        """Test that preprocessing handles RGBA and grayscale images."""
        img_rgb = Image.new('RGB', (300, 300), color='green')
        img_rgba = Image.new('RGBA', (300, 300), color=(0, 255, 0, 128))
        img_gray = Image.new('L', (300, 300), color=100)
        
        for img in [img_rgb, img_rgba, img_gray]:
            result = ModelPreprocessor.process(img)
            self.assertEqual(result.shape, (1, 224, 224, 3))
    
    def test_preprocessing_no_imagenet_normalization(self):
        """CRITICAL: Verify preprocessing does NOT apply ImageNet normalization.
        
        After simple rescale (/255), values should be in [0, 1].
        If ImageNet normalization were applied, values would be in ~[-2, 2].
        """
        img = Image.new('RGB', (224, 224), color=(128, 128, 128))
        result = ModelPreprocessor.process(img)
        
        # Mid-gray (128/255 ≈ 0.502) should be ~0.502, NOT negative
        self.assertGreater(float(result.mean()), 0.0)
        self.assertLess(float(result.mean()), 1.0)


class TestInferenceService(unittest.TestCase):
    """Test InferenceService (TensorFlow/Keras backend)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = inference_service
    
    def test_predict_returns_valid_response_structure(self):
        """Test that predict returns properly structured response."""
        img = Image.new('RGB', (224, 224), color='red')
        result = self.service.predict(img)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("prediction", result)
        self.assertIn("model_info", result)
        self.assertIn("processing_time_ms", result)
    
    def test_predict_includes_required_fields(self):
        """Test that prediction includes all required fields."""
        img = Image.new('RGB', (224, 224), color='blue')
        result = self.service.predict(img)
        
        prediction = result["prediction"]
        self.assertIn("label", prediction)
        self.assertIn("display_label", prediction)
        self.assertIn("confidence", prediction)
        self.assertIn("is_reliable", prediction)
        self.assertIn("scores", prediction)
        
        self.assertIsInstance(prediction["label"], str)
        self.assertIsInstance(prediction["confidence"], float)
        self.assertIsInstance(prediction["is_reliable"], bool)
        self.assertIsInstance(prediction["scores"], dict)
    
    def test_predict_label_is_valid(self):
        """Test that predicted label is one of valid classes."""
        img = Image.new('RGB', (224, 224), color='green')
        result = self.service.predict(img)
        label = result["prediction"]["label"]
        self.assertIn(label, self.service.LABELS)
    
    def test_predict_confidence_in_valid_range(self):
        """Test that confidence score is between 0 and 1."""
        img = Image.new('RGB', (400, 300), color='red')
        result = self.service.predict(img)
        confidence = result["prediction"]["confidence"]
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_predict_scores_sum_to_one(self):
        """Test that all prediction scores sum to approximately 1.0 (softmax)."""
        img = Image.new('RGB', (224, 224), color='yellow')
        result = self.service.predict(img)
        scores = result["prediction"]["scores"]
        total = sum(scores.values())
        self.assertAlmostEqual(total, 1.0, places=3)
    
    def test_predict_is_deterministic(self):
        """Test that predictions are deterministic for same image."""
        img1 = Image.new('RGB', (224, 224), color=(100, 150, 200))
        img2 = Image.new('RGB', (224, 224), color=(100, 150, 200))
        result1 = self.service.predict(img1)
        result2 = self.service.predict(img2)
        self.assertEqual(result1["prediction"]["label"], result2["prediction"]["label"])
        self.assertEqual(result1["prediction"]["confidence"], result2["prediction"]["confidence"])
    
    def test_predict_timing_is_reasonable(self):
        """Test that inference timing is reasonable."""
        img = Image.new('RGB', (224, 224), color='white')
        result = self.service.predict(img)
        total_ms = result["processing_time_ms"]
        self.assertGreater(total_ms, 0)
        self.assertLess(total_ms, 30000)  # Max 30 seconds
    
    def test_predict_labels_match_config(self):
        """Test that prediction uses the correct label set."""
        img = Image.new('RGB', (224, 224), color='white')
        result = self.service.predict(img)
        scores = result["prediction"]["scores"]
        
        # Verify all expected labels are present
        for label in ["PMK", "LATO_LATO", "HEALTHY"]:
            self.assertIn(label, scores)


class TestDisplayLabels(unittest.TestCase):
    """Test Indonesian display label mapping."""
    
    def test_display_labels(self):
        """Test that display labels are properly mapped."""
        from inference_server import InferenceService
        self.assertEqual(
            InferenceService._get_display_label("PMK"),
            "Penyakit Mulut & Kuku (PMK)"
        )
        self.assertEqual(
            InferenceService._get_display_label("LATO_LATO"),
            "Penyakit Lato-Lato (LSD)"
        )
        self.assertEqual(
            InferenceService._get_display_label("HEALTHY"),
            "Sapi Sehat"
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

**Step 2: Run tests**

```bash
cd apps/backend
python3 -m pytest tests/test_inference.py -v
```

**Expected:** All tests pass (10+ tests). If model is not loaded, some will be skipped or fail with clear error — that's acceptable.

**Step 3: Commit**

```bash
git add apps/backend/tests/test_inference.py
git commit -m "test: rewrite tests for TensorFlow backend + rescale preprocessing"
```

---

### Task 9: Integration Test — Full Backend Smoke Test

**Objective:** Verify the entire backend works end-to-end

**Files:**
- Test manually: start server, hit endpoints

**Step 1: Start the backend**

```bash
cd "/mnt/d/Files/Documents/Kuliah/Tugas Akhir/apps/backend"
python3 main.py &
sleep 5
```

**Step 2: Test health endpoint**

```bash
curl http://localhost:8000/api/health
```

**Expected:** `{"status":"ok","model_version":"1.0.0","model_loaded":true,...}`

**Step 3: Test predict endpoint**

```bash
# Create a test image
python3 -c "from PIL import Image; Image.new('RGB', (224,224), color='red').save('/tmp/test_cow.jpg')"

curl -X POST http://localhost:8000/api/predict \
  -F "image=@/tmp/test_cow.jpg"
```

**Expected:** Valid JSON response with `status: "success"`, prediction with 3 scores.

**Step 4: Stop server and commit**

```bash
kill %1 2>/dev/null || true
```

No git changes needed (manual test only).

---

## Verification Checklist (post-implementation)

- [ ] `requirements.txt` updated, `pip install -r requirements.txt` succeeds
- [ ] `config.py` has correct labels: `PMK`, `LATO_LATO`, `HEALTHY`
- [ ] `model/loader.py` loads `mobilenetv2_best.keras` without errors
- [ ] `model_preprocessor.py` does NOT apply ImageNet normalization (verified by test)
- [ ] `inference_server.py` uses TensorFlow predict, not PyTorch
- [ ] `python -m pytest tests/test_inference.py -v` — all tests pass
- [ ] `GET /api/health` returns 200 with model_loaded=true
- [ ] `POST /api/predict` returns valid prediction with 3 class scores
- [ ] Predictions use labels PMK/LATO_LATO/HEALTHY (not FMD/LSD/healthy)
- [ ] Old `.pth` model references completely removed from codebase
