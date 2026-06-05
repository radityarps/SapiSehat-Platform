# TFLite Export Guide — Issue #22 (HITL)

Run this on Kaggle/Colab after the #20 training run to export the selected
MobileNetV2 model to TFLite and verify parity against the Keras server model.

## Prerequisites

- The `.keras` model file from the #20 training run (e.g.
  `run_out_mobilenetv2/mobilenetv2.keras`)
- The `split_manifest.csv` generated inside the same runtime (issue #18)
- The repo cloned on `ai-models` branch

## Commands (Kaggle)

```python
%cd /kaggle/working/repo

# Export + parity check (uses the .keras from the training run):
!python docs/team-1-image/model/tflite_export.py \
    --keras /kaggle/working/run_out_mobilenetv2/mobilenetv2.keras \
    --manifest /kaggle/working/dataset_artifacts/split_manifest.csv \
    --model-name mobilenetv2 \
    --out /kaggle/working/tflite_out
```

## Expected outputs

```
tflite_out/
├── mobilenetv2_float32.tflite           # Float32 parity baseline
├── mobilenetv2_dynamic_range.tflite     # App candidate (quantized)
├── mobilenetv2_keras_test_metrics.json  # Keras metrics on test split
├── mobilenetv2_float32_tflite_test_metrics.json
├── mobilenetv2_dynrange_tflite_test_metrics.json
├── parity_results.json                  # Machine-readable pass/fail
├── preprocessing.json                   # Deterministic preprocessing spec
└── TFLITE_PARITY_REPORT.md             # Human-readable report
```

## Parity thresholds

| Check | Threshold |
|-------|-----------|
| Accuracy drop | ≤ 2 pp |
| Macro F1 drop | ≤ 2 pp |
| Per-class F1 drop | ≤ 3 pp |
| Class-index mismatch | None |
| TFLite size | < 10 MB |

## After download

Copy back to repo:

```
tflite_out/TFLITE_PARITY_REPORT.md → docs/team-1-image/model/TFLITE_PARITY_REPORT.md
tflite_out/parity_results.json → docs/team-1-image/model/results/parity_results.json
tflite_out/preprocessing.json → docs/team-1-image/model/results/preprocessing.json
tflite_out/mobilenetv2_dynamic_range.tflite → (keep out-of-band, reference in report)
```

The `.tflite` files are too large for git. Keep them as Kaggle output artifacts
or upload to a release. Reference the location in the report.

## If parity fails

If dynamic-range quantization fails parity, try Float32 TFLite as the app
candidate (larger but exact). Full int8 quantization is attempted only if both
Float32 and dynamic-range fail the size budget.
