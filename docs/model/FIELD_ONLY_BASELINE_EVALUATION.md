# Field-Only Baseline Evaluation Package

This package supports issue #28. It evaluates the current single-stage classifier on expert-reviewed field-only validation/test rows from the #26 field manifest.

## Inputs

1. `field_manifest.csv` from `docs/model/FIELD_DATA_MANIFEST.md`.
2. Prediction CSV from the current single-stage classifier with columns:
   - `image_id`
   - `predicted_label`
   - `confidence`
   - `score_FMD`
   - `score_LSD`
   - `score_healthy`

## Ground-truth inclusion rules

- Only `label_tier=expert_reviewed` rows are eligible for validation/test ground truth.
- `validation_eligible=include` is used for validation evaluation.
- `test_eligible=include` is used for test evaluation.
- Weak labels and researcher-only labels are excluded from field validation/test metrics.
- Hard-negative rows are excluded from disease-class metrics and kept for threshold/error analysis.

## Preserved runtime expectations

- Class order: `0=FMD`, `1=LSD`, `2=healthy`.
- Preprocessing: EXIF orientation where available, RGB, 224×224, rescale `1/255`.
- Insufficient Visual Evidence policy: confidence below `70%` or top-class margin below `15 percentage points`.

## Run

```bash
python docs/model/field_baseline_evaluation.py \
  --field-manifest docs/model/templates/field_manifest_eval_example.csv \
  --predictions docs/model/templates/field_predictions_example.csv \
  --split test \
  --out docs/model/results/FIELD_ONLY_BASELINE_REPORT.md \
  --metrics-json docs/model/results/field_only_baseline_metrics.json
```

The script writes a Markdown report with macro F1, per-class recall, FMD recall, LSD recall, confusion matrix, Insufficient Visual Evidence rate, False Confident Result rate, and common failure categories.

## Limitation wording

If no expert-reviewed field validation/test set exists yet, do not report field performance. State: “Field-only baseline evaluation is prepared but not executed because expert-reviewed Local Field Image validation/test rows are not yet available.”

