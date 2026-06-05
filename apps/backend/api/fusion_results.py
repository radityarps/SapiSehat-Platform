"""Backend-primary evidence fusion tracer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional
from uuid import uuid4

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
    """In-memory fusion result store for tracer tests."""
    results_by_id: Dict[str, FusionResult] = field(default_factory=dict)

    def create(
        self,
        *,
        farmer_id: str,
        cattle_id: Optional[str],
        image_evidence: Optional[ImageEvidenceRequest],
        nlp_evidence: Optional[NlpEvidenceRequest],
    ) -> FusionResult:
        result = fuse_evidence(
            farmer_id=farmer_id,
            cattle_id=cattle_id,
            image_evidence=image_evidence,
            nlp_evidence=nlp_evidence,
        )
        self.results_by_id[result.id] = result
        return result

    def list_all(self) -> list[FusionResult]:
        return list(self.results_by_id.values())


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


def fuse_evidence(
    *,
    farmer_id: str,
    cattle_id: Optional[str],
    image_evidence: Optional[ImageEvidenceRequest],
    nlp_evidence: Optional[NlpEvidenceRequest],
) -> FusionResult:
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
    elif image_evidence.top_class == nlp_evidence.top_class:
        disease_class = image_evidence.top_class
        confidence = round((image_evidence.confidence + nlp_evidence.confidence) / 2, 4)
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
    if any(getattr(evidence, "inference_mode", None).value == "offline" for evidence in candidates):
        mode = "offline"

    result = FusionResult(
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
        evidence_breakdown={
            "image": _evidence_dump(image_evidence),
            "nlp": _evidence_dump(nlp_evidence),
        },
        conflict_status=conflict_status,
        model_versions={
            "image": image_evidence.model_version if image_evidence is not None else "missing",
            "nlp": nlp_evidence.model_version if nlp_evidence is not None else "missing",
        },
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return result


fusion_result_store = FusionResultStore()
