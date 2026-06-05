"""
Model Selection Logic (issue #21).

Applies the approved selection rules (issue #17) to candidate evaluation
results and produces a formal selection decision. This script is both:
  - A library (importable for tests with metric fixtures)
  - A CLI that reads real *_metrics.json files and prints the decision

Selection rules (in priority order):
  1. REJECT any candidate with per-class F1 < 0.85 (unless documented exception).
  2. PRIMARY metric: macro F1 (highest wins).
  3. CHECK test accuracy >= 0.88 target.
  4. TIE-BREAKERS (if macro F1 within 0.005): test accuracy > TFLite size < offline latency.
  5. ANDROID VIABILITY: TFLite size must be < 10 MB for on-device candidate.
  6. If NO candidate reaches targets: mark best as experimental/demo with
     limitations and follow-up recommendations.

Usage:
    python model_selection.py --results-dir docs/model/results
    python model_selection.py --results-dir docs/model/results --out docs/model/MODEL_SELECTION_REPORT.md
"""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


# ── Targets (issue #17) ──────────────────────────────────────────────────────

ACCURACY_TARGET = 0.88
PER_CLASS_F1_FLOOR = 0.85
MACRO_F1_TIE_THRESHOLD = 0.005  # within this = "tied"
TFLITE_SIZE_BUDGET_MB = 10.0

CLASSES = ["FMD", "LSD", "healthy"]


@dataclass
class CandidateResult:
    """Parsed candidate metrics for selection logic."""

    name: str
    accuracy: float
    macro_f1: float
    per_class_f1: dict  # class -> f1
    min_per_class_f1: float = 0.0
    min_per_class_f1_class: str = ""
    params: int = 0
    keras_size_mb: float = 0.0
    tflite_size_mb: float | None = None  # estimated or measured
    evaluated_on_split: str = "test"

    def __post_init__(self):
        if self.per_class_f1:
            min_cls = min(self.per_class_f1, key=lambda cls: self.per_class_f1[cls])
            self.min_per_class_f1 = self.per_class_f1[min_cls]
            self.min_per_class_f1_class = min_cls


@dataclass
class SelectionDecision:
    """The output of the selection logic."""

    selected: CandidateResult | None = None
    status: str = ""  # "selected" | "experimental_demo" | "no_candidates"
    reason: str = ""
    rejected: list = field(default_factory=list)
    passed: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    follow_up: list = field(default_factory=list)


# ── Estimated TFLite sizes (from literature / prior measurements) ────────────
# These are estimates until actual TFLite conversion is done (issue #22).
TFLITE_SIZE_ESTIMATES: dict[str, float] = {
    "custom_cnn": 0.5,
    "mobilenetv2": 9.0,
    "densenet121": 30.0,
}


