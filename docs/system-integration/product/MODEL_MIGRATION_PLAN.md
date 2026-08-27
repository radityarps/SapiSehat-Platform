# Three-output model migration plan

## Target contract

- Active accepted results: `FMD`, `healthy`.
- Input rejection: `non_cattle`; never fuse or persist it as disease evidence.
- Tensor order: `0=FMD`, `1=healthy`, `2=non_cattle`.
- Input: one RGB Float32 tensor `[1,224,224,3]`, raw values `[0,255]`, with MobileNetV3 internal rescaling.
- Output: one Float32 tensor `[1,3]` containing finite probabilities in `[0,1]` that sum to one.
- Deployment targets: FastAPI backend and active Flutter app. `apps/mobile-android-legacy` remains unchanged.
- `LSD` is historical-only: preserve stored rows unchanged, expose them only through admin/export compatibility paths, and prohibit new active inference results.

## Phase 0 — Artifact gate

1. Import the three-output `.keras` and `.tflite` artifacts without changing active model paths.
2. Generate authoritative metadata for both artifacts: version, SHA-256, byte size, architecture, tensor contract, class order, preprocessing, and source training run.
3. Fail the migration if either artifact does not match the target contract.
4. Run a shared golden corpus through Keras and TFLite. Require identical top class, bounded score drift, explicit FMD/healthy/non-cattle cases, corrupted-image rejection, and representative former-LSD images. Former-LSD images have no required replacement label, but must not produce an LSD field or class.
5. Record evaluation metrics for FMD, healthy, and non-cattle before rollout. Do not infer quality from tensor compatibility alone.

## Phase 1 — Centralize the active contract

1. Define one backend active-output constant `['FMD', 'healthy', 'non_cattle']` and one evidence-class constant `['FMD', 'healthy']`.
2. Replace fallback/default MobileNetV2 metadata and paths with the imported MobileNetV3 artifact metadata. Production must fail closed when the model is absent; do not use deterministic fake inference for the migrated contract.
3. Make model loading validate input/output count, shape, dtype, class order, finite probabilities, and warm-up results before marking the service ready.
4. Keep persisted-label compatibility separate from active outputs: database constraints may continue allowing `LSD` for old rows, but write services must reject LSD unless the request is the historical-sync path with an explicitly retired model version.
5. Version the API/model contract so logs and stored results identify whether a record came from the retired or active classifier.

## Phase 2 — Backend inference and API

1. Replace backend preprocessing with the new model contract: EXIF transpose, RGB conversion, bilinear resize to 224×224, Float32 `[0,255]`, and batch dimension.
2. Replace the active model artifact and class metadata. Remove the MobileNetV2 compatibility patch and development fallback if the new artifact does not need them.
3. Change prediction construction to three ordered scores. Treat `non_cattle` as a typed `422 NON_CATTLE_IMAGE` rejection with confidence, scores, model version, and timing; do not return it as `DiseaseClass`.
4. Restrict accepted prediction schema values to `FMD`, `healthy`, and insufficient-evidence states. Remove active `LSD` display mapping and two-stage assumptions tied to three disease scores.
5. Keep confidence/margin policy only for accepted cattle results. Define reliability after non-cattle rejection, not before it.
6. Update health/model-status output to expose the new version and active class order.

## Phase 3 — Evidence, fusion, and persistence

1. Change new `ImageEvidenceRequest` and `NlpEvidenceRequest` contracts from exactly `{healthy,FMD,LSD}` to exactly `{healthy,FMD}`. `top_class` must be one of those two keys.
2. Reject `non_cattle` before evidence creation and fusion. It must not create fusion rows, detection events, review items, cluster signals, or farmer advisories.
3. Update fusion logic and examples to operate only on FMD/healthy evidence. Remove fabricated LSD scores from Flutter sync payloads, placeholders, seed builders, and tests.
4. Add an explicit historical offline-sync branch: accept LSD only when the payload carries an allow-listed retired model version and historical/offline provenance. Validate and store it unchanged; do not feed it into current fusion, review, cluster, or advisory calculations.
5. Keep database check constraints allowing LSD so existing rows remain readable. Add service-level active-write validation rather than rewriting or deleting historical rows.
6. Exclude LSD rows from normal monitoring/list endpoints and active aggregates. Provide a separately authorized admin/export query that includes historical LSD records and model version.

