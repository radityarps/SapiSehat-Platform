"""FastAPI routes - HTTP layer (replaceable by Go)."""

import asyncio
import hashlib
import io
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Header, Path
from fastapi.responses import JSONResponse
from PIL import Image
from inference_server import get_inference_service, is_model_ready, get_model_status
from api.schemas import (
    PredictResponse,
    HealthResponse,
    FarmerRegisterRequest,
    FarmerLoginRequest,
    FarmerGoogleLoginRequest,
    AgencyLoginRequest,
    AuthResponse,
    AuthAccountResponse,
    AgencyFarmersResponse,
    FarmerAccountRequest,
    FarmerAccountResponse,
    ScanImageStorageNoticeRequest,
    ScanImageStorageNoticeResponse,
    CattleProfileRequest,
    CattleProfileResponse,
    CattleProfileListResponse,
    CattleTimelineEventRequest,
    CattleTimelineEventResponse,
    CattleProfileDetailResponse,
    QuickScanDetectionRequest,
    AttachDetectionRequest,
    DetectionEventResponse,
    DetectionEventListResponse,
    ImageEvidenceRequest,
    ImageEvidenceResponse,
    NlpEvidenceRequest,
    NlpEvidenceResponse,
    NlpPlaceholderRequest,
    NlpPlaceholderResponse,
    FusionRequest,
    FusionResultResponse,
    FusionResultListResponse,
    OfflineDetectionSyncRequest,
    OfflineDetectionSyncResponse,
    StoredMediaRequest,
    StoredMediaResponse,
    StoredMediaListResponse,
    StoredMediaDownloadUrlResponse,
    AgencyRegistryResponse,
    AgencyDetectionMonitoringResponse,
    AgencyRiskSignalSummaryResponse,
    FarmerAreaAdvisoryResponse,
    FollowUpCreateRequest,
    AgencyFollowUpResponse,
    FarmerFollowUpListResponse,
    AuditLogListResponse,
)
from config import settings
from utils.logger import get_logger
from api.farmer_accounts import FarmerConsentState, farmer_account_store
from api.cattle_profiles import CattleEventType, CattleSex, CattleStatus, cattle_profile_store
from api.detection_events import detection_event_store
from api.fusion_results import fusion_result_store
from api.offline_sync import offline_detection_sync_store
from api.media_governance import media_store
from api.object_storage import media_storage_client
from api.audit_logs import audit_log_store
from api.follow_ups import follow_up_store
from api.risk_signals import cluster_risk_signal_store, summarize_risk_signals
from api.authorization import ConsentTier, FarmerRecord, DEMO_AGENCY_USERS, DEMO_FARMERS, DEMO_JURISDICTIONS, can_agency_access_farmer, filter_visible_farmers
from api.surface_auth import issue_token, read_token, seed_default_agency_accounts, surface_account_store

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


def _serialize_auth_account(account):
    return {"id": account.id, "account_type": account.account_type, "email": account.email}

def _serialize_audit_log(event):
    return {
        "id": event.id,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "action": event.action,
        "resource_type": event.resource_type,
        "resource_id": event.resource_id,
        "metadata_json": event.metadata_json,
        "created_at": event.created_at,
    }

def _require_admin_agency(agency_user_id: str):
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    if agency.role.value != "admin":
        raise HTTPException(status_code=403, detail="Audit logs require admin agency role")
    return agency



