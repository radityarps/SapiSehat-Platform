# SapiSehat Platform

SapiSehat adalah platform early detection penyakit sapi untuk peternak dan instansi. Platform mencakup aplikasi farmer mobile, profil ternak lengkap, bukti image Team 1, bukti NLP Team 2, backend fusion, target database PostgreSQL, dan dashboard agency. Modul image MobileNetV2 tetap ada sebagai subsystem Team 1, bukan seluruh produk.

**Tim:** Raditya Rafif Pratama Sasmita & Noval Putra Ramadhan  
**Institusi:** Politeknik Negeri Semarang — Teknik Informatika  
**Deadline:** Juni 2026 (field testing), Juli 2026 (sidang)

## Product Scope

SapiSehat provides disease early detection support, not veterinary diagnosis.

Core capabilities:

- farmer phone-number account
- complete cattle/livestock profile
- image evidence contract for FMD/LSD/healthy signals
- NLP questionnaire/notes evidence contract
- backend-primary fusion with offline sync support
- role + jurisdiction + consent agency access
- agency dashboard for disease risk signals, not confirmed outbreaks
- stored media governance with consent opt-in

Current executable implementation is FastAPI/in-memory tracer proving platform contracts. Target production architecture: Go gateway + Python inference services + PostgreSQL + Next.js/TanStack dashboard.

## Repository Structure

```text
sapisehat/
├── apps/
│   ├── backend/          # FastAPI contract tracer + Python inference prototype
│   ├── dashboard/        # Next.js/TanStack agency dashboard tracer
│   └── mobile/           # Android farmer app / legacy image mobile app
├── docs/
│   ├── README.md              # documentation routing and ownership
│   ├── system-integration/    # shared platform contracts
│   ├── team-1-image/          # image subsystem docs
│   ├── team-2-nlp/            # NLP subsystem docs
│   ├── adr/                   # architecture decision records
│   └── changelog.md           # version history
├── .github/              # issue and PR templates
├── CONTRIBUTING.md       # contribution rules
├── LICENSE
├── package.json
└── .gitignore
```

## Documentation

Start at [docs/README.md](docs/README.md). Shared platform contracts live in [docs/system-integration/README.md](docs/system-integration/README.md).

| Need | Document |
| --- | --- |
| Platform scope | [docs/system-integration/product/PLATFORM_SCOPE.md](docs/system-integration/product/PLATFORM_SCOPE.md) |
| Shared API/fusion contracts | [docs/system-integration/api-contracts/FUSION_CONTRACT.md](docs/system-integration/api-contracts/FUSION_CONTRACT.md) |
| Data model | [docs/system-integration/database/DATA_MODEL.md](docs/system-integration/database/DATA_MODEL.md) |
| Team 1 image work | [docs/team-1-image/README.md](docs/team-1-image/README.md) |
| Team 2 NLP work | [docs/team-2-nlp/README.md](docs/team-2-nlp/README.md) |
| Dashboard contracts | [docs/system-integration/web-dashboard/README.md](docs/system-integration/web-dashboard/README.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

Legacy image-first docs remain for historical subsystem context. They must not override system-integration contracts.

## Quick Start

### Prerequisites

| Tool | Version | Use |
| --- | --- | --- |
| Node.js | 18+ | monorepo scripts |
| pnpm | 10+ | package manager |
| Python | 3.10+ | backend tracer/inference prototype |
| Docker | 24+ | backend containerized flow |
| Android SDK | API 24+ | farmer mobile app |
| adb | latest | device deploy/debug |

### Backend Tracer

```bash
pnpm backend:up
pnpm backend:dev
pnpm backend:logs
pnpm backend:down
```

Backend runs at `http://localhost:8000`. OpenAPI docs: `http://localhost:8000/docs`.

Focused test command:

```bash
python -m pytest apps/backend/tests -q
```

### Mobile

No Android Studio required for scripted deploy. Connect device via USB or WiFi. See [Wireless Debugging](docs/system-integration/mobile/WIRELESS-DEBUGGING.md).

```bash
pnpm mobile:run
pnpm mobile:deploy
pnpm mobile:restart
pnpm mobile:log
pnpm mobile:clean
pnpm mobile:test
```

Set Server URL in app: **Settings → Server URL**.

### Dashboard

Dashboard tracer lives in `apps/dashboard` and targets Next.js + TanStack table patterns.

Important routes:

- `/agency/registry`
- `/agency/detections`
- `/agency/risk-signals`

## Current Tracer APIs

Representative endpoints:

- `POST /api/farmers/accounts`
- `POST /api/farmers/{farmer_id}/cattle`
- `POST /api/evidence/image`
- `POST /api/evidence/nlp`
- `POST /api/fusion/results`
- `POST /api/offline/detections/sync`
- `GET /api/agency/registry`
- `GET /api/agency/detection-monitoring`
- `GET /api/agency/risk-signals`

## Model Files (Team 1 Image Subsystem)

Model files are not committed because they are large.

Expected local files:

1. `apps/backend/model/mobilenetv2_best.keras` for server image inference prototype.
2. `apps/mobile/app/src/main/assets/cattle_disease.tflite` for offline image evidence prototype.

Image model outputs are early detection signals only. They are not veterinary diagnosis.

## Safe Language Policy

Use:

- early detection
- evidence
- disease risk signal
- possible increased risk
- follow-up priority
- needs review

Avoid:

- confirmed outbreak
- diagnosis
- infected/positive case
- certificate/proof of disease

## Development Workflow

```text
main          <- production-ready code
dev           <- integration branch
feat/xxx      <- feature branch
fix/xxx       <- bug fix branch
docs/xxx      <- documentation branch
```

Before PR:

```bash
python -m pytest apps/backend/tests -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contract-first rules and PR checklist.

## License

MIT. See [LICENSE](LICENSE).
