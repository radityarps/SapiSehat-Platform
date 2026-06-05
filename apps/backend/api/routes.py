"""FastAPI routes - HTTP layer (replaceable by Go)."""

import asyncio
import io
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from PIL import Image
from inference_server import get_inference_service, is_model_ready, get_model_status
from api.schemas import PredictResponse, HealthResponse, AgencyFarmersResponse
from config import settings
from utils.logger import get_logger

from api.authorization import (
    DEMO_AGENCY_USERS,
    DEMO_FARMERS,
    DEMO_JURISDICTIONS,
    filter_visible_farmers,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["prediction"])


@router.post("/predict", response_model=PredictResponse)
async def predict(
    image: UploadFile = File(...),
    two_stage: bool = Query(False, description="Developer-only two-stage prototype path"),
    debug_regions: bool = Query(False, description="Include developer-only symptom-region debug data"),
):
    """
    Predict cattle disease from image.

    This is the main inference endpoint.

    Privacy: NO-RETENTION POLICY
    - Image bytes are held in memory only during request processing.
    - No uploaded image is written to disk or persistent storage.
    - No image content is logged.
    - After inference completes, image data is garbage collected.

    - Accepts JPEG, PNG, WebP images
    - Returns prediction with confidence and all class scores
    - Inference logic lives in InferenceService (no FastAPI coupling)

    Args:
        image: Image file to analyze

    Returns:
        Dict with prediction results (serialized by FastAPI)
    """
    # Check model readiness
    if not is_model_ready():
        raise HTTPException(
            status_code=503,
            detail="Model not loaded"
        )

    # Validate content type
    if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
        logger.warning(f"Invalid content type: {image.content_type}")
        raise HTTPException(
            status_code=422,
            detail=f"Invalid image format. Accepted: JPEG, PNG, WebP. Got: {image.content_type}"
        )

    # Read image bytes
    contents = await image.read()
    if not contents:
        raise HTTPException(status_code=422, detail="Empty image file")

    # Load image
    try:
        img_pil = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        logger.warning(f"Failed to open image: {e}")
        raise HTTPException(status_code=422, detail="Invalid or corrupted image file")

    # Run inference with timeout wrapper
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
        result = await asyncio.wait_for(
            threaded,
            timeout=settings.request_timeout,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Request processing exceeded timeout"
        )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Inference failed"))

    return result


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.

    Returns:
        Health status with model readiness and version info.
        HTTP 200 for both "ok" and "degraded" states.
        HTTP 500 only on unexpected internal errors.
    """
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
    """Return farmers visible to agency user after role-jurisdiction-consent filtering.

    This tracer endpoint proves platform data access is not global by default.
    It uses in-memory demo records until the rebuilt Go gateway/PostgreSQL
    implementation replaces this FastAPI prototype.
    """
    agency = DEMO_AGENCY_USERS.get(agency_user_id)
    if agency is None:
        raise HTTPException(status_code=403, detail="Unknown agency user")

    visible_farmers = filter_visible_farmers(
        agency=agency,
        farmers=DEMO_FARMERS,
        jurisdictions=DEMO_JURISDICTIONS,
    )
    return {
        "agency_user_id": agency_user_id,
        "farmers": [farmer.__dict__ for farmer in visible_farmers],
    }
