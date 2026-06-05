# Dataset Preparation Package (issue #18)

Reproducible dataset preparation and label-validation tooling for the SapiSehat
cattle-disease classifier. It enforces the canonical class mapping, removes
duplicate-induced leakage, builds a fixed-seed stratified 70/15/15 split, and
emits reviewable audit artifacts — so the dataset can be verified **before** any
expensive Kaggle/Colab training run.

> **No real dataset images are committed to this repository.** This package
> operates on a dataset path you provide at runtime.

## Get the dataset (run OUTSIDE the repo)

```bash
curl -L "https://universe.roboflow.com/ds/amv0l3zlRz?key=g1mJgO3LIj" > roboflow.zip
unzip roboflow.zip
rm roboflow.zip
```

Keep the extracted images outside the repo (or in a git-ignored path) so they
are never committed.

## Run

```bash
cd apps/backend
python -m dataset_prep.cli --data /path/to/dataset --out ./dataset_artifacts
```

If `--data` is missing or empty, the CLI exits with a clear, non-zero error.

### Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--data` | (required) | Dataset root path |
| `--out` | `dataset_artifacts` | Output directory for artifacts |
| `--seed` | `42` | Fixed seed for reproducible split |
| `--near-dup-threshold` | `5` | Perceptual-hash Hamming threshold (lower = stricter) |
| `--expert-audit` | off | Set only if a vet/animal-health-officer audit was actually done |
| `--fixture` | off | Mark reports as fixture/demo data (used by tests) |

## Supported layouts

- **Roboflow classification export (`_classes.csv`):** images directly inside
  `train/`, `valid/`, `test/` (or the root) with a `_classes.csv` whose header
  is `filename,FMD,LSD,healthy` and one-hot rows. Detected first. Multi-label or
  no-label rows are reported in the validation report and skipped.
- **Direct class folders:** `<data>/FMD/*.jpg`, `<data>/LSD/*.jpg`, `<data>/healthy/*.jpg`
- **Roboflow split folders:** `<data>/train/FMD/*.jpg`, `<data>/test/...`

Source split folders (`train/valid/test`) are flattened — a fresh fixed-seed
split is always generated. Common aliases are mapped to canonical names:
PMK→FMD, Lato-Lato/Lumpy Skin Disease→LSD, Sehat→healthy.

## Canonical class order (fixed)

| Index | Class |
|-------|-------|
| 0 | FMD |
| 1 | LSD |
| 2 | healthy |

## Generated artifacts

| File | Description |
|------|-------------|
| `class_indices.json` | Canonical index↔class mapping |
| `split_manifest.csv` | Per-image split assignment, group id, hashes |
| `class_weights.json` | Balanced train-split class weights |
| `DATASET_SPLIT_REPORT.md` | Split audit: per-class support, duplicates, leakage guarantee |
| `LABEL_VALIDATION.md` | Retained labels, researcher removals, expert-audit status |

## Local Field Image manifest workflow

Issue #26 adds a metadata-only workflow for reviewed field data. Scan History
records are **not** training data by default; a record becomes a dataset
candidate only after it is copied into a reviewed Local Field Image manifest
with explicit label tier, reviewer role, review notes, source/session grouping,
and dataset eligibility.

See:

- `docs/model/FIELD_DATA_MANIFEST.md`
- `docs/model/templates/field_manifest_example.csv`

Validate a manifest:

```bash
cd apps/backend
python -m dataset_prep.field_manifest ../../docs/model/templates/field_manifest_example.csv
```

## Symptom-region annotation protocol

Issue #27 adds the annotation protocol for future two-stage server experiments.
Disease field images need tight bounding boxes around visible symptom regions;
healthy field images keep image-level labels without fake boxes; hard negatives
may optionally mark confusing regions for threshold/error analysis.

See:

- `docs/model/SYMPTOM_REGION_ANNOTATION_PROTOCOL.md`
- `docs/model/templates/symptom_region_annotations_example.csv`

Validate annotation rows:

```bash
cd apps/backend
python -m dataset_prep.symptom_annotations ../../docs/model/templates/symptom_region_annotations_example.csv
```

## Leakage prevention

Exact duplicates (SHA-256 file hash) and near-duplicates (perceptual hash,
Hamming distance ≤ threshold) are merged into duplicate **groups**. Each group
is assigned to exactly one split, so identical/near-identical images never span
train/validation/test.

## Perceptual hashing

- If the optional [`imagehash`](https://pypi.org/project/ImageHash/) package is
  installed, `imagehash.phash` (DCT-based) is used.
- Otherwise a deterministic **average-hash (aHash)** fallback built on
  Pillow + numpy is used.

  **Limitation:** aHash is simpler than pHash. It reliably catches
  resized/recompressed copies and minor edits, but is more sensitive to large
  crops or strong color shifts. Install `imagehash` for stronger near-duplicate
  detection. The active backend is recorded in `DATASET_SPLIT_REPORT.md`.

## Limitations & non-goals

- **No training.** This package never trains a model or computes model metrics.
- **No expert audit by default.** Labels come as-is from the public source.
  `LABEL_VALIDATION.md` documents the absence of a veterinarian/animal-health-
  officer audit as a limitation — it is **not** fabricated. Pass `--expert-audit`
  only when a real audit has been performed and record its details.
- **Class imbalance:** handled via train-split class weights only; validation
  and test splits are never oversampled.

## Tests

```bash
cd apps/backend
python -m pytest tests/test_dataset_prep.py -v
```

Tests generate tiny synthetic fixture images at runtime (no real data) and
verify class mapping, discovery, duplicate detection, split reproducibility,
no cross-split overlap, class weights, and artifact generation.