@router.get("/agency/audit-logs", response_model=AuditLogListResponse, tags=["agency"])
async def list_agency_audit_logs(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List recent audit logs for admin agency users only."""
    _require_admin_agency(agency_user_id)
    events = audit_log_store.list_recent(action=action, resource_type=resource_type, limit=limit)
    return {"audit_logs": [_serialize_audit_log(event) for event in events]}

@router.post("/auth/farmer/register", response_model=AuthResponse, tags=["auth"])
async def register_farmer_surface_account(request: FarmerRegisterRequest):
    """Register farmer mobile account with email/password and issue token."""
    try:
        account = surface_account_store.register_farmer(
            email=request.email,
            password=request.password,
            name=request.name,
            jurisdiction_id=request.jurisdiction_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"access_token": issue_token(account), "token_type": "bearer", "account": _serialize_auth_account(account)}


@router.post("/auth/farmer/login", response_model=AuthResponse, tags=["auth"])
async def login_farmer_surface_account(request: FarmerLoginRequest):
    """Login farmer mobile account with email/password and issue token."""
    account = surface_account_store.authenticate(account_type="farmer", email=request.email, password=request.password)
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": issue_token(account), "token_type": "bearer", "account": _serialize_auth_account(account)}

@router.post("/auth/farmer/google", response_model=AuthResponse, tags=["auth"])
async def login_farmer_google_account(request: FarmerGoogleLoginRequest):
    """Exchange verified Google token for farmer backend JWT."""
    try:
        account = surface_account_store.register_farmer_google(id_token=request.id_token, jurisdiction_id=request.jurisdiction_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"access_token": issue_token(account), "token_type": "bearer", "account": _serialize_auth_account(account)}


@router.post("/auth/agency/login", response_model=AuthResponse, tags=["auth"])
async def login_agency_surface_account(request: AgencyLoginRequest):
    """Login admin-seeded agency dashboard account with email/password."""
    seed_default_agency_accounts()
    account = surface_account_store.authenticate(account_type="agency", email=request.email, password=request.password)
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": issue_token(account), "token_type": "bearer", "account": _serialize_auth_account(account)}

@router.post("/auth/agency/google", tags=["auth"])
async def reject_agency_google_login():
    """Agency Google sign-in disabled in first release."""
    raise HTTPException(status_code=404, detail="Agency Google login not available")


@router.get("/me", response_model=AuthAccountResponse, tags=["auth"])
async def get_current_surface_account(authorization: str = Header(..., alias="Authorization")):
    """Return current account from bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    account = surface_account_store.get_by_id(account_type=str(claims["account_type"]), account_id=str(claims["sub"]))
    if account is None:
        raise HTTPException(status_code=401, detail="Account not found")
    return _serialize_auth_account(account)


def _serialize_cattle(profile):
    return {
        "id": profile.id,
        "farmer_id": profile.farmer_id,
        "tag": profile.tag,
        "sex": profile.sex.value,
        "breed": profile.breed,
        "age_months": profile.age_months,
        "birth_year_estimate": profile.birth_year_estimate,
        "status": profile.status.value,
        "jurisdiction_id": profile.jurisdiction_id,
    }



def _serialize_cattle_event(event):
    return {
        "id": event.id,
        "cattle_id": event.cattle_id,
        "event_type": event.event_type.value,
        "event_date": event.event_date,
        "title": event.title,
        "description": event.description,
        "payload": event.payload,
        "creator_id": event.creator_id,
    }

def _serialize_cattle_detail(profile):
    detail = _serialize_cattle(profile)
    detail["timeline"] = [_serialize_cattle_event(event) for event in cattle_profile_store.list_timeline_events(profile.id)]
    return detail




def _serialize_media(media):
    return {
        "id": media.id,
        "farmer_id": media.farmer_id,
        "cattle_id": media.cattle_id,
        "detection_id": media.detection_id,
        "checksum": media.checksum,
        "consent_scope": media.consent_scope,
        "storage_reference": media.storage_reference,
        "storage_backend": media.storage_backend,
        "object_key": media.object_key,
        "content_type": media.content_type,
        "byte_size": media.byte_size,
        "retention_policy": media.retention_policy,
        "created_at": media.created_at,
    }

def _serialize_agency_follow_up(follow_up):
    return {
        "id": follow_up.id,
        "farmer_id": follow_up.farmer_id,
        "cattle_id": follow_up.cattle_id,
        "status": follow_up.status,
        "public_message": follow_up.public_message,
        "internal_notes": follow_up.internal_notes,
    }

def _serialize_farmer_follow_up(follow_up):
    return {
        "id": follow_up.id,
        "farmer_id": follow_up.farmer_id,
        "cattle_id": follow_up.cattle_id,
        "status": follow_up.status,
        "public_message": follow_up.public_message,
    }

def _serialize_fusion_result(result):
    return {
        "id": result.id,
        "fusion_version": result.fusion_version,
        "inference_mode": result.inference_mode,
        "farmer_id": result.farmer_id,
        "cattle_id": result.cattle_id,
        "disease_class": result.disease_class,
        "confidence": result.confidence,
        "confidence_level": result.confidence_level,
        "reliability": result.reliability,
        "handling_advice_key": result.handling_advice_key,
        "evidence_breakdown": result.evidence_breakdown,
        "conflict_status": result.conflict_status,
        "model_versions": result.model_versions,
        "created_at": result.created_at,
    }

def _serialize_detection(event):
    return {
        "id": event.id,
        "farmer_id": event.farmer_id,
        "cattle_id": event.cattle_id,
        "result_label": event.result_label,
        "confidence": event.confidence,
        "source": event.source,
        "attached": event.attached,
    }

@router.post("/predict", response_model=PredictResponse, tags=["prediction"])
async def predict(
    image: UploadFile = File(...),
    two_stage: bool = Query(False, description="Developer-only two-stage prototype path"),
    debug_regions: bool = Query(False, description="Include developer-only symptom-region debug data"),
):
    """Predict cattle disease from image using no-retention request handling.

    Uploaded image bytes are processed in memory for this request only and are
    not written to backend storage by this legacy prediction endpoint.
    """
    if not is_model_ready():
        raise HTTPException(status_code=503, detail="Model not loaded")

    if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        logger.warning(f"Invalid content type: {image.content_type}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid image format. Accepted: JPEG, PNG, WebP. Got: {image.content_type}",
        )

    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Empty image file")

    try:
        img_pil = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        logger.warning(f"Failed to open image: {e}")
        raise HTTPException(status_code=422, detail="Invalid or corrupted image file")

    service = get_inference_service()
    try:
        use_two_stage = two_stage and settings.two_stage_enabled
        predict_fn = service.predict_two_stage_prototype if use_two_stage else service.predict
        if use_two_stage:
            threaded = asyncio.to_thread(
                predict_fn,
                img_pil,
                include_debug_regions=debug_regions and settings.two_stage_debug_regions_enabled,
            )
        else:
            threaded = asyncio.to_thread(predict_fn, img_pil)
        result = await asyncio.wait_for(threaded, timeout=settings.request_timeout)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request processing exceeded timeout")

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Inference failed"))
    audit_log_store.record(
        actor_type="system",
        actor_id="predict-endpoint",
        action="prediction.created",
        resource_type="prediction",
        resource_id=result["prediction"]["disease_class"],
        metadata_json={"content_type": image.content_type, "two_stage": use_two_stage},
    )
    return result


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    try:
        model_status = get_model_status()
        return {
            "status": "ok" if model_status["model_loaded"] else "degraded",
            "model_loaded": model_status["model_loaded"],
            "model_version": settings.model_version,
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "degraded", "model_loaded": False, "model_version": "unknown"},
        )


