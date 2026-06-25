"""FastAPI routes - HTTP layer (replaceable by Go)."""

import asyncio
import hashlib
import io
from pydantic import BaseModel as BaseModel
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Query,
    Header,
    Path,
)
from fastapi.responses import JSONResponse
from PIL import Image
from inference_server import get_inference_service, is_model_ready, get_model_status
from api.schemas import (
    PredictResponse,
    HealthResponse,
    FarmerRegisterRequest,
    FarmerLoginRequest,
    AgencyLoginRequest,
    AuthResponse,
    AuthAccountResponse,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    FarmerProfileUpdateRequest,
    FarmerArchiveRequest,
    FarmerPreferencesRequest,
    FarmerPreferencesResponse,
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
    FollowUpUpdateRequest,
    AgencyFollowUpResponse,
    FarmerFollowUpListResponse,
    AuditLogListResponse,
    NotificationListResponse,
    NotificationMarkReadResponse,
    NotificationResponse,
)
from config import settings
from utils.logger import get_logger
from api.farmer_accounts import FarmerConsentState, farmer_account_store
from api.cattle_profiles import (
    CattleEventType,
    CattleSex,
    CattleStatus,
    cattle_profile_store,
)
from api.detection_events import detection_event_store
from api.fusion_results import fusion_result_store
from api.offline_sync import offline_detection_sync_store
from api.media_governance import media_store
from api.object_storage import media_storage_client
from api.audit_logs import audit_log_store
from api.follow_ups import follow_up_store
from api.notifications import notification_store
from api.risk_signals import (
    CLUSTER_WINDOW_DAYS,
    HYBRID_ALERT_THRESHOLD,
    RISK_SIGNAL_RELIABILITY,
    cluster_risk_signal_store,
    summarize_risk_signals,
)
from api.authorization import (
    AgencyRole,
    ConsentTier,
    FarmerRecord,
    DEMO_AGENCY_USERS,
    DEMO_FARMERS,
    DEMO_JURISDICTIONS,
    _agency_user_store,
    _jurisdiction_store,
    can_agency_access_farmer,
    filter_visible_farmers,
    refresh_agency_users,
)
from api.surface_auth import (
    issue_token,
    read_token,
    seed_default_agency_accounts,
    seed_default_farmer_accounts,
    surface_account_store,
)
from api.db_models import FarmerPreferenceModel
from api.database import SessionLocal

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


def _serialize_auth_account(account):
    result = {
        "id": account.id,
        "account_type": account.account_type,
        "email": account.email,
        "is_active": account.is_active,
        "name": account.name,
        "jurisdiction_id": account.jurisdiction_id,
    }
    if account.account_type == "agency":
        agency_user = _agency_user_store.get(account.id)
        if agency_user:
            result["role"] = agency_user.role.value
    return result


def _get_farmer_preferences(farmer_id: str):
    with SessionLocal() as session:
        row = session.get(FarmerPreferenceModel, farmer_id)
        if row is None:
            row = FarmerPreferenceModel(farmer_id=farmer_id)
            session.add(row)
            session.commit()
            session.refresh(row)
        return row


def _serialize_farmer_preferences(row):
    return {
        "farmer_id": row.farmer_id,
        "scan_result_notifications": row.scan_result_notifications,
        "sync_notifications": row.sync_notifications,
        "area_risk_advisory_notifications": row.area_risk_advisory_notifications,
        "follow_up_status_notifications": row.follow_up_status_notifications,
        "quiet_hours_enabled": row.quiet_hours_enabled,
        "quiet_hours_start": row.quiet_hours_start,
        "quiet_hours_end": row.quiet_hours_end,
    }


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

def _matches_query(values, query: str | None) -> bool:
    if not query:
        return True
    needle = query.casefold().strip()
    if not needle:
        return True
    return any(needle in str(value or "").casefold() for value in values)

def _filter_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or normalized.casefold() == "all":
        return None
    return normalized

def _same_filter_value(value: str | None, expected: str | None) -> bool:
    normalized = _filter_value(expected)
    if normalized is None:
        return True
    return str(value or "").casefold() == normalized.casefold()


def _serialize_notification(notification):
    return {
        "id": notification.id,
        "account_id": notification.account_id,
        "account_type": notification.account_type,
        "title": notification.title,
        "body": notification.body,
        "link": notification.link,
        "is_read": notification.is_read,
        "created_at": notification.created_at,
    }


def _require_admin_agency(agency_user_id: str):
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    if agency.role.value != "admin":
        raise HTTPException(
            status_code=403, detail="Audit logs require admin agency role"
        )
    return agency


