import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # FastAPI
    fastapi_env: str = os.getenv("FASTAPI_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Model
    model_path: str = os.getenv("MODEL_PATH", "./model/mobilenetv2_best.keras")
    device: str = os.getenv("DEVICE", "cpu")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "4"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Rate limiting
    rate_limit_max_requests: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Model metadata
    model_version: str = "cattle-disease-mobilenetv2-v20260601-s42"
    labels: list = ["FMD", "LSD", "healthy"]
    confidence_threshold: float = 0.60
    field_confidence_threshold: float = 0.70
    field_margin_threshold: float = 0.15
    two_stage_enabled: bool = os.getenv("TWO_STAGE_ENABLED", "false").lower() == "true"
    two_stage_debug_regions_enabled: bool = os.getenv("TWO_STAGE_DEBUG_REGIONS", "false").lower() == "true"
    input_size: int = 224

settings = Settings()
