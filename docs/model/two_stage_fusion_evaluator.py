"""Two-stage fusion evaluator (#30).

Combines full-image classifier scores with top detector crop classifier scores
before backend inference changes. Uses 40% full-image + 60% crop by default.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

CLASSES = ["FMD", "LSD", "healthy"]
INSUFFICIENT = "INSUFFICIENT_VISUAL_EVIDENCE"
DISEASE_REGION_CLASSES = {
    "FMD": {"fmd_mouth_lesion", "fmd_hoof_lesion"},
    "LSD": {"lsd_skin_nodule"},
}


def _scores(row: dict[str, str]) -> dict[str, float]:
    return {cls: float(row.get(f"score_{cls}", "0") or 0) for cls in CLASSES}


def _top_label(scores: dict[str, float]) -> str:
    return max(CLASSES, key=lambda cls: scores[cls])


def _margin(scores: dict[str, float]) -> float:
    values = sorted(scores.values(), reverse=True)
    return values[0] - values[1] if len(values) >= 2 else 0.0


def load_full_scores(path: str | Path) -> dict[str, dict[str, float]]:
    with open(path, encoding="utf-8", newline="") as f:
        return {row["image_id"]: _scores(row) for row in csv.DictReader(f)}


def load_crop_rows(path: str | Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            rows.append({
                "image_id": row["image_id"],
                "box_id": row["box_id"],
                "symptom_region_type": row["symptom_region_type"],
                "detector_confidence": float(row.get("detector_confidence", "0") or 0),
                "scores": _scores(row),
            })
    return rows


def aggregate_top_crops(rows: list[dict], top_k: int = 3) -> tuple[dict[str, dict[str, float]], dict[str, set[str]]]:
    by_image: dict[str, list[dict]] = {}
    for row in rows:
        by_image.setdefault(row["image_id"], []).append(row)
    aggregates: dict[str, dict[str, float]] = {}
    region_types: dict[str, set[str]] = {}
    for image_id, image_rows in by_image.items():
        selected = sorted(image_rows, key=lambda r: r["detector_confidence"], reverse=True)[:top_k]
        aggregates[image_id] = {cls: max((r["scores"][cls] for r in selected), default=0.0) for cls in CLASSES}
        region_types[image_id] = {r["symptom_region_type"] for r in selected}
    return aggregates, region_types


def fuse_scores(full: dict[str, float], crop: dict[str, float], full_weight: float = 0.4) -> dict[str, float]:
    crop_weight = 1.0 - full_weight
    return {cls: full_weight * full.get(cls, 0.0) + crop_weight * crop.get(cls, 0.0) for cls in CLASSES}


def needs_review(label: str, region_types: set[str]) -> bool:
    if label not in DISEASE_REGION_CLASSES:
        return False
    disease_types = {t for types in DISEASE_REGION_CLASSES.values() for t in types}
    present = region_types & disease_types
    return bool(present and not (present & DISEASE_REGION_CLASSES[label]))


def evaluate_fusion(
    truth: dict[str, str],
    full_scores: dict[str, dict[str, float]],
    crop_rows: list[dict],
    *,
    full_weight: float = 0.4,
    min_confidence: float = 0.70,
    min_margin: float = 0.15,
) -> dict:
    crop_scores, region_types = aggregate_top_crops(crop_rows, top_k=3)
    confusion = {true: {pred: 0 for pred in CLASSES + [INSUFFICIENT]} for true in CLASSES}
    false_confident = 0
    insufficient = 0
    review_count = 0
    rows = []
    for image_id, true in truth.items():
        fused = fuse_scores(full_scores[image_id], crop_scores.get(image_id, {cls: 0.0 for cls in CLASSES}), full_weight)
        label = _top_label(fused)
        confidence = fused[label]
        margin = _margin(fused)
        review = needs_review(label, region_types.get(image_id, set()))
        final = label
        if confidence < min_confidence or margin < min_margin:
            final = INSUFFICIENT
            insufficient += 1
        if review:
            review_count += 1
        if final in CLASSES and final != true and confidence >= min_confidence and margin >= min_margin:
            false_confident += 1
        confusion[true][final] += 1
        rows.append({"image_id": image_id, "true_label": true, "final_label": final, "confidence": confidence, "margin": margin, "needs_review": review})
    per_class = {}
    f1s = []
    for cls in CLASSES:
        tp = confusion[cls][cls]
        fn = sum(confusion[cls].values()) - tp
        fp = sum(confusion[other][cls] for other in CLASSES if other != cls)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[cls] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(confusion[cls].values())}
        f1s.append(f1)
    total = len(truth)
    return {
        "evaluated_count": total,
        "fusion": {"full_image_weight": full_weight, "crop_weight": 1.0 - full_weight, "top_k_boxes": 3},
        "macro_f1": sum(f1s) / len(f1s),
        "per_class": per_class,
        "fmd_recall": per_class["FMD"]["recall"],
        "lsd_recall": per_class["LSD"]["recall"],
        "insufficient_visual_evidence_rate": insufficient / total,
        "false_confident_result_rate": false_confident / total,
        "needs_review_rate": review_count / total,
        "confusion_matrix": confusion,
        "evaluated_examples": rows,
    }


def success_gate(two_stage: dict, baseline: dict) -> dict:
    checks = {
        "lower_false_confident_result_rate": two_stage["false_confident_result_rate"] < baseline["false_confident_result_rate"],
        "field_macro_f1_equal_or_better": two_stage["macro_f1"] >= baseline["macro_f1"],
        "fmd_recall_not_worse_by_more_than_5pp": two_stage["fmd_recall"] >= baseline["fmd_recall"] - 0.05,
        "lsd_recall_not_worse_by_more_than_5pp": two_stage["lsd_recall"] >= baseline["lsd_recall"] - 0.05,
        "insufficient_evidence_rate_at_or_below_35pct": two_stage["insufficient_visual_evidence_rate"] <= 0.35,
    }
    return {"passed": all(checks.values()), "checks": checks}


def load_truth(path: str | Path) -> dict[str, str]:
    with open(path, encoding="utf-8", newline="") as f:
        return {row["image_id"]: row["disease_class"] for row in csv.DictReader(f) if row.get("label_tier") == "expert_reviewed" and row.get("test_eligible") == "include"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate two-stage score fusion offline")
    parser.add_argument("--truth", required=True)
    parser.add_argument("--full-scores", required=True)
    parser.add_argument("--crop-scores", required=True)
    parser.add_argument("--baseline-metrics", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    metrics = evaluate_fusion(load_truth(args.truth), load_full_scores(args.full_scores), load_crop_rows(args.crop_scores))
    baseline = json.loads(Path(args.baseline_metrics).read_text(encoding="utf-8"))
    payload = {"two_stage": metrics, "success_gate": success_gate(metrics, baseline)}
    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

