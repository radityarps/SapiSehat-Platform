# Model Candidate Evaluation Report

**Project**: SapiSehat — Cattle Disease Classification (FMD / LSD / Healthy)
**Task**: 3-class image classification
**Date**: 2026-06-01
**Status**: All three candidates evaluated on the prepared 70/15/15 test split.
DenseNet121 achieves the highest macro F1 (0.995); MobileNetV2 selected for
production due to Android viability (see §6).

---

## 1. Objective

Compare candidate CNN architectures for classifying cattle images into three
classes — **FMD** (Foot and Mouth Disease / PMK), **LSD** (Lumpy Skin Disease /
Lato-Lato), and **healthy** — and select the model best suited for both
server-side and on-device (Android/TFLite) inference.

Candidates (issue #17):

1. **Custom CNN** (baseline, trained from random initialization)
2. **MobileNetV2** (ImageNet transfer learning, two-phase fine-tune)
3. **DenseNet121** (ImageNet transfer learning, two-phase fine-tune)

---

## 2. Shared evaluation protocol (issue #17/#20)

All three candidates trained and evaluated under one identical protocol.
Recorded in `run_config.json` per run.

| Aspect | Setting |
|--------|---------|
| Platform | Kaggle (GPU T4 ×2) |
| TensorFlow | 2.18.0 |
| Python | 3.12.13 |
| Class mapping | Fixed canonical order: 0=FMD, 1=LSD, 2=healthy |
| Split | Issue #18 fixed-seed stratified 70/15/15 `split_manifest.csv` |
| Train split | Model fitting (shuffled with fixed seed 42) |
| Valid split | Validation / early stopping |
| Test split | **Final reported metrics** (held out) |
| Input | RGB 224×224×3, rescale 1/255 |
| Augmentation (train only) | Rotation ≤±15°, zoom ≤±10%, mild brightness/contrast, horizontal flip. **No** vertical flip / heavy blur / aggressive crop / extreme color shift |
| Valid/test preprocessing | Deterministic (rescale only) |
| Transfer learning | Two-phase: (1) frozen base + train head at lr=0.001, (2) unfreeze top ~30 layers, fine-tune at lr=1e-5 |
| Custom CNN | Trained from random init (single phase, no pretrained base) |
| Optimizer | Adam |
| Loss | categorical_crossentropy |
| Max epochs | 50 (phase 1) + up to 10 (fine-tune) |
| Early stopping | patience 8, restore best weights |
| LR reduction | ReduceLROnPlateau patience 4, factor 0.2 |
| Class weights | Computed from train split: FMD=1.917, LSD=0.734, healthy=0.896 |
| Batch size | 32 (Custom CNN, MobileNetV2); 16 (DenseNet121) |
| Seed | 42 (single seed; see limitations §7) |
| Training date | 2026-06-01 |

---

## 3. Dataset

| Property | Value |
|----------|-------|
| Source | Roboflow `valll-rtclj/pmk-dan-penyakit-lato-lato` v4 |
| Classes | FMD, LSD, healthy |
| Input size | 224 × 224 × 3 |
| Normalization | rescale 1/255 |
| Split method | Fixed-seed stratified 70/15/15 via issue #18 `dataset_prep` |
| Duplicate handling | Exact (SHA-256) + near (imagehash.phash); groups kept in same split |

### Per-split, per-class support counts

| Split | FMD | LSD | healthy | Total |
|-------|-----|-----|---------|-------|
| train | 234 | 611 | 501 | 1346 |
| valid | 44 | 132 | 116 | 292 |
| test | 49 | 137 | 111 | 297 |
| **all** | **327** | **880** | **728** | **1935** |

---

## 4. Results (test split, seed 42)

### 4.1 Custom CNN (from-scratch baseline)

**Overall accuracy: 0.912** (test, 297 images)

| Class | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| FMD | 0.94 | 0.92 | 0.93 | 49 |
| LSD | 0.91 | 0.90 | 0.90 | 137 |
| healthy | 0.90 | 0.93 | 0.92 | 111 |
| **Macro avg** | **0.92** | **0.91** | **0.92** | 297 |
| **Weighted avg** | **0.91** | **0.91** | **0.91** | 297 |

Confusion matrix:

```
          FMD  LSD  healthy
FMD       45    4      0
LSD        3  123     11
healthy    0    8    103
```

Parameters: 110,147 | Model size: 1.31 MB

Source: [`results/custom_cnn/custom_cnn_metrics.json`](results/custom_cnn/custom_cnn_metrics.json)

### 4.2 MobileNetV2 (ImageNet transfer + fine-tune)

**Overall accuracy: 0.970** (test, 297 images)

| Class | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| FMD | 0.96 | 1.00 | 0.98 | 49 |
| LSD | 0.98 | 0.96 | 0.97 | 137 |
| healthy | 0.96 | 0.97 | 0.97 | 111 |
| **Macro avg** | **0.97** | **0.98** | **0.97** | 297 |
| **Weighted avg** | **0.97** | **0.97** | **0.97** | 297 |

Confusion matrix:

```
          FMD  LSD  healthy
FMD       49    0      0
LSD        2  131      4
healthy    0    3    108
```

Parameters: 2,422,339 | Model size: 22.72 MB (Keras; TFLite ~9 MB)

Source: [`results/mobilenetv2/mobilenetv2_metrics.json`](results/mobilenetv2/mobilenetv2_metrics.json)

### 4.3 DenseNet121 (ImageNet transfer + fine-tune)

**Overall accuracy: 0.993** (test, 297 images)

| Class | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| FMD | 1.00 | 1.00 | 1.00 | 49 |
| LSD | 0.99 | 1.00 | 0.99 | 137 |
| healthy | 1.00 | 0.98 | 0.99 | 111 |
| **Macro avg** | **1.00** | **0.99** | **0.99** | 297 |
| **Weighted avg** | **0.99** | **0.99** | **0.99** | 297 |

Confusion matrix:

```
          FMD  LSD  healthy
FMD       49    0      0
LSD        0  137      0
healthy    0    2    109
```

Parameters: 7,169,091 | Model size: 34.71 MB (Keras)

Source: [`results/densenet/densenet121_metrics.json`](results/densenet/densenet121_metrics.json)

---

## 5. Comparison Summary

| Model | Accuracy (test) | Macro F1 (test) | Per-class F1 min | Params | Keras size | TFLite est. | Android viable |
|-------|-----------------|-----------------|------------------|--------|------------|-------------|----------------|
| Custom CNN | 0.912 | 0.916 | 0.90 (LSD) | 110K | 1.31 MB | ~0.5 MB | ✅ (but under-performs) |
| **MobileNetV2** | **0.970** | **0.972** | **0.97 (LSD)** | **2.4M** | **22.72 MB** | **~9 MB** | **✅ Yes** |
| DenseNet121 | 0.993 | 0.995 | 0.99 (healthy) | 7.2M | 34.71 MB | ~30+ MB | ⚠️ Exceeds 10 MB target |

### Target assessment

| Target | Custom CNN | MobileNetV2 | DenseNet121 |
|--------|-----------|-------------|-------------|
| Test accuracy ≥ 88% | ✅ 91.2% | ✅ 97.0% | ✅ 99.3% |
| Per-class F1 ≥ 85% | ✅ min 90% | ✅ min 97% | ✅ min 99% |
| TFLite < 10 MB | ✅ ~0.5 MB | ✅ ~9 MB | ❌ ~30+ MB |

All three candidates meet the accuracy and per-class F1 targets. DenseNet121
achieves the highest metrics but fails the Android size constraint.

---

## 6. Selected Model and Rationale

**Selected: MobileNetV2**

Rationale:

1. **Meets all targets**: 97.0% test accuracy, 0.972 macro F1, all per-class F1
   ≥ 0.97 — well above the 88% accuracy / 85% per-class F1 thresholds.
2. **Android viable**: TFLite export ~9 MB (within the <10 MB budget documented
   in `apps/mobile/TFLITE_PARITY.md`), runs offline in well under 1 second on
   mid-range ARM64 devices.
3. **Transfer learning efficiency**: Frozen ImageNet base + fine-tuning converges
   quickly on a relatively small dataset (1346 train images), reducing
   overfitting risk versus the from-scratch Custom CNN.
4. **Dual-path consistency**: Same architecture serves both the server (Keras)
   and the mobile offline engine (TFLite), simplifying version traceability.
5. **FMD recall = 1.00**: Perfect recall on the most critical disease class
   (Foot and Mouth Disease) — no FMD cases missed.

DenseNet121 achieves marginally better metrics (0.993 vs 0.970) but is rejected
for the offline path due to model size (~35 MB Keras, ~30+ MB TFLite) exceeding
the 10 MB Android budget. It remains a valid server-only candidate if offline
inference is not required.

Custom CNN demonstrates that transfer learning provides a substantial benefit
(+6 pp accuracy, +5.6 pp macro F1) over training from scratch on this dataset
size.

---

## 7. Limitations

- **Single seed (42)**: Each candidate was trained once. Per the PRD, single-seed
  results are acceptable only when documented as a limitation. Re-run the winner
  with two additional seeds (123, 777) for a robustness check before any final
  claim. This is recommended but not yet done.
- **No veterinarian / animal-health-officer label audit** has been performed.
  Labels are the Roboflow source labels filtered by the issue #18 validation
  step only. This is a documented limitation, not an expert clinical audit.
- **Not a clinical diagnosis**: Outputs are image-classification early-detection
  results, not a veterinary diagnosis.
- **MobileNetV2 Keras size (22.72 MB)** is larger than expected because the full
  model (frozen base + head) is saved. The TFLite conversion (float32) is ~9 MB;
  dynamic-range quantization can reduce further.

---

## 8. Reproducibility

Training date: 2026-06-01
Platform: Kaggle (GPU T4 ×2)
TensorFlow: 2.18.0
Python: 3.12.13
Seed: 42
Data source: prepared_split_manifest (issue #18)
Script: `docs/team-1-image/model/evaluate_candidates.py`
Wrapper: `docs/team-1-image/model/training_wrapper.py`

To reproduce:

```bash
# 1. Generate the 70/15/15 split inside the runtime:
cd apps/backend
python -m dataset_prep.cli --data /path/to/dataset --out dataset_artifacts

# 2. Train + evaluate all three candidates:
python ../../docs/team-1-image/model/evaluate_candidates.py \
    --manifest dataset_artifacts/split_manifest.csv \
    --epochs 50 --fine-tune-epochs 10 --seed 42 \
    --out ../../docs/team-1-image/model/results
```

See [`KAGGLE_RUN_GUIDE.md`](KAGGLE_RUN_GUIDE.md) and
[`TRAINING_WORKFLOW.md`](TRAINING_WORKFLOW.md) for the full Kaggle/Colab steps.

---

## 9. References

- Evaluation script: `docs/team-1-image/model/evaluate_candidates.py`
- Training wrapper + bundle: `docs/team-1-image/model/training_wrapper.py`, `TRAINING_WORKFLOW.md`
- Dataset prep / split: `apps/backend/dataset_prep/`, `DATASET_SPLIT_REPORT.md`
- Custom CNN metrics: [`results/custom_cnn/custom_cnn_metrics.json`](results/custom_cnn/custom_cnn_metrics.json)
- MobileNetV2 metrics: [`results/mobilenetv2/mobilenetv2_metrics.json`](results/mobilenetv2/mobilenetv2_metrics.json)
- DenseNet121 metrics: [`results/densenet/densenet121_metrics.json`](results/densenet/densenet121_metrics.json)
- Confusion matrices: `results/*/[model]_confusion_matrix.png`
- TFLite parity & size/latency: `apps/mobile/TFLITE_PARITY.md`
- Class mapping: canonical order 0=FMD, 1=LSD, 2=healthy
