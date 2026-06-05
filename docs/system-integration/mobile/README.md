# Mobile Flow Contracts

Shared farmer mobile app flows live here.

Use this folder for cattle-first detection flow, quick-scan behavior, offline fusion, sync behavior, consent UX, and cross-team mobile contracts.

Model-specific mobile details belong in Team 1 or Team 2 docs.


## Offline Detection Sync Tracer

Mobile offline flow may run bundled image and NLP models, create local fused detection, then sync through `POST /api/offline/detections/sync`. Client must preserve:

- stable `local_detection_id` until sync completes.
- `local_created_at` from device capture time.
- image and NLP `model_version`.
- evidence `inference_mode: offline`.
- sync status from backend response.


## Migrated Mobile Docs

- [Legacy mobile README](legacy-mobile-readme.md)
- [Mobile full version spec](mobile-full-version-spec.md)
- [Wireless debugging](WIRELESS-DEBUGGING.md)
