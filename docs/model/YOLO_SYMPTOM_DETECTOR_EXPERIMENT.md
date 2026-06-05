# YOLO Symptom-Region Detector Experiment

This package supports issue #29. It configures the first small YOLO-family **Symptom Region Detector** candidate for server-first two-stage inference research. It does not expose farmer-facing boxes.

## Candidate

- Family: small YOLO detector, e.g. `yolov8n`/`yolo11n` depending on available Ultralytics runtime.
- Classes:
  - `0=fmd_mouth_lesion`
  - `1=fmd_hoof_lesion`
  - `2=lsd_skin_nodule`
  - `3=confusing_region`
- Runtime implication: introduces a PyTorch/Ultralytics dependency for the detector while the existing single-stage classifier remains TensorFlow/Keras. This follows `docs/adr/0001-yolo-symptom-region-detector.md`.

## Developer/debug output contract

Detector outputs are developer/debug-only:

```json
{
  "boxes": [
    {
      "x_min": 0.22,
      "y_min": 0.31,
      "x_max": 0.46,
      "y_max": 0.58,
      "confidence": 0.81,
      "symptom_region_type": "fmd_mouth_lesion"
    }
  ]
}
```

No farmer-facing symptom boxes are enabled by this slice.

## Prepare YOLO labels

```bash
python docs/model/yolo_symptom_detector.py convert \
  --annotations docs/model/templates/symptom_region_annotations_example.csv \
  --out run_out/yolo_symptom_detector
```

The converter writes:

- `run_out/yolo_symptom_detector/labels/<image_id>.txt`
- `run_out/yolo_symptom_detector/data.yaml`

Raw images remain outside git and must be arranged by the operator into `images/train`, `images/val`, and `images/test` using the approved field manifest split.

## Train command template

Run only when reviewed annotations and image files exist:

```bash
yolo detect train \
  model=yolov8n.pt \
  data=run_out/yolo_symptom_detector/data.yaml \
  imgsz=640 \
  epochs=50 \
  patience=8 \
  project=run_out \
  name=yolo_symptom_detector
```

Do not commit weights or raw images unless explicitly approved. Commit reports and metrics only.

## Evaluate prediction CSV

Prediction CSV columns:

```text
image_id,symptom_category,x_min,y_min,x_max,y_max,confidence
```

Evaluate simple held-out box metrics at IoU 0.5:

```bash
python docs/model/yolo_symptom_detector.py evaluate \
  --ground-truth docs/model/templates/symptom_region_annotations_example.csv \
  --predictions docs/model/templates/yolo_predictions_example.csv \
  --out /tmp/yolo_symptom_metrics.json
```

Report precision/recall by symptom-region type and overall. Full YOLO training runs may also report mAP50/mAP50-95 from Ultralytics logs.

