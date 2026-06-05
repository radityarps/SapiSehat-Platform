# SapiSehat Mobile (Implementation Start)

Android app scaffold for SapiSehat using:

- Kotlin
- Jetpack Compose + Navigation Compose
- MVVM + Hilt
- Room
- Retrofit/OkHttp
- TensorFlow Lite

## Current status

This initial implementation includes:

- Project structure and Gradle setup
- Domain models and API DTO contracts
- Room schema for detection history
- Preprocessing and inference routing scaffold
- Compose navigation and MVP placeholder screens
- Runtime server URL setting via `Settings -> Server URL`
- Persisted scan image path for history preview (local file copy)
- **Retake/repeat scan feature**: Press "Retake" on any scan result to re-scan and update the existing history entry instead of creating a duplicate. New scans automatically replace old entries in the database.

## Dependencies

Key dependencies and their roles:

### Build system

| Technology       | Version       | Purpose                        |
| ---------------- | ------------- | ------------------------------ |
| Gradle           | 9.4.1         | Build system                   |
| AGP              | 9.2.1         | Android Gradle Plugin          |
| Kotlin           | 2.2.10        | Programming language           |
| KSP              | 2.2.10-2.0.2  | Symbol processing (Hilt, Room) |
| Compose BOM      | 2024.09.00    | Jetpack Compose UI toolkit     |
| Compose Compiler | Kotlin 2.2.10 | Built into Kotlin plugin       |

### Runtime libraries

| Library         | Version | Purpose                       |
| --------------- | ------- | ----------------------------- |
| Hilt            | 2.59    | Dependency injection          |
| Hilt Navigation | 1.2.0   | Hilt + Compose Navigation     |
| Room            | 2.6.1   | Detection history persistence |
| Retrofit        | 2.11.0  | HTTP API client               |
| OkHttp          | 4.12.0  | HTTP transport                |
| Moshi           | 2.11.0† | JSON deserialization          |
| moshi-kotlin    | 1.15.1  | Kotlin adapter for Moshi JSON |
| CameraX         | 1.3.4   | Camera capture                |
| TFLite          | 2.17.0  | On-device inference           |
| ExifInterface   | 1.3.7   | EXIF orientation correction   |
| Coil            | 2.6.0   | Image loading                 |
| DataStore       | 1.0.0   | Settings / preferences        |
| Coroutines      | 1.8.1   | Async programming             |

† Moshi version is inherited from the Retrofit converter artifact.

### KSP2 compatibility note

This project uses KSP `2.2.10-2.0.2` (KSP2). Room 2.6.1 does not fully support KSP2 yet,
so `ksp.useKSP2=false` is set in `gradle.properties` to force KSP1 mode for the Room
annotation processor. This allows Room to work correctly while keeping the newer KSP plugin.

Hilt 2.59 natively supports both KSP1 and KSP2 via its Gradle plugin.

## Run

Anda **tidak perlu Android Studio** untuk build dan deploy. Cukup pastikan device terhubung via USB atau WiFi.

### Connect device

- **USB:** Colokkan kabel, aktifkan USB Debugging di Developer Options
- **WiFi:** Lihat [WIRELESS-DEBUGGING.md](./WIRELESS-DEBUGGING.md) untuk setup wireless ADB

Verifikasi koneksi:

```bash
adb devices
```

### Build & deploy (dari root monorepo)

```bash
# Build + install + launch
pnpm mobile:run

# Build + install saja
pnpm mobile:deploy

# Restart app tanpa rebuild
pnpm mobile:restart

# Lihat logs (filtered)
pnpm mobile:log

# Clean build cache
pnpm mobile:clean

# Run unit tests
pnpm mobile:test
```

### Server URL

Application ID: `com.sapisehat.app`

Default base URL (emulator): `http://10.0.2.2:8000/`

Untuk physical device / LAN testing, ubah URL langsung di dalam app:

- **Settings → Server URL** (contoh: `http://192.168.18.4:8000/`)

## Required model file

Place model in:

- app/src/main/assets/cattle_disease.tflite

This repository already includes `cattle_disease.tflite` in the assets folder.
If you retrain/replace the model, keep the same filename.

## Label conventions

All classification uses canonical labels matching `../../apps/backend/model/class_names.json`:

| Label     | Display                       | Indonesian Name        |
| --------- | ----------------------------- | ---------------------- |
| `FMD`     | Penyakit Mulut dan Kuku (FMD) | Foot and Mouth Disease |
| `LSD`     | Penyakit Lumpy Skin (LSD)     | Lumpy Skin Disease     |
| `healthy` | Sapi Sehat                    | Healthy                |

Both online API responses and offline TFLite outputs use these keys in `allScores`.
Display labels provide Indonesian translations on the result and history screens.

## Preprocessing

Preprocessing is split into two stages:

1. **Client-side** (before upload): EXIF correction, resize max 800×800px, JPEG compress quality 85%
2. **Model-side** (before inference): resize to 224×224px, rescale pixels to [0, 1] range via `/255.0`

