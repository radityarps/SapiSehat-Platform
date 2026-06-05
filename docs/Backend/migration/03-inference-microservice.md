# Python Inference Microservice

**Document:** Phase 3 — Inference Service Refactoring  
**Goal:** Convert existing FastAPI backend into an internal inference microservice  
**Key constraint:** `apps/backend/inference_server.py` — **zero changes** to this file

---

## Table of Contents

1. [Overview](#1-overview)
2. [What Changes and What Doesn't](#2-what-changes-and-what-doesnt)
3. [New Internal Route — /infer](#3-new-internal-route--infer)
4. [Updated main.py](#4-updated-mainpy)
5. [Internal vs External Routing](#5-internal-vs-external-routing)
6. [Dockerfile for Inference Service](#6-dockerfile-for-inference-service)
7. [Minimal Gunicorn Config for Phase 3](#7-minimal-gunicorn-config-for-phase-3)

---

## 1. Overview

In Phase 3, the Python backend becomes an internal microservice:

```
Phase 1 (FastAPI as main server)
  Port 8000 (public)
    └── POST /api/predict  →  InferenceService.predict()

Phase 3 (Python as inference microservice)
  Port 9000 (internal only)
    └── POST /infer  →  InferenceService.predict()
    └── GET  /health →  status check

  Port 8000 (public) → Go Gateway (different container)
```

The Python inference service is **never directly accessible** from the internet. Only the Go gateway talks to it via Docker internal network.

---

## 2. What Changes and What Doesn't

### Files with ZERO Changes

| File | Reason |
|---|---|
| `apps/backend/inference_server.py` | Core logic — no HTTP coupling |
| `apps/backend/model/loader.py` | PyTorch model loading |
| `apps/backend/preprocessing/model_preprocessor.py` | Tahap 2 preprocessing |
| `apps/backend/preprocessing/image_processor.py` | Tahap 1 preprocessing |
| `apps/backend/utils/errors.py` | Exception classes |
| `apps/backend/utils/logger.py` | Logging |
| `apps/backend/config.py` | Settings (add one field) |
| `apps/backend/tests/` | Unit tests still pass |

### Files That Change

| File | Change |
|---|---|
| `apps/backend/api/routes.py` | Add `/infer` internal endpoint |
| `apps/backend/main.py` | Minor: change app title, add internal route |
| `apps/backend/api/schemas.py` | Add `InferRequest` schema |

### New Files

| File | Purpose |
|---|---|
| `apps/backend/Dockerfile.inference` | Docker image for inference-only service |

---

## 3. New Internal Route — /infer

Add this to `apps/backend/api/routes.py`:

```python
# apps/backend/api/routes.py
# Add this new endpoint alongside the existing /api/predict

from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
import io
import time

from ..inference_server import inference_service
from ..utils.errors import InvalidImageError, InferenceError
from ..utils.logger import get_logger
from .schemas import PredictResponse, InferRequest

logger = get_logger(__name__)
router = APIRouter()


# ─── Existing endpoint (kept for Phase 1 compatibility) ───────────────────────

@router.post("/api/predict", response_model=PredictResponse)
async def predict(image: UploadFile = File(...)):
    """
    Phase 1 endpoint — used when FastAPI is the main server.
    In Phase 3, this is no longer called (Go gateway calls /infer instead).
    Kept here for backward compatibility during migration.
    """
    return await _run_inference(image)


# ─── New internal endpoint for Go gateway ─────────────────────────────────────

@router.post("/infer", response_model=PredictResponse)
async def infer_internal(image: UploadFile = File(...)):
    """
    Internal endpoint called by Go gateway (Phase 3).
    NOT exposed to public internet — only reachable via Docker internal network.
    
    Identical behavior to /api/predict but on a dedicated path.
    Go gateway does its own content-type validation before calling this.
    """
    request_id = image.headers.get("X-Request-ID", "unknown")
    logger.info(f"Internal inference request", extra={"request_id": request_id})
    return await _run_inference(image)


@router.get("/health")
async def health():
    """Health check for both Phase 1 and Phase 3."""
    from ..config import settings
    return {
        "status": "ok",
        "model_version": settings.model_version,
        "service": "inference",
    }


# ─── Shared logic ──────────────────────────────────────────────────────────────

async def _run_inference(image: UploadFile) -> PredictResponse:
    """
    Shared inference logic for both /api/predict and /infer.
    This function is the only bridge between HTTP layer and InferenceService.
    """
    # Validate content type (Go gateway already validates, but defense in depth)
    accepted_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if image.content_type not in accepted_types:
        raise HTTPException(
            status_code=422,
            detail={
                "status": "error",
                "message": f"Invalid image format. Accepted: JPEG, PNG, WebP",
                "code": "INVALID_IMAGE_FORMAT",
            }
        )

    # Read image bytes
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=422,
            detail={"status": "error", "message": "Empty image file", "code": "EMPTY_IMAGE"}
        )

    # Convert to PIL Image
    try:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={"status": "error", "message": "Cannot decode image", "code": "DECODE_ERROR"}
        )

    # Run inference — InferenceService has NO HTTP coupling
    try:
        result = inference_service.predict(pil_image)
    except InvalidImageError as e:
        raise HTTPException(status_code=422, detail={"status": "error", "message": str(e), "code": "INVALID_IMAGE"})
    except InferenceError as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e), "code": "INFERENCE_ERROR"})

    return PredictResponse(**result)
```

---

## 4. Updated main.py

The main.py changes are minimal — just the app metadata and a note about Phase 3:

```python
# apps/backend/main.py
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="SapiSehat Inference Service",
    description="Internal cattle disease inference service. In Phase 3, port 9000 only.",
    version="1.0.0",
    # Disable Swagger UI in production (internal service doesn't need it)
    docs_url="/docs" if True else None,
)

# CORS — permissive for internal service (Go gateway handles CORS publicly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Internal only, Go gateway enforces CORS externally
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include all routes
app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )


@app.get("/")
async def root():
    return {
        "name": "SapiSehat Inference Service",
        "note": "Internal service. In Phase 3, use Go gateway on port 8000.",
    }
```

---

## 5. Internal vs External Routing

### Port Strategy

```
Phase 1 (FastAPI as main):
  Port 8000  → apps/backend (FastAPI)  — PUBLIC
  
Phase 3 (after migration):
  Port 8000  → apps/backend/go (Go)    — PUBLIC
  Port 9000  → apps/backend (FastAPI)  — INTERNAL ONLY
```

### Endpoint Mapping

| Phase | Client | Endpoint | Port |
|---|---|---|---|
| Phase 1 | Android app | `POST /api/predict` | 8000 |
| Phase 3 | Android app | `POST /api/predict` | 8000 (Go) |
| Phase 3 | Go gateway | `POST /infer` | 9000 (Python) |

The Android app always talks to port 8000. It never changes.

### Security: Why Port 9000 Must NOT Be Public

```yaml
# In docker-compose.yml (Phase 3):

services:
  go-gateway:
    ports:
      - "8000:8000"       # Public — Android connects here
    
  inference:
    # NO ports: mapping
    # Port 9000 is only on the internal network
    # expose: just documents the port, doesn't publish it
    expose:
      - "9000"
```

If port 9000 were public, attackers could bypass the Go gateway:
- Skip rate limiting
- Skip content-type validation
- Directly flood the Python inference service

---

## 6. Dockerfile for Inference Service

File: `apps/backend/Dockerfile.inference`

This is a modified version of the existing `Dockerfile`, optimized for the internal inference role:

```dockerfile
# apps/backend/Dockerfile.inference
# Internal inference microservice — Phase 3
# Runs on port 9000, not exposed to public internet

FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# ─── Final stage ──────────────────────────────────────────────────────────────
FROM python:3.10-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p logs && chown appuser:appuser logs

USER appuser

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Internal port — NOT published by default
EXPOSE 9000

# Health check via internal /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# Fewer workers than Phase 1 — Go gateway queues requests efficiently
# 2 workers = 2 concurrent inference requests
CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:9000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

Build:

```bash
cd apps/backend
docker build -f Dockerfile.inference -t sapisehat-inference:latest .
```

---

## 7. Minimal Gunicorn Config for Phase 3

### Why Fewer Workers?

In Phase 1:
```
FastAPI handles HTTP + Inference
Workers = 4 (handle HTTP concurrency)
```

In Phase 3:
```
Go handles HTTP concurrency (goroutines, very efficient)
Python handles Inference only (CPU bound)
Workers = 2 (match physical CPU cores, not HTTP concurrency)
```

Go will queue requests waiting for inference. Python workers only need to match hardware capacity, not request rate.

### Worker Formula for Phase 3

```
Python inference workers = CPU cores (for CPU inference)
                         = 1 if using GPU (GPU handles parallelism)

Recommended for 1 vCPU server: workers = 2
Recommended for 2 vCPU server: workers = 4
```

### Phase 3 Gunicorn Config File

File: `apps/backend/gunicorn.inference.conf.py`

```python
# apps/backend/gunicorn.inference.conf.py
# Gunicorn config for Phase 3 inference microservice

import multiprocessing

# ── Workers ───────────────────────────────────────────────────────────────────
# For CPU-bound inference: 1-2 workers per CPU core
# (Go gateway handles request queuing, so fewer workers is fine)
workers = min(2, multiprocessing.cpu_count())
worker_class = "uvicorn.workers.UvicornWorker"

# ── Binding ───────────────────────────────────────────────────────────────────
bind = "0.0.0.0:9000"

# ── Timeouts ──────────────────────────────────────────────────────────────────
# Must be longer than inference time (2-5s) with margin
timeout = 120
graceful_timeout = 30
keepalive = 5

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# ── Performance ───────────────────────────────────────────────────────────────
max_requests = 1000          # Restart worker after N requests (memory leak prevention)
max_requests_jitter = 100    # Randomize restart to avoid all workers restarting at once
preload_app = True           # Load model once before forking (saves RAM)
```

Run with:

```bash
gunicorn main:app -c gunicorn.inference.conf.py
```

---

## Summary

| Component | Phase 1 | Phase 3 |
|---|---|---|
| `inference_server.py` | Called from FastAPI route | Called from FastAPI route (same) |
| Port exposed | 8000 (public) | 9000 (internal only) |
| Workers | 4 | 2 |
| Endpoint used | `/api/predict` | `/infer` |
| Who calls it | Android app | Go gateway |

The inference service is architecturally identical — it just runs on a different port and is hidden behind Go.
