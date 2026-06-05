# Docker Deployment — Phase 3

**Document:** Phase 3 — Docker Compose & Deployment Configuration  
**Services:** Go Gateway (port 8000) + Python Inference (port 9000, internal)

---

## Table of Contents

1. [Directory Structure](#1-directory-structure)
2. [docker-compose.phase3.yml](#2-docker-composephase3yml)
3. [Go Gateway Dockerfile](#3-go-gateway-dockerfile)
4. [Inference Service Dockerfile](#4-inference-service-dockerfile)
5. [Environment Files](#5-environment-files)
6. [Deployment Commands](#6-deployment-commands)
7. [Cloud Run Deployment](#7-cloud-run-deployment)
8. [Nginx Reverse Proxy (Optional)](#8-nginx-reverse-proxy-optional)

---

## 1. Directory Structure

After Phase 3, the relevant files are:

```
apps/backend/
├── main.py                        # FastAPI inference service entry point
├── config.py
├── inference_server.py            # Core — unchanged
├── model/
│   └── cattle_disease.pth         # Model file (not in git)
├── api/
│   └── routes.py                  # Includes /infer endpoint (updated)
├── Dockerfile                     # Phase 1 (kept for reference)
├── Dockerfile.inference           # Phase 3 inference service image
├── docker-compose.yml             # Phase 1 (kept as backup)
└── docker-compose.phase3.yml      # Phase 3 (active)

apps/backend/go/
├── main.go
├── go.mod
├── go.sum
├── config/
├── handlers/
├── middleware/
├── client/
├── models/
└── Dockerfile                     # Go gateway image
```

---

## 2. docker-compose.phase3.yml

File location: `apps/backend/docker-compose.phase3.yml`

```yaml
# docker-compose.phase3.yml
# Phase 3: Go Gateway + Python Inference Microservice
# 
# Usage:
#   docker-compose -f docker-compose.phase3.yml up --build
#   docker-compose -f docker-compose.phase3.yml down

version: "3.9"

services:

  # ─── Go Gateway (public, port 8000) ─────────────────────────────────────────
  go-gateway:
    build:
      context: ./go
      dockerfile: Dockerfile
    image: sapisehat-gateway:latest
    container_name: sapisehat-gateway
    
    ports:
      - "8000:8000"        # Public — Android connects here
    
    environment:
      ENV: ${ENV:-production}
      HOST: "0.0.0.0"
      PORT: "8000"
      INFERENCE_SERVICE_URL: "http://inference:9000"
      REQUEST_TIMEOUT_SEC: "60"
      MODEL_VERSION: ${MODEL_VERSION:-1.0.0}
    
    depends_on:
      inference:
        condition: service_healthy  # Wait for Python to be healthy before starting
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
    
    networks:
      - sapisehat-net
    
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ─── Python Inference Service (internal, port 9000) ──────────────────────────
  inference:
    build:
      context: .
      dockerfile: Dockerfile.inference
    image: sapisehat-inference:latest
    container_name: sapisehat-inference
    
    # !! NO ports: mapping — only accessible via internal network
    # Port 9000 is never exposed to the public internet
    expose:
      - "9000"
    
    environment:
      FASTAPI_ENV: ${ENV:-production}
      MODEL_PATH: /app/model/cattle_disease.pth
      DEVICE: cpu
      LOG_LEVEL: info
      MODEL_VERSION: ${MODEL_VERSION:-1.0.0}
      WORKERS: "2"
    
    volumes:
      # Model file — read-only mount
      - ./model:/app/model:ro
      # Logs — writable
      - inference_logs:/app/logs
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/health"]
      interval: 30s
      timeout: 10s
      # Python needs time to load the 14MB model on startup
      start_period: 60s
      retries: 5
    
    networks:
      - sapisehat-net
    
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "5"


# ─── Network ───────────────────────────────────────────────────────────────────
networks:
  sapisehat-net:
    driver: bridge
    name: sapisehat-net


# ─── Volumes ───────────────────────────────────────────────────────────────────
volumes:
  inference_logs:
    name: sapisehat-inference-logs
```

---

## 3. Go Gateway Dockerfile

File: `apps/backend/go/Dockerfile`

```dockerfile
# Go Gateway Dockerfile
# Multi-stage build — final image ~15MB

# ─── Build stage ───────────────────────────────────────────────────────────────
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Cache dependencies (copy go.mod first for better layer caching)
COPY go.mod go.sum ./
RUN go mod download

# Build binary
# CGO_ENABLED=0: static binary (no C dependencies)
# -ldflags="-w -s": strip debug symbols (smaller binary)
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s" -a -installsuffix cgo -o sapisehat-gateway .


# ─── Final stage ───────────────────────────────────────────────────────────────
FROM alpine:3.18

# Add CA certificates for HTTPS calls
RUN apk --no-cache add ca-certificates curl

# Create non-root user
RUN adduser -D -u 1000 appuser
USER appuser

WORKDIR /home/appuser

# Copy binary from builder stage
COPY --from=builder /app/sapisehat-gateway .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["./sapisehat-gateway"]
```

---

## 4. Inference Service Dockerfile

File: `apps/backend/Dockerfile.inference`

```dockerfile
# Python Inference Microservice Dockerfile
# Phase 3: runs on port 9000, internal only

# ─── Builder stage ─────────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# ─── Final stage ───────────────────────────────────────────────────────────────
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY --chown=appuser:appuser . .

RUN mkdir -p logs && chown appuser:appuser logs

USER appuser

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Internal port only
EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:9000/health || exit 1

CMD ["gunicorn", "main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:9000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

---

## 5. Environment Files

### .env (server environment file)

Create this on the server, not in git:

```bash
# /opt/sapisehat/apps/backend/.env
ENV=production
MODEL_VERSION=1.0.0
```

### .env.example (committed to git)

```bash
# apps/backend/.env.example
# Copy to .env and fill in values

ENV=development
MODEL_VERSION=1.0.0
```

Update `.gitignore` to include:

```gitignore
# Environment files
.env
!.env.example
```

---

## 6. Deployment Commands

### First-time Deployment

```bash
# 1. Clone and setup
ssh user@your-server
cd /opt
git clone https://github.com/your-repo/sapisehat.git
cd sapisehat/apps/backend

# 2. Place model file
# Upload cattle_disease.pth to /opt/sapisehat/apps/backend/model/
mkdir -p model
scp cattle_disease.pth user@your-server:/opt/sapisehat/apps/backend/model/

# 3. Create .env
cp .env.example .env
nano .env  # Set ENV=production

# 4. Create Docker network (if not exists)
docker network create sapisehat-net 2>/dev/null || true

# 5. Build and start
docker-compose -f docker-compose.phase3.yml up --build -d

# 6. Check status
docker-compose -f docker-compose.phase3.yml ps
docker-compose -f docker-compose.phase3.yml logs -f
```

### Update Deployment (rolling update)

```bash
cd /opt/sapisehat/apps/backend

# Pull latest code
git pull origin main

# Rebuild and restart with zero downtime
# Note: Go gateway restarts first, but inference stays up
docker-compose -f docker-compose.phase3.yml up --build -d --no-deps go-gateway

# If inference code changed:
docker-compose -f docker-compose.phase3.yml up --build -d --no-deps inference
```

### View Logs

```bash
# All services
docker-compose -f docker-compose.phase3.yml logs -f

# Go gateway only
docker-compose -f docker-compose.phase3.yml logs -f go-gateway

# Inference only
docker-compose -f docker-compose.phase3.yml logs -f inference

# Last 50 lines
docker-compose -f docker-compose.phase3.yml logs --tail=50 go-gateway
```

### Stop and Start

```bash
# Stop (containers remain, can restart)
docker-compose -f docker-compose.phase3.yml stop

# Start stopped containers
docker-compose -f docker-compose.phase3.yml start

# Stop and remove containers
docker-compose -f docker-compose.phase3.yml down

# Stop, remove containers, and remove volumes
docker-compose -f docker-compose.phase3.yml down -v
```

---

## 7. Cloud Run Deployment

Google Cloud Run is recommended for low-cost deployment. It runs Docker containers serverlessly.

### Why Two Services on Cloud Run

```
Cloud Run Service 1: sapisehat-gateway
  - Port: 8000
  - Public URL: https://sapisehat-gateway-xxx.run.app
  - Requests: 0-1000 concurrent
  - Min instances: 0 (free when idle)
  - Max instances: 3

Cloud Run Service 2: sapisehat-inference
  - Port: 9000
  - URL: internal VPC connector ONLY (no public URL)
  - Requests: queued by Go gateway
  - Min instances: 1 (keep warm — model needs ~5s cold start)
  - Max instances: 2
```

### Cloud Run Service Definitions

**sapisehat-gateway (Go):**

```yaml
# cloud-run-gateway.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: sapisehat-gateway
  annotations:
    run.googleapis.com/ingress: all  # Public
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"
        autoscaling.knative.dev/maxScale: "3"
        run.googleapis.com/vpc-access-connector: projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME
    spec:
      containerConcurrency: 100
      containers:
      - image: gcr.io/PROJECT_ID/sapisehat-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENV
          value: production
        - name: INFERENCE_SERVICE_URL
          value: http://sapisehat-inference:9000   # Internal VPC URL
        - name: MODEL_VERSION
          value: "1.0.0"
        resources:
          limits:
            memory: 128Mi
            cpu: "1"
```

**sapisehat-inference (Python):**

```yaml
# cloud-run-inference.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: sapisehat-inference
  annotations:
    run.googleapis.com/ingress: internal  # INTERNAL ONLY
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"   # Always 1 warm instance (avoid cold start)
        autoscaling.knative.dev/maxScale: "2"
    spec:
      containerConcurrency: 4   # Max 4 concurrent inference requests per instance
      containers:
      - image: gcr.io/PROJECT_ID/sapisehat-inference:latest
        ports:
        - containerPort: 9000
        env:
        - name: FASTAPI_ENV
          value: production
        - name: MODEL_PATH
          value: /app/model/cattle_disease.pth
        resources:
          limits:
            memory: 2Gi    # 14MB model + PyTorch runtime
            cpu: "2"
```

### Deploy to Cloud Run

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID
REGION=asia-southeast2  # Jakarta

# Build and push images
docker build -t gcr.io/$PROJECT_ID/sapisehat-gateway:latest apps/backend/go/
docker build -f apps/backend/Dockerfile.inference \
             -t gcr.io/$PROJECT_ID/sapisehat-inference:latest apps/backend/

docker push gcr.io/$PROJECT_ID/sapisehat-gateway:latest
docker push gcr.io/$PROJECT_ID/sapisehat-inference:latest

# Deploy inference first (no public traffic)
gcloud run deploy sapisehat-inference \
  --image gcr.io/$PROJECT_ID/sapisehat-inference:latest \
  --region $REGION \
  --ingress internal \
  --min-instances 1 \
  --memory 2Gi \
  --cpu 2 \
  --port 9000

# Deploy gateway
gcloud run deploy sapisehat-gateway \
  --image gcr.io/$PROJECT_ID/sapisehat-gateway:latest \
  --region $REGION \
  --ingress all \
  --min-instances 0 \
  --memory 128Mi \
  --cpu 1 \
  --port 8000 \
  --set-env-vars INFERENCE_SERVICE_URL=http://sapisehat-inference

# Get public URL
gcloud run services describe sapisehat-gateway \
  --region $REGION \
  --format "value(status.url)"
```

---

## 8. Nginx Reverse Proxy (Optional)

If deploying to a bare VPS (not Cloud Run), use Nginx as reverse proxy for SSL termination:

```nginx
# /etc/nginx/sites-available/sapisehat

server {
    listen 80;
    server_name api.sapisehat.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.sapisehat.com;

    ssl_certificate     /etc/letsencrypt/live/api.sapisehat.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.sapisehat.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    # Client max body size — allow images up to 10MB
    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:8000;   # Go gateway
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout must be longer than inference time
        proxy_read_timeout 90s;
        proxy_connect_timeout 10s;
    }
}
```

```bash
# Install Certbot for SSL
apt install certbot python3-certbot-nginx
certbot --nginx -d api.sapisehat.com

# Enable site
ln -s /etc/nginx/sites-available/sapisehat /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## Quick Reference

| Command | Purpose |
|---|---|
| `docker-compose -f docker-compose.phase3.yml up -d` | Start all services |
| `docker-compose -f docker-compose.phase3.yml down` | Stop all services |
| `docker-compose -f docker-compose.phase3.yml logs -f` | View all logs |
| `docker-compose -f docker-compose.phase3.yml ps` | Service status |
| `curl http://localhost:8000/api/health` | Check Go gateway health |
| `curl http://localhost:9000/health` | Check inference health (from server) |
