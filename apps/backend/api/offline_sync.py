"""Offline detection sync tracer."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from api.database import SessionLocal, create_all_tables
from api.db_models import FusionResultModel, OfflineSyncedDetectionModel
from api.fusion_results import FusionResult, _fusion_from_row, fuse_evidence
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
    def __post_init__(self) -> None:
        create_all_tables()

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
        with SessionLocal() as session:
            existing = session.get(OfflineSyncedDetectionModel, local_detection_id)
            if existing is not None:
                fusion_row = session.get(FusionResultModel, existing.fusion_result_id)
                if fusion_row is None:
                    raise ValueError("offline sync fusion result missing")
                return SyncedOfflineDetection(
                    local_detection_id=existing.local_detection_id,
                    sync_status=existing.sync_status,
                    fusion_result=_fusion_from_row(fusion_row),
                    local_created_at=existing.local_created_at,
                    synced_at=existing.synced_at,
                )

            result = fuse_evidence(
                farmer_id=farmer_id,
                cattle_id=cattle_id,
                image_evidence=image_evidence,
                nlp_evidence=nlp_evidence,
            )
            result = FusionResult(**{**result.__dict__, "inference_mode": "synced_offline"})
            synced_at = datetime.now(timezone.utc).isoformat()
            session.add(FusionResultModel(**result.__dict__))
            session.add(
                OfflineSyncedDetectionModel(
                    local_detection_id=local_detection_id,
                    sync_status="synced",
                    fusion_result_id=result.id,
                    local_created_at=local_created_at,
                    synced_at=synced_at,
                )
            )
            session.commit()
            return SyncedOfflineDetection(
                local_detection_id=local_detection_id,
                sync_status="synced",
                fusion_result=result,
                local_created_at=local_created_at,
                synced_at=synced_at,
            )

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(OfflineSyncedDetectionModel).delete()
            session.commit()

offline_detection_sync_store = OfflineDetectionSyncStore()
