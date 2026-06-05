"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from config import settings
from api.routes import router
from api.rate_limiter import RateLimiterMiddleware
from utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SapiSehat Backend",
    description="Cattle disease detection API (PMK & LSD)",
    version=settings.model_version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow requests from Android app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter middleware - per-IP sliding window for /api/predict
app.add_middleware(
    RateLimiterMiddleware,
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SapiSehat Backend",
        "version": settings.model_version,
        "docs": "/docs",
        "status": "running"
    }


def _resolve_error_code(exc: HTTPException) -> str:
    """Map HTTPException status code to a defined error code."""
    if exc.status_code == 422:
        return "INVALID_IMAGE"
    elif exc.status_code == 503:
        return "MODEL_NOT_READY"
    elif exc.status_code == 408:
        return "TIMEOUT"
    elif exc.status_code == 429:
        return "RATE_LIMITED"
    else:
        return "INFERENCE_FAILED"


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Convert all HTTPExceptions to standardized error shape."""
    error_code = _resolve_error_code(exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error_code": error_code,
            "message": str(exc.detail)[:256],
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INFERENCE_FAILED",
            "message": "Internal server error",
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting SapiSehat Backend (v{settings.model_version})")
    logger.info(f"Environment: {settings.fastapi_env}")
    logger.info(f"Device: {settings.device}")
    logger.info(f"Model path: {settings.model_path}")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )
