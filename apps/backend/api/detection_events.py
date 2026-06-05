"""Quick-scan detection attachment tracer."""

from __future__ import annotations

from dataclasses import dataclass


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
        self._events_by_id: dict[str, DetectionEvent] = {}
        self._next_id = 1

    def create_quick_scan(self, *, farmer_id: str, result_label: str, confidence: float, source: str) -> DetectionEvent:
        event = DetectionEvent(
            id=f"detection-{self._next_id}",
            farmer_id=farmer_id,
            cattle_id=None,
            result_label=result_label,
            confidence=confidence,
            source=source,
        )
        self._next_id += 1
        self._events_by_id[event.id] = event
        return event

    def attach_to_cattle(self, *, farmer_id: str, detection_id: str, cattle_id: str) -> DetectionEvent | None:
        event = self._events_by_id.get(detection_id)
        if event is None or event.farmer_id != farmer_id or event.cattle_id is not None:
            return None
        attached = DetectionEvent(
            id=event.id,
            farmer_id=event.farmer_id,
            cattle_id=cattle_id,
            result_label=event.result_label,
            confidence=event.confidence,
            source=event.source,
        )
        self._events_by_id[detection_id] = attached
        return attached

    def list_by_cattle_ids(self, cattle_ids: set[str]) -> list[DetectionEvent]:
        return [event for event in self._events_by_id.values() if event.cattle_id in cattle_ids]

    def clear(self) -> None:
        self._events_by_id.clear()
        self._next_id = 1


detection_event_store = DetectionEventStore()
