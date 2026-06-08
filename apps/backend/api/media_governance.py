"""Stored media governance persistence."""

from dataclasses import dataclass
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

class MediaStore:
    def __init__(self) -> None:
        create_all_tables()

    def create(self, *, farmer_id: str, cattle_id: Optional[str], detection_id: Optional[str], checksum: str, consent_scope: str, storage_reference: str) -> StoredMedia:
        with SessionLocal() as session:
            next_id = session.query(StoredMediaModel).count() + 1
            media = StoredMedia(
                id=f"media-{next_id}",
                farmer_id=farmer_id,
                cattle_id=cattle_id,
                detection_id=detection_id,
                checksum=checksum,
                consent_scope=consent_scope,
                storage_reference=storage_reference,
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
    )

media_store = MediaStore()
