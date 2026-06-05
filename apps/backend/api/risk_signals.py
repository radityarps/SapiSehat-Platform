"""Disease risk signal summary tracer."""

from dataclasses import dataclass
from typing import Iterable

from api.fusion_results import FusionResult


@dataclass(frozen=True)
class JurisdictionRiskSignal:
    jurisdiction_id: str
    disease_class: str
    signal_count: int
    window_days: int
    risk_level: str
    priority: str
    summary_label: str


def summarize_risk_signals(results: Iterable[FusionResult], cattle_jurisdictions: dict[str, str]) -> list[JurisdictionRiskSignal]:
    counts: dict[tuple[str, str], int] = {}
    for result in results:
        if result.cattle_id is None:
            continue
        if result.disease_class == "healthy":
            continue
        if result.reliability not in {"reliable", "needs_review"}:
            continue
        jurisdiction_id = cattle_jurisdictions.get(result.cattle_id)
        if jurisdiction_id is None:
            continue
        key = (jurisdiction_id, result.disease_class)
        counts[key] = counts.get(key, 0) + 1

    signals = []
    for (jurisdiction_id, disease_class), count in counts.items():
        elevated = count >= 2
        signals.append(JurisdictionRiskSignal(
            jurisdiction_id=jurisdiction_id,
            disease_class=disease_class,
            signal_count=count,
            window_days=7,
            risk_level="possible_increased_risk" if elevated else "baseline_monitoring",
            priority="follow_up_priority" if elevated else "routine_monitoring",
            summary_label="Possible increased disease risk signal" if elevated else "Routine monitoring signal",
        ))
    return sorted(signals, key=lambda signal: (signal.jurisdiction_id, signal.disease_class))
