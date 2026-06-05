# Assets

Offline inference model lives in this folder.

Expected files:

- `cattle_disease.tflite` — selected MobileNetV2 dynamic-range TFLite artifact.
- `model_metadata.json` — version, class order, preprocessing, checksum, and parity traceability.

Current model:

- Version: `cattle-disease-mobilenetv2-v20260601-s42-dynamic-range`
- Class order: `0 = FMD`, `1 = LSD`, `2 = healthy`
- Preprocessing: RGB decode, EXIF orientation correction where available, 224 × 224 resize, rescale `1/255`
- Parity source: `docs/team-1-image/model/results/tflite_out/TFLITE_PARITY_REPORT.md`

Notes:

- Keep `cattle_disease.tflite` exact filename because app loads it by name.
- To update offline model, replace `.tflite` and update `model_metadata.json` plus `OfflineInferenceEngine.MODEL_VERSION` together.
