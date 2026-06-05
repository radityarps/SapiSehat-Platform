"""
Training Wrapper (issue #19).

Makes the model-training workflow runnable on Kaggle (primary), Google Colab
(fallback), and locally — while keeping `docs/model/evaluate_candidates.py` as
the single source of truth. Kaggle/Colab notebooks are thin wrappers that call
THIS module, which in turn invokes the repo training/evaluation script.

Responsibilities:
  - Resolve a model version string:  cattle-disease-{architecture}-vYYYYMMDD-s{seed}
  - Record runtime metadata (platform, TensorFlow version, seed, dataset
    version/source, training date).
  - Invoke the repo evaluation script (unless --dry-run).
  - Package outputs into a versioned bundle:
        model_training_artifacts_<version>.zip
    containing reports, metrics, preprocessing config, model exports, manifests.

Dry-run mode performs everything EXCEPT the GPU training: it validates
arguments, computes paths/metadata, writes a manifest, and packages whatever
artifacts exist. This lets tests/CI verify the wrapper without a GPU or dataset.

Usage
-----
    # Local dry run (no training, no dataset required):
    python training_wrapper.py --dry-run --architecture mobilenetv2 --seed 42 \
        --out ./run_out

    # Real run (Kaggle/Colab/local with GPU + dataset):
    python training_wrapper.py --data /path/to/dataset \
        --architecture mobilenetv2 --seed 42 --epochs 50 --out ./run_out
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# The single source-of-truth training/evaluation script.
SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_SCRIPT = SCRIPT_DIR / "evaluate_candidates.py"

VALID_ARCHITECTURES = ["custom_cnn", "mobilenetv2", "densenet121"]

# Files the repo script produces that belong in the bundle (best-effort: only
# those that actually exist are added).
BUNDLE_GLOBS = [
    "*_metrics.json",
    "*.keras",
    "*_confusion_matrix.png",
    "comparison_summary.json",
    "preprocessing.json",
    "run_config.json",
]

# Issue #18 dataset-prep artifacts to include in the bundle when available
# (copied from the manifest's directory).
DATASET_PREP_ARTIFACTS = [
    "split_manifest.csv",
    "DATASET_SPLIT_REPORT.md",
    "LABEL_VALIDATION.md",
    "class_indices.json",
    "class_weights.json",
]


def detect_platform() -> str:
    """Best-effort detection of Kaggle / Colab / local."""
    if os.path.exists("/kaggle") or os.environ.get("KAGGLE_KERNEL_RUN_TYPE"):
        return "kaggle"
    if "google.colab" in sys.modules or os.path.exists("/content"):
        return "colab"
    return "local"


def detect_tf_version() -> str:
    try:  # pragma: no cover - exercised only when TF installed
        import tensorflow as tf

        return tf.__version__
    except Exception:
        return "not-installed"


def make_version(architecture: str, seed: int, date: datetime | None = None) -> str:
    """Model version pattern: cattle-disease-{architecture}-vYYYYMMDD-s{seed}."""
    d = (date or datetime.now(timezone.utc)).strftime("%Y%m%d")
    return f"cattle-disease-{architecture}-v{d}-s{seed}"


def dataset_version(data_dir: str | None) -> dict:
    """Summarize dataset source/version without copying images."""
    if not data_dir:
        return {"source": None, "exists": False, "note": "dry-run: no dataset"}
    return {
        "source": data_dir,
        "exists": os.path.isdir(data_dir),
        "note": "User-provided dataset path; images are not committed.",
    }


def build_metadata(args, version: str) -> dict:
    return {
        "model_version": version,
        "architecture": args.architecture,
        "seed": args.seed,
        "epochs": args.epochs,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "platform": detect_platform(),
        "python_version": platform.python_version(),
        "tensorflow_version": detect_tf_version(),
        "data_source_mode": "prepared_split_manifest" if args.manifest else "source_folders",
        "split_manifest": args.manifest,
        "dataset": dataset_version(args.data),
        "source_of_truth_script": str(EVAL_SCRIPT.relative_to(SCRIPT_DIR.parent.parent))
        if str(EVAL_SCRIPT).startswith(str(SCRIPT_DIR.parent.parent))
        else str(EVAL_SCRIPT),
        "dry_run": bool(args.dry_run),
    }


def run_training(args, out_dir: Path) -> int:
    """Invoke the source-of-truth evaluation script. Returns its exit code."""
    cmd = [sys.executable, str(EVAL_SCRIPT)]
    if args.manifest:
        # PREFERRED: train/eval from the approved fixed-seed 70/15/15 split.
        cmd += ["--manifest", args.manifest]
    else:
        cmd += ["--data", args.data]
    cmd += [
        "--epochs", str(args.epochs),
        "--seed", str(args.seed),
        "--out", str(out_dir),
        "--models", args.architecture,
    ]
    print(f"[wrapper] invoking source-of-truth script:\n  {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def copy_dataset_prep_artifacts(manifest_path: str | None, out_dir: Path) -> list[Path]:
    """
    Copy issue #18 dataset-prep artifacts (split manifest, reports) next to the
    run outputs so they are included in the bundle. Returns copied paths.
    """
    copied: list[Path] = []
    if not manifest_path:
        return copied
    import shutil

    manifest_dir = Path(manifest_path).resolve().parent
    for name in DATASET_PREP_ARTIFACTS:
        src = manifest_dir / name
        if src.is_file():
            dst = out_dir / name
            if src.resolve() != dst.resolve():
                shutil.copy2(src, dst)
            copied.append(dst)
    return copied


def collect_bundle_files(out_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in BUNDLE_GLOBS:
        files.extend(sorted(out_dir.glob(pattern)))
    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for f in files:
        if f not in seen and f.is_file():
            seen.add(f)
            unique.append(f)
    return unique


def write_bundle_manifest(out_dir: Path, version: str, metadata: dict,
                          bundle_files: list[Path]) -> Path:
    manifest = {
        "model_version": version,
        "metadata": metadata,
        "artifacts": [f.name for f in bundle_files],
        "artifact_count": len(bundle_files),
        "generated": datetime.now(timezone.utc).isoformat(),
    }
    path = out_dir / "bundle_manifest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


def package_bundle(out_dir: Path, version: str, extra_files: list[Path]) -> Path:
    """Zip the bundle into model_training_artifacts_<version>.zip in out_dir."""
    zip_path = out_dir / f"model_training_artifacts_{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in extra_files:
            if f.is_file() and f.resolve() != zip_path.resolve():
                zf.write(f, arcname=f.name)
    return zip_path


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="training_wrapper",
        description="Kaggle/Colab/local wrapper around the repo training "
        "script. Records metadata and packages a versioned artifact bundle.",
    )
    p.add_argument("--manifest", default=None,
                   help="Path to issue #18 split_manifest.csv (PREFERRED: "
                   "uses the approved fixed-seed 70/15/15 split). When given, "
                   "the dataset-prep artifacts next to it are bundled.")
    p.add_argument("--data", default=None,
                   help="Dataset path (folder fallback; required unless "
                   "--manifest or --dry-run).")
    p.add_argument("--architecture", default="mobilenetv2",
                   choices=VALID_ARCHITECTURES,
                   help="Model candidate to train (default: mobilenetv2).")
    p.add_argument("--seed", type=int, default=42,
                   help="Fixed random seed (default: 42).")
    p.add_argument("--epochs", type=int, default=50,
                   help="Training epochs (default: 50).")
    p.add_argument("--out", default="run_out",
                   help="Output directory for artifacts + bundle.")
    p.add_argument("--dry-run", action="store_true",
                   help="Skip GPU training; still produce metadata, manifest, "
                   "and a (possibly minimal) bundle. For tests/CI.")
    return p


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.manifest and args.data:
        print("ERROR: pass either --manifest or --data, not both.",
              file=sys.stderr)
        return 2
    if not args.dry_run and not args.manifest and not args.data:
        print("ERROR: --manifest or --data is required unless --dry-run is set.",
              file=sys.stderr)
        return 2
    if args.manifest and not os.path.isfile(args.manifest):
        print(f"ERROR: split manifest not found: {args.manifest}",
              file=sys.stderr)
        return 2
    if args.data and not args.dry_run and not os.path.isdir(args.data):
        print(f"ERROR: dataset path not found: {args.data}", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    version = make_version(args.architecture, args.seed)
    metadata = build_metadata(args, version)

    # Always write runtime metadata first so it is captured even if training fails.
    meta_path = out_dir / "runtime_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[wrapper] model version: {version}")
    print(f"[wrapper] platform: {metadata['platform']}  "
          f"TF: {metadata['tensorflow_version']}")
    print(f"[wrapper] runtime metadata -> {meta_path}")

    if args.dry_run:
        print("[wrapper] DRY RUN — skipping training. Validating wrapper only.")
    else:
        rc = run_training(args, out_dir)
        if rc != 0:
            print(f"[wrapper] training script exited with code {rc}", file=sys.stderr)
            return rc

    # Include issue #18 dataset-prep artifacts (split manifest + reports) in the
    # bundle when running in prepared-split mode. Done in both dry-run and real
    # runs so CI can verify the prepared-split path is bundled.
    copied_prep = copy_dataset_prep_artifacts(args.manifest, out_dir)
    if copied_prep:
        print(f"[wrapper] bundled {len(copied_prep)} dataset-prep artifact(s) "
              f"from {Path(args.manifest).resolve().parent}")
    elif args.manifest:
        print("[wrapper] WARNING: no dataset-prep artifacts found next to "
              f"{args.manifest}", file=sys.stderr)

    bundle_files = collect_bundle_files(out_dir)
    # runtime metadata is always part of the bundle.
    if meta_path not in bundle_files:
        bundle_files.insert(0, meta_path)
    # Dataset-prep artifacts (issue #18) may not match BUNDLE_GLOBS; add them.
    for f in copied_prep:
        if f not in bundle_files and f.is_file():
            bundle_files.append(f)
    manifest_path = write_bundle_manifest(out_dir, version, metadata, bundle_files)
    bundle_files.append(manifest_path)

    zip_path = package_bundle(out_dir, version, bundle_files)
    print(f"[wrapper] bundle manifest -> {manifest_path}")
    print(f"[wrapper] versioned bundle -> {zip_path}")
    print(f"[wrapper] bundle contains {len(bundle_files)} files.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(run())