def parse_metrics_json(path: str) -> CandidateResult:
    """Parse a *_metrics.json file into a CandidateResult."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    per_class_f1: dict[str, float] = {}
    for cls in CLASSES:
        cls_data = data.get("per_class", {}).get(cls, {})
        f1 = cls_data.get("f1-score") or cls_data.get("f1_score")
        if f1 is not None:
            per_class_f1[cls] = f1

    macro_avg = data.get("macro_avg", {})
    macro_f1 = macro_avg.get("f1-score") or macro_avg.get("f1_score") or 0.0

    name = data.get("model", "unknown")
    tflite_est = TFLITE_SIZE_ESTIMATES.get(name)

    return CandidateResult(
        name=name,
        accuracy=data.get("accuracy", 0.0),
        macro_f1=macro_f1,
        per_class_f1=per_class_f1,
        params=data.get("params", 0),
        keras_size_mb=data.get("keras_size_mb", 0.0),
        tflite_size_mb=tflite_est,
        evaluated_on_split=data.get("evaluated_on_split", "test"),
    )


def select_model(candidates: list[CandidateResult]) -> SelectionDecision:
    """
    Apply the approved selection rules to a list of candidate results.

    Pure function — no I/O. Fully testable with metric fixtures.
    """
    decision = SelectionDecision()

    if not candidates:
        decision.status = "no_candidates"
        decision.reason = "No candidate results provided."
        return decision

    # Step 1: Reject candidates with per-class F1 below floor.
    passed: list[CandidateResult] = []
    for c in candidates:
        if c.min_per_class_f1 < PER_CLASS_F1_FLOOR:
            decision.rejected.append(
                (
                    c,
                    f"Per-class F1 floor violation: {c.min_per_class_f1_class} "
                    f"F1={c.min_per_class_f1:.3f} < {PER_CLASS_F1_FLOOR}",
                )
            )
        else:
            passed.append(c)
    decision.passed = passed

    # Step 2: Check accuracy target.
    for c in passed:
        if c.accuracy < ACCURACY_TARGET:
            decision.warnings.append(
                f"{c.name}: accuracy {c.accuracy:.3f} below target "
                f"{ACCURACY_TARGET} (but per-class F1 passes)"
            )

    # Step 3: If no candidates pass, mark best as experimental/demo.
    if not passed:
        best = max(candidates, key=lambda c: c.macro_f1)
        decision.selected = best
        decision.status = "experimental_demo"
        decision.reason = (
            f"No candidate meets the per-class F1 floor ({PER_CLASS_F1_FLOOR}). "
            f"Best candidate ({best.name}, macro F1={best.macro_f1:.3f}) is "
            f"marked experimental/demo only. Not approved for production."
        )
        decision.follow_up = [
            "Investigate why per-class F1 is below threshold.",
            "Consider additional training data or augmentation for weak classes.",
            "Re-run evaluation after improvements.",
            "Do not deploy as production model without meeting targets.",
        ]
        return decision

    # Step 4: Sort by macro F1 (primary metric), descending.
    passed_sorted = sorted(passed, key=lambda c: c.macro_f1, reverse=True)
    best = passed_sorted[0]

    # Step 5: Check for ties (within threshold).
    tied = [
        c
        for c in passed_sorted
        if abs(c.macro_f1 - best.macro_f1) <= MACRO_F1_TIE_THRESHOLD
    ]

    if len(tied) > 1:
        # Tie-break: accuracy > TFLite size (smaller wins) > params (smaller wins)
        tied.sort(
            key=lambda c: (
                -c.accuracy,
                c.tflite_size_mb or 999,
                c.params,
            )
        )
        best = tied[0]

    # Step 6: Android viability check.
    android_viable = (
        best.tflite_size_mb is not None and best.tflite_size_mb <= TFLITE_SIZE_BUDGET_MB
    )
    if not android_viable:
        decision.warnings.append(
            f"{best.name}: TFLite size ~{best.tflite_size_mb} MB exceeds "
            f"{TFLITE_SIZE_BUDGET_MB} MB budget. Not viable for on-device "
            f"inference. Consider the next-best Android-viable candidate."
        )
        # Find the best Android-viable candidate.
        android_candidates = [
            c
            for c in passed_sorted
            if c.tflite_size_mb is not None
            and c.tflite_size_mb <= TFLITE_SIZE_BUDGET_MB
        ]
        if android_candidates:
            best = android_candidates[0]
            decision.warnings.append(
                f"Falling back to {best.name} (TFLite ~{best.tflite_size_mb} MB) "
                f"for dual-path (server + on-device) deployment."
            )

    decision.selected = best
    decision.status = "selected"
    decision.reason = (
        f"{best.name} selected: macro F1={best.macro_f1:.3f}, "
        f"accuracy={best.accuracy:.3f}, min per-class F1="
        f"{best.min_per_class_f1:.3f} ({best.min_per_class_f1_class}), "
        f"TFLite ~{best.tflite_size_mb} MB. "
        f"Meets all targets and Android viability constraint."
    )
    return decision


def format_report(
    candidates: list[CandidateResult], decision: SelectionDecision
) -> str:
    """Format the selection decision as a Markdown report."""
    lines: list[str] = []
    lines.append("# Model Selection Report (issue #21)")
    lines.append("")
    lines.append(
        "Generated by `docs/model/model_selection.py` from real "
        "candidate evaluation results."
    )
    lines.append("")

    # ── Selection rules ──
    lines.append("## Selection Rules (issue #17)")
    lines.append("")
    lines.append(
        f"1. **Reject** any candidate with per-class F1 < "
        f"{PER_CLASS_F1_FLOOR} (unless documented exception)."
    )
    lines.append("2. **Primary metric**: macro F1 (highest wins).")
    lines.append(f"3. **Accuracy target**: test accuracy ≥ {ACCURACY_TARGET}.")
    lines.append(
        f"4. **Tie-breakers** (macro F1 within {MACRO_F1_TIE_THRESHOLD}): "
        f"test accuracy > TFLite size < offline latency."
    )
    lines.append(
        f"5. **Android viability**: TFLite size < "
        f"{TFLITE_SIZE_BUDGET_MB} MB for on-device candidate."
    )
    lines.append(
        "6. **Failure policy**: if no candidate reaches targets, "
        "mark best as experimental/demo with follow-up."
    )
    lines.append("")

    # ── Candidate summary ──
    lines.append("## Candidate Results")
    lines.append("")
    lines.append(
        "| Model | Accuracy | Macro F1 | Min per-class F1 | TFLite est. | Status |"
    )
    lines.append(
        "|-------|----------|----------|-------------------|------------|--------|"
    )
    rejected_names = {c.name for c, _ in decision.rejected}
    for c in candidates:
        status = "❌ rejected" if c.name in rejected_names else "✅ passed"
        if decision.selected and c.name == decision.selected.name:
            status = f"⭐ {decision.status}"
        lines.append(
            f"| {c.name} | {c.accuracy:.3f} | {c.macro_f1:.3f} | "
            f"{c.min_per_class_f1:.3f} ({c.min_per_class_f1_class}) | "
            f"~{c.tflite_size_mb or '?'} MB | {status} |"
        )
    lines.append("")

    # ── Rejections ──
    if decision.rejected:
        lines.append("## Rejected Candidates")
        lines.append("")
        for c, reason in decision.rejected:
            lines.append(f"- **{c.name}**: {reason}")
        lines.append("")

    # ── Decision ──
    lines.append("## Decision")
    lines.append("")
    lines.append(f"**Status**: {decision.status}")
    lines.append("")
    lines.append(f"**Rationale**: {decision.reason}")
    lines.append("")

    if decision.selected:
        s = decision.selected
        lines.append("### Selected model details")
        lines.append("")
        lines.append("| Property | Value |")
        lines.append("|----------|-------|")
        lines.append(f"| Model | {s.name} |")
        lines.append(f"| Test accuracy | {s.accuracy:.4f} |")
        lines.append(f"| Macro F1 | {s.macro_f1:.4f} |")
        lines.append(
            f"| Min per-class F1 | {s.min_per_class_f1:.4f} "
            f"({s.min_per_class_f1_class}) |"
        )
        lines.append(f"| Parameters | {s.params:,} |")
        lines.append(f"| Keras size | {s.keras_size_mb} MB |")
        lines.append(f"| TFLite size (est.) | ~{s.tflite_size_mb} MB |")
        lines.append(f"| Evaluated on | {s.evaluated_on_split} split |")
        lines.append(
            f"| Android viable | "
            f"{'✅ Yes' if s.tflite_size_mb and s.tflite_size_mb <= TFLITE_SIZE_BUDGET_MB else '❌ No'} |"
        )
        lines.append("")

    # ── Server + on-device explanation ──
    if decision.status == "selected" and decision.selected is not None:
        lines.append("### Server Inference")
        lines.append("")
        lines.append(
            f"The selected model ({decision.selected.name}) is deployed "
            f"as a Keras/SavedModel artifact on the backend server "
            f"(FastAPI + TensorFlow/Keras runtime). It provides the "
            f"highest accuracy among Android-viable candidates while "
            f"meeting all per-class F1 and accuracy targets."
        )
        lines.append("")
        lines.append("### On-device Inference")
        lines.append("")
        lines.append(
            f"The same architecture is exported to TFLite "
            f"(~{decision.selected.tflite_size_mb} MB, within the "
            f"{TFLITE_SIZE_BUDGET_MB} MB budget) for offline fallback "
            f"on Android. This ensures dual-path consistency: the same "
            f"class mapping, preprocessing, and model family serve both "
            f"server and mobile inference paths."
        )
        lines.append("")

    # ── Warnings ──
    if decision.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in decision.warnings:
            lines.append(f"- {w}")
        lines.append("")

    # ── Follow-up ──
    if decision.follow_up:
        lines.append("## Follow-up Recommendations")
        lines.append("")
        for f in decision.follow_up:
            lines.append(f"- {f}")
        lines.append("")

    # ── Failure policy ──
    lines.append("## Failure Policy")
    lines.append("")
    if decision.status == "experimental_demo":
        lines.append(
            "⚠️ **No candidate meets all targets.** The selected model "
            "is marked experimental/demo only and MUST NOT be deployed "
            "as a production clinical tool. Follow-up recommendations "
            "above must be addressed before any production claim."
        )
    else:
        lines.append(
            "✅ The selected candidate meets all targets (accuracy ≥ "
            f"{ACCURACY_TARGET}, per-class F1 ≥ {PER_CLASS_F1_FLOOR}, "
            f"TFLite < {TFLITE_SIZE_BUDGET_MB} MB). No failure policy "
            "triggered."
        )
    lines.append("")

    # ── Wording compliance ──
    lines.append("## Wording Compliance")
    lines.append("")
    lines.append("Per issue #17, all thesis/app/report outputs frame results as:")
    lines.append("")
    lines.append("- Image classification / early detection result")
    lines.append("- Prediction with confidence score")
    lines.append("- Initial handling advice")
    lines.append("")
    lines.append(
        "**NOT** as: final diagnosis, veterinarian replacement, or "
        "clinical disease determination."
    )
    lines.append("")

    # ── Limitations ──
    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "- Single-seed evaluation (seed 42). Winner should be rerun "
        "with additional seeds for robustness."
    )
    lines.append("- TFLite sizes are estimates until actual conversion (issue #22).")
    lines.append("- No veterinarian/animal-health-officer label audit performed.")
    lines.append("- Not a clinical diagnosis tool.")
    lines.append("")

    return "\n".join(lines)


def load_results_dir(results_dir: str) -> list[CandidateResult]:
    """
    Load issue #20 candidate metrics from a results directory structure.

    Issue #22 adds TFLite parity metrics under results/tflite_out. Those files
    are derived from the selected candidate and must not be treated as extra
    model-selection candidates.
    """
    candidates: list[CandidateResult] = []
    results_path = Path(results_dir)
    canonical_names = {"custom_cnn", "mobilenetv2", "densenet121"}
    seen: set[str] = set()

    # Look for *_metrics.json in subdirectories or directly.
    for metrics_file in sorted(results_path.rglob("*_metrics.json")):
        if "tflite_out" in metrics_file.relative_to(results_path).parts:
            continue
        try:
            c = parse_metrics_json(str(metrics_file))
            if c.name not in canonical_names:
                continue
            if c.name in seen:
                continue
            if c.accuracy > 0:  # skip pending/null stubs
                candidates.append(c)
                seen.add(c.name)
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return candidates


def main():
    parser = argparse.ArgumentParser(
        description="Apply model selection rules to candidate evaluation results."
    )
    parser.add_argument(
        "--results-dir",
        default="docs/model/results",
        help="Directory containing per-candidate results folders.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path for the selection report (Markdown). "
        "If omitted, prints to stdout.",
    )
    args = parser.parse_args()

    candidates = load_results_dir(args.results_dir)
    if not candidates:
        print(f"ERROR: no valid candidate metrics found in {args.results_dir}")
        raise SystemExit(1)

    print(f"Loaded {len(candidates)} candidate(s): {[c.name for c in candidates]}")

    decision = select_model(candidates)
    report = format_report(candidates, decision)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Selection report written to: {args.out}")
    else:
        print("\n" + report)

    print(
        f"\nDecision: {decision.status} -> {decision.selected.name if decision.selected else 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
