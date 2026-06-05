"""
Artifact generation for the dataset-preparation package.

Writes the reviewable outputs required by issue #18:
  - class_indices.json
  - split_manifest.csv
  - class_weights.json
  - DATASET_SPLIT_REPORT.md
  - LABEL_VALIDATION.md

All reports accept a `is_fixture` flag. When True, reports are clearly marked
as fixture/demo data (NOT real training data), per the issue requirements.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone

from .core import (
    CANONICAL_CLASSES,
    CLASS_TO_INDEX,
    ImageRecord,
    PERCEPTUAL_HASH_BACKEND,
    compute_class_weights,
    split_counts,
)

CLASS_INDICES_FILE = "class_indices.json"
SPLIT_MANIFEST_FILE = "split_manifest.csv"
CLASS_WEIGHTS_FILE = "class_weights.json"
SPLIT_REPORT_FILE = "DATASET_SPLIT_REPORT.md"
LABEL_VALIDATION_FILE = "LABEL_VALIDATION.md"


def _fixture_banner(is_fixture: bool) -> str:
    if is_fixture:
        return (
            "> ⚠️ **FIXTURE / DEMO DATA — NOT REAL TRAINING DATA.**\n"
            "> This report was generated from tiny synthetic fixture images "
            "created by the test suite. The numbers below are for pipeline "
            "verification only and must not be cited as dataset statistics or "
            "model evaluation results.\n"
        )
    return (
        "> Generated from a user-provided dataset path. No dataset images are "
        "committed to the repository.\n"
    )


def write_class_indices(out_dir: str) -> str:
    path = os.path.join(out_dir, CLASS_INDICES_FILE)
    data = {str(CLASS_TO_INDEX[c]): c for c in CANONICAL_CLASSES}
    # Also include name->index for convenience.
    data_full = {
        "index_to_class": {str(CLASS_TO_INDEX[c]): c for c in CANONICAL_CLASSES},
        "class_to_index": {c: CLASS_TO_INDEX[c] for c in CANONICAL_CLASSES},
        "canonical_order": CANONICAL_CLASSES,
        "note": "Canonical order is fixed: 0=FMD, 1=LSD, 2=healthy.",
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data_full, f, indent=2)
    return path


def write_split_manifest(out_dir: str, records: list[ImageRecord]) -> str:
    path = os.path.join(out_dir, SPLIT_MANIFEST_FILE)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "filename",
                "relpath",
                "canonical_class",
                "class_index",
                "raw_label",
                "split",
                "group_id",
                "file_hash",
                "perceptual_hash",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r.filename,
                    r.path,
                    r.canonical_class,
                    r.class_index,
                    r.raw_label,
                    r.split,
                    r.group_id,
                    r.file_hash,
                    r.perceptual_hash,
                ]
            )
    return path


def write_class_weights(out_dir: str, records: list[ImageRecord]) -> str:
    path = os.path.join(out_dir, CLASS_WEIGHTS_FILE)
    weights = compute_class_weights(records)
    payload = {
        "method": "balanced: total_train / (num_classes * count_class)",
        "computed_from": "train split only",
        "note": "Validation/test splits are NOT oversampled or reweighted.",
        "weights_by_class": weights,
        "weights_by_index": {
            str(CLASS_TO_INDEX[c]): weights[c] for c in CANONICAL_CLASSES
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def write_split_report(
    out_dir: str,
    records: list[ImageRecord],
    *,
    data_dir: str,
    seed: int,
    ratios: tuple[float, float, float],
    near_dup_threshold: int,
    is_fixture: bool,
) -> str:
    path = os.path.join(out_dir, SPLIT_REPORT_FILE)
    counts = split_counts(records)
    weights = compute_class_weights(records)

    total = len(records)
    n_groups = len({r.group_id for r in records})
    n_exact_dups = total - len({r.file_hash for r in records})

    lines: list[str] = []
    lines.append("# Dataset Split Report")
    lines.append("")
    lines.append(_fixture_banner(is_fixture))
    lines.append("")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"- Source path: `{data_dir}`")
    lines.append(f"- Random seed: `{seed}` (fixed for reproducibility)")
    lines.append(
        f"- Split ratios: train={ratios[0]:.2f}, valid={ratios[1]:.2f}, test={ratios[2]:.2f}"
    )
    lines.append(f"- Perceptual-hash backend: `{PERCEPTUAL_HASH_BACKEND}`")
    lines.append(f"- Near-duplicate Hamming threshold: `{near_dup_threshold}`")
    lines.append("")
    lines.append("## Canonical class mapping")
    lines.append("")
    lines.append("| Index | Class |")
    lines.append("|-------|-------|")
    for c in CANONICAL_CLASSES:
        lines.append(f"| {CLASS_TO_INDEX[c]} | {c} |")
    lines.append("")
    lines.append("## Totals")
    lines.append("")
    lines.append(f"- Total images discovered: **{total}**")
    lines.append(f"- Exact duplicate images (by file hash): **{n_exact_dups}**")
    lines.append(
        f"- Duplicate groups (exact + near, kept together in one split): **{n_groups}**"
    )
    lines.append("")
    lines.append("## Per-split, per-class support counts")
    lines.append("")
    header = "| Split | " + " | ".join(CANONICAL_CLASSES) + " | Total |"
    sep = "|-------|" + "|".join(["-------"] * len(CANONICAL_CLASSES)) + "|-------|"
    lines.append(header)
    lines.append(sep)
    for split in ("train", "valid", "test"):
        row_counts = counts[split]
        row_total = sum(row_counts.values())
        row = (
            f"| {split} | "
            + " | ".join(str(row_counts[c]) for c in CANONICAL_CLASSES)
            + f" | {row_total} |"
        )
        lines.append(row)
    grand_total = sum(sum(counts[s].values()) for s in counts)
    lines.append(f"| **all** | " + " | ".join(
        str(sum(counts[s][c] for s in counts)) for c in CANONICAL_CLASSES
    ) + f" | {grand_total} |")
    lines.append("")
    lines.append("## Train-split class weights (imbalance handling)")
    lines.append("")
    lines.append("Balanced weights computed from the **train split only**. "
                 "Validation/test are not oversampled.")
    lines.append("")
    lines.append("| Class | Weight |")
    lines.append("|-------|--------|")
    for c in CANONICAL_CLASSES:
        lines.append(f"| {c} | {weights[c]} |")
    lines.append("")
    lines.append("## Leakage guarantee")
    lines.append("")
    lines.append(
        "- Exact and near-duplicate images are merged into duplicate groups by "
        "file hash and perceptual hash."
    )
    lines.append(
        "- Each duplicate group is assigned to exactly one split, so the same "
        "(or visually near-identical) image cannot appear in more than one of "
        "train / validation / test."
    )
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def write_label_validation(
    out_dir: str,
    records: list[ImageRecord],
    *,
    unknown_labels: list[str],
    expert_audit: bool,
    is_fixture: bool,
) -> str:
    path = os.path.join(out_dir, LABEL_VALIDATION_FILE)

    # Retained source labels -> canonical class.
    raw_to_canonical: dict[str, str] = {}
    for r in records:
        raw_to_canonical.setdefault(r.raw_label, r.canonical_class)

    lines: list[str] = []
    lines.append("# Label Validation Report")
    lines.append("")
    lines.append(_fixture_banner(is_fixture))
    lines.append("")
    lines.append("## Retained source labels")
    lines.append("")
    lines.append("Source folder labels that were accepted and mapped to a "
                 "canonical class:")
    lines.append("")
    if raw_to_canonical:
        lines.append("| Source label | Canonical class |")
        lines.append("|--------------|-----------------|")
        for raw in sorted(raw_to_canonical):
            lines.append(f"| `{raw}` | {raw_to_canonical[raw]} |")
    else:
        lines.append("_No labeled images were discovered._")
    lines.append("")

    lines.append("## Researcher review removals")
    lines.append("")
    if unknown_labels:
        lines.append(
            "The following source folders could NOT be mapped to a canonical "
            "class and were excluded from the split. A researcher must review "
            "whether these contain valid images that need relabeling:"
        )
        lines.append("")
        for u in unknown_labels:
            lines.append(f"- `{u}` (unmapped — excluded)")
    else:
        lines.append(
            "No folders were excluded for unmappable labels. (Automatic "
            "exclusions are limited to unmapped folders; manual researcher "
            "removals of individual mislabeled images should be recorded here "
            "as they occur.)"
        )
    lines.append("")

    lines.append("## Veterinarian / animal-health-officer sample audit")
    lines.append("")
    if expert_audit:
        lines.append(
            "An expert audit flag was provided. Record the auditor, date, "
            "sample size, and outcomes here."
        )
    else:
        lines.append(
            "> **LIMITATION — NO EXPERT AUDIT PERFORMED.**\n"
            "> No veterinarian or animal-health-officer label audit has been "
            "conducted on this dataset. Labels are taken as-is from the public "
            "source folders. This is documented as a known limitation and has "
            "**not** been fabricated. Before any clinical or field claim, a "
            "qualified expert should audit a representative sample of each class."
        )
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def generate_all(
    out_dir: str,
    records: list[ImageRecord],
    *,
    data_dir: str,
    seed: int,
    ratios: tuple[float, float, float],
    near_dup_threshold: int,
    unknown_labels: list[str],
    expert_audit: bool,
    is_fixture: bool,
) -> dict[str, str]:
    """Generate all artifacts; returns {artifact_name: path}."""
    os.makedirs(out_dir, exist_ok=True)
    return {
        CLASS_INDICES_FILE: write_class_indices(out_dir),
        SPLIT_MANIFEST_FILE: write_split_manifest(out_dir, records),
        CLASS_WEIGHTS_FILE: write_class_weights(out_dir, records),
        SPLIT_REPORT_FILE: write_split_report(
            out_dir,
            records,
            data_dir=data_dir,
            seed=seed,
            ratios=ratios,
            near_dup_threshold=near_dup_threshold,
            is_fixture=is_fixture,
        ),
        LABEL_VALIDATION_FILE: write_label_validation(
            out_dir,
            records,
            unknown_labels=unknown_labels,
            expert_audit=expert_audit,
            is_fixture=is_fixture,
        ),
    }
