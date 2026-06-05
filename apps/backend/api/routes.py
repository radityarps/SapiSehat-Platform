"""FastAPI routes - HTTP layer (replaceable by Go)."""

import asyncio
import io
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Header, Path
from fastapi.responses import JSONResponse
from PIL import Image
from inference_server import get_inference_service, is_model_ready, get_model_status
from api.schemas import (
    PredictResponse,
    HealthResponse,
    AgencyFarmersResponse,
    FarmerAccountRequest,
    FarmerAccountResponse,
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
)
from config import settings
from utils.logger import get_logger
from api.farmer_accounts import farmer_account_store
from api.cattle_profiles import CattleEventType, CattleSex, CattleStatus, cattle_profile_store
from api.detection_events import detection_event_store
from api.authorization import DEMO_AGENCY_USERS, DEMO_FARMERS, DEMO_JURISDICTIONS, filter_visible_farmers

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["prediction"])


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

@router.post("/predict", response_model=PredictResponse)
async def predict(
    image: UploadFile = File(...),
    two_stage: bool = Query(False, description="Developer-only two-stage prototype path"),
    debug_regions: bool = Query(False, description="Include developer-only symptom-region debug data"),
):
    """Predict cattle disease from image."""
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


@router.post("/farmers/{farmer_id}/cattle", response_model=CattleProfileResponse)
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
    return {"cattle": [_serialize_cattle(profile) for profile in cattle_profile_store.list_by_farmer(farmer_id)]}


@router.get("/farmers/{farmer_id}/cattle/{cattle_id}", response_model=CattleProfileDetailResponse)
async def select_farmer_cattle_for_detection(farmer_id: str = Path(...), cattle_id: str = Path(...)):
    """Select one farmer-owned cattle profile before detection starts."""
    profile = cattle_profile_store.get_owned(farmer_id=farmer_id, cattle_id=cattle_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Cattle not found for farmer")
    return _serialize_cattle_detail(profile)


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