@router.get("/agency/audit-logs", response_model=AuditLogListResponse, tags=["agency"])
async def list_agency_audit_logs(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List recent audit logs for agency users."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    action = _filter_value(action)
    resource_type = _filter_value(resource_type)
    events = audit_log_store.list_recent(
        action=action, resource_type=resource_type, limit=limit
    )
    if action:
        events = [event for event in events if _same_filter_value(event.action, action)]
    if resource_type:
        events = [
            event
            for event in events
            if _same_filter_value(event.resource_type, resource_type)
        ]
    events = [
        event
        for event in events
        if _matches_query(
            [
                event.id,
                event.actor_type,
                event.actor_id,
                event.action,
                event.resource_type,
                event.resource_id,
                event.metadata_json,
            ],
            search,
        )
    ]
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
    return {
        "access_token": issue_token(account),
        "token_type": "bearer",
        "account": _serialize_auth_account(account),
    }


@router.post("/auth/farmer/login", response_model=AuthResponse, tags=["auth"])
async def login_farmer_surface_account(request: FarmerLoginRequest):
    """Login farmer mobile account with email/password and issue token."""
    seed_default_farmer_accounts()
    try:
        account = surface_account_store.authenticate(
            account_type="farmer", email=request.email, password=request.password
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {
        "access_token": issue_token(account),
        "token_type": "bearer",
        "account": _serialize_auth_account(account),
    }


@router.post("/auth/agency/login", response_model=AuthResponse, tags=["auth"])
async def login_agency_surface_account(request: AgencyLoginRequest):
    """Login admin-seeded agency dashboard account with email/password."""
    seed_default_agency_accounts()
    try:
        account = surface_account_store.authenticate(
            account_type="agency", email=request.email, password=request.password
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    if account is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    result = _serialize_auth_account(account)
    # Ensure role is always included for agency accounts
    if "role" not in result:
        agency_user = _agency_user_store.get(account.id)
        if agency_user:
            result["role"] = agency_user.role.value
    return {
        "access_token": issue_token(account),
        "token_type": "bearer",
        "account": result,
    }


@router.get("/me", response_model=AuthAccountResponse, tags=["auth"])
async def get_current_surface_account(
    authorization: str = Header(..., alias="Authorization"),
):
    """Return current account from bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    account = surface_account_store.get_by_id(
        account_type=str(claims["account_type"]), account_id=str(claims["sub"])
    )
    if account is None:
        raise HTTPException(status_code=401, detail="Account not found")
    return _serialize_auth_account(account)


@router.put("/me/profile", response_model=AuthAccountResponse, tags=["auth"])
async def update_current_profile(
    request: ProfileUpdateRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    """Update the authenticated account's display name."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    account_id = str(claims["sub"])
    try:
        account = surface_account_store.update_profile(
            account_id=account_id, name=request.name
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_auth_account(account)


@router.post("/me/change-password", response_model=AuthAccountResponse, tags=["auth"])
async def change_current_password(
    request: ChangePasswordRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    """Change the authenticated account's password."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    account_id = str(claims["sub"])
    try:
        account = surface_account_store.change_password(
            account_id=account_id,
            current_password=request.current_password,
            new_password=request.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _serialize_auth_account(account)


@router.put(
    "/farmers/{farmer_id}/profile", response_model=AuthAccountResponse, tags=["farmer"]
)
async def update_farmer_profile(
    farmer_id: str,
    request: FarmerProfileUpdateRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if str(claims["sub"]) != farmer_id or str(claims["account_type"]) != "farmer":
        raise HTTPException(
            status_code=403, detail="Farmer profile update requires same farmer account"
        )
    try:
        account = surface_account_store.update_farmer_profile(
            account_id=farmer_id,
            name=request.name,
            jurisdiction_id=request.jurisdiction_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _serialize_auth_account(account)


@router.get(
    "/farmers/{farmer_id}/preferences",
    response_model=FarmerPreferencesResponse,
    tags=["farmer"],
)
async def get_farmer_preferences(
    farmer_id: str, authorization: str = Header(..., alias="Authorization")
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if str(claims["sub"]) != farmer_id:
        raise HTTPException(
            status_code=403, detail="Preferences require same farmer account"
        )
    return _serialize_farmer_preferences(_get_farmer_preferences(farmer_id))


@router.put(
    "/farmers/{farmer_id}/preferences",
    response_model=FarmerPreferencesResponse,
    tags=["farmer"],
)
async def put_farmer_preferences(
    farmer_id: str,
    request: FarmerPreferencesRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if str(claims["sub"]) != farmer_id:
        raise HTTPException(
            status_code=403, detail="Preferences require same farmer account"
        )
    with SessionLocal() as session:
        row = session.get(FarmerPreferenceModel, farmer_id) or FarmerPreferenceModel(
            farmer_id=farmer_id
        )
        row.scan_result_notifications = request.scan_result_notifications
        row.sync_notifications = request.sync_notifications
        row.area_risk_advisory_notifications = request.area_risk_advisory_notifications
        row.follow_up_status_notifications = request.follow_up_status_notifications
        row.quiet_hours_enabled = request.quiet_hours_enabled
        row.quiet_hours_start = request.quiet_hours_start
        row.quiet_hours_end = request.quiet_hours_end
        session.add(row)
        session.commit()
        session.refresh(row)
        return _serialize_farmer_preferences(row)


@router.post(
    "/farmers/{farmer_id}/account/archive",
    response_model=AuthAccountResponse,
    tags=["farmer"],
)
async def archive_farmer_account(
    farmer_id: str,
    request: FarmerArchiveRequest,
    authorization: str = Header(..., alias="Authorization"),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if str(claims["sub"]) != farmer_id or str(claims["account_type"]) != "farmer":
        raise HTTPException(
            status_code=403, detail="Farmer archive requires same farmer account"
        )
    try:
        account = surface_account_store.archive_farmer(
            account_id=farmer_id, password=request.password
        )
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
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
    detail["timeline"] = [
        _serialize_cattle_event(event)
        for event in cattle_profile_store.list_timeline_events(profile.id)
    ]
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
    two_stage: bool = Query(
        False, description="Developer-only two-stage prototype path"
    ),
    debug_regions: bool = Query(
        False, description="Include developer-only symptom-region debug data"
    ),
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
        if use_two_stage:
            include_debug_regions = (
                debug_regions and settings.two_stage_debug_regions_enabled
            )
            threaded = asyncio.to_thread(
                lambda: service.predict_two_stage_prototype(
                    img_pil,
                    include_debug_regions=include_debug_regions,
                )
            )
        else:
            threaded = asyncio.to_thread(service.predict, img_pil)
        result = await asyncio.wait_for(threaded, timeout=settings.request_timeout)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408, detail="Request processing exceeded timeout"
        )

    if result["status"] == "error":
        raise HTTPException(
            status_code=500, detail=result.get("message", "Inference failed")
        )
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
            content={
                "status": "degraded",
                "model_loaded": False,
                "model_version": "unknown",
            },
        )


@router.get("/agency/farmers", response_model=AgencyFarmersResponse)
async def list_agency_visible_farmers(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Return farmers visible to agency user after role-jurisdiction-consent filtering."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_farmers = filter_visible_farmers(
        agency=agency, farmers=DEMO_FARMERS, jurisdictions=DEMO_JURISDICTIONS
    )
    return {
        "agency_user_id": agency_user_id,
        "farmers": [farmer.__dict__ for farmer in visible_farmers],
    }


@router.post("/farmers/accounts", response_model=FarmerAccountResponse)
async def register_or_sign_in_farmer_account(request: FarmerAccountRequest):
    """Register or sign in farmer using phone-number identity."""
    try:
        account, created = farmer_account_store.upsert_by_phone(
            phone_number=request.phone_number,
            name=request.name,
            address=request.address,
            jurisdiction_id=request.jurisdiction_id,
            consent_state=FarmerConsentState(request.consent_state),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {
        "id": account.id,
        "phone_number": account.phone_number,
        "name": account.name,
        "address": account.address,
        "jurisdiction_id": account.jurisdiction_id,
        "consent_state": account.consent_state.value,
        "created": created,
    }


@router.post(
    "/farmers/{farmer_id}/scan-image-storage-notice",
    response_model=ScanImageStorageNoticeResponse,
)
async def accept_scan_image_storage_notice(
    request: ScanImageStorageNoticeRequest, farmer_id: str = Path(...)
):
    """Store farmer acceptance for scan image storage notice."""
    farmer = farmer_account_store.set_scan_image_storage_notice(
        farmer_id, accepted=request.accepted
    )
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "farmer_id": farmer.id,
        "scan_image_storage_notice_accepted": farmer.scan_image_storage_notice_accepted,
    }


@router.get(
    "/farmers/{farmer_id}/scan-image-storage-notice",
    response_model=ScanImageStorageNoticeResponse,
)
async def get_scan_image_storage_notice(farmer_id: str = Path(...)):
    """Read farmer scan image storage notice acceptance."""
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "farmer_id": farmer.id,
        "scan_image_storage_notice_accepted": farmer.scan_image_storage_notice_accepted,
    }


@router.post(
    "/farmers/{farmer_id}/cattle", response_model=CattleProfileResponse, tags=["farmer"]
)
async def create_cattle_profile(
    request: CattleProfileRequest, farmer_id: str = Path(...)
):
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
            jurisdiction_id=request.jurisdiction_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return _serialize_cattle(profile)


@router.get("/farmers/{farmer_id}/cattle", response_model=CattleProfileListResponse)
async def list_farmer_cattle_for_detection(farmer_id: str = Path(...)):
    """List farmer-owned cattle profiles so mobile can select before detection."""
    if farmer_account_store.get_by_id(farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "cattle": [
            _serialize_cattle(profile)
            for profile in cattle_profile_store.list_by_farmer(farmer_id)
        ]
    }


@router.get(
    "/farmers/{farmer_id}/cattle/{cattle_id}",
    response_model=CattleProfileDetailResponse,
)
async def select_farmer_cattle_for_detection(
    farmer_id: str = Path(...), cattle_id: str = Path(...)
):
    """Select one farmer-owned cattle profile before detection starts."""
    profile = cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=cattle_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return _serialize_cattle_detail(profile)


@router.delete(
    "/farmers/{farmer_id}/cattle/{cattle_id}", response_model=CattleProfileResponse
)
async def archive_farmer_cattle(farmer_id: str = Path(...), cattle_id: str = Path(...)):
    """Archive cattle instead of true deletion in first release."""
    profile = cattle_profile_store.archive(farmer_id=farmer_id, cattle_id=cattle_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return _serialize_cattle(profile)


@router.get("/agency/cattle", response_model=CattleProfileListResponse)
async def list_agency_visible_cattle(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
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


@router.post(
    "/farmers/{farmer_id}/cattle/{cattle_id}/timeline",
    response_model=CattleTimelineEventResponse,
)
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


@router.post(
    "/farmers/{farmer_id}/detections/{detection_id}/attach",
    response_model=DetectionEventResponse,
)
async def attach_quick_scan_detection(
    request: AttachDetectionRequest,
    farmer_id: str = Path(...),
    detection_id: str = Path(...),
):
    """Attach unattached quick-scan result to farmer-owned cattle."""
    if (
        cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=request.cattle_id)
        is None
    ):
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    event = detection_event_store.attach_to_cattle(
        farmer_id=farmer_id,
        detection_id=detection_id,
        cattle_id=request.cattle_id,
    )
    if event is None:
        raise HTTPException(
            status_code=404, detail="Unattached detection not found for farmer"
        )
    return _serialize_detection(event)


@router.get("/agency/detections", response_model=DetectionEventListResponse)
async def list_agency_visible_attached_detections(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """List attached detections visible to agency after cattle authorization."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    events = detection_event_store.list_by_cattle_ids(
        {profile.id for profile in visible_cattle}
    )
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


@router.post(
    "/evidence/nlp/placeholder",
    response_model=NlpPlaceholderResponse,
    tags=["prediction"],
)
async def create_nlp_placeholder(request: NlpPlaceholderRequest):
    """Return explicit NLP-unavailable state without scores, fusion, review, or risk side effects."""
    if farmer_account_store.get_by_id(request.farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if (
        request.cattle_id is not None
        and cattle_profile_store.get_owned(
            farmer_id=request.farmer_id, cattle_id=request.cattle_id
        )
        is None
    ):
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
    if (
        request.cattle_id is not None
        and cattle_profile_store.get_owned(
            farmer_id=request.farmer_id, cattle_id=request.cattle_id
        )
        is None
    ):
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
    return {
        "results": [
            _serialize_fusion_result(result)
            for result in fusion_result_store.list_all()
        ]
    }


@router.post("/offline/detections/sync", response_model=OfflineDetectionSyncResponse)
async def sync_offline_detection(request: OfflineDetectionSyncRequest):
    """Sync mobile-created offline fused detection while preserving local id and evidence versions."""
    if farmer_account_store.get_by_id(request.farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if (
        request.cattle_id is not None
        and cattle_profile_store.get_owned(
            farmer_id=request.farmer_id, cattle_id=request.cattle_id
        )
        is None
    ):
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
        raise HTTPException(
            status_code=403,
            detail="Scan image storage notice must be accepted before storing media",
        )
    if farmer.consent_state != FarmerConsentState.RESEARCH_AND_MONITORING:
        raise HTTPException(
            status_code=403,
            detail="Media storage requires research_and_monitoring consent",
        )
    if request.consent_scope != "research_and_monitoring":
        raise HTTPException(
            status_code=422, detail="consent_scope must be research_and_monitoring"
        )
    if request.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=422,
            detail="content_type must be image/jpeg, image/png, or image/webp",
        )
    if (
        request.cattle_id is not None
        and cattle_profile_store.get_owned(
            farmer_id=request.farmer_id, cattle_id=request.cattle_id
        )
        is None
    ):
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


def _validate_media_storage_allowed(
    *, farmer_id: str, cattle_id: str | None, consent_scope: str, content_type: str
) -> None:
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    if not farmer.scan_image_storage_notice_accepted:
        raise HTTPException(
            status_code=403,
            detail="Scan image storage notice must be accepted before storing media",
        )
    if farmer.consent_state != FarmerConsentState.RESEARCH_AND_MONITORING:
        raise HTTPException(
            status_code=403,
            detail="Media storage requires research_and_monitoring consent",
        )
    if consent_scope != "research_and_monitoring":
        raise HTTPException(
            status_code=422, detail="consent_scope must be research_and_monitoring"
        )
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=422,
            detail="content_type must be image/jpeg, image/png, or image/webp",
        )
    if (
        cattle_id is not None
        and cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=cattle_id)
        is None
    ):
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")


def _media_object_key(
    *, farmer_id: str, media_id: str, filename: str, content_type: str
) -> str:
    extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[
        content_type
    ]
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
    _validate_media_storage_allowed(
        farmer_id=farmer_id,
        cattle_id=cattle_id,
        consent_scope=consent_scope,
        content_type=content_type,
    )
    content = await file.read()
    if len(content) > settings.media_max_upload_bytes:
        raise HTTPException(status_code=413, detail="Media upload too large")
    media_id = f"media-{uuid4().hex}"
    object_key = _media_object_key(
        farmer_id=farmer_id,
        media_id=media_id,
        filename=file.filename or "scan",
        content_type=content_type,
    )
    media_storage_client.put_object(
        object_key=object_key, content=content, content_type=content_type
    )
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
        metadata_json={
            "object_key": object_key,
            "content_type": content_type,
            "byte_size": len(content),
        },
    )
    return _serialize_media(media)


@router.get("/agency/media/{media_id}", response_model=StoredMediaResponse)
async def get_agency_visible_media(
    media_id: str = Path(...),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
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
    record = FarmerRecord(
        farmer.id,
        farmer.name,
        farmer.jurisdiction_id,
        ConsentTier(farmer.consent_state.value),
    )
    if not can_agency_access_farmer(agency, record, DEMO_JURISDICTIONS):
        raise HTTPException(status_code=403, detail="Media not visible to agency")
    return _serialize_media(media)


@router.get(
    "/agency/media/{media_id}/download-url",
    response_model=StoredMediaDownloadUrlResponse,
    tags=["media"],
)
async def get_agency_media_download_url(
    media_id: str = Path(...),
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Issue short-lived URL for agency-visible scan image."""
    media = media_store.get(media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    await get_agency_visible_media(media_id=media_id, agency_user_id=agency_user_id)
    if not media.object_key:
        raise HTTPException(status_code=404, detail="Media object not stored")
    expires_seconds = 900
    url = media_storage_client.presigned_get_url(
        object_key=media.object_key, expires_seconds=expires_seconds
    )
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
async def create_agency_follow_up(
    request: FollowUpCreateRequest,
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Create agency follow-up status; internal notes stay agency-only."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    farmer = farmer_account_store.get_by_id(request.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    record = FarmerRecord(
        farmer.id,
        farmer.name,
        farmer.jurisdiction_id,
        ConsentTier(farmer.consent_state.value),
    )
    if not can_agency_access_farmer(agency, record, DEMO_JURISDICTIONS):
        raise HTTPException(status_code=403, detail="Farmer not visible to agency")
    if (
        request.cattle_id is not None
        and cattle_profile_store.get_owned(
            farmer_id=request.farmer_id, cattle_id=request.cattle_id
        )
        is None
    ):
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
        metadata_json={
            "farmer_id": request.farmer_id,
            "cattle_id": request.cattle_id,
            "status": request.status,
        },
    )
    return _serialize_agency_follow_up(follow_up)


@router.put(
    "/agency/follow-ups/{follow_up_id}",
    response_model=AgencyFollowUpResponse,
    tags=["agency"],
)
async def update_agency_follow_up(
    follow_up_id: str,
    request: FollowUpUpdateRequest,
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Edit an existing follow-up the agency can access."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    existing = follow_up_store.get_by_id(follow_up_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    farmer = farmer_account_store.get_by_id(existing.farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    record = FarmerRecord(
        farmer.id,
        farmer.name,
        farmer.jurisdiction_id,
        ConsentTier(farmer.consent_state.value),
    )
    if not can_agency_access_farmer(agency, record, DEMO_JURISDICTIONS):
        raise HTTPException(status_code=403, detail="Follow-up not visible to agency")
    follow_up = follow_up_store.update(
        follow_up_id,
        status=request.status,
        public_message=request.public_message,
        internal_notes=request.internal_notes,
    )
    audit_log_store.record(
        actor_type="agency",
        actor_id=agency_user_id,
        action="follow_up.updated",
        resource_type="follow_up",
        resource_id=follow_up_id,
        metadata_json={"status": request.status},
    )
    if request.status is not None and request.status != existing.status:
        notification_store.create(
            account_id=existing.farmer_id,
            account_type="farmer",
            title="Follow-up status updated",
            body=f"Your follow-up status is now {request.status.replace('_', ' ')}.",
        )
    return _serialize_agency_follow_up(follow_up)


@router.get(
    "/agency/follow-ups", response_model=list[AgencyFollowUpResponse], tags=["agency"]
)
async def list_agency_follow_up_status(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """List agency follow-up status rows visible to the agency jurisdiction."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    farmers_by_id = farmer_account_store.all_by_id()
    visible = []
    for item in follow_up_store.list_all():
        farmer = farmers_by_id.get(item.farmer_id)
        if farmer is None:
            continue
        record = FarmerRecord(
            farmer.id,
            farmer.name,
            farmer.jurisdiction_id,
            ConsentTier(farmer.consent_state.value),
        )
        if can_agency_access_farmer(agency, record, DEMO_JURISDICTIONS):
            visible.append(item)
    status = _filter_value(status)
    if status:
        visible = [item for item in visible if _same_filter_value(item.status, status)]
    visible = [
        item
        for item in visible
        if _matches_query(
            [
                item.id,
                item.farmer_id,
                item.cattle_id,
                item.status,
                item.public_message,
                item.internal_notes,
            ],
            search,
        )
    ]
    return [_serialize_agency_follow_up(item) for item in visible]


@router.get(
    "/farmers/{farmer_id}/follow-ups", response_model=FarmerFollowUpListResponse
)
async def list_farmer_follow_up_status(farmer_id: str = Path(...)):
    """List farmer-visible follow-up statuses without agency internal notes."""
    if farmer_account_store.get_by_id(farmer_id) is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return {
        "follow_ups": [
            _serialize_farmer_follow_up(item)
            for item in follow_up_store.list_by_farmer(farmer_id)
        ]
    }


@router.get("/agency/registry", response_model=AgencyRegistryResponse)
async def get_agency_dashboard_registry(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    jurisdiction_id: str | None = Query(default=None),
    farmer_id: str | None = Query(default=None),
    cattle_search: str | None = Query(default=None),
    cattle_status: str | None = Query(default=None),
):
    """Return dashboard registry farmers and cattle scoped to agency authorization."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_demo_farmers = filter_visible_farmers(
        agency=agency, farmers=DEMO_FARMERS, jurisdictions=DEMO_JURISDICTIONS
    )
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    farmer_id = _filter_value(farmer_id)
    if farmer_id:
        visible_demo_farmers = [
            farmer
            for farmer in visible_demo_farmers
            if _same_filter_value(farmer.id, farmer_id)
        ]
        visible_cattle = [
            profile
            for profile in visible_cattle
            if _same_filter_value(profile.farmer_id, farmer_id)
        ]
    jurisdiction_id = _filter_value(jurisdiction_id)
    if jurisdiction_id:
        visible_demo_farmers = [
            farmer
            for farmer in visible_demo_farmers
            if _same_filter_value(farmer.jurisdiction_id, jurisdiction_id)
        ]
        visible_cattle = [
            profile
            for profile in visible_cattle
            if _same_filter_value(profile.jurisdiction_id, jurisdiction_id)
        ]
    if search:
        scoped_farmers = visible_demo_farmers
        visible_demo_farmers = [
            farmer
            for farmer in scoped_farmers
            if _matches_query(
                [farmer.id, farmer.name, farmer.address, farmer.jurisdiction_id], search
            )
        ]
        visible_farmer_ids = {farmer.id for farmer in visible_demo_farmers}
        matching_cattle_farmer_ids = {
            profile.farmer_id
            for profile in visible_cattle
            if _matches_query(
                [
                    profile.id,
                    profile.farmer_id,
                    profile.tag,
                    profile.sex,
                    profile.breed,
                    profile.status,
                    profile.jurisdiction_id,
                ],
                search,
            )
        }
        visible_farmer_ids |= matching_cattle_farmer_ids
        visible_demo_farmers = [
            farmer for farmer in scoped_farmers if farmer.id in visible_farmer_ids
        ]
        visible_cattle = [
            profile for profile in visible_cattle if profile.farmer_id in visible_farmer_ids
        ]
    cattle_status = _filter_value(cattle_status)
    if cattle_status:
        visible_cattle = [
            profile
            for profile in visible_cattle
            if _same_filter_value(profile.status, cattle_status)
        ]
    visible_cattle = [
        profile
        for profile in visible_cattle
        if _matches_query(
            [
                profile.id,
                profile.farmer_id,
                profile.tag,
                profile.sex,
                profile.breed,
                profile.status,
                profile.jurisdiction_id,
            ],
            cattle_search,
        )
    ]
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


@router.get(
    "/agency/detection-monitoring",
    response_model=AgencyDetectionMonitoringResponse,
    tags=["agency"],
)
async def get_agency_detection_monitoring(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    disease_class: str | None = Query(default=None),
    farmer_id: str | None = Query(default=None),
    cattle_id: str | None = Query(default=None),
):
    """Return agency-scoped fused detection monitoring rows with safe risk language."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    visible_cattle = cattle_profile_store.list_visible_to_agency(
        agency=agency,
        farmers_by_id=farmer_account_store.all_by_id(),
        jurisdictions=DEMO_JURISDICTIONS,
    )
    results = fusion_result_store.list_by_cattle_ids(
        {profile.id for profile in visible_cattle}
    )
    farmer_id = _filter_value(farmer_id)
    if farmer_id:
        results = [
            result for result in results if _same_filter_value(result.farmer_id, farmer_id)
        ]
    cattle_id = _filter_value(cattle_id)
    if cattle_id:
        results = [
            result for result in results if _same_filter_value(result.cattle_id, cattle_id)
        ]
    disease_class = _filter_value(disease_class)
    if disease_class:
        results = [
            result
            for result in results
            if _same_filter_value(result.disease_class, disease_class)
        ]
    results = [
        result
        for result in results
        if _matches_query(
            [
                result.id,
                result.farmer_id,
                result.cattle_id,
                result.disease_class,
                result.confidence_level,
                result.reliability,
                result.conflict_status,
                result.handling_advice_key,
            ],
            search,
        )
    ]
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
async def get_agency_risk_signal_summary(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
):
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
    risk_level = _filter_value(risk_level)
    if risk_level:
        signals = [
            signal
            for signal in signals
            if _same_filter_value(signal.risk_level, risk_level)
        ]
    signals = [
        signal
        for signal in signals
        if _matches_query(
            [
                signal.id,
                signal.jurisdiction_id,
                signal.disease_class,
                signal.risk_level,
                signal.priority,
                signal.signal_count,
            ],
            search,
        )
    ]
    return {
        "agency_user_id": agency_user_id,
        "rule": {
            "name": "three_or_more_non_healthy_signals_7d",
            "threshold_count": HYBRID_ALERT_THRESHOLD,
            "window_days": CLUSTER_WINDOW_DAYS,
            "included_reliability": sorted(RISK_SIGNAL_RELIABILITY),
            "language": "possible increased risk, not confirmed outbreak or diagnosis",
        },
        "signals": [signal.__dict__ for signal in signals],
        "safe_language": {
            "title": "Disease risk signal summary",
            "description": "Possible increased risk signals for follow-up prioritization. Not confirmed outbreak. Not veterinary diagnosis.",
        },
    }


@router.get(
    "/farmers/{farmer_id}/area-advisory",
    response_model=FarmerAreaAdvisoryResponse,
    tags=["farmer"],
)
async def get_farmer_area_advisory(farmer_id: str = Path(...)):
    """Return farmer-safe district advisory when cluster risk signal exists in farmer jurisdiction."""
    farmer = farmer_account_store.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=404, detail="Farmer not found")
    signals = [
        signal
        for signal in cluster_risk_signal_store.list_all()
        if signal.jurisdiction_id == farmer.jurisdiction_id
        and signal.risk_level == "possible_increased_risk"
    ]
    return {
        "farmer_id": farmer.id,
        "jurisdiction_id": farmer.jurisdiction_id,
        "advisory_active": bool(signals),
        "title": "Area disease-risk advisory" if signals else "No area advisory",
        "message": "Increased disease-risk reports in your district. Monitor cattle, improve biosecurity, and contact animal health officers if symptoms appear."
        if signals
        else "No increased district-level disease-risk reports are active for your area.",
        "signals": [signal.__dict__ for signal in signals],
        "safe_language": {
            "scope": "district-level advisory only",
            "privacy": "does not expose other farmers, cattle identities, or exact scan details",
            "disclaimer": "not confirmed diagnosis or outbreak declaration",
        },
    }


# --- User Management (admin-only) ---


class AgencyUserCreateRequest(BaseModel):
    id: str
    role: str
    jurisdiction_id: str


class AgencyUserUpdateRequest(BaseModel):
    role: str
    jurisdiction_id: str | None = None


@router.get("/agency/users", tags=["agency"])
async def list_agency_users(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
    search: str | None = Query(default=None),
    role: str | None = Query(default=None),
):
    """List all agency users. Admin only."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None or agency.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    users = _agency_user_store.list_all()
    role = _filter_value(role)
    if role:
        users = [user for user in users if _same_filter_value(user.role.value, role)]
    users = [
        user
        for user in users
        if _matches_query([user.id, user.role.value, user.jurisdiction_id], search)
    ]
    return {
        "users": [
            {"id": u.id, "role": u.role.value, "jurisdiction_id": u.jurisdiction_id}
            for u in users
        ]
    }


@router.post("/agency/users", tags=["agency"], status_code=201)
async def create_agency_user(
    request: AgencyUserCreateRequest,
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Create a new agency user. Admin only."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None or agency.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    valid_roles = [r.value for r in AgencyRole]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=422, detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    _agency_user_store.ensure_exists(request.id, request.role, request.jurisdiction_id)
    refresh_agency_users()
    return {
        "id": request.id,
        "role": request.role,
        "jurisdiction_id": request.jurisdiction_id,
    }


@router.put("/agency/users/{user_id}", tags=["agency"])
async def update_agency_user(
    user_id: str,
    request: AgencyUserUpdateRequest,
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """Update an agency user's role/jurisdiction. Admin only."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None or agency.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    valid_roles = [r.value for r in AgencyRole]
    if request.role not in valid_roles:
        raise HTTPException(
            status_code=422, detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    updated = _agency_user_store.update_role(
        user_id, request.role, request.jurisdiction_id
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    refresh_agency_users()
    return {
        "id": updated.id,
        "role": updated.role.value,
        "jurisdiction_id": updated.jurisdiction_id,
    }


@router.delete("/agency/users/{user_id}", tags=["agency"])
async def delete_agency_user(
    user_id: str, agency_user_id: str = Header(..., alias="X-Agency-User-Id")
):
    """Delete an agency user. Admin only."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None or agency.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    deleted = _agency_user_store.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    refresh_agency_users()
    return {"deleted": True}


@router.get("/agency/jurisdictions", tags=["agency"])
async def list_jurisdictions(
    agency_user_id: str = Header(..., alias="X-Agency-User-Id"),
):
    """List all available jurisdictions."""
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")
    jurisdictions = _jurisdiction_store.all_by_id()
    return {
        "jurisdictions": [
            {
                "id": j.id,
                "name": j.name,
                "level": j.level,
                "parent_id": j.parent_id,
                "latitude": j.latitude,
                "longitude": j.longitude,
            }
            for j in jurisdictions.values()
        ]
    }


@router.get(
    "/notifications", response_model=NotificationListResponse, tags=["notifications"]
)
async def list_notifications(
    authorization: str = Header(..., alias="Authorization"),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
):
    """List notifications for the authenticated account."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    account_id = str(claims["sub"])
    account_type = str(claims["account_type"])
    notifications = notification_store.list_for_account(
        account_id, account_type, unread_only=unread_only, limit=limit
    )
    return {
        "notifications": [_serialize_notification(n) for n in notifications],
        "unread_count": notification_store.unread_count(account_id, account_type),
    }


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
    tags=["notifications"],
)
async def mark_notification_read(
    notification_id: str,
    authorization: str = Header(..., alias="Authorization"),
):
    """Mark a single notification as read."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    account_id = str(claims["sub"])
    account_type = str(claims["account_type"])
    notification = notification_store.mark_read(
        notification_id, account_id, account_type
    )
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return _serialize_notification(notification)


@router.patch(
    "/notifications/read-all",
    response_model=NotificationMarkReadResponse,
    tags=["notifications"],
)
async def mark_all_notifications_read(
    authorization: str = Header(..., alias="Authorization"),
):
    """Mark all notifications as read for the authenticated account."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        claims = read_token(authorization.removeprefix("Bearer "))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    account_id = str(claims["sub"])
    account_type = str(claims["account_type"])
    count = notification_store.mark_all_read(account_id, account_type)
    return {"marked_count": count}
