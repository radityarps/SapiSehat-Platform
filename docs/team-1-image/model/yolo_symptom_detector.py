"""YOLO symptom-region detector experiment helpers (#29).

Prepares approved symptom-region annotations for a small YOLO-family detector
and evaluates detector prediction CSVs. This file does not train on import.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

DETECTOR_CLASSES = ["fmd_mouth_lesion", "fmd_hoof_lesion", "lsd_skin_nodule", "confusing_region"]
CLASS_TO_INDEX = {name: index for index, name in enumerate(DETECTOR_CLASSES)}


def convert_annotations_to_yolo(annotation_csv: str | Path, out_dir: str | Path) -> dict[str, list[str]]:
    """Write one YOLO label txt per image_id using normalized annotation rows."""
    out = Path(out_dir)
    labels_dir = out / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[str]] = {}

    with open(annotation_csv, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            image_id = row.get("image_id", "").strip()
            category = row.get("symptom_category", "").strip()
            if not image_id or not category:
                continue
            if category not in CLASS_TO_INDEX:
                raise ValueError(f"Unknown detector class: {category}")
            x_min = float(row["x_min"])
            y_min = float(row["y_min"])
            x_max = float(row["x_max"])
            y_max = float(row["y_max"])
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            width = x_max - x_min
            height = y_max - y_min
            line = f"{CLASS_TO_INDEX[category]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}"
            grouped.setdefault(image_id, []).append(line)

    for image_id, lines in grouped.items():
        (labels_dir / f"{image_id}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    data_yaml = out / "data.yaml"
    data_yaml.write_text(
        "path: .\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        f"names: {json.dumps({i: name for i, name in enumerate(DETECTOR_CLASSES)})}\n",
        encoding="utf-8",
    )
    return grouped


def _iou(a: dict[str, float], b: dict[str, float]) -> float:
    x_left = max(a["x_min"], b["x_min"])
    y_top = max(a["y_min"], b["y_min"])
    x_right = min(a["x_max"], b["x_max"])
    y_bottom = min(a["y_max"], b["y_max"])
    if x_right <= x_left or y_bottom <= y_top:
        return 0.0
    intersection = (x_right - x_left) * (y_bottom - y_top)
    area_a = (a["x_max"] - a["x_min"]) * (a["y_max"] - a["y_min"])
    area_b = (b["x_max"] - b["x_min"]) * (b["y_max"] - b["y_min"])
    return intersection / (area_a + area_b - intersection)


def _read_boxes(path: str | Path, *, prediction: bool) -> list[dict]:
    boxes = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            category = row["symptom_category"].strip()
            if category not in CLASS_TO_INDEX:
                continue
            boxes.append({
                "image_id": row["image_id"].strip(),
                "symptom_category": category,
                "x_min": float(row["x_min"]),
                "y_min": float(row["y_min"]),
                "x_max": float(row["x_max"]),
                "y_max": float(row["y_max"]),
                "confidence": float(row.get("confidence", "1") or 1) if prediction else 1.0,
            })
    return boxes


def evaluate_predictions(ground_truth_csv: str | Path, predictions_csv: str | Path, iou_threshold: float = 0.5) -> dict:
    """Compute simple box precision/recall by class with one-to-one matching."""
    gt_boxes = _read_boxes(ground_truth_csv, prediction=False)
    pred_boxes = sorted(_read_boxes(predictions_csv, prediction=True), key=lambda box: box["confidence"], reverse=True)
    matched_gt: set[int] = set()
    per_class = {name: {"tp": 0, "fp": 0, "fn": 0} for name in DETECTOR_CLASSES}

    for pred in pred_boxes:
        best_index = -1
        best_iou = 0.0
        for index, gt in enumerate(gt_boxes):
            if index in matched_gt:
                continue
            if gt["image_id"] != pred["image_id"] or gt["symptom_category"] != pred["symptom_category"]:
                continue
            score = _iou(gt, pred)
            if score > best_iou:
                best_iou = score
                best_index = index
        if best_index >= 0 and best_iou >= iou_threshold:
            matched_gt.add(best_index)
            per_class[pred["symptom_category"]]["tp"] += 1
        else:
            per_class[pred["symptom_category"]]["fp"] += 1

    for index, gt in enumerate(gt_boxes):
        if index not in matched_gt:
            per_class[gt["symptom_category"]]["fn"] += 1

    metrics = {}
    for cls, counts in per_class.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        metrics[cls] = {**counts, "precision": precision, "recall": recall}
    totals = {
        "tp": sum(v["tp"] for v in per_class.values()),
        "fp": sum(v["fp"] for v in per_class.values()),
        "fn": sum(v["fn"] for v in per_class.values()),
    }
    totals["precision"] = totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else 0.0
    totals["recall"] = totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else 0.0
    return {"iou_threshold": iou_threshold, "per_class": metrics, "overall": totals}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare/evaluate YOLO symptom detector experiment")
    sub = parser.add_subparsers(dest="command", required=True)
    convert = sub.add_parser("convert")
    convert.add_argument("--annotations", required=True)
    convert.add_argument("--out", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--ground-truth", required=True)
    evaluate.add_argument("--predictions", required=True)
    evaluate.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.command == "convert":
        grouped = convert_annotations_to_yolo(args.annotations, args.out)
        print(f"Wrote YOLO labels for {len(grouped)} image(s)")
    else:
        metrics = evaluate_predictions(args.ground_truth, args.predictions)
        Path(args.out).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

