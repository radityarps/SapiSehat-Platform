# Migration Runbook — FastAPI to Go+Python

**Document:** Phase 3 — Step-by-Step Migration Guide  
**Risk Level:** Medium (migration involves routing change)  
**Downtime:** Zero (hot swap strategy)  
**Estimated Time:** 4–8 hours (excluding Go development time)

---

## Table of Contents

1. [Pre-Migration Checklist](#1-pre-migration-checklist)
2. [Migration Strategy Overview](#2-migration-strategy-overview)
3. [Step 1 — Prepare Go Gateway](#step-1--prepare-go-gateway)
4. [Step 2 — Add /infer Endpoint to Python](#step-2--add-infer-endpoint-to-python)
5. [Step 3 — Build and Test Locally](#step-3--build-and-test-locally)
6. [Step 4 — Deploy Inference Microservice](#step-4--deploy-inference-microservice)
7. [Step 5 — Deploy Go Gateway](#step-5--deploy-go-gateway)
8. [Step 6 — Validate Android App](#step-6--validate-android-app)
9. [Step 7 — Decommission Old FastAPI](#step-7--decommission-old-fastapi)
10. [Rollback Procedure](#10-rollback-procedure)
11. [Post-Migration Verification](#11-post-migration-verification)

---

## 1. Pre-Migration Checklist

Complete ALL items before starting migration. Do not proceed if any item is unchecked.

### Code Readiness

```
□ Go gateway code complete and reviewed (see 02-go-gateway.md)
□ /infer endpoint added to apps/backend/api/routes.py
□ All unit tests pass: cd apps/backend && make test
□ Go gateway unit tests pass: cd apps/backend/go && go test ./...
□ Docker images build successfully (both go-gateway and inference)
□ docker-compose.phase3.yml file created and validated
```

### Infrastructure Readiness

```
□ Server has at least 2 GB RAM (Python model = 500MB, Go = ~50MB)
□ Docker and docker-compose installed on server
□ SSL certificate valid (if using HTTPS)
□ DNS pointing to server
□ Backup of current docker-compose.yml saved as docker-compose.phase1.yml
```

### Monitoring Readiness

```
□ Access to server SSH
□ Ability to view Docker logs in real time
□ Android test device available for validation
□ Know your server's public IP address for testing
```

---

## 2. Migration Strategy Overview

### Zero-Downtime Hot Swap

The strategy runs both Phase 1 and Phase 3 simultaneously during validation:

```
Timeline:
T+0h   Start — Phase 1 running on port 8000
T+1h   Deploy inference service on port 9000
T+2h   Test Go gateway locally (port 8001 temporarily)
T+3h   Cut over: switch port 8000 from FastAPI to Go
T+4h   Validate with Android app
T+5h   Decommission old FastAPI
```

### Port Strategy During Migration

```
During migration only:
  Port 8000 → FastAPI (Phase 1) — still serving Android
  Port 8001 → Go Gateway (testing only)
  Port 9000 → Python Inference Service

After validation:
  Port 8000 → Go Gateway
  Port 9000 → Python Inference Service
  (FastAPI on 8000 removed)
```

---

## Step 1 — Prepare Go Gateway

### 1.1 Develop Go code locally

Follow [02-go-gateway.md](02-go-gateway.md) to write the Go code.

### 1.2 Verify Go builds

```bash
cd apps/backend/go

# Download dependencies
go mod tidy

# Build binary
go build -o sapisehat-gateway .

# Verify binary works
./sapisehat-gateway &
curl http://localhost:8000/api/health
# Expected: {"status": "degraded", ...}  (inference service not yet running — OK)
pkill sapisehat-gateway
```

### 1.3 Build Docker image

```bash
cd apps/backend/go
docker build -f Dockerfile -t sapisehat-gateway:latest .
docker images sapisehat-gateway
# Expected: image size ~10-20MB
```

### 1.4 Run Go tests

```bash
cd apps/backend/go
go test ./... -v
# All tests must pass
```

---

## Step 2 — Add /infer Endpoint to Python

### 2.1 Edit routes.py

Following [03-inference-microservice.md](03-inference-microservice.md), add the `/infer` endpoint:

```bash
# Edit the file
code apps/backend/api/routes.py
```

Add the `POST /infer` endpoint (see 03-inference-microservice.md Section 3 for full code).

### 2.2 Verify /infer endpoint works

```bash
cd apps/backend

# Start FastAPI (Phase 1 mode, port 8000)
make run

# In another terminal, test /infer endpoint
curl -X POST http://localhost:8000/infer \
  -F "image=@test_image.jpg" \
  -H "Content-Type: multipart/form-data"

# Expected: same response as /api/predict
```

### 2.3 Run all Python tests

```bash
cd apps/backend
make test
# All 11 tests must pass — zero regressions
```

### 2.4 Test that /api/predict still works

```bash
# Existing endpoint must still work (Phase 1 backward compatibility)
curl -X POST http://localhost:8000/api/predict \
  -F "image=@test_image.jpg"
# Expected: normal prediction response
```

---

## Step 3 — Build and Test Locally

### 3.1 Start inference service on port 9000

```bash
cd apps/backend

# Stop Phase 1 instance first
pkill gunicorn  # or Ctrl+C the running make run

# Start in Phase 3 mode (port 9000)
PORT=9000 uvicorn main:app --port 9000 --host 0.0.0.0
```

Verify:

```bash
curl http://localhost:9000/health
# Expected: {"status": "ok", "model_version": "1.0.0", ...}

curl -X POST http://localhost:9000/infer \
  -F "image=@test_image.jpg"
# Expected: prediction response
```

### 3.2 Start Go gateway on port 8001 (temporary test port)

```bash
PORT=8001 \
INFERENCE_SERVICE_URL=http://localhost:9000 \
./apps/backend/go/sapisehat-gateway
```

### 3.3 Test full flow through Go gateway

```bash
# Through Go gateway → to Python inference
curl -X POST http://localhost:8001/api/predict \
  -F "image=@test_image.jpg"

# Expected: same response as direct Python call
```

### 3.4 Compare responses

Both responses must match. Pay attention to:
- `status` field
- `prediction.label`
- `prediction.confidence`
- `prediction.scores` keys

```bash
# Direct Python
curl -s -X POST http://localhost:9000/infer -F "image=@test_image.jpg" > response_python.json

# Through Go gateway
curl -s -X POST http://localhost:8001/api/predict -F "image=@test_image.jpg" > response_go.json

# Compare
diff response_python.json response_go.json
# Acceptable differences: processing_time_ms (timing varies)
# NOT acceptable: label, confidence, scores
```

### 3.5 Test with Docker Compose

```bash
# Use Phase 3 docker-compose (see 05-docker-deployment.md)
docker-compose -f docker-compose.phase3.yml up --build

# Test
curl -X POST http://localhost:8000/api/predict -F "image=@test_image.jpg"
curl http://localhost:8000/api/health
```

---

## Step 4 — Deploy Inference Microservice

Deploy Python inference service first (before switching Go to port 8000).

### 4.1 Upload code to server

```bash
# From local machine
git add apps/backend/api/routes.py  # Updated with /infer
git commit -m "feat: add /infer internal endpoint for Phase 3"
git push origin main

# On server
ssh user@your-server
cd /opt/sapisehat
git pull origin main
```

### 4.2 Build inference Docker image on server

```bash
cd /opt/sapisehat/apps/backend
docker build -f Dockerfile.inference -t sapisehat-inference:latest .
```

### 4.3 Start inference service on port 9000

```bash
docker run -d \
  --name sapisehat-inference \
  --network sapisehat-net \  # Create this network first if it doesn't exist
  -p 9000:9000 \
  -v /opt/sapisehat/apps/backend/model:/app/model:ro \
  -e MODEL_PATH=/app/model/cattle_disease.pth \
  sapisehat-inference:latest

docker ps | grep inference
docker logs sapisehat-inference
```

### 4.4 Verify inference service is running

```bash
# From server (internal test)
curl http://localhost:9000/health
# Expected: {"status": "ok"}

# Test inference (from server)
curl -X POST http://localhost:9000/infer \
  -F "image=@/opt/test_image.jpg"
```

> Do NOT expose port 9000 externally. This test is from the server itself.

---

## Step 5 — Deploy Go Gateway

FastAPI is still running on port 8000 during this step.

### 5.1 Upload Go binary or Docker image to server

Option A — Copy binary:

```bash
# Build on local machine (cross-compile for Linux)
cd apps/backend/go
GOOS=linux GOARCH=amd64 go build -o sapisehat-gateway .

# Upload to server
scp sapisehat-gateway user@your-server:/opt/sapisehat/
```

Option B — Docker (recommended):

```bash
# Build and push to registry (or transfer image)
docker build -f apps/backend/go/Dockerfile -t sapisehat-gateway:latest apps/backend/go/

# Save image to file
docker save sapisehat-gateway:latest | gzip > gateway.tar.gz
scp gateway.tar.gz user@your-server:/opt/sapisehat/

# On server: load image
docker load < gateway.tar.gz
```

### 5.2 Test Go gateway on port 8001 first

```bash
# On server, start Go on port 8001 (not 8000 yet)
docker run -d \
  --name sapisehat-gateway-test \
  --network sapisehat-net \
  -p 8001:8000 \
  -e INFERENCE_SERVICE_URL=http://sapisehat-inference:9000 \
  -e MODEL_VERSION=1.0.0 \
  sapisehat-gateway:latest

# Test
curl http://your-server:8001/api/health
curl -X POST http://your-server:8001/api/predict -F "image=@/opt/test_image.jpg"
```

### 5.3 Cut over — switch port 8000 to Go

Only do this after the test on 8001 succeeds.

```bash
# Stop Phase 1 FastAPI on port 8000
docker stop sapisehat-backend-v1
docker rm sapisehat-backend-v1

# Start Go gateway on port 8000
docker run -d \
  --name sapisehat-gateway \
  --network sapisehat-net \
  -p 8000:8000 \
  -e INFERENCE_SERVICE_URL=http://sapisehat-inference:9000 \
  -e MODEL_VERSION=1.0.0 \
  --restart unless-stopped \
  sapisehat-gateway:latest

# Remove test instance
docker stop sapisehat-gateway-test
docker rm sapisehat-gateway-test
```

---

## Step 6 — Validate Android App

Use a real Android device with the SapiSehat app installed.

### 6.1 Capture a sapi photo

Open the app and take a photo of a cow (or use a test photo from the gallery).

### 6.2 Send to server

Verify the app sends the prediction request and receives a response.

Expected flow:

```
Android → POST /api/predict (port 8000)
         → Go Gateway receives it
         → Go Gateway forwards to Python (port 9000, /infer)
         → Python runs inference
         → Python responds to Go
         → Go responds to Android
         → App shows result
```

### 6.3 Validation checklist

```
□ App shows prediction result (SEHAT / PMK / LATO_LATO)
□ Confidence value displayed correctly
□ Response time acceptable (< 10 seconds)
□ No error dialogs in app
□ Health endpoint responds: curl http://your-server/api/health
□ No errors in Go gateway logs: docker logs sapisehat-gateway
□ No errors in inference logs: docker logs sapisehat-inference
```

---

## Step 7 — Decommission Old FastAPI

Only do this AFTER Android app validation succeeds and you've waited at least 24 hours.

```bash
# Remove old Phase 1 containers (if any still running)
docker stop sapisehat-backend-v1 2>/dev/null || true
docker rm sapisehat-backend-v1 2>/dev/null || true

# Archive Phase 1 Docker image (keep it for potential rollback for 30 days)
docker tag sapisehat-backend:latest sapisehat-backend:phase1-archive
docker rmi sapisehat-backend:latest 2>/dev/null || true

# Remove Phase 1 docker-compose.yml if using Phase 3 version
mv docker-compose.yml docker-compose.phase1.bak.yml
cp docker-compose.phase3.yml docker-compose.yml

echo "Phase 3 migration complete"
```

---

## 10. Rollback Procedure

If anything goes wrong during Steps 5–6, rollback is fast.

### Immediate Rollback (< 5 minutes)

```bash
# Stop Go gateway
docker stop sapisehat-gateway
docker rm sapisehat-gateway

# Restart Phase 1 FastAPI on port 8000
docker run -d \
  --name sapisehat-backend-v1 \
  -p 8000:8000 \
  -v /opt/sapisehat/apps/backend/model:/app/model:ro \
  sapisehat-backend:phase1-archive \
  gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8000

# Verify rollback
curl http://your-server:8000/api/health
```

Android app reconnects automatically — no app update needed.

### Rollback Decision Criteria

Rollback immediately if:
- Android app shows errors after Step 5 cut-over
- Response JSON format is different from Phase 1
- p95 latency increases by more than 2x
- Error rate exceeds 5%

Do NOT rollback for:
- Minor latency differences (< 500ms)
- Log format differences
- Temporary startup errors (wait 60s for model to load)

---

## 11. Post-Migration Verification

Run these checks 24 hours after migration to confirm stability.

### Log Analysis

```bash
# Check Go gateway error rate
docker logs sapisehat-gateway --since 24h | grep '"status": 5' | wc -l
# Expected: < 10 errors per 24 hours in normal usage

# Check inference service errors
docker logs sapisehat-inference --since 24h | grep "ERROR" | wc -l

# Check for OOM kills
docker inspect sapisehat-inference | grep OOMKilled
# Expected: false
```

### Performance Verification

```bash
# Install hey (HTTP load testing tool)
go install github.com/rakyll/hey@latest

# Baseline test: 50 concurrent requests
hey -n 100 -c 10 \
  -m POST \
  -F image=@test_image.jpg \
  http://your-server:8000/api/predict

# Expected (compared to Phase 1):
# - Similar or faster p50/p95 latency
# - Higher throughput (more req/s under concurrency)
# - No timeouts at 10 concurrent requests
```

### Memory Usage

```bash
docker stats sapisehat-gateway sapisehat-inference --no-stream

# Expected:
# go-gateway:  ~50-100 MB RAM
# inference:   ~600-800 MB RAM (model loaded)
# Total:       ~700-900 MB (vs Phase 1: ~1.5 GB for 4 workers)
```

---

## Summary Timeline

| Step | Duration | Risk |
|---|---|---|
| Pre-migration checklist | 1h | None |
| Build and test locally | 2h | None |
| Deploy inference service (port 9000) | 30m | Low (not on port 8000) |
| Test Go on port 8001 | 30m | Low (not on port 8000) |
| **Cut over port 8000 to Go** | 5m | **Medium — has rollback** |
| Android validation | 30m | None (can rollback in 5m) |
| Decommission old FastAPI | 10m | None |
| **Total** | **~4-5 hours** | **Rollback always available** |
