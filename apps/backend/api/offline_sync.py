"""Offline detection sync tracer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

from api.fusion_results import FusionResult, fuse_evidence
from api.schemas import ImageEvidenceRequest, NlpEvidenceRequest


@dataclass(frozen=True)
class SyncedOfflineDetection:
    local_detection_id: str
    sync_status: str
    fusion_result: FusionResult
    local_created_at: str
    synced_at: str


@dataclass
class OfflineDetectionSyncStore:
    synced_by_local_id: Dict[str, SyncedOfflineDetection] = field(default_factory=dict)

    def sync(
        self,
        *,
        local_detection_id: str,
        farmer_id: str,
        cattle_id: Optional[str],
        local_created_at: str,
        image_evidence: Optional[ImageEvidenceRequest],
        nlp_evidence: Optional[NlpEvidenceRequest],
    ) -> SyncedOfflineDetection:
        existing = self.synced_by_local_id.get(local_detection_id)
        if existing is not None:
            return existing
        result = fuse_evidence(
            farmer_id=farmer_id,
            cattle_id=cattle_id,
            image_evidence=image_evidence,
            nlp_evidence=nlp_evidence,
        )
        result = FusionResult(
            **{**result.__dict__, "inference_mode": "synced_offline"}
        )
        synced = SyncedOfflineDetection(
            local_detection_id=local_detection_id,
            sync_status="synced",
            fusion_result=result,
            local_created_at=local_created_at,
            synced_at=datetime.now(timezone.utc).isoformat(),
        )
        self.synced_by_local_id[local_detection_id] = synced
        return synced


offline_detection_sync_store = OfflineDetectionSyncStore()
