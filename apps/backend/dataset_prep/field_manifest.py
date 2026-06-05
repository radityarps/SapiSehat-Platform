"""Field data manifest validation for real-world reliability work (#26).

This module validates metadata only. It never reads or copies field images.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

DISEASE_CLASSES = {"FMD", "LSD", "healthy"}
HARD_NEGATIVE = "hard_negative"
LABEL_TIERS = {"expert_reviewed", "researcher_reviewed", "farmer_weak"}
REVIEWER_ROLES = {"veterinarian", "animal_health_officer", "researcher", "farmer"}
ELIGIBILITY_VALUES = {"include", "exclude"}
REQUIRED_COLUMNS = [
    "image_id",
    "image_path",
    "source_session_id",
    "field_source",
    "disease_class",
    "is_hard_negative",
    "label_tier",
    "reviewer_role",
    "reviewer_id",
    "review_date",
    "review_notes",
    "train_eligible",
    "validation_eligible",
    "test_eligible",
    "scan_history_record_id",
]


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]
    target_counts: dict[str, int]

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_true(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def _is_include(value: str) -> bool:
    return value.strip().lower() == "include"


def validate_rows(rows: list[dict[str, str]]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    target_counts = {"FMD": 0, "LSD": 0, "healthy": 0, HARD_NEGATIVE: 0}
    seen_ids: set[str] = set()

    for row_number, row in enumerate(rows, start=2):
        prefix = f"row {row_number}"
        image_id = row.get("image_id", "").strip()
        if not image_id:
            errors.append(f"{prefix}: image_id is required")
        elif image_id in seen_ids:
            errors.append(f"{prefix}: duplicate image_id '{image_id}'")
        seen_ids.add(image_id)

        label_tier = row.get("label_tier", "").strip()
        reviewer_role = row.get("reviewer_role", "").strip()
        disease_class = row.get("disease_class", "").strip()
        hard_negative = _is_true(row.get("is_hard_negative", ""))

        if label_tier not in LABEL_TIERS:
            errors.append(f"{prefix}: label_tier must be one of {sorted(LABEL_TIERS)}")
        if reviewer_role not in REVIEWER_ROLES:
            errors.append(f"{prefix}: reviewer_role must be one of {sorted(REVIEWER_ROLES)}")

        if hard_negative:
            if disease_class:
                errors.append(f"{prefix}: hard-negative rows must leave disease_class empty")
            target_counts[HARD_NEGATIVE] += 1
        else:
            if disease_class not in DISEASE_CLASSES:
                errors.append(f"{prefix}: disease_class must be FMD, LSD, or healthy")
            elif label_tier == "expert_reviewed":
                target_counts[disease_class] += 1

        train = row.get("train_eligible", "").strip().lower()
        valid = row.get("validation_eligible", "").strip().lower()
        test = row.get("test_eligible", "").strip().lower()
        for field_name, value in (
            ("train_eligible", train),
            ("validation_eligible", valid),
            ("test_eligible", test),
        ):
            if value not in ELIGIBILITY_VALUES:
                errors.append(f"{prefix}: {field_name} must be include or exclude")

        if label_tier != "expert_reviewed" and (_is_include(valid) or _is_include(test)):
            errors.append(
                f"{prefix}: validation/test eligibility requires expert_reviewed label tier"
            )
        if label_tier == "farmer_weak" and not _is_include(train):
            warnings.append(f"{prefix}: farmer weak label recorded but not training-eligible")

        if row.get("scan_history_record_id", "").strip():
            warnings.append(
                f"{prefix}: Scan History reference is metadata only; row is training data only after this manifest review"
            )

    for key, count in target_counts.items():
        if count < 50:
            warnings.append(f"target not met: {key} has {count}/50 expert-reviewed entries")

    return ValidationResult(errors=errors, warnings=warnings, target_counts=target_counts)


def validate_manifest(path: str | Path) -> ValidationResult:
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            return ValidationResult(
                errors=[f"missing required columns: {', '.join(missing)}"],
                warnings=[],
                target_counts={"FMD": 0, "LSD": 0, "healthy": 0, HARD_NEGATIVE: 0},
            )
        return validate_rows(list(reader))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Local Field Image manifest metadata")
    parser.add_argument("manifest", help="Path to field_manifest.csv")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_manifest(args.manifest)
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print("Target counts:")
    for key, value in result.target_counts.items():
        print(f"  {key}: {value}/50")
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

