# Kaggle Run Guide for Issue #20

Use this guide to run the proposal-aligned three-candidate model evaluation on Kaggle. The goal is to generate real test-split metrics for:

- Custom CNN
- MobileNetV2
- DenseNet121

Do **not** fabricate metrics. Do **not** close issue #20 until the real Kaggle/Colab outputs are copied back into the repository and reviewed.

## 0. Optional: upload repo archive instead of cloning

If you want to upload the current local repo state to Kaggle as a dataset, create an archive from the current commit:

```bash
git archive --format=zip HEAD -o sapisehat-repo.zip
```

Then upload `sapisehat-repo.zip` to Kaggle as a private dataset, or use the normal `git clone` approach below.

## 1. Create Kaggle notebook

1. Open Kaggle.
2. Create a new notebook.
3. Set accelerator to GPU: **Notebook settings → Accelerator → GPU**.
4. Add your Roboflow dataset as Kaggle input.

## 2. Get repository code into Kaggle

### Option A — clone branch from GitHub

```python
!git clone -b ai-models https://github.com/radityarps/Tugas-Akhir-Klasifikasi-Penyakit-Sapi-CNN.git repo
```

### Option B — use uploaded `sapisehat-repo.zip`

If you uploaded `sapisehat-repo.zip` as a Kaggle dataset, unzip it:

```python
!mkdir -p /kaggle/working/repo
!unzip -q /kaggle/input/YOUR-REPO-DATASET/sapisehat-repo.zip -d /kaggle/working/repo
```

Replace `YOUR-REPO-DATASET` with the Kaggle dataset folder name.

## 3. Set repository paths and install dependencies

Kaggle environment warning: avoid heredoc cells such as `!python - <<'PY' ... PY` in Python notebooks. Kaggle can split them incorrectly. Use `python -c "..."` one-liners or `%%bash` cells instead.

First locate the repository root. If you cloned or unzipped from `/kaggle/working`, the root is usually:

```text
/kaggle/working/repo
```

If you accidentally cloned/unzipped while already inside another repo folder, it may be nested, for example:

```text
/kaggle/working/repo/apps/backend/repo
```

Find the real backend folder:

```python
!find /kaggle/working -type d -path "*/apps/backend/dataset_prep" -print
```

If output is:

```text
/kaggle/working/repo/apps/backend/dataset_prep
```

use:

```python
REPO = "/kaggle/working/repo"
BACKEND = f"{REPO}/apps/backend"
```

If output is nested like:

```text
/kaggle/working/repo/apps/backend/repo/apps/backend/dataset_prep
```

use:

```python
REPO = "/kaggle/working/repo/apps/backend/repo"
BACKEND = f"{REPO}/apps/backend"
```

Verify paths:

```python
print("REPO:", REPO)
print("BACKEND:", BACKEND)
!ls -lah "$REPO/docs/team-1-image/model"
!ls -lah "$BACKEND/dataset_prep"
```

Install backend/model dependencies from the real backend folder.

Do **not** use plain `pip install -r requirements.txt` on Kaggle if it upgrades TensorFlow to a version that does not match Kaggle CuDNN. A known bad combination is TensorFlow `2.19.0` with Kaggle CuDNN `9.1`, which can fail with:

```text
Loaded runtime CuDNN library: 9.1.0 but source was compiled with: 9.3.0
DNN library initialization failed
```

Use the Kaggle-compatible stack below instead:

```python
%cd $BACKEND
!python -m pip uninstall -y tensorflow keras numpy scipy jax jaxlib
!python -m pip install --no-cache-dir --force-reinstall "numpy==1.26.4" "scipy==1.14.1"
!python -m pip install --no-cache-dir --force-reinstall "tensorflow==2.18.0" "keras==3.8.0"
!python -m pip install --no-cache-dir fastapi uvicorn gunicorn pillow imagehash pydantic pydantic-settings python-multipart python-dotenv hypothesis httpx scikit-learn matplotlib seaborn
```

Why uninstall `jax`/`jaxlib`: TensorFlow import can fail on Kaggle with an `ml_dtypes` conflict like:

```text
ValueError: JAX requires ml_dtypes version 0.5 or newer; installed version is 0.4.1.
```

Training does not need JAX.

