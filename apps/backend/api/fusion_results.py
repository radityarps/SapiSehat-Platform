"""Backend-primary evidence fusion persistence."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

from api.database import SessionLocal, create_all_tables
from api.db_models import FusionResultModel
from api.schemas import ImageEvidenceRequest, NlpEvidenceRequest

@dataclass(frozen=True)
class FusionResult:
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

@dataclass
class FusionResultStore:
    def __post_init__(self) -> None:
        create_all_tables()

    def create(self, *, farmer_id: str, cattle_id: Optional[str], image_evidence: Optional[ImageEvidenceRequest], nlp_evidence: Optional[NlpEvidenceRequest]) -> FusionResult:
        result = fuse_evidence(farmer_id=farmer_id, cattle_id=cattle_id, image_evidence=image_evidence, nlp_evidence=nlp_evidence)
        with SessionLocal() as session:
            session.add(FusionResultModel(**result.__dict__))
            session.commit()
        return result

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(FusionResultModel).delete()
            session.commit()

    def list_all(self) -> list[FusionResult]:
        with SessionLocal() as session:
            rows = session.query(FusionResultModel).order_by(FusionResultModel.created_at).all()
            return [_fusion_from_row(row) for row in rows]

    def list_by_cattle_ids(self, cattle_ids: set[str]) -> list[FusionResult]:
        if not cattle_ids:
            return []
        with SessionLocal() as session:
            rows = (
                session.query(FusionResultModel)
                .filter(FusionResultModel.cattle_id.in_(cattle_ids))
                .order_by(FusionResultModel.created_at)
                .all()
            )
            return [_fusion_from_row(row) for row in rows]


def confidence_level(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


def handling_advice_key(disease_class: str, reliability: str) -> str:
    if reliability in {"needs_review", "insufficient_evidence", "low_reliability"}:
        return "advice.contact_vet_or_extension_officer"
    if disease_class == "healthy":
        return "advice.monitor_routine"
    return "advice.isolate_and_contact_vet"


def _evidence_dump(evidence):
    return evidence.model_dump() if evidence is not None else None


def fuse_evidence(*, farmer_id: str, cattle_id: Optional[str], image_evidence: Optional[ImageEvidenceRequest], nlp_evidence: Optional[NlpEvidenceRequest]) -> FusionResult:
    if image_evidence is None and nlp_evidence is None:
        raise ValueError("image_evidence or nlp_evidence is required")

    usable_image = image_evidence is not None and image_evidence.quality_status.value != "rejected"
    usable_nlp = nlp_evidence is not None
    conflict_status = "none"

    if image_evidence is None:
        conflict_status = "missing_image"
    elif not usable_image:
        conflict_status = "low_quality_image"
    elif nlp_evidence is None:
        conflict_status = "missing_nlp"
    elif image_evidence.top_class != nlp_evidence.top_class:
        conflict_status = "image_nlp_conflict"

    candidates = []
    if usable_image:
        candidates.append(image_evidence)
    if usable_nlp:
        candidates.append(nlp_evidence)

    if not candidates:
        disease_class = "healthy"
        confidence = 0.0
    elif len(candidates) == 1:
        disease_class = candidates[0].top_class
        confidence = candidates[0].confidence
    elif candidates[0].top_class == candidates[1].top_class:
        disease_class = candidates[0].top_class
        confidence = round((candidates[0].confidence + candidates[1].confidence) / 2, 4)
    else:
        stronger = max(candidates, key=lambda evidence: evidence.confidence)
        disease_class = stronger.top_class
        confidence = stronger.confidence

    level = confidence_level(confidence)
    if level == "low":
        reliability = "insufficient_evidence"
    elif conflict_status == "image_nlp_conflict":
        reliability = "needs_review"
    elif conflict_status in {"missing_image", "missing_nlp", "low_quality_image"}:
        reliability = "low_reliability"
    else:
        reliability = "reliable"

    mode = "online"
    if len(candidates) > 1:
        mode = "hybrid"
    if any(evidence.inference_mode.value == "offline" for evidence in candidates):
        mode = "offline"

    return FusionResult(
        id=f"fusion-{uuid4().hex[:12]}",
        fusion_version="fusion-tracer-1.0.0",
        inference_mode=mode,
        farmer_id=farmer_id,
        cattle_id=cattle_id,
        disease_class=disease_class,
        confidence=confidence,
        confidence_level=level,
        reliability=reliability,
        handling_advice_key=handling_advice_key(disease_class, reliability),
        evidence_breakdown={"image": _evidence_dump(image_evidence), "nlp": _evidence_dump(nlp_evidence)},
        conflict_status=conflict_status,
        model_versions={"image": image_evidence.model_version if image_evidence is not None else "missing", "nlp": nlp_evidence.model_version if nlp_evidence is not None else "missing"},
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _fusion_from_row(row: FusionResultModel) -> FusionResult:
    return FusionResult(
        id=row.id,
        fusion_version=row.fusion_version,
        inference_mode=row.inference_mode,
        farmer_id=row.farmer_id,
        cattle_id=row.cattle_id,
        disease_class=row.disease_class,
        confidence=row.confidence,
        confidence_level=row.confidence_level,
        reliability=row.reliability,
        handling_advice_key=row.handling_advice_key,
        evidence_breakdown=row.evidence_breakdown,
        conflict_status=row.conflict_status,
        model_versions=row.model_versions,
        created_at=row.created_at,
    )

fusion_result_store = FusionResultStore()
