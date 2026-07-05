# sapisehat_mobile

Flutter farmer app for SapiSehat — cattle disease early-detection platform for Indonesian farmers.

## Stack

- Flutter 3.x / Dart 3.x
- Riverpod (`flutter_riverpod`) for state management
- `geolocator` for GPS address auto-fill
- `http` for Nominatim reverse geocoding
- `flutter_dotenv` for API base URL config
- `flutter_svg` for onboarding illustrations
- On-device TFLite inference fallback via `offline_inference.dart` (`tflite_flutter` + `image`)

## Quick start

```bash
# Install dependencies
flutter pub get

# Run on connected device / emulator (debug mode)
pnpm mobile:run

# Build debug APK
pnpm mobile:build

# Deploy to connected device
pnpm mobile:deploy
```

## Environment

Copy `.env.example` to `.env` and set `SAPISEHAT_API_BASE_URL`:

```env
SAPISEHAT_API_BASE_URL=http://10.0.2.2:8000   # Android emulator → host
```

In debug mode (`kDebugMode = true`), login and register fields are pre-filled with dev credentials:

| Field | Value |
|-------|-------|
| Email | `farmer@example.com` |
| Password | `strong-password` |
| Name | `Demo Farmer` |
| Jurisdiction | `tembalang` |

In release builds, all fields are empty.

## Navigation

Bottom navigation (5 tabs):

| Tab | Screen | Description |
|-----|--------|-------------|
| Sapi | `CattleScreen` | Cattle list, create, edit, status |
| Scan | `ScanScreen` | Camera scan (online) + offline fallback |
| Riwayat | `HistoryScreen` | Backend-first detection history with pending-local fallback |
| Panduan | `GuideScreen` | Safe farmer guidance |
| Setelan | `SettingsScreen` | Profile card, preferences, logout confirmation, archive |

Profile editing is accessed from Settings → "Edit profil" button.

## Features

- **Farmer login / register** — email/password with input validation and terms checkbox
- **GPS address auto-fill** — Nominatim reverse geocode fills address + district on edit profile and register
- **Cattle CRUD** — list, create, edit, archive cattle profiles
- **Camera scan** — online-first flow: `/api/predict` produces image evidence, then `/api/fusion/results` stores backend-primary result. If online save fails, result is kept as local `pending_sync` fallback.
- **Offline TFLite fallback** — on-device inference when backend/network prediction fails. Assets live under `assets/model/` and include `model_metadata.json`. Preprocessing decodes image, applies EXIF orientation, resizes to `224x224`, and rescales RGB to `1/255`.
- **Detection history** — backend results are source of truth when reachable; pending local results appear as fallback. Matching local image paths are merged into backend cards so scan thumbnails remain visible. Manual pull-to-refresh is supported.
- **Result management** — detection result detail and history cards can reassign linked cattle, delete scan results with success/failure toasts, and export/share PDF without exposing raw cattle IDs.
- **Cattle display** — cattle name is primary text, tag is secondary; selectors and detection results use `{name} ({tag})`, with `Belum dikaitkan` when no linked cattle is available.
- **Settings** — notification preferences, profile card, logout confirmation with success/failure toasts, and account archive.

## Permissions (Android)

Declared in `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

Location permission is requested at runtime only when the GPS button is tapped on the address field. A custom dialog explains the reason before the OS prompt appears.

## Seeded dev accounts

| Email | Password | Jurisdiction |
|-------|----------|-------------|
| `farmer@example.com` | `strong-password` | tembalang |
| `farmer2@example.com` | `strong-password` | banyumanik |
