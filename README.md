# SapiSehat

Aplikasi Android untuk deteksi penyakit sapi (PMK dan Lato-Lato) menggunakan foto, berbasis model CNN MobileNetV2.

**Tim:** Raditya Rafif Pratama Sasmita & Noval Putra Ramadhan  
**Institusi:** Politeknik Negeri Semarang — Teknik Informatika  
**Deadline:** Juni 2026 (field testing), Juli 2026 (sidang)

---

## Struktur Repositori

```
sapisehat/
├── apps/
│   ├── backend/          # FastAPI inference server (Python)
│   └── mobile/           # Android app (Kotlin)
├── docs/
│   ├── architecture/     # System architecture documentation
│   ├── backend/          # Backend API & migration docs
│   ├── mobile/           # Mobile app documentation
│   ├── changelog.md      # Version history
│   └── PRD.md            # Product Requirements Document
├── package.json          # pnpm scripts (build, deploy, test)
└── .gitignore
```

---

## Quick Start

### Prerequisites

| Tool           | Version  | Keperluan                          |
| -------------- | -------- | ---------------------------------- |
| Node.js        | 18+      | Monorepo scripts                   |
| pnpm           | 10+      | Package manager                    |
| Docker         | 24+      | Backend containerized              |
| Android SDK    | API 24+  | Mobile (Android Studio opsional)   |
| adb            | latest   | Deploy & debug ke device           |

### Backend

```bash
# Build & jalankan (dari root)
pnpm backend:up

# Development (hot reload)
pnpm backend:dev

# Lihat logs
pnpm backend:logs

# Stop
pnpm backend:down
```

Backend berjalan di `http://localhost:8000`. Docs: `http://localhost:8000/docs`

### Mobile

Tidak perlu Android Studio. Pastikan device terhubung via USB atau WiFi (lihat [Wireless Debugging](docs/Mobile/WIRELESS-DEBUGGING.md)).

```bash
# Build + install + launch di device
pnpm mobile:run

# Build + install saja
pnpm mobile:deploy

# Restart app tanpa rebuild
pnpm mobile:restart

# Lihat logs
pnpm mobile:log

# Clean build
pnpm mobile:clean
```

Atur Server URL dari dalam aplikasi: **Settings → Server URL** (tanpa rebuild).

---

## Apps

### `apps/backend` — FastAPI Inference Server

- **Tech:** Python 3.10, FastAPI, TensorFlow, MobileNetV2
- **Model:** `mobilenetv2_best.keras` (~20MB, tersedia via Docker volume mount)
- **Endpoint:** `POST /api/predict` — terima gambar sapi, return diagnosis
- **Docs:** [API reference](docs/backend/README.md)
- **Dev guide:** [docs/backend/development.md](docs/backend/development.md)

```bash
make backend-run       # Development (hot reload)
make backend-test      # Run unit tests
make backend-docker    # Build & run via Docker
```

### `apps/mobile` — Android App

- **Tech:** Kotlin, Jetpack Compose, MVVM, Hilt, Room, CameraX, TFLite (offline fallback)
- **Min SDK:** API 24 (Android 7.0)
- **Docs:** [Mobile setup](docs/Mobile/README.md) | [Wireless Debugging](docs/Mobile/WIRELESS-DEBUGGING.md)

```bash
pnpm mobile:run        # Build + install + launch
pnpm mobile:deploy     # Build + install
pnpm mobile:restart    # Restart tanpa rebuild
pnpm mobile:log        # Logcat filtered
pnpm mobile:clean      # Clean build cache
pnpm mobile:test       # Run unit tests
```

---

## Workflow Development

### Jalankan backend

```bash
pnpm dev
```

Ini menjalankan backend via Docker Compose.

### Cek semua test

```bash
pnpm test
```

---

## Model File

File model **tidak di-commit** ke git karena ukurannya besar (~20MB).

Cara setup:

1. Pastikan file `mobilenetv2_best.keras` ada di `apps/backend/model/`
2. Untuk development dengan Docker: file model otomatis tersedia via volume mount
3. Untuk Android offline: gunakan `cattle_disease.tflite` di `apps/mobile/app/src/main/assets/`
4. Jika ingin mengganti model offline, replace file dengan nama yang sama: `cattle_disease.tflite`

---

## Docs

| Dokumen                                                                                          | Deskripsi                               |
| ------------------------------------------------------------------------------------------------ | --------------------------------------- |
| [docs/architecture/overview.md](docs/architecture/overview.md)                                   | System architecture & data flow         |
| [docs/backend/README.md](docs/backend/README.md)                                                 | Backend API reference & setup           |
| [docs/backend/development.md](docs/backend/development.md)                                       | Backend development guide               |
| [docs/mobile/README.md](docs/mobile/README.md)                                                   | Mobile app documentation                |
| [docs/changelog.md](docs/changelog.md)                                                           | Version history                         |
| [docs/backend/migration/01-overview.md](docs/backend/migration/01-overview.md)                   | Arsitektur backend & rencana migrasi Go |
| [docs/backend/migration/02-go-gateway.md](docs/backend/migration/02-go-gateway.md)               | Implementasi Go Gateway (Phase 3)       |
| [docs/backend/migration/04-migration-runbook.md](docs/backend/migration/04-migration-runbook.md) | Langkah-langkah migrasi ke Go           |

---

## Branching Strategy

```
main          ← production-ready code only
dev           ← integration branch
feat/xxx      ← fitur baru (dari dev)
fix/xxx       ← bug fix (dari dev)
```

```bash
# Mulai fitur baru
git checkout dev
git checkout -b feat/nama-fitur

# Selesai → PR ke dev
# Setelah testing → PR dari dev ke main
```
