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


class AgencyVisibleFarmer(BaseModel):
    """Farmer record visible to an agency user after authorization filtering."""
    id: str
    name: str
    jurisdiction_id: str
    consent_tier: str

class AgencyFarmersResponse(BaseModel):
    """Agency-scoped farmer list response."""
    agency_user_id: str
    farmers: List[AgencyVisibleFarmer]


class FarmerAccountRequest(BaseModel):
    """Register or sign in farmer by phone-number identity."""
    phone_number: str = Field(min_length=8, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    jurisdiction_id: str = Field(min_length=1, max_length=120)

class FarmerAccountResponse(BaseModel):
    """Phone-number farmer account response."""
    id: str
    phone_number: str
    name: str
    jurisdiction_id: str
    consent_state: str
    created: bool


class CattleProfileRequest(BaseModel):
    """Create cattle profile linked to farmer account."""
    tag: str = Field(min_length=1, max_length=80)
    sex: str
    breed: str = Field(default="unknown", max_length=120)
    age_months: Optional[int] = Field(default=None, ge=0)
    birth_year_estimate: Optional[int] = Field(default=None, ge=1900, le=2100)
    status: str = "active"
    jurisdiction_id: str = Field(min_length=1, max_length=120)

class CattleProfileResponse(BaseModel):
    """Cattle profile response."""
    id: str
    farmer_id: str
    tag: str
    sex: str
    breed: str
    age_months: Optional[int]
    birth_year_estimate: Optional[int]
    status: str
    jurisdiction_id: str

class CattleProfileListResponse(BaseModel):
    """Selectable cattle list for detection."""
    cattle: List[CattleProfileResponse]
