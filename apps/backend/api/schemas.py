"""Pydantic schemas for API requests/responses."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum


class DiseaseClass(str, Enum):
    """Disease classification labels."""
    FMD = "FMD"
    LSD = "LSD"
    HEALTHY = "healthy"
    INSUFFICIENT_VISUAL_EVIDENCE = "INSUFFICIENT_VISUAL_EVIDENCE"

class SymptomRegionDebug(BaseModel):
    """Developer-only symptom-region debug output."""
    x_min: float = Field(ge=0.0, le=1.0)
    y_min: float = Field(ge=0.0, le=1.0)
    x_max: float = Field(ge=0.0, le=1.0)
    y_max: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    symptom_region_type: str


class PredictionResult(BaseModel):
    """Single prediction result."""
    disease_class: DiseaseClass
    display_label_key: str  # e.g., "disease.pmk"
    confidence: float = Field(ge=0.0, le=1.0)
    is_reliable: bool
    scores: Dict[str, float]  # Exactly 3 entries
    outcome: str = "DISEASE_CLASS"
    needs_review: bool = False
    symptom_regions_debug: Optional[List[SymptomRegionDebug]] = None


class ModelInfo(BaseModel):
    """Model information."""
    version: str  # Semantic versioning "MAJOR.MINOR.PATCH"
    inference_pipeline: Optional[str] = None


class PredictResponse(BaseModel):
    """Response from /api/predict endpoint."""
    status: str = "success"
    prediction: PredictionResult
    model_info: ModelInfo
    processing_time_ms: int = Field(ge=0)
    preprocessing_time_ms: int = Field(ge=0)
    inference_time_ms: int = Field(ge=0)


class HealthResponse(BaseModel):
    """Response from /api/health endpoint."""
    status: str  # "ok" or "degraded"
    model_loaded: bool
    model_version: str


class ErrorResponse(BaseModel):
    """Standardized error response."""
    status: str = "error"
    error_code: str
    message: str = Field(max_length=256)
