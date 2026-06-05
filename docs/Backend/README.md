> **Legacy backend note:** This document describes the Python/FastAPI image inference prototype and tracer backend. Current target architecture is Go gateway + Python inference services; shared contracts live in [system integration backend](../system-integration/backend/README.md) and [platform PRD](../system-integration/product/PRD-platform-rebuild.md).

# SapiSehat Backend

FastAPI backend for cattle disease detection (PMK & LSD) using MobileNetV2 CNN.

## Features

- ✅ FastAPI for high-performance REST API
- ✅ MobileNetV2 model for efficient inference
- ✅ Two-stage preprocessing (client + model)
- ✅ Singleton model loader (load once in memory)
- ✅ Pure inference logic (no HTTP coupling)
- ✅ Docker containerization
- ✅ Unit tests
- ✅ Architecture ready for Go migration (Phase 3)

## Project Structure

```
backend/
├── main.py                      # FastAPI entry point
├── config.py                    # Configuration management
├── inference_server.py          # Core inference logic (pure)
├── model/
│   └── loader.py               # Singleton model loader
├── preprocessing/
│   ├── model_preprocessor.py    # Tahap 2: Model preprocessing
│   └── image_processor.py       # Tahap 1: Client preprocessing
├── api/
│   ├── routes.py               # FastAPI routes
│   └── schemas.py              # Pydantic models
├── utils/
│   ├── logger.py               # Structured logging
│   └── errors.py               # Custom exceptions
├── tests/
│   └── test_inference.py       # Unit tests
├── go/                         # Phase 3: Go gateway (placeholder)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Installation

### Local Setup

1. **Create Python environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Copy environment file**

   ```bash
   cp .env.example .env
   ```

4. **Obtain model file**
   - Place `mobilenetv2_best.keras` in `./model/` directory
   - Model should be MobileNetV2 checkpoint with 3 output classes (FMD, LSD, healthy)

5. **Run tests**

   ```bash
   python -m pytest tests/ -v
   # Or
   python -m unittest discover tests/
   ```

6. **Run locally**

   ```bash
   python main.py
   ```

   API available at: `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Docker Setup

1. **Build image**

   ```bash
   docker-compose build
   ```

2. **Run container**

   ```bash
   docker-compose up
   ```

3. **Test endpoint**
   ```bash
   curl -X POST "http://localhost:8000/api/predict" \
     -F "image=@test_image.jpg"
   ```

## API Endpoints

### POST /api/predict

Predict cattle disease from image.

**Privacy (No-Retention Policy):** Uploaded images are held in memory only during request processing. No image is written to disk, persisted to storage, or logged. After inference completes, image data is garbage collected.

**Request:**

```bash
curl -X POST "http://localhost:8000/api/predict" \
  -F "image=@photo.jpg"
```

**Response:**

```json
{
  "status": "success",
  "prediction": {
    "disease_class": "FMD",
    "display_label_key": "disease.pmk",
    "confidence": 0.9432,
    "is_reliable": true,
    "scores": {
      "FMD": 0.9432,
      "LSD": 0.0258,
      "healthy": 0.031
    }
  },
  "model_info": {
    "version": "1.0.0"
  },
  "processing_time_ms": 2345,
  "preprocessing_time_ms": 234,
  "inference_time_ms": 2111
}
```

### GET /api/health

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "model_version": "1.0.0"
}
```

## Configuration

See `.env.example` for all available configuration options:

| Variable          | Default                        | Description                          |
| ----------------- | ------------------------------ | ------------------------------------ |
| `FASTAPI_ENV`     | development                    | Environment (development/production) |
| `DEBUG`           | true                           | Enable debug mode                    |
| `MODEL_PATH`      | ./model/mobilenetv2_best.keras | Path to model file                   |
| `DEVICE`          | cpu                            | Compute device (cpu/cuda)            |
| `HOST`            | 0.0.0.0                        | Server host                          |
| `PORT`            | 8000                           | Server port                          |
| `WORKERS`         | 4                              | Gunicorn workers                     |
| `REQUEST_TIMEOUT` | 60                             | Request timeout in seconds           |
| `LOG_LEVEL`       | info                           | Logging level                        |

## Development

### Adding Features

The codebase is designed to separate concerns:

1. **HTTP Layer** (`api/routes.py`): Thin wrapper around inference
2. **Inference Logic** (`inference_server.py`): Pure logic, no HTTP coupling
3. **Model** (`model/loader.py`): Singleton for memory efficiency
4. **Preprocessing** (`preprocessing/`): Stateless functions

This separation enables easy migration to Go in Phase 3.

### Running Tests

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test file
python -m unittest tests.test_inference -v

# Run specific test
python -m unittest tests.test_inference.TestInferenceService.test_predict_returns_valid_response_structure -v

# With coverage
pip install coverage
coverage run -m unittest discover tests/
coverage report
```

### Logging

Structured JSON logging is used for production monitoring:

```json
{
  "timestamp": "2026-05-01T10:30:45.123456",
  "level": "INFO",
  "logger": "inference_server",
  "message": "Inference: FMD (94.32%) preprocessing=234ms, inference=2111ms, total=2345ms",
  "module": "inference_server",
  "function": "predict",
  "line": 123
}
```

## Deployment

### Google Cloud Run

```bash
gcloud run deploy sapisehat-backend \
  --source . \
  --region asia-southeast1 \
  --memory 2Gi \
  --timeout 60 \
  --allow-unauthenticated
```

### AWS EC2

See [development.md](development.md) for EC2 deployment instructions.

### Docker Compose

For local development with hot-reload:

```bash
docker-compose up
```

For production:

```bash
docker-compose -f docker-compose.yml build
docker-compose -f docker-compose.yml up -d
```

## Performance Metrics

| Metric                  | Target | Status  |
| ----------------------- | ------ | ------- |
| Inference latency (CPU) | 2-5s   | ✅      |
| Preprocessing latency   | <500ms | ✅      |
| Model size              | ~20MB  | ✅      |
| API response time       | <3s    | ✅      |
| Accuracy (test set)     | ≥88%   | Pending |

## Phase 3: Go Migration

When concurrent traffic exceeds 200 requests/min, migrate to Go gateway:

```
Phase 1 (Current): FastAPI → TensorFlow
Phase 3 (Future): Go Gateway → Python Inference Service → TensorFlow
```

See `/go/main.go` for placeholder implementation.

## Troubleshooting

### Model not found

```
Error: Model file not found: ./model/mobilenetv2_best.keras
```

**Solution:** Ensure model file is placed in `./model/` directory.

### CUDA / GPU not available

If you have NVIDIA GPU but TensorFlow doesn't detect it:

```bash
# Check GPU availability
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# Install CUDA-enabled TensorFlow
pip install tensorflow[and-cuda]
```

### High latency

- First request after startup is slower (model loading) — this is normal
- Subsequent requests should be fast
- If consistently slow, consider:
  - Using GPU (10-20x faster)
  - Quantizing model (30% faster)
  - Batch processing (multiple images at once)

## Contributing

1. Follow code style and architecture patterns
2. Add tests for new features
3. Update documentation
4. Keep inference logic pure (no HTTP coupling)

## License

Internal project - Teknik Informatika, Politeknik Negeri Semarang

## Authors

- Raditya Rafif Pratama Sasmita
- Noval Putra Ramadhan
