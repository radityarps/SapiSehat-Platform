# Go Migration — Overview & Architecture

**Document:** Phase 3 Architecture  
**Status:** Planned (post-MVP, July 2026+)  
**Prerequisite:** Phase 1 (FastAPI MVP) and Phase 2 (deployment) must be complete and stable.

---

## Table of Contents

1. [Why Migrate to Go?](#1-why-migrate-to-go)
2. [What Changes and What Stays](#2-what-changes-and-what-stays)
3. [Architecture Diagram](#3-architecture-diagram)
4. [When to Trigger Migration](#4-when-to-trigger-migration)
5. [Migration Documents](#5-migration-documents)

---

## 1. Why Migrate to Go?

### Current Bottleneck (FastAPI)

FastAPI with Gunicorn handles concurrency through OS processes:

```
4 Gunicorn workers
 ├── Worker 1: Processing request  → 2-5s blocked
 ├── Worker 2: Processing request  → 2-5s blocked
 ├── Worker 3: Idle
 └── Worker 4: Idle

Max concurrent requests = number of workers
Each worker processes 1 request at a time
```

**Problem:** Inference is CPU-bound and blocks the worker for 2–5 seconds. Adding more workers means more RAM consumption (each loads the 14MB model).

### Go Advantage

Go handles concurrency through goroutines (lightweight threads):

```
Go Server (1 process)
 ├── Goroutine 1: Accept connection → forward to inference
 ├── Goroutine 2: Accept connection → forward to inference
 ├── Goroutine 3: Wait for inference response
 ├── Goroutine N: ...
 └── (thousands of goroutines, very low memory)

Goroutines are non-blocking → Go accepts new connections
while Python inference is running
```

**Benefit:** Go can handle 1000+ concurrent connections with low overhead, queuing inference requests efficiently.

### Performance Comparison

| Aspect | FastAPI (Phase 1) | Go + Python (Phase 3) |
|---|---|---|
| Max concurrent connections | ~20–50 | 1000+ |
| Memory per connection | ~50MB (new worker) | ~5KB (goroutine) |
| Inference speed | Same (Python PyTorch) | Same (Python PyTorch) |
| Request queuing | OS process queue | Go channel (explicit) |
| Horizontal scaling | Manual | Auto with orchestration |
| Cold start time | ~5s | <1s |

> **Note:** Inference speed does NOT improve — Go delegates inference to Python.
> The gain is purely in request handling capacity and memory efficiency.

---

## 2. What Changes and What Stays

### Architecture Before (Phase 1)

```
Android App
     │  HTTP POST /api/predict
     ▼
┌────────────────────────────────┐
│  FastAPI (Python, Port 8000)   │
│  ┌──────────────────────────┐  │
│  │  HTTP Layer              │  │
│  │  - Parse multipart form  │  │
│  │  - Validate content type │  │
│  │  - Handle CORS           │  │
│  └──────────────┬───────────┘  │
│                 │               │
│  ┌──────────────▼───────────┐  │
│  │  InferenceService        │  │
│  │  - Tahap 2 preprocessing │  │
│  │  - PyTorch inference     │  │
│  │  - Format result         │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
```

### Architecture After (Phase 3)

```
Android App
     │  HTTP POST /api/predict   (same API, no Android changes)
     ▼
┌────────────────────────────────┐
│  Go Gateway (Port 8000)        │  ← NEW (replaces FastAPI HTTP layer)
│  - Accept request              │
│  - Validate content type       │
│  - Rate limiting               │
│  - CORS handling               │
│  - Connection pooling          │
│  - Request ID logging          │
└────────────┬───────────────────┘
             │  HTTP POST /infer (internal)
             ▼
┌────────────────────────────────┐
│  Python Inference Service      │  ← UNCHANGED LOGIC (new HTTP wrapper)
│  (Port 9000, internal only)    │
│  ┌──────────────────────────┐  │
│  │  InferenceService        │  │
│  │  - Tahap 2 preprocessing │  │  ← apps/backend/inference_server.py
│  │  - PyTorch inference     │  │     (zero changes to this file)
│  │  - Format result         │  │
│  └──────────────────────────┘  │
└────────────────────────────────┘
```

### What STAYS the same

| Component | File | Status |
|---|---|---|
| InferenceService | `apps/backend/inference_server.py` | **Unchanged** |
| ModelLoader | `apps/backend/model/loader.py` | **Unchanged** |
| ModelPreprocessor | `apps/backend/preprocessing/model_preprocessor.py` | **Unchanged** |
| API contract | `POST /api/predict` response JSON | **Unchanged** |
| Android app | All Kotlin code | **Unchanged** |

### What CHANGES

| Component | Change |
|---|---|
| HTTP server | FastAPI → Go (Gin framework) |
| Port 8000 | Go process instead of Python |
| Port 9000 | New: Python inference microservice |
| `apps/backend/main.py` | Add `/infer` internal endpoint |
| `apps/backend/api/routes.py` | Expose internal `/infer` route |
| Docker Compose | Add `go-gateway` service |

---

## 3. Architecture Diagram

### Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Android App                              │
│                  POST /api/predict (image)                       │
└──────────────────────────┬──────────────────────────────────────┘
                            │
                            │ Public Internet (HTTPS)
                            │
┌──────────────────────────▼──────────────────────────────────────┐
│                      Load Balancer                               │
│                   (Cloud Run / Nginx)                            │
└──────────────────────────┬──────────────────────────────────────┘
                            │
                            │
┌──────────────────────────▼──────────────────────────────────────┐
│                    Go Gateway (Port 8000)                        │
│                                                                  │
│  1. Parse multipart/form-data                                    │
│  2. Validate: JPEG | PNG | WebP                                  │
│  3. Generate request ID                                          │
│  4. Check Redis cache (optional)                                 │
│  5. Forward to inference service                                 │
│  6. Return response to Android                                   │
│                                                                  │
│  Concurrency: Goroutines (1000+ concurrent)                      │
│  Connection pool to Python: 10 connections                       │
└──────────────────────────┬──────────────────────────────────────┘
                            │
                            │ Internal Docker network
                            │ (never exposed publicly)
                            │
┌──────────────────────────▼──────────────────────────────────────┐
│                Python Inference Service (Port 9000)              │
│                                                                  │
│  FastAPI (minimal, internal only)                                │
│  POST /infer → InferenceService.predict()                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │   InferenceService (apps/backend/inference_server.py)      │ │
│  │   - ModelPreprocessor (Tahap 2)                            │ │
│  │   - ModelLoader (singleton, PyTorch)                       │ │
│  │   - Softmax + label mapping                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Workers: 2–4 Gunicorn (inference is CPU-bound)                  │
│  Model: cattle_disease.pth (loaded once per worker)              │
└──────────────────────────────────────────────────────────────────┘
```

### Docker Network

```
docker-compose network: sapisehat-internal

Public:   0.0.0.0:8000 → go-gateway
Private:  go-gateway → inference:9000 (internal only)

Inference service NOT exposed to internet.
```

---

## 4. When to Trigger Migration

Do not migrate prematurely. Measure first.

### Trigger Conditions (ALL must be true)

```
Condition 1: Concurrent requests
  ✅ Regularly seeing 200+ req/min during peak hours

Condition 2: Latency degradation
  ✅ p95 latency > 5 seconds (versus baseline ~3s)
  ✅ HTTP 503 errors appear in logs

Condition 3: Memory pressure
  ✅ Server RAM usage consistently > 80%
  ✅ OOM kill events in Docker logs

Condition 4: Cost justification
  ✅ Cloud Run cost > $30/month
  ✅ OR horizontal scaling requires 3+ instances
```

### How to Check

```bash
# Check request rate
grep "POST /api/predict" access.log | wc -l

# Check p95 latency from response logs
grep "processing_time_ms" app.log | awk -F: '{print $2}' | sort -n | tail -5

# Check memory usage
docker stats sapisehat-backend

# Check error rate
grep "503\|500" access.log | wc -l
```

### Decision Matrix

| Concurrent Users | Monthly Cost | Recommendation |
|---|---|---|
| < 50 req/min | < $10 | Stay on FastAPI |
| 50–200 req/min | $10–30 | Scale FastAPI workers first |
| 200–500 req/min | $30–60 | **Consider Go migration** |
| 500+ req/min | $60+ | **Do Go migration** |

---

## 5. Migration Documents

| Document | Description |
|---|---|
| [01-overview.md](01-overview.md) | This document |
| [02-go-gateway.md](02-go-gateway.md) | Full Go gateway implementation with code |
| [03-inference-microservice.md](03-inference-microservice.md) | Python inference microservice refactoring |
| [04-migration-runbook.md](04-migration-runbook.md) | Step-by-step migration guide |
| [05-docker-deployment.md](05-docker-deployment.md) | Docker Compose and deployment configuration |
| [06-performance-benchmarks.md](06-performance-benchmarks.md) | How to benchmark and validate migration |

---

*Architecture designed for zero-downtime migration. Android app sees no changes.*
