# SapiSehat — Architecture Documentation

**Version:** 1.0.0  
**Last Updated:** May 4, 2026  
**Maintainers:** Raditya Rafif Pratama Sasmita & Noval Putra Ramadhan

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Deployment Architecture](#deployment-architecture)
7. [Security Considerations](#security-considerations)
8. [Future Architecture (Phase 3)](#future-architecture-phase-3)

---

## System Overview

SapiSehat is a cattle disease detection system that uses a Convolutional Neural Network (CNN) to classify images of cattle into three categories: **FMD** (Foot and Mouth Disease / PMK), **LSD** (Lumpy Skin Disease / Lato-Lato), and **healthy**. The system consists of two main components:

1. **Backend API Server** — FastAPI application running TensorFlow for model inference
2. **Android Mobile App** — Kotlin application for image capture and result display

### Architecture Principles

- **Separation of Concerns** — Inference logic is decoupled from HTTP layer
- **Online-First, Offline Fallback** — Server inference preferred; TFLite backup when offline
- **Containerization** — Docker for consistent development and deployment
- **Stateless Processing** — Each inference request is independent

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         ANDROID MOBILE APP                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Camera/Gallery│  │ Preprocessing│  │  Inference Router    │   │
│  │   (CameraX)  │  │  (Tahap 1)   │  │  (Online/Offline)    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
│         │    ┌────────────┴──────────────────────┘               │
│         │    │          ┌──────────┐    ┌────────────────┐       │
│         │    │  ONLINE  │ Retrofit │    │  TFLite (Off)  │       │
│         │    │          └────┬─────┘    └────────────────┘       │
└─────────┼────┼──────────────┼───────────────────────────────────┘
          │    │              │
          │    │    ┌─────────▼──────────────────────────────────┐
          │    │    │            FASTAPI BACKEND                  │
          │    │    │  ┌─────────────────────────────────────┐   │
          │    │    │  │  HTTP Layer (api/routes.py)          │   │
          │    │    │  │  - Request parsing                   │   │
          │    │    │  │  - CORS handling                     │   │
          │    │    │  │  - Error handling                    │   │
          │    │    │  └──────────────┬──────────────────────┘   │
          │    │    │                 │                           │
          │    │    │  ┌──────────────▼──────────────────────┐   │
          │    │    │  │  Inference Layer (inference_server)  │   │
          │    │    │  │  - Image preprocessing (Tahap 2)     │   │
          │    │    │  │  - Model inference                   │   │
          │    │    │  │  - Result formatting                 │   │
          │    │    │  └──────────────┬──────────────────────┘   │
          │    │    │                 │                           │
          │    │    │  ┌──────────────▼──────────────────────┐   │
          │    │    │  │  Model Layer (model/loader.py)       │   │
          │    │    │  │  - TensorFlow model singleton         │   │
          │    │    │  │  - MobileNetV2 (2.4M params)          │   │
          │    │    │  │  - Input: [1, 224, 224, 3]            │   │
          │    │    │  │  - Output: [FMD, LSD, healthy]        │   │
          │    │    │  └──────────────────────────────────────┘   │
          │    │    └──────────────────────────────────────────────┘
```

---

## Component Architecture

### Backend Components

```
apps/backend/
├── main.py                      # FastAPI application entry point
├── config.py                    # Environment-based configuration (Pydantic)
├── inference_server.py          # Pure inference logic (no HTTP coupling)
├── api/
│   ├── __init__.py
│   ├── routes.py                # HTTP endpoint definitions
│   └── schemas.py               # Pydantic request/response models
├── model/
│   ├── __init__.py
│   ├── loader.py                # Singleton TensorFlow model loader
│   └── mobilenetv2_best.keras   # Trained model file
├── preprocessing/
│   ├── __init__.py
│   ├── image_processor.py       # Tahap 1: Client-side preprocessing
│   └── model_preprocessor.py    # Tahap 2: Model-ready preprocessing
├── utils/
│   ├── __init__.py
│   ├── logger.py                # Structured JSON logging
│   └── errors.py                # Custom exception classes
├── tests/
│   ├── __init__.py
│   └── test_inference.py        # Unit tests
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Development container orchestration
├── gunicorn_config.py           # Production WSGI server config
└── requirements.txt             # Python dependencies
```

### Component Responsibilities

| Component                             | Responsibility                      | Dependencies                     |
| ------------------------------------- | ----------------------------------- | -------------------------------- |
| `main.py`                             | App creation, middleware, lifecycle | config, api.routes, utils.logger |
| `config.py`                           | Environment variable management     | pydantic-settings                |
| `api/routes.py`                       | HTTP request/response handling      | inference_server, api.schemas    |
| `api/schemas.py`                      | Request/response validation         | pydantic                         |
| `inference_server.py`                 | Core prediction logic               | model.loader, preprocessing      |
| `model/loader.py`                     | Model loading (singleton)           | tensorflow, utils.errors         |
| `preprocessing/model_preprocessor.py` | Image → tensor transformation       | numpy                            |
| `utils/logger.py`                     | Structured logging                  | logging                          |
| `utils/errors.py`                     | Custom exception hierarchy          | —                                |

### Mobile Components

```
apps/mobile/
├── app/src/main/java/com/sapisehat/app/
│   ├── ui/
│   │   ├── camera/              # Camera capture screen (CameraX)
│   │   ├── result/              # Diagnosis result screen
│   │   ├── history/             # Detection history (Room)
│   │   ├── navigation/          # Compose navigation graph
│   │   └── theme/               # Material 3 theming
│   ├── data/
│   │   ├── api/                 # Retrofit API client
│   │   ├── local/               # Room database + TFLite
│   │   └── repository/          # Data access pattern
│   └── domain/
│       └── model/               # Domain entities
└── app/src/main/assets/
    └── cattle_disease.tflite    # Offline model
```

---

## Data Flow

### Online Inference Flow

```
1. User captures/selects image
         │
2. Tahap 1 Preprocessing (on device)
   - EXIF orientation correction
   - Resize max 800×800px
   - JPEG compress quality 85%
   - Strip EXIF metadata
         │
3. HTTP POST /api/predict
   Content-Type: image/jpeg
         │
4. FastAPI receives image bytes
         │
5. Tahap 2 Preprocessing (on server)
   - Resize to 224×224px
   - Rescale pixel values: 0-255 → 0.0-1.0
         │
6. Model Inference (TensorFlow)
   - Input: numpy array [1, 224, 224, 3]
   - Output: raw logits [FMD, LSD, healthy]
         │
7. Post-processing
   - Softmax normalization
   - Confidence threshold check (>0.60)
   - Display label mapping
         │
8. JSON Response
   {
     "status": "success",
     "prediction": {
       "label": "healthy",
       "display_label": "Sapi Sehat",
       "confidence": 0.9871,
       "is_reliable": true,
       "scores": {"FMD": 0.0041, "LSD": 0.0088, "healthy": 0.9871}
     },
     "model_info": {"version": "1.0.0"},
     "processing_time_ms": 113
   }
```

### Offline Fallback Flow

```
1-2. Same as online (capture + Tahap 1 preprocessing)
         │
3. Network check → FAILED or TIMEOUT
         │
4. TFLite Inference (on device)
   - Tahap 2 preprocessing in Kotlin (same rescale norm: pixel / 255.0)
   - Run TFLite interpreter with canonical labels (FMD, LSD, healthy)
   - Identical score keys and output format as server
         │
5. Display result (same UI as online)
```

> **Preprocessing consistency:** Both backend (`model_preprocessor.py`) and mobile
> (`ModelPreprocessor.kt`) use simple rescale normalization (`pixel / 255.0`) — no
> ImageNet mean/std subtraction. This matches the model's training pipeline.
>
> **Canonical labels:** All classification uses `FMD`, `LSD`, `healthy` as defined in
> `apps/backend/model/class_names.json`. Display labels provide Indonesian translations.

---

## Technology Stack

### Backend

| Technology  | Version | Purpose                 |
| ----------- | ------- | ----------------------- |
| Python      | 3.10+   | Runtime                 |
| FastAPI     | 0.115+  | Web framework           |
| TensorFlow  | 2.19+   | Deep learning framework |
| MobileNetV2 | —       | CNN architecture        |
| Uvicorn     | 0.30+   | ASGI server (dev)       |
| Gunicorn    | 23.0+   | WSGI server (prod)      |
| Pydantic    | 2.9+    | Data validation         |
| Pillow      | 10.4+   | Image processing        |
| Docker      | 24+     | Containerization        |

### Mobile

| Technology      | Version        | Purpose                  |
| --------------- | -------------- | ------------------------ |
| Kotlin          | 2.2.10         | Programming language     |
| Jetpack Compose | BOM 2024.09.00 | UI framework             |
| Hilt            | 2.59           | Dependency injection     |
| KSP             | 2.2.10-2.0.2   | Symbol processing        |
| Room            | 2.6.1          | Local database           |
| Retrofit        | 2.11.0         | HTTP client              |
| OkHttp          | 4.12.0         | HTTP transport           |
| Moshi           | 2.11.0†        | JSON deserialization     |
| moshi-kotlin    | 1.15.1         | Kotlin adapter for Moshi |
| CameraX         | 1.3.4          | Camera API               |
| TFLite          | 2.17.0         | On-device inference      |

### Model

| Property           | Value                      |
| ------------------ | -------------------------- |
| Architecture       | MobileNetV2                |
| Parameters         | 2,416,067 (~2.4M)          |
| Input Shape        | [1, 224, 224, 3]           |
| Output Classes     | 3 (FMD, LSD, healthy)      |
| Model Format       | .keras (TensorFlow native) |
| File Size          | ~20 MB                     |
| Training Framework | TensorFlow / Keras         |
| Preprocessing      | Rescale to [0, 1]          |

---

## Deployment Architecture

### Development

```
┌────────────────────────────────────┐
│         DOCKER COMPOSE              │
│  ┌──────────────────────────────┐  │
│  │  sapisehat-backend            │  │
│  │  - uvicorn --reload           │  │
│  │  - Volume: .:/app             │  │
│  │  - Volume: /app/__pycache__   │  │
│  │  - Port: 8000:8000            │  │
│  │  - Hot reload enabled         │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

### Production (Planned)

```
┌──────────────────────────────────────────────────┐
│                  CLOUD PROVIDER                    │
│  ┌────────────────────────────────────────────┐  │
│  │           LOAD BALANCER                     │  │
│  └────────────┬───────────────────────────────┘  │
│               │                                    │
│     ┌─────────┴─────────┐                         │
│     │                   │                          │
│  ┌──▼──────────┐  ┌─────▼───────┐                 │
│  │ Backend #1  │  │ Backend #2  │                 │
│  │ Gunicorn    │  │ Gunicorn    │                 │
│  │ Workers: 4  │  │ Workers: 4  │                 │
│  └─────────────┘  └─────────────┘                 │
│                                                    │
│  Model file: ~20 MB (bundled in container)         │
│  Memory: 2 GB per instance (recommended)           │
│  Auto-scaling: CPU > 70% for 2 min                 │
└────────────────────────────────────────────────────┘
```

---

## Security Considerations

| Area               | Implementation                                                        |
| ------------------ | --------------------------------------------------------------------- |
| **CORS**           | Allowed origins configurable; currently `*` for development           |
| **File Upload**    | Content type validation (JPEG, PNG, WebP only)                        |
| **File Size**      | Limited by FastAPI/uvicorn defaults                                   |
| **Error Exposure** | Generic 500 messages in production; details logged server-side        |
| **Container**      | Non-root user (`appuser`), minimal base image                         |
| **Dependencies**   | Pinned versions in `requirements.txt`, regular security audits needed |
| **EXIF Stripping** | Client-side metadata removal for privacy                              |
| **Authentication** | Not implemented (internal/mobile app use)                             |

---

## Future Architecture (Phase 3)

When traffic exceeds 200 requests/minute, a Go gateway can be introduced:

```
┌────────────────────────────────────────────────┐
│              ANDROID APP                        │
└──────────────┬─────────────────────────────────┘
               │ HTTP (port 8000)
┌──────────────▼─────────────────────────────────┐
│          GO GATEWAY                             │
│  - Request routing                              │
│  - Concurrency (goroutines)                     │
│  - Rate limiting                                │
│  - Circuit breaking                             │
└──────────────┬─────────────────────────────────┘
               │ gRPC or HTTP (port 9000)
┌──────────────▼─────────────────────────────────┐
│     PYTHON INFERENCE SERVICE                    │
│  - Pure model inference                         │
│  - No HTTP logic (already decoupled!)           │
│  - MobileNetV2 + TensorFlow                     │
└────────────────────────────────────────────────┘
```

This is possible because the inference logic is already **decoupled** from HTTP
(via `inference_server.py`). The Go gateway simply replaces `api/routes.py`.

---

## Related Documents

- [README.md](../../README.md) — Project overview and quick start
- [PRD.md](../PRD.md) — Product Requirements Document
- [DEVELOPMENT.md](../backend/development.md) — Backend development guide
- [Backend README](../backend/README.md) — API reference and setup
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — Contribution guidelines
- [CHANGELOG.md](../changelog.md) — Version history