Verify TensorFlow + GPU + CuDNN with a real conv smoke test:

```python
!python -c "import tensorflow as tf; print('TF:', tf.__version__); print('GPUs:', tf.config.list_physical_devices('GPU')); x=tf.random.normal([8,224,224,3]); m=tf.keras.Sequential([tf.keras.layers.Conv2D(8,3,activation='relu'), tf.keras.layers.GlobalAveragePooling2D(), tf.keras.layers.Dense(3,activation='softmax')]); y=m(x); print('conv smoke OK:', y.shape)"
```

Expected:

```text
TF: 2.18.0
GPUs: [PhysicalDevice(...)]
conv smoke OK: (8, 3)
```

Warnings like these are noisy but acceptable if the conv smoke test passes:

```text
Unable to register cuFFT factory
Unable to register cuDNN factory
Unable to register cuBLAS factory
computation placer already registered
```

Confirm `imagehash` and `dataset_prep` import from the same environment:

```python
!python -c "import imagehash; import dataset_prep.core as core; print('imagehash:', getattr(imagehash, '__version__', 'installed')); print('perceptual hash backend:', core.PERCEPTUAL_HASH_BACKEND)"
```

Expected backend:

```text
perceptual hash backend: imagehash.phash
```

If `ModuleNotFoundError: No module named 'dataset_prep'` appears, you are not in the backend folder or `PYTHONPATH` is wrong. Use the `find` command above and reset `REPO`/`BACKEND` to the path that contains `apps/backend/dataset_prep`.

## 4. Find dataset path

List Kaggle input folders:

```python
!find /kaggle/input -maxdepth 4 -type d | head -120
```

Pick the folder that contains your Roboflow export. It may look like one of these:

```text
/kaggle/input/pmk-dan-penyakit-lato-lato
/kaggle/input/pmk-dan-penyakit-lato-lato/train
/kaggle/input/pmk-dan-penyakit-lato-lato/valid
/kaggle/input/pmk-dan-penyakit-lato-lato/test
```

Set `DATA` to the dataset root:

```python
DATA = "/kaggle/input/YOUR-DATASET-FOLDER"
print(DATA)
```

Replace `YOUR-DATASET-FOLDER` with the real Kaggle input folder.

## 5. Generate prepared 70/15/15 split inside Kaggle

Important: do this inside Kaggle. Do **not** upload a Windows-generated `split_manifest.csv`, because Windows image paths will not exist in Kaggle.

```python
%cd $BACKEND
!python -m dataset_prep.cli \
  --data "$DATA" \
  --out /kaggle/working/dataset_artifacts
```

Check generated artifacts:

```python
!ls -lah /kaggle/working/dataset_artifacts
!grep "Perceptual-hash backend" /kaggle/working/dataset_artifacts/DATASET_SPLIT_REPORT.md
!cat /kaggle/working/dataset_artifacts/DATASET_SPLIT_REPORT.md
```

Expected files:

```text
class_indices.json
class_weights.json
DATASET_SPLIT_REPORT.md
LABEL_VALIDATION.md
split_manifest.csv
```

Expected hash backend:

```text
Perceptual-hash backend: `imagehash.phash`
```

## 6. Smoke-test MobileNetV2 with 3 epochs

Run a short test before spending GPU time on full training:

```python
%cd $REPO
!python docs/team-1-image/model/training_wrapper.py \
  --manifest /kaggle/working/dataset_artifacts/split_manifest.csv \
  --architecture mobilenetv2 \
  --seed 42 \
  --epochs 3 \
  --out /kaggle/working/run_out_mobilenetv2_smoke
```

Smoke test should produce:

```text
/kaggle/working/run_out_mobilenetv2_smoke/runtime_metadata.json
/kaggle/working/run_out_mobilenetv2_smoke/run_config.json
/kaggle/working/run_out_mobilenetv2_smoke/preprocessing.json
/kaggle/working/run_out_mobilenetv2_smoke/mobilenetv2_metrics.json
/kaggle/working/run_out_mobilenetv2_smoke/model_training_artifacts_*.zip
```

If smoke fails, fix before running all candidates.

## 7. Run real candidate training

All runs must use the same prepared split manifest:

