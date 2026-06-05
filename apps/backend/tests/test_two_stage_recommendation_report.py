from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "docs/model/TWO_STAGE_MODEL_COMPARISON_RECOMMENDATION.md"


def test_report_preserves_single_stage_as_main_implementation():
    text = REPORT.read_text(encoding="utf-8")

    assert "main proposal-aligned implementation remains the three-class CNN classifier" in text
    assert "Android/on-device inference should remain the existing single-stage TFLite" in text
    assert "server-first future-work" in text


def test_report_requires_real_expert_reviewed_same_test_set():
    text = REPORT.read_text(encoding="utf-8")

    assert "same expert-reviewed field-only test set" in text
    assert "label_tier=expert_reviewed" in text
    assert "test_eligible=include" in text
    assert "weak labels excluded" in text
    assert "Do not report real model performance unless these inputs are present" in text
    assert "Template" in text and "CSV/JSON" in text


def test_report_applies_success_gate_and_recommendation():
    text = REPORT.read_text(encoding="utf-8")

    assert "False Confident Result rate" in text
    assert "Macro F1" in text
    assert "FMD recall" in text
    assert "LSD recall" in text
    assert "Insufficient Visual Evidence rate" in text
    assert "≤35%" in text
    assert "keep two-stage architecture as future work" in text
    assert "Data needs before continuing" in text
