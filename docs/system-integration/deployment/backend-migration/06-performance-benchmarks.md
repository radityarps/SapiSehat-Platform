# Performance Benchmarks

**Document:** Phase 3 — Measuring and Validating Migration  
**Tools:** `hey` (HTTP load test), `docker stats` (memory), logs analysis

---

## Table of Contents

1. [Tools Setup](#1-tools-setup)
2. [Phase 1 Baseline (FastAPI)](#2-phase-1-baseline-fastapi)
3. [Phase 3 Benchmark (Go + Python)](#3-phase-3-benchmark-go--python)
4. [Expected Results](#4-expected-results)
5. [Memory Comparison](#5-memory-comparison)
6. [Latency Percentiles Explanation](#6-latency-percentiles-explanation)
7. [When Benchmarks Indicate a Problem](#7-when-benchmarks-indicate-a-problem)

---

## 1. Tools Setup

### Install `hey` (HTTP load test tool)

```bash
# Linux (using Go)
go install github.com/rakyll/hey@latest

# Mac
brew install hey

# Windows (using Go)
go install github.com/rakyll/hey@latest
# or download binary from: https://github.com/rakyll/hey/releases

# Verify
hey --version
```

### Install `jq` (JSON log parsing)

```bash
# Linux
apt install jq

# Mac
brew install jq

# Windows
choco install jq
# or download from: https://stedolan.github.io/jq/download/
```

### Prepare test image

```bash
# Download a 500KB test image
curl -o test_cow.jpg "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Cow_female_black_white.jpg/320px-Cow_female_black_white.jpg"

# Verify file size
ls -lh test_cow.jpg
# Should be around 20–100 KB
```

---

## 2. Phase 1 Baseline (FastAPI)

Run these benchmarks BEFORE migration and save the results.

### 2.1 Single request latency

```bash
# Single request — get baseline latency
time curl -s -X POST http://localhost:8000/api/predict \
  -F "image=@test_cow.jpg" | jq .processing_time_ms

# Run 3 times and record
# Expected: 2000–5000 ms (PyTorch inference time)
```

### 2.2 Sequential requests (no concurrency)

```bash
# 20 sequential requests, 1 at a time
hey -n 20 -c 1 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict

# Save output
hey -n 20 -c 1 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase1_sequential.txt
```

### 2.3 Low concurrency

```bash
# 50 requests, 5 concurrent
hey -n 50 -c 5 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase1_c5.txt

# 50 requests, 10 concurrent
hey -n 50 -c 10 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase1_c10.txt
```

### 2.4 Memory usage during load

```bash
# In one terminal: run load test
hey -n 100 -c 10 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict &

# In another terminal: monitor memory
docker stats sapisehat-backend --no-stream
# Or for continuous monitoring:
watch -n 1 'docker stats sapisehat-backend --no-stream'
```

### 2.5 Record Phase 1 results

Fill in this table with your actual measurements:

```
Phase 1 Baseline Results:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Date: _______________
Server spec: ___ vCPU, ___ GB RAM

Single request:
  Inference time (p50): ___ ms
  Total time (p50): ___ ms

Sequential (c=1, n=20):
  p50: ___ ms
  p95: ___ ms
  p99: ___ ms
  RPS: ___

Low concurrency (c=5, n=50):
  p50: ___ ms
  p95: ___ ms
  p99: ___ ms
  RPS: ___
  Error rate: ___%

High concurrency (c=10, n=50):
  p50: ___ ms
  p95: ___ ms
  p99: ___ ms
  RPS: ___
  Error rate: ___%

Memory:
  Idle: ___ MB
  Under load (c=10): ___ MB
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 3. Phase 3 Benchmark (Go + Python)

Run these AFTER migration, against the same server.

### 3.1 Single request latency (end-to-end)

```bash
# Same test as Phase 1
time curl -s -X POST http://localhost:8000/api/predict \
  -F "image=@test_cow.jpg" | jq .processing_time_ms

# Expected: similar to Phase 1 (inference time is unchanged)
# Go gateway overhead is < 5ms — negligible
```

### 3.2 Sequential requests

```bash
hey -n 20 -c 1 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase3_sequential.txt
```

### 3.3 Concurrency benchmarks

```bash
# 5 concurrent
hey -n 50 -c 5 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase3_c5.txt

# 10 concurrent
hey -n 50 -c 10 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase3_c10.txt

# 20 concurrent — stress test
# Phase 1 would likely timeout here
# Phase 3 should handle it with queuing
hey -n 100 -c 20 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase3_c20.txt
```

### 3.4 High concurrency comparison

This is where Phase 3 shows its advantage:

```bash
# 50 concurrent requests — impossible for Phase 1 with 4 workers
# Phase 3 queues these via Go goroutines
hey -n 200 -c 50 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict > benchmark_phase3_c50.txt

# View summary
cat benchmark_phase3_c50.txt | grep -A 20 "Summary:"
```

### 3.5 Memory under load

```bash
hey -n 200 -c 20 \
  -m POST \
  -F image=@test_cow.jpg \
  http://localhost:8000/api/predict &

# Monitor both services
watch -n 1 'docker stats sapisehat-gateway sapisehat-inference --no-stream'
```

### 3.6 Compare results

```bash
# Create comparison summary
echo "=== PHASE 1 ===" && cat benchmark_phase1_c10.txt | grep -A 5 "Summary:"
echo ""
echo "=== PHASE 3 ===" && cat benchmark_phase3_c10.txt | grep -A 5 "Summary:"
```

---

## 4. Expected Results

### Latency (Phase 1 vs Phase 3, single request)

```
Single Request (c=1):

Component              Phase 1    Phase 3    Change
──────────────────────────────────────────────────
PyTorch inference      2500ms     2500ms     0ms    ← unchanged
Python preprocessing    100ms      100ms     0ms    ← unchanged
HTTP overhead (FastAPI)   5ms        -       -5ms
Go HTTP overhead           -        1ms     +1ms
Internal Python call       -        2ms     +2ms
──────────────────────────────────────────────────
Total p50              2605ms     2603ms     -2ms   ← virtually identical

Key insight: Single request latency is the SAME.
The difference is invisible to users.
```

### Throughput (Phase 1 vs Phase 3, high concurrency)

```
High Concurrency (c=20, n=100):

Metric             Phase 1    Phase 3    Change
───────────────────────────────────────────────
p50 latency        3200ms     3100ms     -100ms
p95 latency        8500ms     4200ms    -4300ms  ✓ major improvement
p99 latency       15000ms     6500ms    -8500ms  ✓ major improvement
Error rate (503)     12%        0%       -12%    ✓ major improvement
RPS                  1.2        3.8     +3.2     ✓ 3x throughput
Memory usage        1.5 GB    750 MB    -750MB   ✓ half the memory

Key insight: Under high concurrency, Phase 3 is dramatically better.
p95 latency drops by ~50%, errors drop to 0%, memory halved.
```

### Why the Difference?

```
Phase 1 (c=20):
  Worker 1: Processing request #1 (2.5s blocked)
  Worker 2: Processing request #2 (2.5s blocked)
  Worker 3: Processing request #3 (2.5s blocked)
  Worker 4: Processing request #4 (2.5s blocked)
  Request #5-20: Waiting in OS queue → long p95/p99
  When queue fills: 503 Service Unavailable

Phase 3 (c=20):
  Go goroutines: Accept all 20 connections immediately
  Python worker 1: Processing request #1 (2.5s)
  Python worker 2: Processing request #2 (2.5s)
  Go queue: Request #3-20 waiting efficiently (non-blocking)
  
  Requests process in batches:
  - Batch 1: requests 1-2 → 2.5s
  - Batch 2: requests 3-4 → 5.0s total
  - Batch 3: requests 5-6 → 7.5s total
  ...
  Request #20: ~25s total (but no errors, no 503)
```

---

## 5. Memory Comparison

### Phase 1 Memory (4 Gunicorn workers)

```
Each Python worker loads the model independently:
  Worker 1: Python runtime + PyTorch + model = ~380 MB
  Worker 2: Python runtime + PyTorch + model = ~380 MB
  Worker 3: Python runtime + PyTorch + model = ~380 MB
  Worker 4: Python runtime + PyTorch + model = ~380 MB
  ──────────────────────────────────────────────────────
  Total: ~1.5 GB RAM
  
Note: Some memory is shared by the OS (copy-on-write).
Actual usage may be ~800 MB, peaks at ~1.5 GB under load.
```

### Phase 3 Memory (Go + 2 Python workers)

```
Go gateway:
  Go runtime + program = ~50 MB
  (handles 1000+ concurrent connections with goroutines)

Python inference service (2 workers):
  Worker 1: Python runtime + PyTorch + model = ~380 MB
  Worker 2: Python runtime + PyTorch + model = ~380 MB
  ──────────────────────────────────────────────────────
  Total: ~810 MB RAM

Savings: ~700 MB (nearly half)
```

### Measure Actual Memory

```bash
# Measure idle memory
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" \
  sapisehat-gateway sapisehat-inference

# Measure under load
hey -n 50 -c 10 -m POST -F image=@test_cow.jpg \
  http://localhost:8000/api/predict &

sleep 5  # Let load start

docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" \
  sapisehat-gateway sapisehat-inference

wait  # Wait for load test to finish
```

---

## 6. Latency Percentiles Explanation

Understanding p50/p95/p99 in the context of SapiSehat:

```
p50 (median):
  50% of requests finish FASTER than this
  Example: p50 = 2500ms → half your requests take < 2.5s
  Most important for "average user" experience

p95:
  95% of requests finish FASTER than this
  5% take longer than p95
  Example: p95 = 4000ms → 1 in 20 requests takes > 4s
  Important for "slow user" experience

p99:
  99% of requests finish FASTER than this
  1% take longer than p99
  Example: p99 = 8000ms → 1 in 100 requests takes > 8s
  Important for detecting worst-case scenarios

For SapiSehat:
  Target p50: < 5000ms  (acceptable for image inference)
  Target p95: < 8000ms  (user will wait, but not abandon)
  Target p99: < 15000ms (rare, but app should show loading indicator)
  
  Android app should show a loading spinner for any request > 2s.
  Android app should timeout and fallback to TFLite after 30s.
```

### Reading `hey` Output

```
$ hey -n 50 -c 10 ... http://localhost:8000/api/predict

Summary:
  Total:        45.2543 secs        ← total test duration
  Slowest:      12.3042 secs        ← p100 (worst case)
  Fastest:      2.1534 secs         ← p0 (best case)
  Average:      8.0891 secs         ← mean
  Requests/sec: 1.1049              ← throughput

Response time histogram:
  2.153 [1]  |
  3.182 [12] |■■■■■■■■■■■
  4.211 [15] |■■■■■■■■■■■■■■
  ...

Latency distribution:
  10% in 2.3012 secs   ← p10
  25% in 2.8843 secs   ← p25
  50% in 3.2031 secs   ← p50 (median) ← most important
  75% in 8.1234 secs   ← p75
  90% in 10.234 secs   ← p90
  95% in 11.845 secs   ← p95 ← watch this
  99% in 12.201 secs   ← p99 ← watch this

Status code distribution:
  [200] 47 responses   ← success
  [503] 3 responses    ← errors (FastAPI overwhelmed)
```

---

## 7. When Benchmarks Indicate a Problem

### Problem: Phase 3 is slower than Phase 1 for single requests

```
Symptom: p50 latency increased by > 200ms

Diagnosis steps:
1. Check Go → Python network latency
   curl http://localhost:9000/health  # Should respond in < 10ms

2. Check connection pool health
   docker logs sapisehat-gateway | grep "connection"

3. Check if Python is healthy
   docker logs sapisehat-inference | tail -20

Fix options:
  - Increase connection pool size in client/inference.go
  - Check Docker network performance
  - Ensure both containers are on same Docker network
```

### Problem: High error rate under concurrency

```
Symptom: 503 errors in Phase 3 at c=20

Diagnosis:
1. Check inference service capacity
   docker logs sapisehat-inference | grep "worker timeout"

2. Check Go gateway timeout setting
   - Is REQUEST_TIMEOUT_SEC too short? (Should be > inference time)

3. Check Python workers
   docker stats sapisehat-inference  # Is memory maxed out?

Fix options:
  - Increase Python workers: WORKERS=4 in docker-compose.phase3.yml
  - Increase REQUEST_TIMEOUT_SEC: from 60 to 120
  - Increase server RAM and add workers
```

### Problem: Memory keeps growing

```
Symptom: inference container memory grows over time

Diagnosis:
  docker stats sapisehat-inference  # Memory growing over hours?

Fix:
  - Already handled by Gunicorn max_requests=1000 in gunicorn.inference.conf.py
  - Workers restart after 1000 requests to prevent memory leaks
  - If still growing: check for image objects not being freed in Python code
```

### Minimum Acceptable Results for Phase 3

Migration is considered successful only when ALL criteria are met:

```
□ Single request p50 latency: ≤ Phase 1 p50 + 500ms
□ c=10 p95 latency: < 10 seconds
□ c=10 error rate: 0%
□ c=20 error rate: < 1%
□ Memory (idle): < 1 GB
□ Android app: zero errors over 10 test predictions
□ /api/health: returns {"status": "ok"} within 1 second
```

If any criterion fails, rollback using the procedure in [04-migration-runbook.md](04-migration-runbook.md#10-rollback-procedure).

---

## Quick Command Reference

```bash
# Baseline single request
time curl -s -X POST http://localhost:8000/api/predict -F "image=@test_cow.jpg"

# Sequential benchmark (n=20, c=1)
hey -n 20 -c 1 -m POST -F image=@test_cow.jpg http://localhost:8000/api/predict

# Concurrency benchmark (n=50, c=10)
hey -n 50 -c 10 -m POST -F image=@test_cow.jpg http://localhost:8000/api/predict

# Memory usage
docker stats --no-stream sapisehat-gateway sapisehat-inference

# Check Go gateway logs for errors
docker logs sapisehat-gateway | grep -i error | tail -20

# Check inference service logs for timeouts
docker logs sapisehat-inference | grep -i timeout | tail -20
```
