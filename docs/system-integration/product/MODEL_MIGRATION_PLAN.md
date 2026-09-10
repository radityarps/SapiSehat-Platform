# Three-output model migration plan

## Goal

Replace active backend and Flutter inference with the verified MobileNetV3 model whose raw ordered outputs are `non_sapi`, `pmk`, and `sehat`. Backend and Flutter map them respectively to canonical `non_cattle`, `FMD`, and `healthy` outcomes while keeping the existing scan, sync, history, evidence, and dashboard flows substantially unchanged.

`non_cattle` is an input rejection, not an **Active Detection Class**. New accepted evidence uses only `FMD` and `healthy`. Existing `LSD` data remains unchanged, but active inference and product UI must not create or advertise new LSD results.

## Blocking input

Before implementation, supply the matching `.keras` and `.tflite` artifacts with:

- model version and source training run;
- SHA-256 checksums;
- input/output shape and dtype;
- exact raw class order, canonical label mapping, and preprocessing contract;
- a small labelled verification set containing FMD, healthy, and non-cattle examples.

Do not activate either model until both artifacts satisfy the contract in `docs/adr/0005-three-output-fmd-model-contract.md` and produce the same top class on the verification set.

## Implementation scope

### Backend

- Replace the active model artifact and metadata without retaining fake inference fallback.
- Preprocess images as EXIF-corrected RGB Float32 `[1,224,224,3]` values in `[0,255]`.
- Validate tensor count, shape, dtype, finite probabilities, probability range/sum, exact raw output order, and canonical mapping before readiness.
- Return accepted FMD/healthy predictions through the existing result flow.
- Return `non_cattle` as typed `422 NON_CATTLE_IMAGE`; stop before disease evidence, fusion, review items, cluster signals, and farmer advice.
- Make new image/NLP evidence and fusion payloads contain exactly FMD and healthy scores.
- Reject new active LSD writes. Keep existing LSD rows readable and unchanged.

### Flutter Farmer App

- Replace the bundled TFLite artifact and metadata with the verified pair.
- Use the same input preprocessing, raw output order, and canonical mapping as the backend, with no fallback class order or model version.
- Represent `non_cattle` as a rejection flow rather than a disease result.
- Keep online-first behavior and use offline inference only for connectivity or backend-availability failures.
- Send only FMD/healthy scores for new evidence and sync payloads.
- Remove active LSD labels, filters, guide content, result advice, and fabricated LSD scores.

### Next.js TanStack Dashboard

- Remove LSD from active filters, cards, tables, summaries, copy, and seed/demo data.
- Preserve existing jurisdiction, review, follow-up, and monitoring flows for FMD.
- Do not delete or rewrite historical LSD records. A new historical export/admin feature is deferred unless separately requested.

`apps/mobile-android-legacy` and model training are out of scope.

## Acceptance checks

- Backend and Flutter both read raw indexes as `0=non_sapi`, `1=pmk`, `2=sehat` and map them as `non_sapi→non_cattle`, `pmk→FMD`, `sehat→healthy`.
- The same verification images produce the same top class online and offline within an agreed score tolerance recorded with the artifacts.
- FMD and healthy continue through the existing accepted-result flow.
- Non-cattle produces a rejection and creates no disease evidence or downstream risk object.
- New active payloads, APIs, and UI contain no LSD class or fabricated LSD score.
- Existing LSD database rows remain unchanged and readable through existing authorized compatibility paths, if any.
- Backend tests, Flutter tests/analyze, dashboard checks, and one physical Android smoke test pass.

## Rollout

Release backend compatibility first, then deploy the verified backend model and matching Flutter model version. Roll back by restoring the previous matching model/contract pair; never relabel or delete records produced by either version.

## Deferred until requested

- A dedicated historical LSD CSV export or new admin surface.
- Telemetry-driven retired-client ingestion and retirement policy.
- Broader dashboard redesign.
- Changes to fusion weighting beyond removing LSD from new evidence.
