"""Disease risk signal summary tracer."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from api.database import SessionLocal, create_all_tables
from api.db_models import ClusterRiskSignalModel
from api.fusion_results import FusionResult


HYBRID_ALERT_THRESHOLD = 3
CLUSTER_WINDOW_DAYS = 7
RISK_SIGNAL_RELIABILITY = {"reliable", "needs_review"}


@dataclass(frozen=True)
class JurisdictionRiskSignal:
    id: str
    jurisdiction_id: str
    disease_class: str
    signal_count: int
    window_days: int
    risk_level: str
    priority: str
    summary_label: str
    source_result_ids: list[str]


def _parse_created_at(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _window_anchor(results: list[FusionResult]) -> datetime:
    timestamps = [
        parsed
        for result in results
        if (parsed := _parse_created_at(result.created_at)) is not None
    ]
    return max(timestamps) if timestamps else datetime.now(timezone.utc)


def summarize_risk_signals(
    results: Iterable[FusionResult], cattle_jurisdictions: dict[str, str]
) -> list[JurisdictionRiskSignal]:
    results = list(results)
    window_end = _window_anchor(results)
    window_start = window_end - timedelta(days=CLUSTER_WINDOW_DAYS)
    counts: dict[tuple[str, str], int] = {}
    source_ids: dict[tuple[str, str], list[str]] = {}
    for result in results:
        if result.cattle_id is None:
            continue
        created_at = _parse_created_at(result.created_at)
        if created_at is None or created_at < window_start or created_at > window_end:
            continue
        if result.disease_class == "healthy":
            continue
        if result.reliability not in RISK_SIGNAL_RELIABILITY:
            continue
        jurisdiction_id = cattle_jurisdictions.get(result.cattle_id)
        if jurisdiction_id is None:
            continue
        key = (jurisdiction_id, result.disease_class)
        counts[key] = counts.get(key, 0) + 1
        source_ids.setdefault(key, []).append(result.id)

    signals = []
    for (jurisdiction_id, disease_class), count in counts.items():
        elevated = count >= HYBRID_ALERT_THRESHOLD
        signals.append(JurisdictionRiskSignal(
            id=f"cluster-risk-{jurisdiction_id}-{disease_class}".lower(),
            jurisdiction_id=jurisdiction_id,
            disease_class=disease_class,
            signal_count=count,
            window_days=CLUSTER_WINDOW_DAYS,
            risk_level="possible_increased_risk" if elevated else "baseline_monitoring",
            priority="follow_up_priority" if elevated else "routine_monitoring",
            summary_label="Possible increased disease risk signal" if elevated else "Routine monitoring signal",
            source_result_ids=source_ids[(jurisdiction_id, disease_class)],
        ))
    return sorted(signals, key=lambda signal: (signal.jurisdiction_id, signal.disease_class))


class ClusterRiskSignalStore:
    """Materialized cluster risk signals for agency dashboard reads."""

    def __init__(self) -> None:
        create_all_tables()

    def replace_all(self, signals: list[JurisdictionRiskSignal]) -> None:
        with SessionLocal() as session:
            session.query(ClusterRiskSignalModel).delete()
            for signal in signals:
                session.add(ClusterRiskSignalModel(**signal.__dict__))
            session.commit()

    def list_all(self) -> list[JurisdictionRiskSignal]:
        with SessionLocal() as session:
            rows = session.query(ClusterRiskSignalModel).order_by(ClusterRiskSignalModel.jurisdiction_id, ClusterRiskSignalModel.disease_class).all()
            return [_signal_from_row(row) for row in rows]

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(ClusterRiskSignalModel).delete()
            session.commit()


def _signal_from_row(row: ClusterRiskSignalModel) -> JurisdictionRiskSignal:
    return JurisdictionRiskSignal(
        id=row.id,
        jurisdiction_id=row.jurisdiction_id,
        disease_class=row.disease_class,
        signal_count=row.signal_count,
        window_days=row.window_days,
        risk_level=row.risk_level,
        priority=row.priority,
        summary_label=row.summary_label,
        source_result_ids=row.source_result_ids,
    )


cluster_risk_signal_store = ClusterRiskSignalStore()
