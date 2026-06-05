"""Field-only baseline evaluation package (#28).

Consumes an expert-reviewed field manifest plus prediction CSV for the current
single-stage classifier. Computes real metrics only; no field data means no
claimed result.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

CLASSES = ["FMD", "LSD", "healthy"]
INSUFFICIENT = "INSUFFICIENT_VISUAL_EVIDENCE"
MIN_CONFIDENCE = 0.70
MIN_MARGIN = 0.15


@dataclass(frozen=True)
class FieldExample:
    image_id: str
    true_label: str
    split: str


@dataclass(frozen=True)
class Prediction:
    image_id: str
    predicted_label: str
    confidence: float
    scores: dict[str, float]


def _include_for_eval(row: dict[str, str], split: str) -> bool:
    if row.get("label_tier", "").strip() != "expert_reviewed":
        return False
    if row.get("is_hard_negative", "").strip().lower() in {"true", "1", "yes"}:
        return False
    label = row.get("disease_class", "").strip()
    if label not in CLASSES:
        return False
    eligibility_column = "validation_eligible" if split == "validation" else "test_eligible"
    return row.get(eligibility_column, "").strip().lower() == "include"


def load_field_examples(path: str | Path, split: str = "test") -> list[FieldExample]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        FieldExample(row["image_id"], row["disease_class"].strip(), split)
        for row in rows
        if _include_for_eval(row, split)
    ]


def load_predictions(path: str | Path) -> dict[str, Prediction]:
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    predictions: dict[str, Prediction] = {}
    for row in rows:
        scores = {cls: float(row.get(f"score_{cls}", "0") or 0) for cls in CLASSES}
        predictions[row["image_id"]] = Prediction(
            image_id=row["image_id"],
            predicted_label=row["predicted_label"].strip(),
            confidence=float(row.get("confidence", "0") or 0),
            scores=scores,
        )
    return predictions


def top_margin(scores: dict[str, float]) -> float:
    values = sorted(scores.values(), reverse=True)
    if len(values) < 2:
        return 0.0
    return values[0] - values[1]


def apply_policy(prediction: Prediction) -> str:
    if prediction.predicted_label == INSUFFICIENT:
        return INSUFFICIENT
    if prediction.confidence < MIN_CONFIDENCE or top_margin(prediction.scores) < MIN_MARGIN:
        return INSUFFICIENT
    return prediction.predicted_label


def evaluate(examples: list[FieldExample], predictions: dict[str, Prediction]) -> dict:
    if not examples:
        raise ValueError("No expert-reviewed field validation/test examples available")

    missing = [example.image_id for example in examples if example.image_id not in predictions]
    if missing:
        raise ValueError(f"Missing predictions for {len(missing)} image(s): {', '.join(missing[:5])}")

    confusion = {true: {pred: 0 for pred in CLASSES + [INSUFFICIENT]} for true in CLASSES}
    failure_categories = {
        "insufficient_visual_evidence": 0,
        "false_confident_result": 0,
        "class_confusion": 0,
    }

    evaluated = []
    for example in examples:
        prediction = predictions[example.image_id]
        final_label = apply_policy(prediction)
        confusion[example.true_label][final_label] += 1
        false_confident = (
            final_label in CLASSES
            and final_label != example.true_label
            and prediction.confidence >= MIN_CONFIDENCE
            and top_margin(prediction.scores) >= MIN_MARGIN
        )
        if final_label == INSUFFICIENT:
            failure_categories["insufficient_visual_evidence"] += 1
        elif final_label != example.true_label:
            failure_categories["class_confusion"] += 1
        if false_confident:
            failure_categories["false_confident_result"] += 1
        evaluated.append({
            "image_id": example.image_id,
            "true_label": example.true_label,
            "predicted_label": prediction.predicted_label,
            "final_label": final_label,
            "confidence": prediction.confidence,
            "top_margin": top_margin(prediction.scores),
            "false_confident_result": false_confident,
        })

    per_class = {}
    f1_values = []
    for cls in CLASSES:
        tp = confusion[cls][cls]
        fn = sum(confusion[cls].values()) - tp
        fp = sum(confusion[other][cls] for other in CLASSES if other != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cls] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(confusion[cls].values())}
        f1_values.append(f1)

    total = len(examples)
    return {
        "evaluated_count": total,
        "class_order": CLASSES,
        "preprocessing": "RGB, EXIF orientation where available, 224x224, rescale 1/255",
        "policy": {"min_confidence": MIN_CONFIDENCE, "min_top_class_margin": MIN_MARGIN},
        "macro_f1": sum(f1_values) / len(f1_values),
        "per_class": per_class,
        "fmd_recall": per_class["FMD"]["recall"],
        "lsd_recall": per_class["LSD"]["recall"],
        "confusion_matrix": confusion,
        "insufficient_visual_evidence_rate": failure_categories["insufficient_visual_evidence"] / total,
        "false_confident_result_rate": failure_categories["false_confident_result"] / total,
        "failure_categories": failure_categories,
        "evaluated_examples": evaluated,
    }


def format_report(metrics: dict) -> str:
    lines = [
        "# Field-Only Baseline Evaluation Report",
        "",
        "Current single-stage classifier evaluated on expert-reviewed field-only validation/test data.",
        "Weak labels are excluded from ground truth. Hard-negative rows are excluded from disease-class metrics and handled in threshold/error-analysis work.",
        "",
        "## Protocol",
        "",
        f"- Class order: `{metrics['class_order']}`",
        f"- Preprocessing: {metrics['preprocessing']}",
        f"- Insufficient Visual Evidence: confidence < {MIN_CONFIDENCE:.2f} or top-class margin < {MIN_MARGIN:.2f}",
        "",
        "## Metrics",
        "",
        f"- Evaluated field examples: **{metrics['evaluated_count']}**",
        f"- Macro F1: **{metrics['macro_f1']:.4f}**",
        f"- FMD recall: **{metrics['fmd_recall']:.4f}**",
        f"- LSD recall: **{metrics['lsd_recall']:.4f}**",
        f"- Insufficient Visual Evidence rate: **{metrics['insufficient_visual_evidence_rate']:.4f}**",
        f"- False Confident Result rate: **{metrics['false_confident_result_rate']:.4f}**",
        "",
        "## Per-class metrics",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for cls in CLASSES:
        row = metrics["per_class"][cls]
        lines.append(f"| {cls} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['support']} |")
    lines += ["", "## Confusion matrix", "", "Rows are true labels. Columns include disease classes plus Insufficient Visual Evidence.", ""]
    lines.append("| True \\ Pred | " + " | ".join(CLASSES + [INSUFFICIENT]) + " |")
    lines.append("|---|" + "|".join(["---:"] * (len(CLASSES) + 1)) + "|")
    for true in CLASSES:
        lines.append("| " + true + " | " + " | ".join(str(metrics["confusion_matrix"][true][pred]) for pred in CLASSES + [INSUFFICIENT]) + " |")
    lines += [
        "",
        "## Failure categories for follow-up",
        "",
    ]
    for key, value in metrics["failure_categories"].items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate current single-stage model on expert-reviewed field-only set")
    parser.add_argument("--field-manifest", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--split", choices=["validation", "test"], default="test")
    parser.add_argument("--out", required=True, help="Output markdown report path")
    parser.add_argument("--metrics-json", help="Optional metrics JSON output path")
    args = parser.parse_args(argv)

    examples = load_field_examples(args.field_manifest, args.split)
    predictions = load_predictions(args.predictions)
    metrics = evaluate(examples, predictions)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(format_report(metrics), encoding="utf-8")
    if args.metrics_json:
        metrics_path = Path(args.metrics_json)
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

