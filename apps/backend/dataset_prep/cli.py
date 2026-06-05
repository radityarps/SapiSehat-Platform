"""
Dataset-preparation CLI (issue #18).

Runs the full pipeline against a USER-PROVIDED dataset path and writes
reviewable artifacts. It does NOT download, commit, or train on data.

The real dataset is NOT in this repo. To obtain it (run OUTSIDE the repo so
images are never committed):

    curl -L "https://universe.roboflow.com/ds/amv0l3zlRz?key=g1mJgO3LIj" > roboflow.zip
    unzip roboflow.zip
    rm roboflow.zip

Then:

    python -m dataset_prep.cli --data /path/to/dataset --out ./dataset_artifacts

Layouts supported:
  - Class folders directly:   <data>/FMD/*.jpg, <data>/LSD/*.jpg, <data>/healthy/*.jpg
  - Roboflow split folders:   <data>/train/FMD/*.jpg, <data>/test/...  (source
    split is flattened; a fresh fixed-seed split is generated)
"""

from __future__ import annotations

import argparse
import sys

from . import artifacts
from .core import (
    DEFAULT_SEED,
    DEFAULT_SPLIT,
    discover_images,
    group_exact_duplicates,
    group_near_duplicates,
    stratified_split,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dataset_prep",
        description="Prepare and validate the cattle-disease dataset "
        "(canonical classes 0=FMD, 1=LSD, 2=healthy). Operates on a "
        "user-provided dataset path; no images are committed or downloaded.",
    )
    p.add_argument(
        "--data",
        required=True,
        help="Path to the dataset root (class folders or Roboflow "
        "train/valid/test layout).",
    )
    p.add_argument(
        "--out",
        default="dataset_artifacts",
        help="Output directory for generated artifacts (default: dataset_artifacts).",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for the stratified split (default: {DEFAULT_SEED}).",
    )
    p.add_argument(
        "--near-dup-threshold",
        type=int,
        default=5,
        help="Perceptual-hash Hamming distance threshold for near-duplicates "
        "(default: 5). Lower = stricter.",
    )
    p.add_argument(
        "--expert-audit",
        action="store_true",
        help="Set when a veterinarian/animal-health-officer label audit HAS "
        "been performed (otherwise the report documents its absence as a "
        "limitation).",
    )
    p.add_argument(
        "--fixture",
        action="store_true",
        help="Mark generated reports as fixture/demo data (used by tests).",
    )
    return p


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        records, unknown = discover_images(args.data)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(
            "Provide a valid dataset path with --data. The real dataset is "
            "not bundled in this repository; download it separately (see "
            "module docstring) and pass its path.",
            file=sys.stderr,
        )
        return 2

    if not records:
        print(
            "ERROR: No labeled images were discovered under "
            f"'{args.data}'.",
            file=sys.stderr,
        )
        if unknown:
            print(
                "Unmapped folders found: " + ", ".join(unknown),
                file=sys.stderr,
            )
        print(
            "Expected class folders named like FMD/PMK, LSD/Lato-Lato, "
            "healthy/Sehat (optionally nested under train/valid/test).",
            file=sys.stderr,
        )
        return 3

    ratios = DEFAULT_SPLIT

    # Pipeline: exact dup hashing -> near-dup grouping -> stratified split.
    group_exact_duplicates(records)
    group_near_duplicates(records, threshold=args.near_dup_threshold)
    stratified_split(records, ratios=ratios, seed=args.seed)

    written = artifacts.generate_all(
        args.out,
        records,
        data_dir=args.data,
        seed=args.seed,
        ratios=ratios,
        near_dup_threshold=args.near_dup_threshold,
        unknown_labels=unknown,
        expert_audit=args.expert_audit,
        is_fixture=args.fixture,
    )

    print(f"Discovered {len(records)} labeled images.")
    if unknown:
        print(f"Skipped {len(unknown)} unmapped folder(s): {', '.join(unknown)}")
    print(f"Artifacts written to '{args.out}':")
    for name, path in written.items():
        print(f"  - {name}: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
