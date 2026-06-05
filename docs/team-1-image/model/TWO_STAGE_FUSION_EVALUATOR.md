# Two-Stage Fusion Evaluator

This package supports issue #30. It evaluates server-first two-stage fusion offline before backend inference changes.

## Fusion rule

- Run full-image classifier on original image.
- Run crop classifier on crops from the top three detector boxes after suppression.
- Aggregate crop scores by per-class maximum.
- Fuse initial score:

```text
0.4 * full_image_score + 0.6 * crop_score
```

Thresholds remain tunable on validation data:

- minimum confidence: `0.70`
- minimum top-class margin: `0.15`

## Reliability rule

Conflicting symptom-region types mark result as `needs_review` / lower reliability. Example: fused label `FMD` with only `lsd_skin_nodule` detector boxes.

## Success gate

Two-stage candidate passes only if all are true versus current single-stage field baseline:

- lower False Confident Result rate
- field macro F1 equal or better
- FMD recall not worse by more than 5 percentage points
- LSD recall not worse by more than 5 percentage points
- Insufficient Visual Evidence rate at or below 35%

## Run

```bash
python docs/team-1-image/model/two_stage_fusion_evaluator.py \
  --truth docs/team-1-image/model/templates/field_manifest_eval_example.csv \
  --full-scores docs/team-1-image/model/templates/field_predictions_example.csv \
  --crop-scores docs/team-1-image/model/templates/two_stage_crop_scores_example.csv \
  --baseline-metrics docs/team-1-image/model/templates/field_baseline_metrics_example.json \
  --out /tmp/two_stage_fusion_metrics.json
```

