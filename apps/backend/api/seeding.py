"""Development sample data seeding.

Runs at startup in development environment only.
Creates realistic cattle profiles with complete livestock fields,
detection fusion results, follow-ups, and notifications.
Idempotent — skips if data already exists.
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


# Seed plan: (name, jurisdiction, address, image_top, nlp_top, cattle_profiles)
# cattle_profiles: list of dicts with complete livestock fields
SEED_PLAN = [
    (
        "Pak Budi",
        "tembalang",
        "Jl. Ngesrep Timur V No. 12, Tembalang",
        "FMD",
        "FMD",
        [
            {
                "tag": "TEM-001",
                "sex": "female",
                "breed": "Sapi Bali",
                "age_months": 36,
                "name": "Mawar",
                "color": "coklat kemerahan",
                "weight_kg": 280.0,
                "reproductive_status": "pregnant",
                "is_pregnant": True,
                "last_calving_date": "2025-08-15",
                "last_vaccination_date": "2026-01-10",
                "last_deworming_date": "2025-12-01",
                "health_notes": "Kondisi baik, sedang bunting 6 bulan.",
                "purchase_date": "2023-03-01",
                "purchase_price_idr": 15000000,
                "notes": "Sapi unggulan kandang.",
            },
            {
                "tag": "TEM-002",
                "sex": "male",
                "breed": "Sapi Limousin",
                "age_months": 18,
                "name": "Jago",
                "color": "hitam",
                "weight_kg": 320.0,
                "reproductive_status": "open",
                "is_pregnant": False,
                "last_vaccination_date": "2026-02-05",
                "purchase_date": "2024-09-15",
                "purchase_price_idr": 18000000,
            },
        ],
    ),
    (
        "Bu Wati",
        "tembalang",
        "Jl. Tirto Agung No. 5, Tembalang",
        "FMD",
        "FMD",
        [
            {
                "tag": "TEM-003",
                "sex": "female",
                "breed": "Sapi Bali",
                "age_months": 48,
                "color": "coklat",
                "weight_kg": 260.0,
                "reproductive_status": "lactating",
                "last_calving_date": "2026-03-20",
                "last_vaccination_date": "2026-01-15",
                "health_notes": "Baru melahirkan, sedang menyusui.",
            }
        ],
    ),
    (
        "Pak Joko",
        "tembalang",
        "Jl. Bukit Agung Raya No. 8, Tembalang",
        "FMD",
        "LSD",
        [
            {
                "tag": "TEM-004",
                "sex": "female",
                "breed": "Sapi PO",
                "age_months": 24,
                "color": "putih",
                "weight_kg": 210.0,
                "last_vaccination_date": "2025-11-20",
                "last_deworming_date": "2026-01-05",
            }
        ],
    ),
    (
        "Pak Slamet",
        "banyumanik",
        "Jl. Banyumanik Raya No. 22, Banyumanik",
        "LSD",
        "LSD",
        [
            {
                "tag": "BAN-001",
                "sex": "female",
                "breed": "Sapi Brahman",
                "age_months": 30,
                "name": "Melati",
                "color": "abu-abu",
                "weight_kg": 350.0,
                "reproductive_status": "pregnant",
                "is_pregnant": True,
                "last_vaccination_date": "2026-02-10",
                "purchase_date": "2023-07-01",
                "purchase_price_idr": 22000000,
            },
            {
                "tag": "BAN-002",
                "sex": "male",
                "breed": "Sapi Brahman",
                "color": "abu-abu muda",
                "weight_kg": 180.0,
                "birth_year_estimate": 2025,
                "age_months": None,
                "last_deworming_date": "2026-01-20",
                "notes": "Pedet dari Melati.",
            },
        ],
    ),
    (
        "Bu Rina",
        "banyumanik",
        "Jl. Setiabudi No. 44, Banyumanik",
        "LSD",
        "LSD",
        [
            {
                "tag": "BAN-003",
                "sex": "female",
                "breed": "Sapi Simmental",
                "age_months": 42,
                "color": "coklat putih",
                "weight_kg": 420.0,
                "reproductive_status": "dry",
                "last_vaccination_date": "2025-12-15",
                "purchase_price_idr": 25000000,
            }
        ],
    ),
    (
        "Pak Agus",
        "banyumanik",
        "Jl. Pudak Payung No. 3, Banyumanik",
        "LSD",
        "LSD",
        [
            {
                "tag": "BAN-004",
                "sex": "male",
                "breed": "Sapi Madura",
                "age_months": 60,
                "color": "merah bata",
                "weight_kg": 290.0,
                "health_notes": "Bekas luka di kaki kiri, sudah sembuh.",
                "purchase_date": "2021-04-10",
                "purchase_price_idr": 12000000,
            }
        ],
    ),
    (
        "Bu Sri",
        "semarang-city",
        "Jl. Pandanaran No. 1, Semarang",
        "healthy",
        "healthy",
        [
            {
                "tag": "SMG-001",
                "sex": "female",
                "breed": "Sapi Frisien Holstein",
                "age_months": 36,
                "name": "Susu",
                "color": "hitam putih",
                "weight_kg": 480.0,
                "reproductive_status": "lactating",
                "last_calving_date": "2026-02-01",
                "last_vaccination_date": "2026-01-20",
                "last_deworming_date": "2025-11-15",
                "purchase_date": "2023-01-15",
                "purchase_price_idr": 30000000,
                "notes": "Sapi perah, produksi susu 15L/hari.",
            }
        ],
    ),
]


def seed_development_sample_data() -> None:
    """Seed sample cattle/detections/follow-ups in development only."""
    from config import settings

    if settings.fastapi_env not in {"development", "test"}:
        return

    from api.cattle_profiles import (
        CattleProfile,
        CattleSex,
        CattleStatus,
        cattle_profile_store,
    )
    from api.farmer_accounts import FarmerConsentState, farmer_account_store
    from api.follow_ups import follow_up_store
    from api.fusion_results import fusion_result_store
    from api.risk_signals import cluster_risk_signal_store, summarize_risk_signals
    from api.schemas import ImageEvidenceRequest, NlpEvidenceRequest
    from api.surface_auth import seed_default_agency_accounts, seed_default_farmer_accounts

    seed_default_agency_accounts()
    seed_default_farmer_accounts()

    if fusion_result_store.list_all():
        logger.info("Sample seed skipped: fusion results already present.")
        return

    logger.info("Seeding development sample data...")

    created: list[tuple[str, str]] = []
    cattle_by_id: dict[str, CattleProfile] = {}
    for idx, (name, jur, address, image_top, nlp_top, cattle_list) in enumerate(SEED_PLAN):
        farmer, _ = farmer_account_store.upsert_by_phone(
            phone_number=f"08120000{idx:03d}",
            name=name,
            address=address,
            jurisdiction_id=jur,
            consent_state=FarmerConsentState.AGENCY_MONITORING,
        )

        first_cattle_id: str | None = None
        for cattle_data in cattle_list:
            if (
                cattle_data.get("age_months") is None
                and cattle_data.get("birth_year_estimate") is None
            ):
                cattle_data = {**cattle_data, "age_months": 24}
            cattle = cattle_profile_store.create(
                farmer=farmer,
                tag=cattle_data["tag"],
                sex=CattleSex(cattle_data["sex"]),
                breed=cattle_data.get("breed", "unknown"),
                age_months=cattle_data.get("age_months"),
                birth_year_estimate=cattle_data.get("birth_year_estimate"),
                status=CattleStatus.ACTIVE,
                jurisdiction_id=jur,
                name=cattle_data.get("name"),
                color=cattle_data.get("color"),
                weight_kg=cattle_data.get("weight_kg"),
                reproductive_status=cattle_data.get("reproductive_status"),
                is_pregnant=cattle_data.get("is_pregnant"),
                last_calving_date=cattle_data.get("last_calving_date"),
                last_vaccination_date=cattle_data.get("last_vaccination_date"),
                last_deworming_date=cattle_data.get("last_deworming_date"),
                health_notes=cattle_data.get("health_notes"),
                purchase_date=cattle_data.get("purchase_date"),
                purchase_price_idr=cattle_data.get("purchase_price_idr"),
                notes=cattle_data.get("notes"),
            )
            cattle_by_id[cattle.id] = cattle
            first_cattle_id = first_cattle_id or cattle.id

        if first_cattle_id is None:
            continue
        fusion_result_store.create(
            farmer_id=farmer.id,
            cattle_id=first_cattle_id,
            image_evidence=ImageEvidenceRequest(**_image(image_top)),
            nlp_evidence=NlpEvidenceRequest(**_nlp(nlp_top)),
        )
        created.append((farmer.id, first_cattle_id))

    statuses = ["needs_follow_up", "in_progress", "completed"]
    for i, (farmer_id, cattle_id) in enumerate(created[:3]):
        follow_up_store.create(
            farmer_id=farmer_id,
            cattle_id=cattle_id,
            status=statuses[i % len(statuses)],
            public_message="Mohon pantau kondisi ternak dan jaga kebersihan kandang.",
            internal_notes="Sample follow-up for development environment.",
        )

    cattle_jurisdictions = {
        cattle_id: cattle.jurisdiction_id for cattle_id, cattle in cattle_by_id.items()
    }
    cluster_risk_signal_store.replace_all(
        summarize_risk_signals(fusion_result_store.list_all(), cattle_jurisdictions)
    )
    logger.info("Development sample data seeded (%d farmers).", len(created))