The model-side preprocessing is identical on both mobile (Kotlin) and backend (Python) —
no ImageNet mean/std normalization is applied. This matches the model's training pipeline.

## Database migration

Room database version is 7. Migration history:

| Version | Change |
|---------|--------|
| 3 | Added `imagePath` column for stored scan images |
| 4–5 | Schema refinements (destructive migration for pre-release builds) |
| 6 | Added `appVersion` and `modelVersion` columns to `detection_records` |
| 7 | Added `imageSource`, `preprocessingSummary`, `latitude`, `longitude`, `deletedAt`, `pdfCachePath` columns to `detection_records` |

Migrations 5→6 and 6→7 are non-destructive (ALTER TABLE ADD COLUMN). Earlier migrations may
use destructive fallback, which is acceptable for pre-release builds.

## Troubleshooting

### API not working on mobile but working on Postman

**Symptom:** Backend health check works in Postman/curl, but the Android app shows no API logs in Docker. Logcat shows `InferenceRouter: online failed, falling back to offline`.

**Common causes and fixes:**

| Issue                          | Check                                                       | Fix                                                                                                                          |
| ------------------------------ | ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Cleartext HTTP blocked         | Logcat: `Cleartext HTTP traffic not permitted`              | Ensure `AndroidManifest.xml` has `android:usesCleartextTraffic="true"` (needed for `http://10.0.2.2:8000/`)                  |
| Moshi serialization error      | Logcat: `Unable to create converter for PredictResponseDto` | Ensure `moshi-kotlin` dependency is in `build.gradle.kts` and `KotlinJsonAdapterFactory` is registered in `NetworkModule.kt` |
| Backend not running            | `curl http://localhost:8000/api/health` fails               | Run `docker compose up -d` in `apps/backend/`                                                                                |
| Physical device (not emulator) | `10.0.2.2` only works on emulator                           | Open app `Settings -> Server URL`, then set machine LAN IP (e.g., `http://192.168.1.100:8000/`)                               |
| Camera capture fails silently  | No `Camera: takePhoto()` log                                | Ensure camera permission is granted; check for `Camera: binding failed` or `Camera: takePicture() threw` logs                |

### Debugging with Logcat

Filter logs by the app's diagnostic tag:

```bash
adb logcat -s SapiSehat:*
```

Expected healthy pipeline trace:

```
Camera: takePhoto() triggered
Camera: image saved successfully, uri=...
ViewModel: classify() called with uri=...
InferenceRouter: classify() started, uri=...
InferenceRouter: preprocessed image — XXXXX bytes
InferenceRouter: isOnline=true, routing to ONLINE
OnlineInferenceClient: sending predict request (XXXXX bytes)
OnlineInferenceClient: response received — status=success, prediction=FMD
ViewModel: classify() success — label=FMD, confidence=0.85, mode=ONLINE
```

### Moshi Kotlin adapter

The project requires `moshi-kotlin` for JSON serialization of Kotlin data classes (`PredictResponseDto`, `PredictionDto`). The `NetworkModule` must use `KotlinJsonAdapterFactory`:

```kotlin
MoshiConverterFactory.create(
    Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
)
```

Without this, Moshi falls back to Java reflection which cannot handle Kotlin types and throws `IllegalArgumentException: Cannot serialize Kotlin type`.

## PDF Report Generation

The app can generate a shareable PDF report for any detection result via `PdfReportGenerator`.

**How it's triggered:**
- The result screen's **Share** button generates the PDF and immediately opens the Android share sheet (`ACTION_SEND`, `application/pdf`) so the report can be sent to any app.
- There is no separate "Export PDF" button — sharing and exporting are unified into the single Share action. The generated file path is persisted to `pdfCachePath` for saved detections.
- Plain-text/image sharing has been removed; the report is always shared as a PDF.

**Report contents:**
- Captured cattle image (scaled to fit)
- Detection result: early indication label, confidence %, reliability flag
- All class scores breakdown
- Technical metadata: app version, model version, preprocessing summary, inference mode
- Consent status and coarse location (if available, GPS or manual)
- Device info (Android version, manufacturer, model)
- Disclaimer stating this is an AI early indication, not a veterinary diagnosis

**Privacy by design — excluded from reports:**
- IMEI / serial number
- Account ID / user identity
- Precise GPS coordinates (only coarse 2-decimal format)

**Implementation details:**
- Uses Android's `PdfDocument` API (no third-party PDF library)
- Output saved to `{cacheDir}/reports/report_{id}_{timestamp}.pdf`
- The `pdfCachePath` column in Room (added in DB v7) stores the generated file path
- Shared via `FileProvider` using the `${packageName}.fileprovider` authority
- Singleton via Hilt (`@Singleton`, `@Inject constructor`)
- Returns `null` on failure (non-throwing)

## Next implementation slices

1. Camera/gallery real image selection flow
2. Result screen score bars + recommendation text
3. Robust error mapping and retry UX
4. Instrumented tests for offline fallback matrix
