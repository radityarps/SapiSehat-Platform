# Team 1 Image Documentation

Team 1 owns image-based early detection implementation across mobile and backend.

## Scope

Team 1 owns:

- image classification model behavior
- image preprocessing and quality gates
- image inference contracts and model versions
- mobile image capture/offline image model behavior
- backend image inference service behavior
- image-specific validation and evaluation
- symptom-region detector experiments when used by image subsystem

Team 1 does not own:

- NLP symptom model behavior
- shared platform data model
- shared fusion policy
- agency dashboard contracts
- shared privacy/retention/access-control policy

## Required Shared Contracts

Before changing image evidence shape or behavior, update:

- [Fusion Contract](../system-integration/api-contracts/FUSION_CONTRACT.md)
- [Data Model](../system-integration/database/DATA_MODEL.md) when stored image evidence/media changes
- [System Integration README](../../README.md) when ownership/routing changes

## Image Docs

Migrated image/model docs live in `docs/team-1-image/model`. Treat those docs as Team 1 image subsystem material and keep shared API/data/fusion rules in `docs/system-integration`.


## Image Evidence Contract Tracer

Issue #7 adds the first executable Team 1 image evidence contract. Image evidence must include:

1. `source: image`.
2. `model_version`.
3. `inference_mode: online|offline`.
4. `disease_scores` with exactly `healthy`, `FMD`, and `LSD`.
5. `top_class` matching the highest disease score.
6. `confidence` from 0.0 to 1.0.
7. `quality_status: accepted|warning|rejected`.
8. `rejection_reasons` when `quality_status` is `rejected`.

Rejected image evidence must be marked not accepted for fusion so poor image inputs do not create misleading reliable results.

Prototype validation endpoint: `POST /api/evidence/image`.
