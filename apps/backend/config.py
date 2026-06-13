import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def resolve_cors_origins(*, fastapi_env: str, cors_origins: str) -> list[str]:
    """Resolve CORS origins with production wildcard guard."""
    origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    if not origins:
        origins = ["*"] if fastapi_env in {"development", "test"} else []
    if fastapi_env == "production" and "*" in origins:
        raise ValueError("CORS_ORIGINS must not contain wildcard in production")
    return origins


def resolve_backend_path(path_value: str) -> str:
    """Resolve model paths from repo root or backend app directory."""
    path = Path(path_value)
    if path.is_absolute() or path.exists():
        return str(path)
    backend_relative = Path(__file__).resolve().parent / path
    if backend_relative.exists():
        return str(backend_relative)
    return path_value

UNSAFE_JWT_SECRETS = {"", "sapisehat-dev-token-secret", "change-me", "dev-secret"}

def validate_production_settings(settings: "Settings") -> None:
    """Fail fast when production uses unsafe defaults."""
    if settings.fastapi_env != "production":
        return
    if settings.jwt_secret in UNSAFE_JWT_SECRETS or len(settings.jwt_secret) < 32:
        raise ValueError("JWT_SECRET must be set to a strong production secret")
    if not settings.s3_bucket:
        raise ValueError("S3_BUCKET must be set in production")
    if not settings.s3_access_key_id or settings.s3_access_key_id == "minioadmin":
        raise ValueError("S3_ACCESS_KEY_ID must be set to a production value")
    if not settings.s3_secret_access_key or settings.s3_secret_access_key == "minioadmin":
        raise ValueError("S3_SECRET_ACCESS_KEY must be set to a production value")
    if settings.google_auth_enabled and not settings.google_client_id:
        raise ValueError("GOOGLE_CLIENT_ID must be set when Google auth is enabled")


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # FastAPI
    fastapi_env: str = os.getenv("FASTAPI_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"

    # Model
    model_path: str = resolve_backend_path(os.getenv("MODEL_PATH", "./model/tes1_best.keras"))
    model_class_names_path: str = resolve_backend_path(os.getenv("MODEL_CLASS_NAMES_PATH", "./model/class_names.json"))
    device: str = os.getenv("DEVICE", "cpu")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    workers: int = int(os.getenv("WORKERS", "4"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "sapisehat-dev-token-secret")
    media_max_upload_bytes: int = int(os.getenv("MEDIA_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    s3_bucket: str = os.getenv("S3_BUCKET", "sapisehat-scan-images")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_access_key_id: str = os.getenv("S3_ACCESS_KEY_ID", "minioadmin")
    s3_secret_access_key: str = os.getenv("S3_SECRET_ACCESS_KEY", "minioadmin")
    s3_force_path_style: bool = os.getenv("S3_FORCE_PATH_STYLE", "true").lower() == "true"
    google_auth_enabled: bool = os.getenv("GOOGLE_AUTH_ENABLED", "false").lower() == "true"
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_id_token_issuers: str = os.getenv("GOOGLE_ID_TOKEN_ISSUERS", "https://accounts.google.com,accounts.google.com")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Seeding
    # SEED_TIER: production = admin only, staging = all accounts, development = all accounts + sample data.
    # Defaults to FASTAPI_ENV when unset.
    seed_tier: str = os.getenv("SEED_TIER", "")
    master_admin_email: str = os.getenv("MASTER_ADMIN_EMAIL", "admin@sapisehat.id")
    master_admin_password: str = os.getenv("MASTER_ADMIN_PASSWORD", "admin123")
    master_admin_name: str = os.getenv("MASTER_ADMIN_NAME", "Admin Agency")
    master_admin_jurisdiction: str = os.getenv("MASTER_ADMIN_JURISDICTION", "central-java")

    # Rate limiting
    rate_limit_max_requests: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "1000"))
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

    @property
    def allowed_cors_origins(self) -> list[str]:
        return resolve_cors_origins(fastapi_env=self.fastapi_env, cors_origins=self.cors_origins)

    @property
    def allowed_google_id_token_issuers(self) -> list[str]:
        return [issuer.strip() for issuer in self.google_id_token_issuers.split(",") if issuer.strip()]

    @property
    def resolved_seed_tier(self) -> str:
        """Seed tier, defaulting to FASTAPI_ENV when SEED_TIER is unset."""
        tier = (self.seed_tier or self.fastapi_env or "development").lower()
        if tier == "test":
            tier = "development"
        if tier not in {"production", "staging", "development"}:
            tier = "development"
        return tier

settings = Settings()
validate_production_settings(settings)
