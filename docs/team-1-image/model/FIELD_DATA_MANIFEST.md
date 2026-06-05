# Field Data Label-Tier and Manifest Workflow

This workflow supports issue #26 and future real-world reliability work. It defines how **Local Field Image** entries become dataset candidates without treating app **Scan History** as training data by default.

## Core rule

Scan History records are local product records, not dataset rows. A Scan History item may become training data only after it is copied into this reviewed Local Field Image manifest with explicit consent, reviewer metadata, label tier, and dataset eligibility.

## Manifest file

Use `field_manifest.csv` with these required columns:

| Column | Meaning |
|---|---|
| `image_id` | Stable non-identifying field image id. Must be unique. |
| `image_path` | Local or dataset-relative image path. Do not commit raw images. |
| `source_session_id` | Collection session/group id to keep related images traceable. |
| `field_source` | Farm/collection source alias, not precise private address. |
| `disease_class` | `FMD`, `LSD`, `healthy`, or empty for hard-negative rows. |
| `is_hard_negative` | `true` when image is poor evidence, non-target condition, or out-of-scope. |
| `label_tier` | `expert_reviewed`, `researcher_reviewed`, or `farmer_weak`. |
| `reviewer_role` | `veterinarian`, `animal_health_officer`, `researcher`, or `farmer`. |
| `reviewer_id` | Non-public reviewer alias/code. |
| `review_date` | ISO date of review. |
| `review_notes` | Usability, mismatch, symptom visibility, or limitation notes. |
| `train_eligible` | `include` or `exclude`. Weak labels may be training-only. |
| `validation_eligible` | `include` or `exclude`. Requires `expert_reviewed`. |
| `test_eligible` | `include` or `exclude`. Requires `expert_reviewed`. |
| `scan_history_record_id` | Optional source pointer. Metadata only; not automatic training consent. |

## Label tiers

- `expert_reviewed`: veterinarian or animal health officer reviewed disease label. Required for validation/test eligibility.
- `researcher_reviewed`: researcher reviewed image usability and obvious mismatch. May be training-eligible only when limitation is documented.
- `farmer_weak`: farmer-provided label or context. Weak label; training-only if used, never validation/test.

## Reviewer responsibilities

- Expert reviewer: confirms field label for FMD, LSD, healthy, or hard-negative status when evidence is sufficient.
- Researcher reviewer: removes corrupt, irrelevant, duplicate, privacy-risk, or obvious-mismatch images; records limitations.
- Farmer/source contributor: may provide context, but this remains weak until expert-confirmed.

## Dataset eligibility rules

1. `validation_eligible=include` or `test_eligible=include` requires `label_tier=expert_reviewed`.
2. Weak labels may be marked `train_eligible=include` only when `label_tier=farmer_weak` is preserved.
3. Hard-negative rows use `is_hard_negative=true` and empty `disease_class`.
4. Hard negatives are for threshold tuning/error analysis first, not automatic unknown-class training.
5. Missing expert review must be documented as limitation wording: “not expert-reviewed; training-only candidate; not used for validation/test claims.”

## Target before model update

- 50 expert-reviewed Local Field Image entries for `FMD`.
- 50 expert-reviewed Local Field Image entries for `LSD`.
- 50 expert-reviewed Local Field Image entries for `healthy`.
- 50 expert-reviewed Hard-Negative Field Image entries.

## Validate manifest

```bash
cd apps/backend
python -m dataset_prep.field_manifest ../../docs/team-1-image/model/templates/field_manifest_example.csv
```

Validator checks required columns, allowed values, weak-label restrictions, validation/test expert-review requirement, duplicate image ids, Scan History warning, and 50-entry target progress.