```text
/kaggle/working/dataset_artifacts/split_manifest.csv
```

### 7.1 Custom CNN

```python
%cd $REPO
!python docs/team-1-image/model/training_wrapper.py \
  --manifest /kaggle/working/dataset_artifacts/split_manifest.csv \
  --architecture custom_cnn \
  --seed 42 \
  --epochs 50 \
  --out /kaggle/working/run_out_custom_cnn
```

### 7.2 MobileNetV2

```python
%cd $REPO
!python docs/team-1-image/model/training_wrapper.py \
  --manifest /kaggle/working/dataset_artifacts/split_manifest.csv \
  --architecture mobilenetv2 \
  --seed 42 \
  --epochs 50 \
  --out /kaggle/working/run_out_mobilenetv2
```

### 7.3 DenseNet121

```python
%cd $REPO
!python docs/team-1-image/model/training_wrapper.py \
  --manifest /kaggle/working/dataset_artifacts/split_manifest.csv \
  --architecture densenet121 \
  --seed 42 \
  --epochs 50 \
  --out /kaggle/working/run_out_densenet121
```

## 8. Package outputs for download

```python
!zip -r /kaggle/working/model_run_outputs.zip \
  /kaggle/working/dataset_artifacts \
  /kaggle/working/run_out_custom_cnn \
  /kaggle/working/run_out_mobilenetv2 \
  /kaggle/working/run_out_densenet121
```

Download:

```python
from IPython.display import FileLink
FileLink('/kaggle/working/model_run_outputs.zip')
```

Click the generated link, or use Kaggle output download UI.

## 9. Copy results back into repo

After downloading and extracting `model_run_outputs.zip` locally, copy real outputs into the repository.

Copy metrics:

```text
run_out_custom_cnn/custom_cnn_metrics.json       → docs/team-1-image/model/results/custom_cnn_metrics.json
run_out_mobilenetv2/mobilenetv2_metrics.json     → docs/team-1-image/model/results/mobilenetv2_metrics.json
run_out_densenet121/densenet121_metrics.json     → docs/team-1-image/model/results/densenet121_metrics.json
```

Copy confusion matrices:

```text
run_out_custom_cnn/custom_cnn_confusion_matrix.png       → docs/team-1-image/model/results/custom_cnn_confusion_matrix.png
run_out_mobilenetv2/mobilenetv2_confusion_matrix.png     → docs/team-1-image/model/results/mobilenetv2_confusion_matrix.png
run_out_densenet121/densenet121_confusion_matrix.png     → docs/team-1-image/model/results/densenet121_confusion_matrix.png
```

Copy shared run artifacts from one successful run, or keep per-run copies if needed:

```text
preprocessing.json
run_config.json
runtime_metadata.json
bundle_manifest.json
comparison_summary.json
```

Update:

```text
docs/team-1-image/model/MODEL_EVALUATION_REPORT.md
```

Use real **test-split** metrics only. Remove `PENDING_HITL_RUN` only after real metrics are present.

## 10. Verify locally after copying results

Run quick checks:

```bash
git status --short
```

Confirm metrics are not pending/null:

```bash
rg -n "PENDING_HITL_RUN|null|TBD|old-split" docs/team-1-image/model/MODEL_EVALUATION_REPORT.md docs/team-1-image/model/results
```

Some `old-split` wording may remain only if it clearly labels legacy MobileNetV2 numbers as legacy, not final.

Run relevant tests:

```bash
cd apps/backend
python -m pytest tests/test_training_wrapper.py tests/test_dataset_prep.py -q
```

## 11. Ask for review

After results are copied back, ask:

```text
Review #20 real training results.
```

Review will check:

- all three candidates have real metrics
- metrics are evaluated on `test`
- class order is `FMD`, `LSD`, `healthy`
- report matches JSON files
- confusion matrices exist
- no fabricated or pending values remain
- target pass/fail is documented

## 12. What not to do

- Do not close issue #20 before real metrics exist.
- Do not start issue #21 before #20 real metrics are reviewed.
- Do not start issue #22 before model selection is complete.
- Do not upload Windows-generated `split_manifest.csv` to Kaggle for training.
- Do not commit real dataset images.
- Do not claim final clinical diagnosis; keep wording as early detection / prediction / confidence.
