"""Quick-scan detection attachment persistence."""

from __future__ import annotations

from dataclasses import dataclass

from api.database import SessionLocal, create_all_tables
from api.db_models import DetectionEventModel

@dataclass(frozen=True)
class DetectionEvent:
    id: str
    farmer_id: str
    cattle_id: str | None
    result_label: str
    confidence: float
    source: str

    @property
    def attached(self) -> bool:
        return self.cattle_id is not None

class DetectionEventStore:
    def __init__(self) -> None:
        create_all_tables()

    def create_quick_scan(self, *, farmer_id: str, result_label: str, confidence: float, source: str) -> DetectionEvent:
        with SessionLocal() as session:
            next_id = session.query(DetectionEventModel).count() + 1
            event = DetectionEvent(
                id=f"detection-{next_id}",
                farmer_id=farmer_id,
                cattle_id=None,
                result_label=result_label,
                confidence=confidence,
                source=source,
            )
            session.add(
                DetectionEventModel(
                    id=event.id,
                    farmer_id=event.farmer_id,
                    cattle_id=event.cattle_id,
                    result_label=event.result_label,
                    confidence=event.confidence,
                    source=event.source,
                )
            )
            session.commit()
            return event

    def attach_to_cattle(self, *, farmer_id: str, detection_id: str, cattle_id: str) -> DetectionEvent | None:
        with SessionLocal() as session:
            row = session.get(DetectionEventModel, detection_id)
            if row is None or row.farmer_id != farmer_id or row.cattle_id is not None:
                return None
            row.cattle_id = cattle_id
            session.commit()
            session.refresh(row)
            return _detection_from_row(row)

    def list_by_cattle_ids(self, cattle_ids: set[str]) -> list[DetectionEvent]:
        if not cattle_ids:
            return []
        with SessionLocal() as session:
            rows = (
                session.query(DetectionEventModel)
                .filter(DetectionEventModel.cattle_id.in_(cattle_ids))
                .order_by(DetectionEventModel.id)
                .all()
            )
            return [_detection_from_row(row) for row in rows]

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(DetectionEventModel).delete()
            session.commit()


def _detection_from_row(row: DetectionEventModel) -> DetectionEvent:
    return DetectionEvent(
        id=row.id,
        farmer_id=row.farmer_id,
        cattle_id=row.cattle_id,
        result_label=row.result_label,
        confidence=row.confidence,
        source=row.source,
    )

detection_event_store = DetectionEventStore()
