> **Team 1 image subsystem note:** TFLite parity applies to offline image evidence only, not the whole SapiSehat platform. Shared platform contracts live in `docs/../README.md`. Shared platform contracts path: `docs/system-integration/README.md`.

# TFLite Parity and Version Traceability

## Model Asset

- **File**: `app/src/main/assets/cattle_disease.tflite`
- **Version**: `MobileNetV2-tflite-v1` (tracked in `OfflineInferenceEngine.MODEL_VERSION`)
- **Architecture**: MobileNetV2, 3-class classifier (FMD, LSD, healthy)

## Size Target

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| TFLite model size | <10 MB | ~9 MB | ✅ Pass |

## Accuracy Parity

| Metric | Target | Notes |
|--------|--------|-------|
| Accuracy drop vs server | ≤2% | Validated during model export via `torch → ONNX → TFLite` pipeline |

### Parity Check Procedure

1. Export server model to TFLite:
   ```bash
   cd apps/backend
   python -c "
   import torch
   from model.loader import ModelLoader
   model = ModelLoader().model
   # Export and compare predictions on test set
   "
   ```

2. Run both models on the same test images and compare:
   - Top-1 class agreement rate should be ≥98%
   - Mean confidence difference should be <0.02

3. Document any exceptions in this file.

## Latency Target

| Metric | Target | Device | Notes |
|--------|--------|--------|-------|
| Offline inference | <1s | ARM64 Android (mid-range) | Measured end-to-end including preprocessing |

### Measurement Procedure

1. Run inference on device with `processingMs` field in `DetectionResult`
2. Check history records for offline scans
3. Typical latency: 200-500ms on modern ARM64 devices

## Version Traceability

Model version is exposed in:
- **Result detail**: Technical Information → Model Version
- **History**: Persisted in `DetectionEntity.modelVersion`
- **PDF report**: Technical Information section
- **Settings**: Model Version row (shows offline model version)

### Online Model Version
- Returned by server in `model_info.version` field of predict response
- Persisted with each online scan result

### Offline Model Version
- Constant `OfflineInferenceEngine.MODEL_VERSION = "MobileNetV2-tflite-v1"`
- Updated when the `.tflite` asset is replaced
- Persisted with each offline scan result

## Version Mismatch Handling

Currently, online and offline models may have different versions. The app:
- Displays the actual model version used for each scan
- Does not block inference on version mismatch
- Users can see which version produced each result in history/detail/PDF

## Unmeasured Metrics Exception

The following metrics have NOT been independently measured on-device and rely on
export-time validation only:

- **Accuracy parity**: The ≤2% drop target is validated during the
  `torch → ONNX → TFLite` export pipeline using a held-out test set. No
  automated on-device accuracy regression test currently exists.
- **Latency target**: The <1s target is based on manual observation on
  representative devices. No automated benchmark suite runs in CI.

These gaps are accepted for the current project scope (Tugas Akhir). If the app
moves to production, automated on-device benchmarks should be added.
