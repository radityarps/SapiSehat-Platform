# Changelog

All notable changes to the SapiSehat project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-05-04

### Added

- FastAPI backend with TensorFlow inference server
- MobileNetV2 CNN model for cattle disease classification (3 classes: FMD, LSD, healthy)
- `/api/predict` endpoint — image classification with confidence scores
- `/api/health` endpoint — model and server health monitoring
- `/api/model/status` endpoint — detailed model information
- Docker containerization with multi-stage build
- Docker Compose development setup with hot-reload
- Android mobile app scaffold (Kotlin, Jetpack Compose, MVVM)
- Offline inference fallback via TensorFlow Lite
- Two-stage image preprocessing (client-side + model-side)
- Singleton model loader for memory efficiency
- Structured JSON logging
- Unit tests for inference service
- CORS middleware for mobile app communication
- Structured error handling with custom exceptions

### Changed

- Migrated model framework from PyTorch to TensorFlow/Keras
- Updated classification labels to FMD, LSD, healthy
- Model format: `.keras` (TensorFlow native)
- Preprocessing pipeline: simplified to rescale normalization

### Technical Details

- **Model:** MobileNetV2, 2.4M parameters
- **Input size:** 224×224×3 (RGB)
- **Model size:** ~20 MB (.keras format)
- **Inference time:** ~100 ms (CPU)
- **Python:** 3.10+
- **TensorFlow:** 2.19+
- **FastAPI:** 0.115+

### Documentation

- Root README with project overview and quick start
- Backend README with API reference and setup guide
- Architecture documentation (ARCHITECTURE.md)
- Development guide (DEVELOPMENT.md)
- Product Requirements Document (PRD)
- Contributing guide (CONTRIBUTING.md)
- MIT License

## [Unreleased]

### Added

