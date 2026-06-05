# Go Gateway — Full Implementation

**Document:** Phase 3 — Go Gateway Code  
**Directory:** `apps/backend/go/`  
**Go Version:** 1.21+  
**Framework:** Gin (HTTP) + standard library

---

## Table of Contents

1. [Project Structure](#1-project-structure)
2. [go.mod — Module Definition](#2-gomod--module-definition)
3. [main.go — Entry Point](#3-maingo--entry-point)
4. [handlers/predict.go — Prediction Handler](#4-handlerspredicttgo--prediction-handler)
5. [handlers/health.go — Health Handler](#5-handlershealtthgo--health-handler)
6. [middleware/logger.go — Request Logging](#6-middlewareloggergo--request-logging)
7. [middleware/cors.go — CORS Handling](#7-middlewarecorsgo--cors-handling)
8. [client/inference.go — Inference Client](#8-clientinferencego--inference-client)
9. [config/config.go — Configuration](#9-configconfiggo--configuration)
10. [models/response.go — Response Models](#10-modelsresponsego--response-models)
11. [How to Build and Test](#11-how-to-build-and-test)

---

## 1. Project Structure

```
apps/backend/go/
├── main.go                    # Entry point
├── go.mod                     # Go module definition
├── go.sum                     # Dependency checksums (auto-generated)
├── config/
│   └── config.go              # Environment-based configuration
├── handlers/
│   ├── predict.go             # POST /api/predict handler
│   └── health.go              # GET /api/health handler
├── middleware/
│   ├── logger.go              # Structured request logging
│   └── cors.go                # CORS configuration
├── client/
│   └── inference.go           # HTTP client to Python inference service
└── models/
    └── response.go            # Response struct definitions
```

---

## 2. go.mod — Module Definition

File: `apps/backend/go/go.mod`

```go
module sapisehat-gateway

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/google/uuid v1.4.0
)
```

Run after creating this file:

```bash
cd apps/backend/go
go mod tidy
```

---

## 3. main.go — Entry Point

File: `apps/backend/go/main.go`

```go
package main

import (
    "fmt"
    "log"
    "net/http"

    "github.com/gin-gonic/gin"
    "sapisehat-gateway/config"
    "sapisehat-gateway/handlers"
    "sapisehat-gateway/middleware"
)

func main() {
    // Load config from environment
    cfg := config.Load()

    // Set Gin mode
    if cfg.Env == "production" {
        gin.SetMode(gin.ReleaseMode)
    }

    // Create router
    router := gin.New()

    // Middleware
    router.Use(middleware.Logger())    // Request logging
    router.Use(middleware.CORS())      // CORS for Android app
    router.Use(gin.Recovery())         // Panic recovery

    // Routes
    api := router.Group("/api")
    {
        api.POST("/predict", handlers.Predict(cfg))
        api.GET("/health",   handlers.Health(cfg))
    }

    // Root
    router.GET("/", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{
            "name":    "SapiSehat Gateway",
            "version": cfg.ModelVersion,
            "status":  "running",
        })
    })

    // Start server
    addr := fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)
    log.Printf("SapiSehat Gateway starting on %s", addr)
    log.Printf("Forwarding inference to: %s", cfg.InferenceServiceURL)

    if err := router.Run(addr); err != nil {
        log.Fatalf("Server failed to start: %v", err)
    }
}
```

---

## 4. handlers/predict.go — Prediction Handler

File: `apps/backend/go/handlers/predict.go`

```go
package handlers

import (
    "io"
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
    "sapisehat-gateway/client"
    "sapisehat-gateway/config"
    "sapisehat-gateway/models"
)

// Predict handles POST /api/predict
// This is a thin HTTP layer — all inference logic is in the Python service
func Predict(cfg *config.Config) gin.HandlerFunc {
    // Create inference client once (connection pool shared across requests)
    inferenceClient := client.NewInferenceClient(cfg.InferenceServiceURL, cfg.RequestTimeoutSec)

    return func(c *gin.Context) {
        requestID := uuid.New().String()
        c.Header("X-Request-ID", requestID)

        // Step 1: Get uploaded file
        file, header, err := c.Request.FormFile("image")
        if err != nil {
            c.JSON(http.StatusUnprocessableEntity, models.ErrorResponse{
                Status:  "error",
                Message: "image field is required",
                Code:    "MISSING_IMAGE",
            })
            return
        }
        defer file.Close()

        // Step 2: Validate content type
        contentType := header.Header.Get("Content-Type")
        if !isValidImageType(contentType) {
            c.JSON(http.StatusUnprocessableEntity, models.ErrorResponse{
                Status:  "error",
                Message: "Invalid image format. Accepted: JPEG, PNG, WebP",
                Code:    "INVALID_IMAGE_FORMAT",
            })
            return
        }

        // Step 3: Read image bytes
        imageBytes, err := io.ReadAll(file)
        if err != nil {
            c.JSON(http.StatusInternalServerError, models.ErrorResponse{
                Status:  "error",
                Message: "Failed to read image",
                Code:    "READ_ERROR",
            })
            return
        }

        if len(imageBytes) == 0 {
            c.JSON(http.StatusUnprocessableEntity, models.ErrorResponse{
                Status:  "error",
                Message: "Empty image file",
                Code:    "EMPTY_IMAGE",
            })
            return
        }

        // Step 4: Forward to Python inference service
        result, err := inferenceClient.Predict(imageBytes, contentType, requestID)
        if err != nil {
            c.JSON(http.StatusServiceUnavailable, models.ErrorResponse{
                Status:  "error",
                Message: "Inference service unavailable",
                Code:    "INFERENCE_UNAVAILABLE",
            })
            return
        }

        // Step 5: Return result to Android
        c.JSON(http.StatusOK, result)
    }
}

// isValidImageType checks if content type is accepted
func isValidImageType(contentType string) bool {
    accepted := []string{"image/jpeg", "image/jpg", "image/png", "image/webp"}
    for _, t := range accepted {
        if strings.EqualFold(contentType, t) {
            return true
        }
    }
    return false
}
```

---

## 5. handlers/health.go — Health Handler

File: `apps/backend/go/handlers/health.go`

```go
package handlers

import (
    "net/http"
    "time"

    "github.com/gin-gonic/gin"
    "sapisehat-gateway/client"
    "sapisehat-gateway/config"
)

// Health handles GET /api/health
// Checks both Go gateway and Python inference service health
func Health(cfg *config.Config) gin.HandlerFunc {
    inferenceClient := client.NewInferenceClient(cfg.InferenceServiceURL, 5)

    return func(c *gin.Context) {
        // Check Python inference service
        inferenceStatus := "ok"
        inferenceErr := ""
        
        if err := inferenceClient.HealthCheck(); err != nil {
            inferenceStatus = "degraded"
            inferenceErr = err.Error()
        }

        status := "ok"
        httpStatus := http.StatusOK
        
        if inferenceStatus != "ok" {
            status = "degraded"
            httpStatus = http.StatusServiceUnavailable
        }

        response := gin.H{
            "status":        status,
            "model_version": cfg.ModelVersion,
            "gateway":       "go",
            "timestamp":     time.Now().UTC().Format(time.RFC3339),
            "services": gin.H{
                "go_gateway": "ok",
                "inference":  inferenceStatus,
            },
        }

        if inferenceErr != "" {
            response["inference_error"] = inferenceErr
        }

        c.JSON(httpStatus, response)
    }
}
```

---

## 6. middleware/logger.go — Request Logging

File: `apps/backend/go/middleware/logger.go`

```go
package middleware

import (
    "encoding/json"
    "fmt"
    "time"

    "github.com/gin-gonic/gin"
)

// Logger returns Gin middleware that writes structured JSON logs
func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path
        method := c.Request.Method

        // Process request
        c.Next()

        // Calculate duration
        duration := time.Since(start)
        statusCode := c.Writer.Status()
        requestID := c.GetHeader("X-Request-ID")

        // Build log entry
        logEntry := map[string]interface{}{
            "timestamp":   time.Now().UTC().Format(time.RFC3339),
            "level":       logLevel(statusCode),
            "method":      method,
            "path":        path,
            "status":      statusCode,
            "duration_ms": duration.Milliseconds(),
            "request_id":  requestID,
            "ip":          c.ClientIP(),
        }

        if len(c.Errors) > 0 {
            logEntry["errors"] = c.Errors.Errors()
        }

        logJSON, _ := json.Marshal(logEntry)
        fmt.Println(string(logJSON))
    }
}

func logLevel(statusCode int) string {
    switch {
    case statusCode >= 500:
        return "ERROR"
    case statusCode >= 400:
        return "WARN"
    default:
        return "INFO"
    }
}
```

---

## 7. middleware/cors.go — CORS Handling

File: `apps/backend/go/middleware/cors.go`

```go
package middleware

import (
    "net/http"

    "github.com/gin-gonic/gin"
)

// CORS returns Gin middleware for Cross-Origin Resource Sharing
// Configured to allow requests from Android app
func CORS() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Header("Access-Control-Allow-Origin", "*")
        c.Header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        c.Header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Request-ID")
        c.Header("Access-Control-Expose-Headers", "X-Request-ID")

        // Handle preflight request
        if c.Request.Method == http.MethodOptions {
            c.AbortWithStatus(http.StatusNoContent)
            return
        }

        c.Next()
    }
}
```

---

## 8. client/inference.go — Inference Client

File: `apps/backend/go/client/inference.go`

This is the core connection between Go gateway and Python inference service.

```go
package client

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "mime/multipart"
    "net"
    "net/http"
    "time"
)

// InferenceClient manages HTTP connection to Python inference service
type InferenceClient struct {
    baseURL    string
    httpClient *http.Client
}

// PredictResponse matches the JSON from Python InferenceService.predict()
// This struct mirrors api/schemas.py PredictResponse
type PredictResponse struct {
    Status string `json:"status"`
    Prediction *PredictionResult `json:"prediction,omitempty"`
    ModelInfo *ModelInfo `json:"model_info,omitempty"`
    ProcessingTimeMs int `json:"processing_time_ms"`
    PreprocessingTimeMs *int `json:"preprocessing_time_ms,omitempty"`
    InferenceTimeMs *int `json:"inference_time_ms,omitempty"`
    Message *string `json:"message,omitempty"`
}

type PredictionResult struct {
    Label        string             `json:"label"`
    DisplayLabel string             `json:"display_label"`
    Confidence   float64            `json:"confidence"`
    IsReliable   bool               `json:"is_reliable"`
    Scores       map[string]float64 `json:"scores"`
}

type ModelInfo struct {
    Version string `json:"version"`
}

// NewInferenceClient creates a client with connection pooling
func NewInferenceClient(baseURL string, timeoutSec int) *InferenceClient {
    return &InferenceClient{
        baseURL: baseURL,
        httpClient: &http.Client{
            Timeout: time.Duration(timeoutSec) * time.Second,
            Transport: &http.Transport{
                // Connection pooling — reuse connections to Python service
                MaxIdleConns:        10,
                MaxIdleConnsPerHost: 10,
                IdleConnTimeout:     90 * time.Second,
                
                // Dial timeout
                DialContext: (&net.Dialer{
                    Timeout:   30 * time.Second,
                    KeepAlive: 30 * time.Second,
                }).DialContext,
            },
        },
    }
}

// Predict forwards image bytes to Python inference service
// contentType: "image/jpeg", "image/png", or "image/webp"
// requestID: for tracing through logs
func (c *InferenceClient) Predict(imageBytes []byte, contentType string, requestID string) (*PredictResponse, error) {
    // Build multipart form body (matches what Python /infer endpoint expects)
    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)

    // Add image field
    part, err := writer.CreateFormFile("image", "photo.jpg")
    if err != nil {
        return nil, fmt.Errorf("failed to create form file: %w", err)
    }

    if _, err := part.Write(imageBytes); err != nil {
        return nil, fmt.Errorf("failed to write image bytes: %w", err)
    }

    writer.Close()

    // Build request
    req, err := http.NewRequest("POST", c.baseURL+"/infer", body)
    if err != nil {
        return nil, fmt.Errorf("failed to create request: %w", err)
    }

    req.Header.Set("Content-Type", writer.FormDataContentType())
    req.Header.Set("X-Request-ID", requestID)  // Pass through for log tracing

    // Send request
    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("inference service request failed: %w", err)
    }
    defer resp.Body.Close()

    // Read response
    respBytes, err := io.ReadAll(resp.Body)
    if err != nil {
        return nil, fmt.Errorf("failed to read inference response: %w", err)
    }

    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("inference service returned %d: %s", resp.StatusCode, string(respBytes))
    }

    // Parse JSON
    var result PredictResponse
    if err := json.Unmarshal(respBytes, &result); err != nil {
        return nil, fmt.Errorf("failed to parse inference response: %w", err)
    }

    return &result, nil
}

// HealthCheck pings the Python inference service
func (c *InferenceClient) HealthCheck() error {
    resp, err := c.httpClient.Get(c.baseURL + "/health")
    if err != nil {
        return fmt.Errorf("inference service unreachable: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("inference service unhealthy: status %d", resp.StatusCode)
    }

    return nil
}
```

---

## 9. config/config.go — Configuration

File: `apps/backend/go/config/config.go`

```go
package config

import (
    "os"
    "strconv"
)

// Config holds all configuration loaded from environment variables
type Config struct {
    // Server
    Env  string
    Host string
    Port int

    // Inference service
    InferenceServiceURL string
    RequestTimeoutSec   int

    // Model metadata
    ModelVersion string
}

// Load reads config from environment variables with sensible defaults
func Load() *Config {
    return &Config{
        Env:                 getEnv("ENV", "development"),
        Host:                getEnv("HOST", "0.0.0.0"),
        Port:                getEnvInt("PORT", 8000),
        InferenceServiceURL: getEnv("INFERENCE_SERVICE_URL", "http://localhost:9000"),
        RequestTimeoutSec:   getEnvInt("REQUEST_TIMEOUT_SEC", 60),
        ModelVersion:        getEnv("MODEL_VERSION", "1.0.0"),
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
    if value := os.Getenv(key); value != "" {
        if intValue, err := strconv.Atoi(value); err == nil {
            return intValue
        }
    }
    return defaultValue
}
```

---

## 10. models/response.go — Response Models

File: `apps/backend/go/models/response.go`

```go
package models

// ErrorResponse is returned when a request fails
// Matches the error format expected by the Android app
type ErrorResponse struct {
    Status  string `json:"status"`
    Message string `json:"message"`
    Code    string `json:"code"`
}
```

---

## 11. How to Build and Test

### Prerequisites

```bash
# Install Go 1.21+
# Windows: https://go.dev/dl/
# Linux:   sudo apt install golang-go
# Mac:     brew install go

go version  # Should show 1.21+
```

### Build Steps

```bash
cd apps/backend/go

# Download dependencies
go mod tidy

# Build binary
go build -o sapisehat-gateway .

# Run
./sapisehat-gateway
```

### Run with Environment Variables

```bash
ENV=production \
HOST=0.0.0.0 \
PORT=8000 \
INFERENCE_SERVICE_URL=http://inference:9000 \
REQUEST_TIMEOUT_SEC=60 \
./sapisehat-gateway
```

### Build Docker Image

```dockerfile
# apps/backend/go/Dockerfile

# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Cache dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o sapisehat-gateway .

# Final stage — minimal image
FROM alpine:3.18

RUN apk --no-cache add ca-certificates curl

WORKDIR /root/

COPY --from=builder /app/sapisehat-gateway .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["./sapisehat-gateway"]
```

Build:

```bash
cd apps/backend/go
docker build -t sapisehat-gateway:latest .

# Image size should be ~15MB (vs ~1GB for Python FastAPI)
docker images sapisehat-gateway
```

### Unit Tests

```bash
cd apps/backend/go

# Run all tests
go test ./...

# With verbose output
go test ./... -v

# With coverage
go test ./... -cover
```

Example test for inference client:

```go
// client/inference_test.go
package client

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestPredictSuccess(t *testing.T) {
    // Mock inference service
    mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{
            "status": "success",
            "prediction": {
                "label": "SEHAT",
                "display_label": "Sapi Sehat",
                "confidence": 0.9432,
                "is_reliable": true,
                "scores": {
                    "SEHAT": 0.9432,
                    "PMK": 0.0312,
                    "LATO_LATO": 0.0256
                }
            },
            "model_info": {"version": "1.0.0"},
            "processing_time_ms": 2345
        }`))
    }))
    defer mockServer.Close()

    client := NewInferenceClient(mockServer.URL, 10)
    result, err := client.Predict([]byte("fake-image-bytes"), "image/jpeg", "test-request-id")

    if err != nil {
        t.Fatalf("Expected no error, got: %v", err)
    }

    if result.Status != "success" {
        t.Errorf("Expected status 'success', got: %s", result.Status)
    }

    if result.Prediction.Label != "SEHAT" {
        t.Errorf("Expected label 'SEHAT', got: %s", result.Prediction.Label)
    }
}

func TestHealthCheck(t *testing.T) {
    // Mock healthy inference service
    mockServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{"status": "ok"}`))
    }))
    defer mockServer.Close()

    client := NewInferenceClient(mockServer.URL, 5)
    err := client.HealthCheck()

    if err != nil {
        t.Errorf("Expected no error for healthy service, got: %v", err)
    }
}

func TestPredictServiceDown(t *testing.T) {
    // No mock server = service unavailable
    client := NewInferenceClient("http://localhost:99999", 1)
    _, err := client.Predict([]byte("fake"), "image/jpeg", "test-id")

    if err == nil {
        t.Error("Expected error when service is down")
    }
}
```

Run tests:

```bash
go test ./client/... -v
```

---

## Response Schema Compatibility

The Go gateway passes through Python responses unchanged. The Android app receives the same JSON it received from FastAPI.

```
Android App expects:
{
  "status": "success",
  "prediction": {
    "label": "PMK",
    "display_label": "Penyakit Mulut & Kuku",
    "confidence": 0.9432,
    "is_reliable": true,
    "scores": { "SEHAT": 0.031, "PMK": 0.943, "LATO_LATO": 0.026 }
  },
  "model_info": { "version": "1.0.0" },
  "processing_time_ms": 2345
}

Go passes this through exactly — no transformation.
```

---

*This Go gateway is a thin proxy. All inference logic remains in Python.*
