"""Symptom-region annotation validation for two-stage field work (#27)."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

DISEASE_CLASSES = {"FMD", "LSD"}
ALL_CLASSES = {"FMD", "LSD", "healthy"}
SYMPTOM_CATEGORIES = {"fmd_mouth_lesion", "fmd_hoof_lesion", "lsd_skin_nodule", "confusing_region"}
REQUIRED_COLUMNS = [
    "image_id",
    "disease_class",
    "is_hard_negative",
    "annotation_id",
    "symptom_category",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "annotator_id",
    "review_status",
    "review_notes",
]


@dataclass(frozen=True)
class AnnotationValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "").strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def validate_rows(rows: list[dict[str, str]]) -> AnnotationValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    boxes_by_image: dict[str, int] = {}
    seen_annotation_ids: set[str] = set()
    classes_by_image: dict[str, set[str]] = {}

    for row_number, row in enumerate(rows, start=2):
        prefix = f"row {row_number}"
        image_id = row.get("image_id", "").strip()
        disease_class = row.get("disease_class", "").strip()
        hard_negative = _is_true(row.get("is_hard_negative", ""))
        annotation_id = row.get("annotation_id", "").strip()
        category = row.get("symptom_category", "").strip()

        if not image_id:
            errors.append(f"{prefix}: image_id is required")
        if disease_class not in ALL_CLASSES and not hard_negative:
            errors.append(f"{prefix}: disease_class must be FMD, LSD, or healthy")
        if annotation_id:
            if annotation_id in seen_annotation_ids:
                errors.append(f"{prefix}: duplicate annotation_id '{annotation_id}'")
            seen_annotation_ids.add(annotation_id)

        classes_by_image.setdefault(image_id, set()).add(disease_class or "hard_negative")

        has_box = bool(annotation_id or category or row.get("x_min", "").strip())
        if disease_class == "healthy" and has_box:
            errors.append(f"{prefix}: healthy images must not have fake symptom-region boxes")
        if hard_negative and disease_class == "healthy":
            errors.append(f"{prefix}: hard-negative is not confirmed healthy")

        if not has_box:
            continue

        boxes_by_image[image_id] = boxes_by_image.get(image_id, 0) + 1
        if category not in SYMPTOM_CATEGORIES:
            errors.append(f"{prefix}: symptom_category must be one of {sorted(SYMPTOM_CATEGORIES)}")
        if disease_class == "FMD" and category not in {"fmd_mouth_lesion", "fmd_hoof_lesion", "confusing_region"}:
            errors.append(f"{prefix}: FMD boxes must use mouth/hoof lesion categories")
        if disease_class == "LSD" and category not in {"lsd_skin_nodule", "confusing_region"}:
            errors.append(f"{prefix}: LSD boxes must use skin nodule category")
        if hard_negative and category != "confusing_region":
            errors.append(f"{prefix}: hard-negative boxes may only mark confusing_region")

        coords = {name: _float(row, name) for name in ("x_min", "y_min", "x_max", "y_max")}
        if any(value is None for value in coords.values()):
            errors.append(f"{prefix}: box coordinates are required numbers")
        else:
            x_min = coords["x_min"] or 0.0
            y_min = coords["y_min"] or 0.0
            x_max = coords["x_max"] or 0.0
            y_max = coords["y_max"] or 0.0
            if not (0.0 <= x_min < x_max <= 1.0 and 0.0 <= y_min < y_max <= 1.0):
                errors.append(f"{prefix}: coordinates must be normalized with x_min < x_max and y_min < y_max")

    for image_id, classes in classes_by_image.items():
        if len(classes) > 1:
            warnings.append(f"image {image_id}: multiple disease classes across annotation rows: {sorted(classes)}")
    disease_images = {
        row.get("image_id", "").strip()
        for row in rows
        if row.get("disease_class", "").strip() in DISEASE_CLASSES and not _is_true(row.get("is_hard_negative", ""))
    }
    for image_id in sorted(disease_images):
        if boxes_by_image.get(image_id, 0) == 0:
            errors.append(f"image {image_id}: disease field image requires at least one symptom-region box")

    return AnnotationValidationResult(errors=errors, warnings=warnings)


def validate_manifest(path: str | Path) -> AnnotationValidationResult:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return AnnotationValidationResult(errors=[f"missing required columns: {', '.join(missing)}"], warnings=[])
        return validate_rows(list(reader))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate symptom-region annotation manifest")
    parser.add_argument("manifest", help="Path to symptom_region_annotations.csv")
    args = parser.parse_args(argv)
    result = validate_manifest(args.manifest)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if result.ok:
        print("Annotation manifest valid")
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