@router.get("/agency/farmers", response_model=AgencyFarmersResponse)
async def list_agency_visible_farmers(agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Return farmers visible to agency user after role-jurisdiction-consent filtering."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_farmers = filter_visible_farmers(agency=agency, farmers=DEMO_FARMERS, jurisdictions=DEMO_JURISDICTIONS)
    return {"agency_user_id": agency_user_id, "farmers": [farmer.__dict__ for farmer in visible_farmers]}


@router.post("/farmers/accounts", response_model=FarmerAccountResponse)
async def register_or_sign_in_farmer_account(request: FarmerAccountRequest):
    """Register or sign in farmer using phone-number identity."""
    try:
        account, created = farmer_account_store.upsert_by_phone(
            phone_number=request.phone_number,
            name=request.name,
            jurisdiction_id=request.jurisdiction_id,
            consent_state=FarmerConsentState(request.consent_state),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "id": account.id,
        "phone_number": account.phone_number,
        "name": account.name,
        "jurisdiction_id": account.jurisdiction_id,
        "consent_state": account.consent_state.value,
        "created": created,
    }

@router.post("/farmers/{farmer_id}/scan-image-storage-notice", response_model=ScanImageStorageNoticeResponse)
async def accept_scan_image_storage_notice(request: ScanImageStorageNoticeRequest, farmer_id: str = Path(...)):
    """Store farmer acceptance for scan image storage notice."""
    farmer = farmer_account_store.set_scan_image_storage_notice(farmer_id, accepted=request.accepted)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "farmer_id": farmer.id,
        "scan_image_storage_notice_accepted": farmer.scan_image_storage_notice_accepted,
    }