## Phase 4 — Flutter on-device inference

1. Replace `assets/model/cattle_disease.tflite` and `model_metadata.json` with the verified MobileNetV3 Float32 three-output artifact.
2. Make metadata strict and authoritative: no fallback class order or fallback model version. Validate asset name, checksum where practical, input size, input/output shape and dtype, preprocessing, and exact class order.
3. Change preprocessing from `/255` nested values to raw RGB Float32 `[0,255]` after EXIF correction and bilinear resize. Prefer a typed contiguous input buffer supported by `tflite_flutter`; avoid adding another dependency.
4. Validate one input/one output, `[1,224,224,3]` Float32 input, `[1,3]` Float32 output, finite values, range, and probability sum before mapping results.
5. Map index 0 to FMD, 1 to healthy, and 2 to non-cattle. Return non-cattle as a rejection outcome, not a normal `ScanResult` disease label.
6. Preserve online-first behavior, but fall back offline only for connectivity/server-availability failures. Do not hide backend contract or parsing failures behind offline inference.
7. Send only FMD/healthy evidence scores for new sync/fusion payloads. Include model version and rejection outcome in queued records so the backend can distinguish active results from retired-client history.

## Phase 5 — Remove active LSD product behavior

1. Remove LSD from farmer-facing onboarding, guide categories/articles/search hints, scan result advice, active history, filters, and new-result copy.
2. Remove LSD from agency active filters, cards, monitoring tables, risk summaries, seed data, and active API descriptions. Do not delete old database rows.
3. Add a restricted admin/export compatibility surface for historical LSD rows. Label them as retired-model history and include model version and timestamp.
4. Replace product text such as “PMK & LSD” with FMD/PMK early detection plus explicit non-cattle rejection wording.
5. Leave `apps/mobile-android-legacy` untouched as requested, but mark its bundled model and LSD behavior as retired/non-release reference in its README.
6. Separate dataset tooling scope from runtime scope: keep old LSD datasets immutable for reproducibility, but create a new three-output manifest/workflow rather than silently redefining existing canonical datasets.

## Phase 6 — Tests and release gates

1. Backend unit/contract tests:
   - exact model/tensor/class-order validation;
   - FMD and healthy success responses;
   - non-cattle typed rejection;
   - no LSD in active prediction/evidence/OpenAPI examples;
   - two-class fusion behavior;
   - active writes reject LSD;
   - allow-listed retired offline sync preserves LSD;
   - normal reads/aggregates exclude historical LSD;
   - admin/export can retrieve historical LSD.
2. Flutter tests:
   - raw `[0,255]` preprocessing and EXIF orientation;
   - three-score mapping and tensor mismatch failure;
   - non-cattle rejection flow;
   - online/offline parity on the golden corpus;
   - no active LSD guide/filter/result UI;
   - queued retired-version LSD compatibility fixture remains serializable if required for old queue import.
3. Integration tests:
   - same image yields the same top class online and offline;
   - non-cattle creates no evidence, fusion, review item, or cluster signal;
   - FMD creates the expected evidence/follow-up path;
   - healthy creates no risky review item;
   - historical LSD remains exportable but absent from active screens.
4. Run backend tests, Flutter tests/analyze, database migration tests, and a physical Android smoke test before release.

## Rollout and rollback

1. Release the backend compatibility layer first: new inference contract plus retired-client historical sync handling.
2. Activate the validated Keras model, then release Flutter with the matching TFLite/model version.
3. Observe non-cattle rejection rate, FMD/healthy distribution, confidence distribution, online/offline disagreement, inference latency, and old-client LSD sync count.
4. Do not roll back by relabeling records. Roll back by reactivating the previous model/version and matching API contract while preserving records with their original model versions.
5. Remove retired-client LSD ingestion only after the supported old-app queue window has elapsed and telemetry shows no remaining sync traffic.

## Done when

- Backend and Flutter use the same verified three-output model family and class order.
- New inference can produce only FMD, healthy, or non-cattle rejection.
- New fusion accepts only FMD/healthy evidence.
- No active UI advertises or filters LSD.
- Existing LSD rows are unchanged, hidden from active product surfaces, and available through authorized admin/export.
- Golden-corpus parity and full integration tests pass, with a documented rollback artifact pair.
