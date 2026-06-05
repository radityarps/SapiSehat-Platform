# Image + NLP Fusion Contract

## Purpose

Define shared contract for combining Team 1 image evidence and Team 2 NLP symptom evidence into one early detection result.

Backend fusion is the online source of truth. Mobile may perform offline local fusion using bundled image and NLP models, then sync the offline result to backend when connectivity returns.

## Inputs

### Image Evidence

Owned by Team 1.

Expected fields:

```json
{
  "source": "image",
  "model_version": "string",
  "inference_mode": "online|offline",
  "disease_scores": {
    "FMD": 0.0,
    "LSD": 0.0,
    "healthy": 0.0
  },
  "top_class": "FMD|LSD|healthy",
  "confidence": 0.0,
  "quality_status": "accepted|rejected|warning",
  "rejection_reasons": ["too_blurry"],
  "debug": {}
}
```

### NLP Evidence

Owned by Team 2.

Expected fields:

```json
{
  "source": "nlp",
  "model_version": "string",
  "inference_mode": "online|offline",
  "questionnaire_answers": {},
  "notes_present": true,
  "disease_scores": {
    "FMD": 0.0,
    "LSD": 0.0,
    "healthy": 0.0
  },
  "top_class": "FMD|LSD|healthy",
  "confidence": 0.0,
  "evidence_terms": ["mouth_lesion", "skin_nodule"],
  "debug": {}
}
```

## Fusion Output

Owned by system integration contract.

Expected fields:

```json
{
  "fusion_version": "string",
  "inference_mode": "online|offline|synced_offline",
  "cattle_id": "uuid|null",
  "farmer_id": "uuid",
  "disease_class": "FMD|LSD|healthy",
  "confidence": 0.0,
  "confidence_level": "high|medium|low",
  "reliability": "reliable|low_reliability|needs_review|insufficient_evidence",
  "handling_advice_key": "string",
  "evidence_breakdown": {
    "image": {},
    "nlp": {}
  },
  "conflict_status": "none|image_nlp_conflict|missing_image|missing_nlp|low_quality_image",
  "created_at": "ISO-8601",
  "synced_at": "ISO-8601|null"
}
```

## Conflict Rules

Minimum rules before implementation:

1. If image and NLP top classes match and both confidence levels are medium or high, result may be reliable.
2. If image and NLP top classes conflict, result must be marked `needs_review` or `low_reliability`.
3. If image is rejected by quality gate, NLP may still produce a result, but conflict status must include `low_quality_image` or `missing_image`.
4. If both evidence streams are low confidence, result should be `insufficient_evidence`.
5. Backend-fused online result is canonical after successful sync.
6. Offline result must preserve local image and NLP evidence versions for audit.

## Storage Rules

Fusion result may be stored with:

- farmer id
- cattle id or null for quick scan
- image evidence summary
- NLP evidence summary
- raw image/media reference when storage policy and consent allow
- questionnaire answers and notes according to consent/access rules

## Open Decisions

- Fusion weighting formula.
- Thresholds for confidence and conflict.
- Whether `healthy` should be allowed when image and NLP evidence are both weak.
- Exact sync conflict handling if offline result changes after backend re-fusion.


## Team 1 Image Evidence Validation Rules

Executable tracer: `POST /api/evidence/image`. The validator enforces:

- `disease_scores` has exactly `healthy`, `FMD`, and `LSD`.
- each disease score is between 0.0 and 1.0.
- `top_class` matches the highest disease score.
- `model_version` and `inference_mode` are present.
- rejected image evidence includes at least one `rejection_reasons` entry.
- rejected image evidence returns `accepted_for_fusion: false`.
