# Symptom Region Annotation Protocol

This protocol supports issue #27 and future server-first two-stage experiments. It defines human annotation expectations for Local Field Image entries after the #26 manifest workflow.

## Scope

- Disease field images require bounding boxes around visible disease-relevant evidence.
- Do not draw whole-cow-only boxes when visible symptom evidence is smaller.
- Healthy field images keep image-level `healthy` labels only. Do not create fake symptom boxes for healthy images.
- Hard-negative field images are marked for threshold tuning and error analysis. Optional boxes may mark confusing regions, but this does not create an unknown disease class.

## Accepted symptom-region categories

| Disease/context | Category | Annotate |
|---|---|---|
| FMD | `fmd_mouth_lesion` | Visible mouth/tongue/gum lesion area. |
| FMD | `fmd_hoof_lesion` | Visible hoof/foot lesion area. |
| LSD | `lsd_skin_nodule` | Visible skin nodule cluster or clear single nodule. |
| Hard negative | `confusing_region` | Region that could confuse model but is not confirmed FMD/LSD evidence. |

## Box rules

1. Use tight boxes around visible symptom evidence, not background or whole animal.
2. Use multiple boxes when separate symptom regions are visible.
3. Coordinates in CSV templates are normalized floats: `0.0 <= x_min < x_max <= 1.0`, `0.0 <= y_min < y_max <= 1.0`.
4. If disease image has no visible symptom evidence, do not force a box; send row back for reviewer disagreement or mark as hard-negative/insufficient evidence candidate if appropriate.
5. Confusing hard-negative boxes remain `confusing_region` and are used for threshold/error analysis first.

## Quality checks

- Missing boxes: every FMD/LSD disease field image must have at least one symptom-region box.
- Invalid boxes: reject empty, inverted, out-of-range, or non-numeric coordinates.
- Healthy images: reject any symptom-region box.
- Hard negatives: allow only optional `confusing_region` boxes.
- Duplicate images: keep duplicate/near-duplicate grouping from dataset prep; do not let duplicate disagreements enter validation/test without review.
- Reviewer disagreement: record disagreement in `review_notes`; expert reviewer decides final training eligibility.

## Template and validator

Template:

```text
docs/team-1-image/model/templates/symptom_region_annotations_example.csv
```

Validate:

```bash
cd apps/backend
python -m dataset_prep.symptom_annotations ../../docs/team-1-image/model/templates/symptom_region_annotations_example.csv
```

Validator checks accepted categories, healthy no-box rule, hard-negative confusing-region rule, disease image box requirement, duplicate annotation ids, invalid boxes, and reviewer disagreement warnings.

