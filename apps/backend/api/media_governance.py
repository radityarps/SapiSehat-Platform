"""Stored media governance tracer."""

from dataclasses import dataclass
from typing import Optional


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
        self._media_by_id: dict[str, StoredMedia] = {}
        self._next_id = 1

    def create(self, *, farmer_id: str, cattle_id: Optional[str], detection_id: Optional[str], checksum: str, consent_scope: str, storage_reference: str) -> StoredMedia:
        media = StoredMedia(
            id=f"media-{self._next_id}",
            farmer_id=farmer_id,
            cattle_id=cattle_id,
            detection_id=detection_id,
            checksum=checksum,
            consent_scope=consent_scope,
            storage_reference=storage_reference,
        )
        self._next_id += 1
        self._media_by_id[media.id] = media
        return media

    def get(self, media_id: str) -> StoredMedia | None:
        return self._media_by_id.get(media_id)


media_store = MediaStore()
