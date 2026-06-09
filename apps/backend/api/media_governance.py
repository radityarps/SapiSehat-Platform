"""Stored media governance persistence."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from api.database import SessionLocal, create_all_tables
from api.db_models import StoredMediaModel

@dataclass(frozen=True)
class StoredMedia:
    id: str
    farmer_id: str
    cattle_id: Optional[str]
    detection_id: Optional[str]
    checksum: str
    consent_scope: str
    storage_reference: str
    storage_backend: str
    object_key: str
    content_type: str
    byte_size: int
    retention_policy: str
    created_at: str

class MediaStore:
    def __init__(self) -> None:
        create_all_tables()

    def create(self, *, farmer_id: str, cattle_id: Optional[str], detection_id: Optional[str], checksum: str, consent_scope: str, storage_reference: str, content_type: str, byte_size: int, retention_policy: str, storage_backend: str = "metadata-only", object_key: str = "", media_id: str | None = None) -> StoredMedia:
        with SessionLocal() as session:
            next_id = session.query(StoredMediaModel).count() + 1
            media = StoredMedia(
                id=media_id or f"media-{next_id}",
                farmer_id=farmer_id,
                cattle_id=cattle_id,
                detection_id=detection_id,
                checksum=checksum,
                consent_scope=consent_scope,
                storage_reference=storage_reference,
                storage_backend=storage_backend,
                object_key=object_key,
                content_type=content_type,
                byte_size=byte_size,
                retention_policy=retention_policy,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(StoredMediaModel(**media.__dict__))
            session.commit()
            return media

    def get(self, media_id: str) -> StoredMedia | None:
        with SessionLocal() as session:
            row = session.get(StoredMediaModel, media_id)
            return _media_from_row(row) if row is not None else None

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(StoredMediaModel).delete()
            session.commit()


def _media_from_row(row: StoredMediaModel) -> StoredMedia:
    return StoredMedia(
        id=row.id,
        farmer_id=row.farmer_id,
        cattle_id=row.cattle_id,
        detection_id=row.detection_id,
        checksum=row.checksum,
        consent_scope=row.consent_scope,
        storage_reference=row.storage_reference,
        storage_backend=row.storage_backend,
        object_key=row.object_key,
        content_type=row.content_type,
        byte_size=row.byte_size,
        retention_policy=row.retention_policy,
        created_at=row.created_at,
    )

media_store = MediaStore()
