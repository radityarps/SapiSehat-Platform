"""Environment-aware data seeding.

Seed tiers (config.resolved_seed_tier):
  - production:  master admin account only.
  - staging:     master admin + district officer + 2 farmer accounts.
  - development: staging accounts + sample cattle, detections, and risk signals.

Account seeding is handled lazily on login by surface_auth.seed_default_*.
This module adds the development-only sample operational data, created
through the real API flow so records are valid and scope-correct.
"""

from __future__ import annotations

from api.notifications import notification_store
from config import ACTIVE_DETECTION_CLASSES
from utils.logger import get_logger

logger = get_logger(__name__)


def _scores(top_class: str, confidence: float) -> dict[str, float]:
    if top_class not in ACTIVE_DETECTION_CLASSES:
        raise ValueError("seed top_class must be FMD or healthy")
    other_class = next(label for label in ACTIVE_DETECTION_CLASSES if label != top_class)
    return {top_class: confidence, other_class: round(1.0 - confidence, 4)}


def _image(top_class: str, confidence: float = 0.82) -> dict:
    return {
        "source": "image",
        "model_version": "image-seed",
        "inference_mode": "online",
        "disease_scores": _scores(top_class, confidence),
        "top_class": top_class,
        "confidence": confidence,
        "quality_status": "accepted",
        "rejection_reasons": [],
    }


def _nlp(top_class: str, confidence: float = 0.78) -> dict:
    return {
        "source": "nlp",
        "model_version": "nlp-seed",
        "inference_mode": "online",
        "questionnaire_answers": {"mouth_lesion": True},
        "notes_present": False,
        "disease_scores": _scores(top_class, confidence),
        "top_class": top_class,
        "confidence": confidence,
        "evidence_terms": ["mouth_lesion"],
    }


def seed_development_sample_data() -> None:
    """Seed sample cattle/detections/risk-signals in development tier only."""
    from config import settings

    if settings.resolved_seed_tier != "development":
        return

    # Local import to avoid circular import at module load.
    from fastapi.testclient import TestClient  # type: ignore[import-not-found]
    from main import app

    client = TestClient(app)

    # Skip if sample data already exists (admin sees all detections).
    login = client.post(
        "/api/auth/agency/login",
        json={
            "email": settings.master_admin_email,
            "password": settings.master_admin_password,
        },
    )
    if login.status_code != 200:
        logger.warning(
            "Sample seed skipped: admin login failed (%s)", login.status_code
        )
        return
    auth = login.json()
    headers = {
        "Authorization": f"Bearer {auth['access_token']}",
        "X-Agency-User-Id": auth["account"]["id"],
    }
    existing = client.get("/api/agency/detection-monitoring", headers=headers)
    has_detections = (
        existing.status_code == 200 and len(existing.json().get("detections", [])) > 0
    )

    # Seed sample notifications for development accounts (idempotent).
    admin_id = auth["account"]["id"]
    _seed_sample_notifications(admin_id)

    if has_detections:
        logger.info("Sample seed skipped: detections already present.")
        return

    logger.info("Seeding development sample data...")

    # (name, jurisdiction, address, image_top, nlp_top)
    plan = [
        (
            "Pak Budi",
            "tembalang",
            "Jl. Ngesrep Timur V No. 12, Tembalang",
            "FMD",
            "FMD",
        ),
        ("Bu Wati", "tembalang", "Jl. Tirto Agung No. 5, Tembalang", "FMD", "FMD"),
        (
            "Pak Joko",
            "tembalang",
            "Jl. Bukit Agung Raya No. 8, Tembalang",
            "FMD",
            "healthy",
        ),
        (
            "Pak Slamet",
            "banyumanik",
            "Jl. Banyumanik Raya No. 22, Banyumanik",
            "healthy",
            "healthy",
        ),
        ("Bu Rina", "banyumanik", "Jl. Setiabudi No. 44, Banyumanik", "healthy", "healthy"),
        ("Pak Agus", "banyumanik", "Jl. Pudak Payung No. 3, Banyumanik", "FMD", "healthy"),
        (
            "Bu Sri",
            "semarang-city",
            "Jl. Pandanaran No. 1, Semarang",
            "healthy",
            "healthy",
        ),
    ]

    created = []
    for idx, (name, jur, address, image_top, nlp_top) in enumerate(plan):
        farmer = client.post(
            "/api/farmers/accounts",
            json={
                "phone_number": f"08120000{idx:03d}",
                "name": name,
                "address": address,
                "jurisdiction_id": jur,
                "consent_state": "agency_monitoring",
            },
        )
        if farmer.status_code != 200:
            logger.warning("seed farmer failed: %s", farmer.text)
            continue
        farmer_id = farmer.json()["id"]
        cattle = client.post(
            f"/api/farmers/{farmer_id}/cattle",
            json={
                "tag": f"{jur[:3].upper()}-{idx:03d}",
                "sex": "female",
                "breed": "sapi bali",
                "age_months": 24,
                "jurisdiction_id": jur,
            },
        )
        if cattle.status_code != 200:
            logger.warning("seed cattle failed: %s", cattle.text)
            continue
        cattle_id = cattle.json()["id"]
        client.post(
            "/api/fusion/results",
            json={
                "farmer_id": farmer_id,
                "cattle_id": cattle_id,
                "image_evidence": _image(image_top),
                "nlp_evidence": _nlp(nlp_top),
            },
        )
        created.append((farmer_id, cattle_id))

    # Seed a few follow-ups via the admin account.
    statuses = ["pending", "in_progress", "completed"]
    for i, (farmer_id, cattle_id) in enumerate(created[:3]):
        client.post(
            "/api/agency/follow-ups",
            headers=headers,
            json={
                "farmer_id": farmer_id,
                "cattle_id": cattle_id,
                "status": statuses[i % len(statuses)],
                "public_message": "Mohon pantau kondisi ternak dan jaga kebersihan kandang.",
                "internal_notes": "Sample follow-up for development environment.",
            },
        )

    logger.info("Development sample data seeded (%d cattle).", len(created))


def _seed_sample_notifications(admin_id: str) -> None:
    """Create sample notifications for development accounts if none exist."""
    from api.farmer_accounts import farmer_account_store

    existing = notification_store.list_for_account(admin_id, "agency", limit=1)
    if existing:
        return
    notification_store.create(
        account_id=admin_id,
        account_type="agency",
        title="New risk signal",
        body="FMD risk signal detected in Tembalang district. Review the risk signal map.",
        link="/agency/risk-signals",
    )
    notification_store.create(
        account_id=admin_id,
        account_type="agency",
        title="Follow-up completed",
        body="Officer marked a follow-up as completed for a Banyumanik farmer.",
        link="/agency/follow-ups",
    )
    for farmer in list(farmer_account_store.all_by_id().values())[:2]:
        notification_store.create(
            account_id=farmer.id,
            account_type="farmer",
            title="Follow-up recorded",
            body="An agency officer recorded a follow-up for your cattle.",
        )
