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


class FarmerRegisterRequest(BaseModel):
    """Register farmer mobile account with email/password."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)
    jurisdiction_id: str = Field(min_length=1, max_length=120)


class FarmerLoginRequest(BaseModel):
    """Login farmer mobile account with email/password."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class AgencyLoginRequest(BaseModel):
    """Login agency dashboard account with email/password."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class AuthAccountResponse(BaseModel):
    """Authenticated surface account."""

    id: str
    account_type: str
    email: str
    is_active: bool = True
    name: str = ""
    jurisdiction_id: str = ""
    role: Optional[str] = None


class FarmerProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    jurisdiction_id: str = Field(min_length=1, max_length=120)


class FarmerArchiveRequest(BaseModel):
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class FarmerPreferencesResponse(BaseModel):
    farmer_id: str
    scan_result_notifications: bool
    sync_notifications: bool
    area_risk_advisory_notifications: bool
    follow_up_status_notifications: bool
    quiet_hours_enabled: bool
    quiet_hours_start: str
    quiet_hours_end: str


class FarmerPreferencesRequest(BaseModel):
    scan_result_notifications: bool = True
    sync_notifications: bool = True
    area_risk_advisory_notifications: bool = False
    follow_up_status_notifications: bool = True
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "21:00"
    quiet_hours_end: str = "06:00"


class AuthResponse(BaseModel):
    """Access token response for surface auth."""

    access_token: str
    token_type: str = "bearer"
    account: AuthAccountResponse


class FarmerGoogleLoginRequest(BaseModel):
    """Farmer Google sign-in token exchange."""

    id_token: str = Field(min_length=1)
    jurisdiction_id: str = Field(min_length=1, max_length=120)


class FollowUpCreateRequest(BaseModel):
    """Agency-created follow-up status with hidden internal notes."""

    farmer_id: str = Field(min_length=1, max_length=120)
    cattle_id: Optional[str] = Field(default=None, max_length=120)
    status: str = Field(min_length=1, max_length=40)
    public_message: str = Field(min_length=1, max_length=500)
    internal_notes: str = Field(default="", max_length=1000)


class AgencyFollowUpResponse(BaseModel):
    """Agency-visible follow-up status."""

    id: str
    farmer_id: str
    cattle_id: Optional[str]
    status: str
    public_message: str
    internal_notes: str


class FollowUpUpdateRequest(BaseModel):
    """Agency edit of an existing follow-up."""

    status: Optional[str] = Field(default=None, max_length=40)
    public_message: Optional[str] = Field(default=None, max_length=500)
    internal_notes: Optional[str] = Field(default=None, max_length=1000)


class FarmerFollowUpResponse(BaseModel):
    """Farmer-visible follow-up status without internal notes."""

    id: str
    farmer_id: str
    cattle_id: Optional[str]
    status: str
    public_message: str


class FarmerFollowUpListResponse(BaseModel):
    """Farmer follow-up status list."""

    follow_ups: List[FarmerFollowUpResponse]


class AuditLogResponse(BaseModel):
    """Audit log entry."""

    id: str
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    metadata_json: Dict[str, object]
    created_at: str


class AuditLogListResponse(BaseModel):
    """Audit log list."""

    audit_logs: List[AuditLogResponse]


class NotificationResponse(BaseModel):
    """User notification item."""

    id: str
    account_id: str
    account_type: str
    title: str
    body: str
    link: Optional[str]
    is_read: bool
    created_at: str


class NotificationListResponse(BaseModel):
    """Notification list."""

    notifications: List[NotificationResponse]
    unread_count: int


class NotificationMarkReadResponse(BaseModel):
    """Result of marking notifications read."""

    marked_count: int


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
    consent_state: str = "private"


class FarmerAccountResponse(BaseModel):
    """Phone-number farmer account response."""

    id: str
    phone_number: str
    name: str
    jurisdiction_id: str
    consent_state: str
    created: bool


class ScanImageStorageNoticeRequest(BaseModel):
    """Farmer acceptance for first-scan image storage notice."""

    accepted: bool


class ScanImageStorageNoticeResponse(BaseModel):
    """Current scan image storage notice acceptance state."""

    farmer_id: str
    scan_image_storage_notice_accepted: bool


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


class CattleTimelineEventRequest(BaseModel):
    """Create operational cattle timeline event."""

    event_type: str = "vaccination"
    event_date: str = Field(min_length=10, max_length=10)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1000)
    payload: Dict[str, object] = Field(default_factory=dict)
    creator_id: str = Field(min_length=1, max_length=120)


class CattleTimelineEventResponse(BaseModel):
    """Cattle timeline event response."""

    id: str
    cattle_id: str
    event_type: str
    event_date: str
    title: str
    description: str
    payload: Dict[str, object]
    creator_id: str


class CattleProfileDetailResponse(CattleProfileResponse):
    """Cattle detail with timeline."""

    timeline: List[CattleTimelineEventResponse]


class QuickScanDetectionRequest(BaseModel):
    """Create unattached quick-scan detection."""

    farmer_id: str = Field(min_length=1, max_length=120)
    result_label: str = Field(min_length=1, max_length=120)
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "quick_scan"


class AttachDetectionRequest(BaseModel):
    """Attach quick-scan detection to owned cattle."""

    cattle_id: str = Field(min_length=1, max_length=120)


class DetectionEventResponse(BaseModel):
    """Detection event response."""

    id: str
    farmer_id: str
    cattle_id: Optional[str]
    result_label: str
    confidence: float
    source: str
    attached: bool


class DetectionEventListResponse(BaseModel):
    """Detection event list response."""

    detections: List[DetectionEventResponse]


class ImageEvidenceQualityStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WARNING = "warning"


class ImageEvidenceInferenceMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class ImageEvidenceRequest(BaseModel):
    """Team 1 image evidence contract payload."""

    source: str = "image"
    model_version: str = Field(min_length=1, max_length=80)
    inference_mode: ImageEvidenceInferenceMode
    disease_scores: Dict[str, float]
    top_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    quality_status: ImageEvidenceQualityStatus
    rejection_reasons: List[str] = Field(default_factory=list)
    debug: Dict[str, object] = Field(default_factory=dict)

    @classmethod
    def _required_score_keys(cls) -> set[str]:
        return {"healthy", "FMD", "LSD"}

    def model_post_init(self, __context):
        if self.source != "image":
            raise ValueError("source must be image")
        if set(self.disease_scores.keys()) != self._required_score_keys():
            raise ValueError(
                "disease_scores must contain exactly healthy, FMD, and LSD"
            )
        if any(score < 0.0 or score > 1.0 for score in self.disease_scores.values()):
            raise ValueError("disease_scores values must be between 0 and 1")
        if self.top_class not in self._required_score_keys():
            raise ValueError("top_class must be healthy, FMD, or LSD")
        if self.top_class != max(self.disease_scores, key=self.disease_scores.get):
            raise ValueError("top_class must match highest disease score")
        if (
            self.quality_status == ImageEvidenceQualityStatus.REJECTED
            and not self.rejection_reasons
        ):
            raise ValueError("rejected image evidence requires rejection_reasons")


class ImageEvidenceResponse(ImageEvidenceRequest):
    """Validated Team 1 image evidence response."""

    accepted_for_fusion: bool


class NlpEvidenceInferenceMode(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class NlpEvidenceRequest(BaseModel):
    """Team 2 NLP evidence contract payload."""

    source: str = "nlp"
    model_version: str = Field(min_length=1, max_length=80)
    inference_mode: NlpEvidenceInferenceMode
    questionnaire_answers: Dict[str, object] = Field(default_factory=dict)
    notes_present: bool
    disease_scores: Dict[str, float]
    top_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_terms: List[str] = Field(default_factory=list)
    debug: Dict[str, object] = Field(default_factory=dict)

    @classmethod
    def _required_score_keys(cls) -> set[str]:
        return {"healthy", "FMD", "LSD"}

    def model_post_init(self, __context):
        if self.source != "nlp":
            raise ValueError("source must be nlp")
        if not self.questionnaire_answers and not self.notes_present:
            raise ValueError("questionnaire_answers or notes_present is required")
        if set(self.disease_scores.keys()) != self._required_score_keys():
            raise ValueError(
                "disease_scores must contain exactly healthy, FMD, and LSD"
            )
        if any(score < 0.0 or score > 1.0 for score in self.disease_scores.values()):
            raise ValueError("disease_scores values must be between 0 and 1")
        if self.top_class not in self._required_score_keys():
            raise ValueError("top_class must be healthy, FMD, or LSD")
        if self.top_class != max(self.disease_scores, key=self.disease_scores.get):
            raise ValueError("top_class must match highest disease score")


class NlpEvidenceResponse(NlpEvidenceRequest):
    """Validated Team 2 NLP evidence response."""

    accepted_for_fusion: bool


class NlpPlaceholderRequest(BaseModel):
    """Temporary NLP placeholder input until Team 2 artifact is ready."""

    farmer_id: str = Field(min_length=1, max_length=120)
    cattle_id: Optional[str] = None
    symptom_text: str = Field(default="", max_length=2000)
    questionnaire_answers: Dict[str, object] = Field(default_factory=dict)


class NlpPlaceholderResponse(BaseModel):
    """Explicit NLP-unavailable response with no fusion side effects."""

    status: str
    evidence_state: str
    accepted_for_fusion: bool
    creates_review_item: bool
    creates_risk_signal: bool
    message: str


class FusionRequest(BaseModel):
    """Backend-primary fusion request."""

    farmer_id: str = Field(min_length=1, max_length=120)
    cattle_id: Optional[str] = None
    image_evidence: Optional[ImageEvidenceRequest] = None
    nlp_evidence: Optional[NlpEvidenceRequest] = None


class FusionResultResponse(BaseModel):
    """Stored fusion result response."""

    id: str
    fusion_version: str
    inference_mode: str
    farmer_id: str
    cattle_id: Optional[str]
    disease_class: str
    confidence: float
    confidence_level: str
    reliability: str
    handling_advice_key: str
    evidence_breakdown: Dict[str, object]
    conflict_status: str
    model_versions: Dict[str, str]
    created_at: str


class FusionResultListResponse(BaseModel):
    """Fusion result list response."""

    results: List[FusionResultResponse]


class OfflineDetectionSyncRequest(BaseModel):
    """Offline fused detection sync request from mobile."""

    local_detection_id: str = Field(min_length=1, max_length=160)
    farmer_id: str = Field(min_length=1, max_length=120)
    cattle_id: Optional[str] = None
    local_created_at: str = Field(min_length=10, max_length=40)
    image_evidence: Optional[ImageEvidenceRequest] = None
    nlp_evidence: Optional[NlpEvidenceRequest] = None
    offline_fused_result: Dict[str, object] = Field(default_factory=dict)


class OfflineDetectionSyncResponse(BaseModel):
    """Synced offline detection response."""

    local_detection_id: str
    sync_status: str
    local_created_at: str
    synced_at: str
    fusion_result: FusionResultResponse


class StoredMediaRequest(BaseModel):
    """Stored media metadata request governed by consent."""

    farmer_id: str = Field(min_length=1, max_length=120)
    cattle_id: Optional[str] = None
    detection_id: Optional[str] = None
    checksum: str = Field(min_length=8, max_length=128)
    consent_scope: str = Field(min_length=1, max_length=80)
    storage_reference: str = Field(min_length=1, max_length=240)
    content_type: str = Field(default="image/jpeg", max_length=80)
    byte_size: int = Field(default=0, ge=0)
    retention_policy: str = Field(default="first_release_monitoring", max_length=80)


class StoredMediaResponse(BaseModel):
    """Stored media metadata response."""

    id: str
    farmer_id: str
    cattle_id: Optional[str]
    detection_id: Optional[str]
    checksum: str
    consent_scope: str
    storage_reference: str
    storage_backend: str
    object_key: str
    content_type: str
    byte_size: int
    retention_policy: str
    created_at: str


class StoredMediaListResponse(BaseModel):
    """Stored media list response."""

    media: List[StoredMediaResponse]


class StoredMediaDownloadUrlResponse(BaseModel):
    """Short-lived media download URL response."""

    media_id: str
    url: str
    expires_seconds: int


class AgencyRegistryResponse(BaseModel):
    """Agency dashboard registry response."""

    agency_user_id: str
    farmers: List[AgencyVisibleFarmer]
    cattle: List[CattleProfileResponse]
    filters: Dict[str, object]


class AgencyDetectionMonitoringResponse(BaseModel):
    """Agency dashboard detection monitoring response."""

    agency_user_id: str
    detections: List[FusionResultResponse]
    safe_language: Dict[str, str]


class JurisdictionRiskSignalResponse(BaseModel):
    """Jurisdiction-level disease risk signal summary."""

    id: str
    jurisdiction_id: str
    disease_class: str
    signal_count: int
    window_days: int
    risk_level: str
    priority: str
    summary_label: str
    source_result_ids: List[str]


class AgencyRiskSignalSummaryResponse(BaseModel):
    """Agency dashboard disease risk signal summary response."""

    agency_user_id: str
    rule: Dict[str, object]
    signals: List[JurisdictionRiskSignalResponse]
    safe_language: Dict[str, str]


class FarmerAreaAdvisoryResponse(BaseModel):
    """Farmer-safe area advisory derived from district cluster risk signals."""

    farmer_id: str
    jurisdiction_id: str
    advisory_active: bool
    title: str
    message: str
    signals: List[JurisdictionRiskSignalResponse]
    safe_language: Dict[str, str]