@router.get("/farmers/{farmer_id}/scan-image-storage-notice", response_model=ScanImageStorageNoticeResponse)
async def get_scan_image_storage_notice(farmer_id: str = Path(...)):
    """Read farmer scan image storage notice acceptance."""
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "farmer_id": farmer.id,
        "scan_image_storage_notice_accepted": farmer.scan_image_storage_notice_accepted,
    }


@router.post("/farmers/{farmer_id}/cattle", response_model=CattleProfileResponse, tags=["farmer"])
async def create_cattle_profile(request: CattleProfileRequest, farmer_id: str = Path(...)):
    """Create cattle profile linked to farmer account before detection."""
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    try:
        profile = cattle_profile_store.create(
            farmer=farmer,
            tag=request.tag,
            sex=CattleSex(request.sex),
            breed=request.breed,
            age_months=request.age_months,
            birth_year_estimate=request.birth_year_estimate,
            status=CattleStatus(request.status),
            jurisdiction_id=request.jurisdiction_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_cattle(profile)


@router.get("/farmers/{farmer_id}/cattle", response_model=CattleProfileListResponse)
async def list_farmer_cattle_for_detection(farmer_id: str = Path(...)):
    """List farmer-owned cattle profiles so mobile can select before detection."""
    if farmer_account_store.get_by_id(farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {"cattle": [_serialize_cattle(profile) for profile in cattle_profile_store.list_by_farmer(farmer_id)]}


@router.get("/farmers/{farmer_id}/cattle/{cattle_id}", response_model=CattleProfileDetailResponse)
async def select_farmer_cattle_for_detection(farmer_id: str = Path(...), cattle_id: str = Path(...)):
    """Select one farmer-owned cattle profile before detection starts."""
    profile = cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=cattle_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return _serialize_cattle_detail(profile)

@router.delete("/farmers/{farmer_id}/cattle/{cattle_id}", response_model=CattleProfileResponse)
async def archive_farmer_cattle(farmer_id: str = Path(...), cattle_id: str = Path(...)):
    """Archive cattle instead of true deletion in first release."""
    profile = cattle_profile_store.archive(farmer_id=farmer_id, cattle_id=cattle_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return _serialize_cattle(profile)


@router.get("/agency/cattle", response_model=CattleProfileListResponse)
async def list_agency_visible_cattle(agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """List cattle visible to agency after role-jurisdiction-consent filtering."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    return {"cattle": [_serialize_cattle(profile) for profile in visible]}

@router.post("/farmers/{farmer_id}/cattle/{cattle_id}/timeline", response_model=CattleTimelineEventResponse)
async def add_farmer_cattle_timeline_event(
    request: CattleTimelineEventRequest,
    farmer_id: str = Path(...),
    cattle_id: str = Path(...),
):
    """Add operational cattle event to owned cattle timeline."""
    try:
        event = cattle_profile_store.add_timeline_event(
            farmer_id=farmer_id,
            cattle_id=cattle_id,
            event_type=CattleEventType(request.event_type),
            event_date=request.event_date,
            title=request.title,
            description=request.description,
            payload=request.payload,
            creator_id=request.creator_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if event is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return _serialize_cattle_event(event)

@router.get("/agency/cattle/{cattle_id}", response_model=CattleProfileDetailResponse)
async def get_agency_visible_cattle_detail(
    cattle_id: str = Path(...),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Read cattle detail with timeline when agency is authorized."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    for profile in visible:
        if profile.id == cattle_id:
            return _serialize_cattle_detail(profile)
    raise HTTPException(status_code=404, detail="Cattle not visible to agency")


@router.post("/detections/quick-scan", response_model=DetectionEventResponse)
async def create_quick_scan_detection(request: QuickScanDetectionRequest):
    """Create unattached emergency quick-scan detection."""
    if farmer_account_store.get_by_id(request.farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    event = detection_event_store.create_quick_scan(
        farmer_id=request.farmer_id,
        result_label=request.result_label,
        confidence=request.confidence,
        source=request.source,
    )
    return _serialize_detection(event)

@router.post("/farmers/{farmer_id}/detections/{detection_id}/attach", response_model=DetectionEventResponse)
async def attach_quick_scan_detection(
    request: AttachDetectionRequest,
    farmer_id: str = Path(...),
    detection_id: str = Path(...),
):
    """Attach unattached quick-scan result to farmer-owned cattle."""
    if cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=request.cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    event = detection_event_store.attach_to_cattle(
        farmer_id=farmer_id,
        detection_id=detection_id,
        cattle_id=request.cattle_id,
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Unattached detection not found for farmer")
    return _serialize_detection(event)

@router.get("/agency/detections", response_model=DetectionEventListResponse)
async def list_agency_visible_attached_detections(agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """List attached detections visible to agency after cattle authorization."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    events = detection_event_store.list_by_cattle_ids({profile.id for profile in visible_cattle})
    return {"detections": [_serialize_detection(event) for event in events]}


@router.post("/evidence/image", response_model=ImageEvidenceResponse)
async def validate_image_evidence(request: ImageEvidenceRequest):
    """Validate Team 1 image evidence contract for fusion consumers."""
    return {
        **request.model_dump(),
        "accepted_for_fusion": request.quality_status.value != "rejected",
    }


@router.post("/evidence/nlp", response_model=NlpEvidenceResponse)
async def validate_nlp_evidence(request: NlpEvidenceRequest):
    """Validate Team 2 NLP evidence contract for fusion consumers."""
    return {
        **request.model_dump(),
        "accepted_for_fusion": True,
    }

@router.post("/evidence/nlp/placeholder", response_model=NlpPlaceholderResponse, tags=["prediction"])
async def create_nlp_placeholder(request: NlpPlaceholderRequest):
    """Return explicit NLP-unavailable state without scores, fusion, review, or risk side effects."""
    if farmer_account_store.get_by_id(request.farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if request.cattle_id is not None and cattle_profile_store.get_owned(farmer_id=request.farmer_id, cattle_id=request.cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return {
        "status": "unavailable",
        "evidence_state": "nlp_unavailable",
        "accepted_for_fusion": False,
        "creates_review_item": False,
        "creates_risk_signal": False,
        "message": "Team 2 NLP evidence is not available yet. This placeholder does not produce scores or affect fusion, review items, or risk signals.",
    }


@router.post("/fusion/results", response_model=FusionResultResponse)
async def create_backend_primary_fusion_result(request: FusionRequest):
    """Fuse Team 1 image and Team 2 NLP evidence into safe early detection result."""
    if farmer_account_store.get_by_id(request.farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if request.cattle_id is not None and cattle_profile_store.get_owned(farmer_id=request.farmer_id, cattle_id=request.cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    try:
        result = fusion_result_store.create(
            farmer_id=request.farmer_id,
            cattle_id=request.cattle_id,
            image_evidence=request.image_evidence,
            nlp_evidence=request.nlp_evidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_fusion_result(result)

@router.get("/fusion/results", response_model=FusionResultListResponse)
async def list_fusion_results():
    """List stored backend-primary fusion tracer results."""
    return {"results": [_serialize_fusion_result(result) for result in fusion_result_store.list_all()]}


@router.post("/offline/detections/sync", response_model=OfflineDetectionSyncResponse)
async def sync_offline_detection(request: OfflineDetectionSyncRequest):
    """Sync mobile-created offline fused detection while preserving local id and evidence versions."""
    if farmer_account_store.get_by_id(request.farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if request.cattle_id is not None and cattle_profile_store.get_owned(farmer_id=request.farmer_id, cattle_id=request.cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    try:
        synced = offline_detection_sync_store.sync(
            local_detection_id=request.local_detection_id,
            farmer_id=request.farmer_id,
            cattle_id=request.cattle_id,
            local_created_at=request.local_created_at,
            image_evidence=request.image_evidence,
            nlp_evidence=request.nlp_evidence,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "local_detection_id": synced.local_detection_id,
        "sync_status": synced.sync_status,
        "local_created_at": synced.local_created_at,
        "synced_at": synced.synced_at,
        "fusion_result": _serialize_fusion_result(synced.fusion_result),
    }


@router.post("/media", response_model=StoredMediaResponse, tags=["media"])
async def create_stored_media_metadata(request: StoredMediaRequest):
    """Store media metadata only when farmer consent permits research/monitoring."""
    farmer = farmer_account_store.get_by_id(request.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if not farmer.scan_image_storage_notice_accepted:
        raise HTTPException(status_code=403, detail="Scan image storage notice must be accepted before storing media")
    if farmer.consent_state != FarmerConsentState.RESEARCH_AND_MONITORING:
        raise HTTPException(status_code=403, detail="Media storage requires research_and_monitoring consent")
    if request.consent_scope != "research_and_monitoring":
        raise HTTPException(status_code=422, detail="consent_scope must be research_and_monitoring")
    if request.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=422, detail="content_type must be image/jpeg, image/png, or image/webp")
    if request.cattle_id is not None and cattle_profile_store.get_owned(farmer_id=request.farmer_id, cattle_id=request.cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    media = media_store.create(
        farmer_id=request.farmer_id,
        cattle_id=request.cattle_id,
        detection_id=request.detection_id,
        checksum=request.checksum,
        consent_scope=request.consent_scope,
        storage_reference=request.storage_reference,
        content_type=request.content_type,
        byte_size=request.byte_size,
        retention_policy=request.retention_policy,
    )
    return _serialize_media(media)

def _validate_media_storage_allowed(*, farmer_id: str, cattle_id: str | None, consent_scope: str, content_type: str) -> None:
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if not farmer.scan_image_storage_notice_accepted:
        raise HTTPException(status_code=403, detail="Scan image storage notice must be accepted before storing media")
    if farmer.consent_state != FarmerConsentState.RESEARCH_AND_MONITORING:
        raise HTTPException(status_code=403, detail="Media storage requires research_and_monitoring consent")
    if consent_scope != "research_and_monitoring":
        raise HTTPException(status_code=422, detail="consent_scope must be research_and_monitoring")
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=422, detail="content_type must be image/jpeg, image/png, or image/webp")
    if cattle_id is not None and cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")


def _media_object_key(*, farmer_id: str, media_id: str, filename: str, content_type: str) -> str:
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[content_type]
    now = datetime.now(timezone.utc)
    return f"scan-images/{farmer_id}/{now:%Y}/{now:%m}/{media_id}.{extension}"


@router.post("/media/uploads", response_model=StoredMediaResponse, tags=["media"])
async def upload_scan_image_media(
    farmer_id: str = Form(...),
    cattle_id: str | None = Form(default=None),
    detection_id: str | None = Form(default=None),
    consent_scope: str = Form(default="research_and_monitoring"),
    retention_policy: str = Form(default="first_release_monitoring"),
    file: UploadFile = File(...),
):
    """Upload scan image bytes to MinIO/S3-compatible object storage."""
    content_type = file.content_type or "application/octet-stream"
    _validate_media_storage_allowed(farmer_id=farmer_id, cattle_id=cattle_id, consent_scope=consent_scope, content_type=content_type)
    content = await file.read()
    if len(content) > settings.media_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Media upload too large")
    media_id = f"media-{uuid4().hex}"
    object_key = _media_object_key(farmer_id=farmer_id, media_id=media_id, filename=file.filename or "scan", content_type=content_type)
    media_storage_client.put_object(object_key=object_key, content=content, content_type=content_type)
    checksum = hashlib.sha256(content).hexdigest()
    media = media_store.create(
        farmer_id=farmer_id,
        cattle_id=cattle_id,
        detection_id=detection_id,
        checksum=checksum,
        consent_scope=consent_scope,
        storage_reference=object_key,
        storage_backend=media_storage_client.backend,
        object_key=object_key,
        content_type=content_type,
        byte_size=len(content),
        retention_policy=retention_policy,
        media_id=media_id,
    )
    audit_log_store.record(
        actor_type="farmer",
        actor_id=farmer_id,
        action="media.uploaded",
        resource_type="media",
        resource_id=media.id,
        metadata_json={"object_key": object_key, "content_type": content_type, "byte_size": len(content)},
    )
    return _serialize_media(media)

@router.get("/agency/media/{media_id}", response_model=StoredMediaResponse)
async def get_agency_visible_media(media_id: str = Path(...), agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Read media metadata only when agency passes role-jurisdiction-consent gates."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    media = media_store.get(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    farmer = farmer_account_store.get_by_id(media.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    record = FarmerRecord(farmer.id, farmer.name, farmer.jurisdiction_id, ConsentTier(farmer.consent_state.value))
    if not can_agency_access_farmer(agency, record, DEMO_JURISDICTIONS):
        raise HTTPException(status_code=403, detail="Media not visible to agency")
    return _serialize_media(media)


@router.get("/agency/media/{media_id}/download-url", response_model=StoredMediaDownloadUrlResponse, tags=["media"])
async def get_agency_media_download_url(media_id: str = Path(...), agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Issue short-lived URL for agency-visible scan image."""
    media = media_store.get(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    await get_agency_visible_media(media_id=media_id, agency_user_id=agency_user_id)
    if not media.object_key:
        raise HTTPException(status_code=404, detail="Media object not stored")
    expires_seconds = 900
    url = media_storage_client.presigned_get_url(object_key=media.object_key, expires_seconds=expires_seconds)
    audit_log_store.record(
        actor_type="agency",
        actor_id=agency_user_id,
        action="media.download_url_issued",
        resource_type="media",
        resource_id=media.id,
        metadata_json={"expires_seconds": expires_seconds},
    )
    return {
        "media_id": media.id,
        "url": url,
        "expires_seconds": expires_seconds,
    }


@router.post("/agency/follow-ups", response_model=AgencyFollowUpResponse)
async def create_agency_follow_up(request: FollowUpCreateRequest, agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Create agency follow-up status; internal notes stay agency-only."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    farmer = farmer_account_store.get_by_id(request.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    record = FarmerRecord(farmer.id, farmer.name, farmer.jurisdiction_id, ConsentTier(farmer.consent_state.value))
    if not can_agency_access_farmer(agency, record, DEMO_JURISDICTIONS):
        raise HTTPException(status_code=403, detail="Farmer not visible to agency")
    if request.cattle_id is not None and cattle_profile_store.get_owned(farmer_id=request.farmer_id, cattle_id=request.cattle_id) is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    follow_up = follow_up_store.create(
        farmer_id=request.farmer_id,
        cattle_id=request.cattle_id,
        status=request.status,
        public_message=request.public_message,
        internal_notes=request.internal_notes,
    )
    audit_log_store.record(
        actor_type="agency",
        actor_id=agency_user_id,
        action="follow_up.created",
        resource_type="follow_up",
        resource_id=follow_up.id,
        metadata_json={"farmer_id": request.farmer_id, "cattle_id": request.cattle_id, "status": request.status},
    )
    return _serialize_agency_follow_up(follow_up)

@router.get("/farmers/{farmer_id}/follow-ups", response_model=FarmerFollowUpListResponse)
async def list_farmer_follow_up_status(farmer_id: str = Path(...)):
    """List farmer-visible follow-up statuses without agency internal notes."""
    if farmer_account_store.get_by_id(farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {"follow_ups": [_serialize_farmer_follow_up(item) for item in follow_up_store.list_by_farmer(farmer_id)]}


@router.get("/agency/registry", response_model=AgencyRegistryResponse)
async def get_agency_dashboard_registry(agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Return dashboard registry farmers and cattle scoped to agency authorization."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_demo_farmers = filter_visible_farmers(agency=agency, farmers=DEMO_FARMERS, jurisdictions=DEMO_JURISDICTIONS)
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    return {
        "agency_user_id": agency_user_id,
        "farmers": [farmer.__dict__ for farmer in visible_demo_farmers],
        "cattle": [_serialize_cattle(profile) for profile in visible_cattle],
        "filters": {
            "search": "name/tag",
            "jurisdiction_id": agency.jurisdiction_id,
            "consent_scope": "agency_monitoring_or_research_and_monitoring",
            "table_pattern": "TanStack Table compatible columns",
        },
    }


@router.get("/agency/detection-monitoring", response_model=AgencyDetectionMonitoringResponse, tags=["agency"])
async def get_agency_detection_monitoring(agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Return agency-scoped fused detection monitoring rows with safe risk language."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    results = fusion_result_store.list_by_cattle_ids({profile.id for profile in visible_cattle})
    return {
        "agency_user_id": agency_user_id,
        "detections": [_serialize_fusion_result(result) for result in results],
        "safe_language": {
            "title": "Disease risk signals",
            "description": "Early detection signals for monitoring and follow-up, not confirmed diagnosis or outbreak declaration.",
            "forbidden_terms": "confirmed outbreak, confirmed diagnosis",
        },
    }


@router.get("/agency/risk-signals", response_model=AgencyRiskSignalSummaryResponse)
async def get_agency_risk_signal_summary(agency_user_id: str = Header(..., alias="X-Agency-User-Id")):
    """Return jurisdiction-level possible increased disease risk signals inside agency scope."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    visible_cattle_ids = {profile.id for profile in visible_cattle}
    results = fusion_result_store.list_by_cattle_ids(visible_cattle_ids)
    jurisdictions = {profile.id: profile.jurisdiction_id for profile in visible_cattle}
    signals = summarize_risk_signals(results, jurisdictions)
    cluster_risk_signal_store.replace_all(signals)
    signals = cluster_risk_signal_store.list_all()
    return {
        "agency_user_id": agency_user_id,
        "rule": {
            "name": "three_or_more_non_healthy_signals_7d",
            "threshold_count": 3,
            "window_days": 7,
            "included_reliability": ["reliable", "needs_review"],
            "language": "possible increased risk, not confirmed outbreak or diagnosis",
        },
        "signals": [signal.__dict__ for signal in signals],
        "safe_language": {
            "title": "Disease risk signal summary",
            "description": "Possible increased risk signals for follow-up prioritization. Not confirmed outbreak. Not veterinary diagnosis.",
        },
    }

@router.get("/farmers/{farmer_id}/area-advisory", response_model=FarmerAreaAdvisoryResponse, tags=["farmer"])
async def get_farmer_area_advisory(farmer_id: str = Path(...)):
    """Return farmer-safe district advisory when cluster risk signal exists in farmer jurisdiction."""
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    signals = [signal for signal in cluster_risk_signal_store.list_all() if signal.jurisdiction_id == farmer.jurisdiction_id and signal.risk_level == "possible_increased_risk"]
    return {
        "farmer_id": farmer.id,
        "jurisdiction_id": farmer.jurisdiction_id,
        "advisory_active": bool(signals),
        "title": "Area disease-risk advisory" if signals else "No area advisory",
        "message": "Increased disease-risk reports in your district. Monitor cattle, improve biosecurity, and contact animal health officers if symptoms appear." if signals else "No increased district-level disease-risk reports are active for your area.",
        "signals": [signal.__dict__ for signal in signals],
        "safe_language": {
            "scope": "district-level advisory only",
            "privacy": "does not expose other farmers, cattle identities, or exact scan details",
            "disclaimer": "not confirmed diagnosis or outbreak declaration",
        },
    }
