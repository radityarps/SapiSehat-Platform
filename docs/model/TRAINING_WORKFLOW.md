# Model Training Workflow (issue #19)

How to run the cattle-disease model training/evaluation on **Kaggle** (primary),
**Google Colab** (fallback), or **locally** — while keeping the repository
script as the single source of truth.

## Source of truth

```
docs/model/evaluate_candidates.py   # trains + evaluates candidates (the truth)
docs/model/training_wrapper.py       # thin wrapper: metadata + versioned bundle
docs/model/notebooks/kaggle_train.py # paste-into-Kaggle cell
docs/model/notebooks/colab_train.py  # paste-into-Colab cell
```

Notebooks contain **no training logic** — they only call
`training_wrapper.py`, which calls `evaluate_candidates.py`. There is no
secret-only notebook logic.

## What the wrapper does

1. Computes the model version: `cattle-disease-{architecture}-vYYYYMMDD-s{seed}`.
2. Records `runtime_metadata.json` (platform, TensorFlow version, seed, dataset
   source, `data_source_mode`, `split_manifest`, training date, python version,
   dry-run flag).
3. Invokes `evaluate_candidates.py` (unless `--dry-run`).
4. Packages a versioned bundle:
   `model_training_artifacts_<version>.zip` containing the metrics JSON, model
   exports (`.keras`), confusion-matrix PNGs, `comparison_summary.json`,
   `preprocessing.json`, `run_config.json`, `runtime_metadata.json`,
   `bundle_manifest.json`, and — in prepared-split mode — the issue #18
   dataset-prep artifacts (`split_manifest.csv`, `DATASET_SPLIT_REPORT.md`,
   `LABEL_VALIDATION.md`, `class_indices.json`, `class_weights.json`).

## Dataset (two modes)

The real dataset is **not** committed. Choose one input mode:

### Prepared split — `--manifest` (RECOMMENDED, issue #18 integration)

> **Path portability:** the `split_manifest.csv` stores absolute image paths. To
> run on Kaggle/Colab, generate the split **inside that runtime** so paths point
> at the local dataset — see [`KAGGLE_RUN_GUIDE.md`](KAGGLE_RUN_GUIDE.md) for the
> exact #20 three-candidate commands. The eval script fails fast if manifest
> paths are unreadable in the current environment.

Run the dataset-prep package first to produce the approved fixed-seed
stratified **70/15/15** split, then point the wrapper at the manifest:

```bash
cd apps/backend
python -m dataset_prep.cli --data "/path/to/dataset" --out dataset_artifacts
# produces dataset_artifacts/split_manifest.csv (+ reports)

python ../../docs/model/training_wrapper.py \
    --manifest dataset_artifacts/split_manifest.csv \
    --architecture mobilenetv2 --seed 42 --epochs 50 --out run_out
```

In this mode `evaluate_candidates.py`:

- trains on the **train** split (shuffled with the fixed `--seed`),
- uses the **valid** split for validation / early stopping,
- reports **final metrics on the held-out test split**,

so the raw Roboflow `train/valid` folders are never used and the documented
split is guaranteed. The dataset-prep artifacts sitting next to the manifest are
copied into the versioned bundle automatically.

### Folder fallback — `--data` (legacy)

For folder-classification training, `evaluate_candidates.py` expects
`<data>/train/<class>/...` and `<data>/valid/<class>/...` and computes final
metrics on the `valid` folder. Prefer `--manifest` so the approved split is
used instead of the raw source split.

## Kaggle (primary)

1. Notebook settings → Accelerator → **GPU**.
2. Clone the repo and add the dataset as a Kaggle input.
3. Paste `docs/model/notebooks/kaggle_train.py` into a cell, edit `DATA_DIR`,
   and run (it defaults to the prepared-split path). Or directly:

   ```bash
   !git clone https://github.com/radityarps/Tugas-Akhir-Klasifikasi-Penyakit-Sapi-CNN.git repo
   # Build the approved fixed-seed 70/15/15 split (issue #18):
   !cd repo/apps/backend && python -m dataset_prep.cli \
       --data /kaggle/input/pmk-dan-penyakit-lato-lato \
       --out /kaggle/working/dataset_artifacts
   # Train from the manifest (test split -> final metrics):
   !python repo/docs/model/training_wrapper.py \
       --manifest /kaggle/working/dataset_artifacts/split_manifest.csv \
       --architecture mobilenetv2 --seed 42 --epochs 50 \
       --out /kaggle/working/run_out
   ```

4. Download `model_training_artifacts_*.zip` from `/kaggle/working/run_out` and
   copy it back into the repo (e.g. `docs/model/artifacts/`).

## Google Colab (fallback)

1. Runtime → Change runtime type → **T4 GPU**.
2. Clone the repo; mount Drive or download the dataset into `/content/data`.
3. Paste `docs/model/notebooks/colab_train.py`, edit `DATA_DIR`, and run
   (defaults to the prepared-split path). Or:

   ```bash
   !git clone https://github.com/radityarps/Tugas-Akhir-Klasifikasi-Penyakit-Sapi-CNN.git repo
   !cd repo/apps/backend && python -m dataset_prep.cli \
       --data /content/data --out /content/dataset_artifacts
   !python repo/docs/model/training_wrapper.py \
       --manifest /content/dataset_artifacts/split_manifest.csv \
       --architecture mobilenetv2 --seed 42 --epochs 50 \
       --out /content/run_out
   ```

## Local dry run (no GPU, no dataset)

Validates the wrapper, metadata, manifest, and bundle packaging without
training. Used by CI/tests:

```bash
python docs/model/training_wrapper.py --dry-run \
    --architecture mobilenetv2 --seed 42 --out ./run_out
```

## Local real run

```bash
python docs/model/training_wrapper.py \
    --data /path/to/dataset --architecture mobilenetv2 --seed 42 --epochs 50 \
    --out ./run_out
```

## Arguments

| Flag | Default | Purpose |
|------|---------|---------|
| `--manifest` | (none) | Issue #18 `split_manifest.csv` — uses the approved fixed-seed 70/15/15 split (preferred). Mutually exclusive with `--data`. |
| `--data` | (none) | Dataset folder (legacy fallback). Required unless `--manifest` or `--dry-run`. |
| `--architecture` | `mobilenetv2` | `custom_cnn` / `mobilenetv2` / `densenet121` |
| `--seed` | `42` | Fixed seed for reproducibility (also seeds the train-split shuffle) |
| `--epochs` | `50` | Training epochs |
| `--out` | `run_out` | Output directory for artifacts + bundle |
| `--dry-run` | off | Skip training; still emit metadata/manifest/bundle |

## Tests

```bash
cd apps/backend
python -m pytest tests/test_training_wrapper.py -v
```

Dry-run tests verify argument handling, version-string pattern, runtime
metadata, bundle manifest, and the versioned zip — without a GPU or dataset.

## Limitations

- The wrapper does not itself train without a GPU+dataset; full training is run
  on Kaggle/Colab. Metrics are produced by the source-of-truth script and must
  not be fabricated.
- Generated artifacts (`run_out/`, bundles) are git-ignored; copy the versioned
  bundle back into the repo deliberately after a real run.
