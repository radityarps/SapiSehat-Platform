"""Milestone 5 cluster trigger rule unit tests."""

from datetime import datetime, timedelta, timezone

from api.fusion_results import FusionResult
from api.risk_signals import summarize_risk_signals


def result(
    id: str,
    *,
    cattle_id: str,
    disease_class: str = "FMD",
    reliability: str = "reliable",
    created_at: datetime | None = None,
) -> FusionResult:
    return FusionResult(
        id=id,
        fusion_version="test",
        inference_mode="hybrid",
        farmer_id="farmer-1",
        cattle_id=cattle_id,
        disease_class=disease_class,
        confidence=0.8,
        confidence_level="high",
        reliability=reliability,
        handling_advice_key="advice.isolate_and_contact_vet",
        evidence_breakdown={},
        conflict_status="none",
        model_versions={},
        created_at=(created_at or datetime.now(timezone.utc)).isoformat(),
    )


def test_three_risky_results_same_disease_same_district_within_seven_days_trigger_alert():
    now = datetime(2026, 6, 19, tzinfo=timezone.utc)

    signals = summarize_risk_signals(
        [
            result("r1", cattle_id="c1", created_at=now - timedelta(days=6)),
            result("r2", cattle_id="c2", created_at=now - timedelta(days=2)),
            result("r3", cattle_id="c3", created_at=now),
        ],
        {"c1": "tembalang", "c2": "tembalang", "c3": "tembalang"},
    )

    assert len(signals) == 1
    assert signals[0].signal_count == 3
    assert signals[0].risk_level == "possible_increased_risk"
    assert signals[0].priority == "follow_up_priority"


def test_two_risky_results_do_not_cross_threshold():
    signals = summarize_risk_signals(
        [result("r1", cattle_id="c1"), result("r2", cattle_id="c2")],
        {"c1": "tembalang", "c2": "tembalang"},
    )

    assert len(signals) == 1
    assert signals[0].signal_count == 2
    assert signals[0].risk_level == "baseline_monitoring"


def test_cross_district_results_do_not_combine_into_one_cluster():
    signals = summarize_risk_signals(
        [
            result("r1", cattle_id="c1"),
            result("r2", cattle_id="c2"),
            result("r3", cattle_id="c3"),
        ],
        {"c1": "tembalang", "c2": "tembalang", "c3": "banyumanik"},
    )

    by_jurisdiction = {signal.jurisdiction_id: signal for signal in signals}
    assert by_jurisdiction["tembalang"].signal_count == 2
    assert by_jurisdiction["tembalang"].risk_level == "baseline_monitoring"
    assert by_jurisdiction["banyumanik"].signal_count == 1


def test_old_results_outside_seven_day_window_do_not_count():
    now = datetime(2026, 6, 19, tzinfo=timezone.utc)

    signals = summarize_risk_signals(
        [
            result("old", cattle_id="c1", created_at=now - timedelta(days=8)),
            result("r2", cattle_id="c2", created_at=now - timedelta(days=2)),
            result("r3", cattle_id="c3", created_at=now - timedelta(days=1)),
            result("r4", cattle_id="c4", created_at=now),
        ],
        {"c1": "tembalang", "c2": "tembalang", "c3": "tembalang", "c4": "tembalang"},
    )

    assert len(signals) == 1
    assert signals[0].source_result_ids == ["r2", "r3", "r4"]
    assert signals[0].signal_count == 3