- **FastAPI platform backend foundation**: Added surface-specific farmer and agency auth, PostgreSQL-backed accounts, farmer-owned cattle records, detection records, follow-up workflow, cluster risk signals, scan image storage notice gate, archive-only behavior, and dashboard-ready agency APIs.
- **Private scan image object storage**: Added S3-compatible media upload path (`POST /api/media/uploads`), local MinIO development bucket, private object keys, media metadata persistence, and backend-issued signed URL endpoint for authorized agency image preview/download.
- **Production backend hardening**: Added production config guards for JWT secret, CORS origins, S3 bucket/credentials, and Google client ID when Google auth is enabled.
- **Backend audit logs**: Added persistent audit events for predictions, media uploads, signed media URL issuance, and follow-up creation, plus admin-only `GET /api/agency/audit-logs` read API.
- **Backend release smoke and root test entrypoint**: Added `apps/backend/scripts/release_smoke.sh`, optional real MinIO smoke test, and root `tests/test_backend_suite.py` so `python -m pytest tests -q` from repo root runs backend checks.
- **NLP placeholder and farmer advisory APIs**: Added `POST /api/evidence/nlp/placeholder` with no scores/fusion/risk side effects, plus `GET /api/farmers/{farmer_id}/area-advisory` for safe district-level farmer advisory from cluster risk signals.
- **Backend ops fixtures**: Added DB constraint/index audit tests, dashboard API contract fixture, and `apps/backend/scripts/backup_export.sh` for SQLite copy backup or PostgreSQL `pg_dump` export.
- **Retake/repeat scan feature**: Users can now press "Retake" on a scan result to re-scan and update the existing history entry instead of creating a duplicate. When retaking from history detail, the new scan replaces the old entry in the database. Implementation uses `NavigationViewModel` with StateFlow-based navigation triggers and `DetectionRepository.saveDetection(updateDetectionId)` to perform UPDATE (via Room's `OnConflictStrategy.REPLACE`) instead of INSERT.
- **Postman API collection**: Created `docs/Postman/SapiSehat API.postman_collection.json` with pre-built requests for `/api/health` and `/api/predict`, automated test scripts, and example responses (200 FMD, 200 Healthy, 422, 503).
- **Bruno API collection**: Replaced the legacy Postman JSON collection with `docs/system-integration/api-contracts/bruno/SapiSehat API.openapi.yaml`, a Bruno-importable OpenAPI YAML collection for `/api/health` and `/api/predict`.
- **Diagnostic logging**: Added structured `android.util.Log` tracing with tag `SapiSehat` across 4 files (`CameraRoute`, `CameraViewModel`, `InferenceRouter`, `OnlineInferenceClient`). Filterable via `adb logcat -s SapiSehat:*`. Logs cover the full pipeline: camera capture → classify trigger → isOnline decision → API request/response → final result.

### Changed

- **Moshi dependency**: Added explicit `moshi-kotlin:1.15.1` dependency (previously Moshi was inherited transitively from `converter-moshi:2.11.0` without Kotlin adapter support).
- **Gradle & AGP upgrade**: Upgraded Gradle from 8.x to 9.4.1 and AGP from 8.x to 9.2.1
- **Kotlin upgrade**: Upgraded Kotlin from 1.9.x to 2.2.10, with Compose Compiler bundled in the Kotlin plugin
- **Hilt upgrade**: Upgraded Hilt from 2.52 to 2.59 to resolve KSP2 incompatibility (`KspTaskJvm` class not found in KSP2). Hilt 2.59 natively supports both KSP1 and KSP2 task classes.
- **KSP upgrade**: Set KSP to 2.2.10-2.0.2 (KSP2-native plugin). Both Hilt and KSP plugins declared at root `build.gradle.kts` with `apply false` to avoid classloader isolation issues in Gradle 9.x.
- **Room KSP compatibility**: Added `ksp.useKSP2=false` to `gradle.properties` to force KSP1 mode for Room 2.6.1, which does not yet fully support KSP2 type signatures (`unexpected jvm signature V`)
- **Guide UX redesign**: Refactored Panduan into a blog-style list with article cards, search/filter toggles in the header, and a full article detail route.
- **16 KB packaging compatibility (debug path)**: Restricted packaged ABIs to ARM (`arm64-v8a`, `armeabi-v7a`) and upgraded CameraX to `1.4.2` to avoid shipping problematic `x86_64` native libraries in debug builds.

### Fixed

- **Cleartext HTTP blocked (API unreachable)**: Added `android:usesCleartextTraffic="true"` to `AndroidManifest.xml`. Android 9+ (API 28+) blocks cleartext HTTP by default, causing all `http://10.0.2.2:8000/` requests to fail with `IOException: Cleartext HTTP traffic not permitted`. This was the root cause of zero API logs in Docker despite Postman working correctly.
- **Moshi Kotlin serialization crash**: Added `moshi-kotlin:1.15.1` dependency and configured `KotlinJsonAdapterFactory` in `NetworkModule.kt`. Without it, Moshi refused to serialize Kotlin data classes (`PredictResponseDto`, `PredictionDto`), causing `IllegalArgumentException: Unable to create converter` on every API response.
- **CameraX silent capture failure**: Wrapped `ImageCapture.takePicture()` in try-catch and wired the `onError` callback to `onCaptureError()` (previously an empty comment). Capture failures now surface as Snackbar errors instead of being silently swallowed by Compose's click handler.
- **CameraX binding failures silently swallowed**: Replaced empty `catch (_: Exception) { }` in the camera binding code with `Log.e` + `onCaptureError()`. If `bindToLifecycle` fails, the user now gets an error message instead of a blank preview with no feedback.
- **`isOnline()` returning false on emulators**: Removed the `NET_CAPABILITY_VALIDATED` requirement from `InferenceRouter.isOnline()`. Emulators may not set this flag even when the host has full internet connectivity, causing the app to always skip online inference and fall back to offline (which crashes without TFLite model).
- **Mobile-backend label unification**: Unified all classification labels to canonical `FMD`/`LSD`/`healthy` across offline TFLite, Room database, and online API. Previously, offline used `SEHAT`/`PMK`/`LATO_LATO` causing same-disease history fragmentation.
- **Score key mismatch**: Fixed `DetectionRepository` to read scores by canonical keys (`FMD`/`LSD`/`healthy`) for both online and offline inference modes. Previously, online scores were silently stored as `0.0`.
- **Preprocessing alignment**: Changed mobile offline preprocessing from ImageNet mean/std normalization to simple rescale (`pixel / 255.0`), matching the backend `model_preprocessor.py`.
- **Display label persistence**: Added `displayLabel` column to `DetectionEntity` so history shows human-readable Indonesian names instead of raw class codes.
- **Database schema**: Bumped Room version to 2 with destructive migration (column renames: `scoreSehat→scoreHealthy`, `scorePmk→scoreFmd`, `scoreLatoLato→scoreLsd`).
- **Package namespace fix**: Changed Android `namespace`/`applicationId` from `"sapisehat"` to `"com.sapisehat.app"` to comply with Android's dotted package name requirement. Refactored all 26 Kotlin source files and directory tree.
- **Missing ExifInterface dependency**: Added `androidx.exifinterface:exifinterface:1.3.7` dependency required by `ClientPreprocessor.kt` for EXIF orientation correction.
- **TFLite Interpreter API fix**: Updated `OfflineInferenceEngine.kt` to wrap model bytes in `ByteBuffer` for TFLite 2.17.0 compatibility (constructor no longer accepts bare `ByteArray`).
- **App language switching**: Implemented per-app locale application flow (Settings + startup) so selecting English/Indonesian updates visible UI consistently across navigation labels and guide screens.
- **Localization coverage gaps**: Replaced hardcoded Indonesian labels in navbar, guide headers, guide filter chips, and guide detail UI with `stringResource(...)` backed by `values/strings.xml` and `values-en/strings.xml`.
- **Startup crash after locale migration**: Fixed `AppCompatActivity` theme mismatch by setting application theme to `Theme.AppCompat.Light.NoActionBar` in `AndroidManifest.xml`.
- **Text size setting now works app-wide**: Wired `settings_text_size` from DataStore into root Compose theme and added scalable `Typography` utilities so Small/Medium/Large apply immediately across screens.

### Planned

- Go gateway for high-concurrency scenarios
- Model quantization for faster inference
- Batch prediction endpoint
- Image quality validation endpoint
- Comprehensive instrumented tests for Android
- CI/CD pipeline with GitHub Actions
- Cloud deployment guides (GCP Cloud Run, AWS EC2)
