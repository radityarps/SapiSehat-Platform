> **Legacy backend note:** Use this for FastAPI/image tracer development only. Current shared backend direction lives in [system integration backend](../../system-integration/backend/README.md). Shared backend contracts path: `docs/system-integration/backend/README.md`.

# SapiSehat Backend - Development Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI HTTP Server (Port 8000)                            │
├─────────────────────────────────────────────────────────────┤
│  - Request parsing                                          │
│  - CORS handling                                            │
│  - Error handling                                           │
│  - Response formatting                                      │
├─────────────────────────────────────────────────────────────┤
│  InferenceService (inference_server.py)                     │
├─────────────────────────────────────────────────────────────┤
│  - Pure inference logic (NO HTTP dependencies)              │
│  - Image preprocessing (Tahap 2)                            │
│  - Model inference                                          │
│  - Result formatting                                        │
├─────────────────────────────────────────────────────────────┤
│  ModelLoader (Singleton)                                    │
├─────────────────────────────────────────────────────────────┤
│  TensorFlow MobileNetV2 Model                                  │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Separation of Concerns

- **HTTP Layer** (FastAPI): Handles requests/responses
- **Inference Layer** (InferenceService): Pure logic, testable
- **Model Layer** (ModelLoader): Resource management

**Why:** Allows replacing HTTP layer (FastAPI → Go) without touching inference logic.

### 2. Singleton Model Loading

```python
# Model loaded ONCE in memory, reused for all requests
inference_service = InferenceService()  # Loads model on module import
```

**Why:** Model is 14MB and takes time to load. Load once, use many times.

### 3. Stateless Preprocessing

```python
# ModelPreprocessor.process() is pure function
# Same input → same output, every time
tensor = ModelPreprocessor.process(image)
```

**Why:** Can be ported to Go or other languages easily.

### 4. No HTTP Coupling in Inference

```python
# ✅ GOOD - InferenceService doesn't know about HTTP
result = inference_service.predict(image)

# ❌ BAD - Don't do this
from fastapi import Request
def predict(request: Request):
    # This couples inference to FastAPI
```

**Why:** Enables microservice architecture and testing.

## Development Workflow

### 1. Local Development (with hot-reload)

```bash
# Install dev dependencies
pip install -r requirements.txt pytest pytest-cov

# Run with hot-reload
python main.py

# In another terminal, test
curl http://localhost:8000/api/health
```

### 2. Running Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test
python -m pytest tests/test_inference.py::TestInferenceService::test_predict_returns_valid_response_structure -v

# With coverage
pytest --cov=. tests/
```

### 3. Docker Development

```bash
# Build and run
docker-compose build
docker-compose up

# View logs
docker-compose logs -f backend

# Test
curl http://localhost:8000/api/health

# Stop
docker-compose down
```

## Adding New Features

### Example: Add Image Validation Endpoint

**Step 1:** Add to `inference_server.py` (pure logic)

```python
class InferenceService:
    def validate_image(self, image: Image.Image) -> Dict[str, Any]:
        """Validate image quality."""
        return {
            "is_valid": True,
            "size": image.size,
            "mode": image.mode
        }
```

**Step 2:** Add test to `tests/test_inference.py`

```python
class TestInferenceService(unittest.TestCase):
    def test_validate_image(self):
        img = Image.new('RGB', (224, 224))
        result = self.service.validate_image(img)
        self.assertTrue(result["is_valid"])
```

**Step 3:** Add route to `api/routes.py`

```python
@router.post("/validate")
async def validate(image: UploadFile = File(...)):
    img = Image.open(io.BytesIO(await image.read()))
    result = inference_service.validate_image(img)
    return result
```

**Step 4:** Add schema to `api/schemas.py` (if needed)

```python
class ValidateResponse(BaseModel):
    is_valid: bool
    size: tuple
    mode: str
```

## Debugging

### Enable Verbose Logging

```bash
# Set log level in .env
LOG_LEVEL=debug

# Or via command line
FASTAPI_ENV=development DEBUG=true python main.py
```

### Debug Model Loading

```python
from model.loader import ModelLoader
loader = ModelLoader()
print(f"Model device: {loader.device}")
print(f"Model: {loader.model}")
```

### Trace Inference

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("inference_server")
logger.debug("Starting inference...")
```

## Performance Profiling

### Measure Inference Speed

```python
import time
from PIL import Image

img = Image.new('RGB', (224, 224))

start = time.time()
result = inference_service.predict(img)
elapsed = time.time() - start

print(f"Inference time: {elapsed:.2f}s")
print(f"Preprocessing: {result['preprocessing_time_ms']}ms")
print(f"Model inference: {result['inference_time_ms']}ms")
```

### Profile with cProfile

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... your code here ...
result = inference_service.predict(img)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## Common Issues & Solutions

### Issue: Model loads on every request

**Problem:** Model loaded multiple times, wasting memory

**Solution:** Use singleton pattern (already implemented in `ModelLoader`)

```python
# ✅ CORRECT
loader = ModelLoader()  # Returns same instance every time

# ❌ WRONG
model = tf.keras.models.load_model("model.keras")  # Loads every time
```

### Issue: Different predictions between requests for same image

**Problem:** Inference logic is non-deterministic

**Solution:** Set random seeds

```python
import tensorflow as tf
import numpy as np

tf.random.set_seed(42)
np.random.seed(42)
```

### Issue: Out of Memory (OOM)

**Problem:** Processing too large images or batch

**Solution:** Limit image size in preprocessing

```python
MAX_DIMENSION = 800  # Resize larger images down
```

### Issue: Slow inference on CPU

**Problem:** No GPU acceleration

**Solution:**

1. Enable GPU if available
2. Quantize model (30% faster)
3. Use smaller model

```python
# Check GPU
import tensorflow as tf
gpus = tf.config.list_physical_devices('GPU')
print(f"GPU available: {len(gpus) > 0}")

# TensorFlow automatically uses GPU if available — no manual device placement needed
```

## Deployment Checklist

Before deploying to production:

- [ ] All tests pass locally
- [ ] Tests pass in Docker container
- [ ] Model file included in deployment
- [ ] `.env` configured for production
- [ ] CORS settings configured
- [ ] Health check endpoint working
- [ ] Error logging configured
- [ ] Request timeouts set appropriately
- [ ] Model file size acceptable for platform
- [ ] GPU/CPU considerations documented

## Next Steps: Phase 3 Go Migration

When ready to scale beyond 200 req/min:

1. **Decouple inference service**
   - Run as separate Python microservice (port 9000)
   - Communicate via gRPC or REST

2. **Create Go gateway**
   - HTTP server on port 8000
   - Routes requests to inference service
   - Handles concurrency with goroutines

3. **Deploy with Docker Compose**

   ```yaml
   services:
     go-gateway:
       image: sapisehat-go:latest
       ports:
         - "8000:8000"
     inference:
       image: sapisehat-inference:latest
       ports:
         - "9000:9000"
   ```

4. **Zero downtime migration**
   - Android app talks to same API (port 8000)
   - Backend implementation changes transparently

See `go/main.go` for Go implementation template.

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TensorFlow Documentation](https://www.tensorflow.org/api_docs)
- [MobileNetV2 Paper](https://arxiv.org/abs/1801.04381)
- [Docker Documentation](https://docs.docker.com/)
- [Google Cloud Run](https://cloud.google.com/run/docs)

## Contact

For questions or issues:

- Create issue in project repository
- Contact: raditya.rafif@student.pnj.ac.id
