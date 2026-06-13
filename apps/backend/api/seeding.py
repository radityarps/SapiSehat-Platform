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

from utils.logger import get_logger

logger = get_logger(__name__)


def _image(top_class: str, confidence: float = 0.82) -> dict:
    return {
        "source": "image",
        "model_version": "image-seed",
        "inference_mode": "online",
        "disease_scores": {
            "healthy": 0.1,
            "FMD": confidence if top_class == "FMD" else 0.1,
            "LSD": confidence if top_class == "LSD" else 0.1,
        },
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
        "disease_scores": {
            "healthy": 0.1,
            "FMD": confidence if top_class == "FMD" else 0.1,
            "LSD": confidence if top_class == "LSD" else 0.1,
        },
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
    from fastapi.testclient import TestClient
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
        logger.warning("Sample seed skipped: admin login failed (%s)", login.status_code)
        return
    auth = login.json()
    headers = {
        "Authorization": f"Bearer {auth['access_token']}",
        "X-Agency-User-Id": auth["account"]["id"],
    }
    existing = client.get("/api/agency/detection-monitoring", headers=headers)
    if existing.status_code == 200 and len(existing.json().get("detections", [])) > 0:
        logger.info("Sample seed skipped: detections already present.")
        return

    logger.info("Seeding development sample data...")

    # (name, jurisdiction, image_top, nlp_top) — 3+ non-healthy in tembalang
    # and banyumanik to cross the cluster-risk threshold.
    plan = [
        ("Pak Budi", "tembalang", "FMD", "FMD"),
        ("Bu Wati", "tembalang", "FMD", "FMD"),
        ("Pak Joko", "tembalang", "FMD", "LSD"),
        ("Pak Slamet", "banyumanik", "LSD", "LSD"),
        ("Bu Rina", "banyumanik", "LSD", "LSD"),
        ("Pak Agus", "banyumanik", "LSD", "LSD"),
        ("Bu Sri", "semarang-city", "healthy", "healthy"),
    ]

    created = []
    for idx, (name, jur, image_top, nlp_top) in enumerate(plan):
        farmer = client.post(
            "/api/farmers/accounts",
            json={
                "phone_number": f"08120000{idx:03d}",
                "name": name,
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
