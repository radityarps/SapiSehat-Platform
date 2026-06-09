# Backend Contracts

Shared backend contracts live here.

Current first-release backend is the FastAPI platform backend under `apps/backend`. It owns auth boundaries, PostgreSQL persistence, farmer/cattle records, media metadata, private object storage integration, dashboard APIs, image evidence handling, and future Team 2 NLP fusion.

Model-specific training details belong in Team 1 or Team 2 docs.

## Current Backend Status

- FastAPI platform backend is active direction; Go gateway rewrite is not current scope.
- PostgreSQL is production target; SQLite remains dev/test fallback.
- Farmer accounts use email/password plus Google-login endpoint placeholder.
- Agency accounts use email/password only and are admin seeded.
- Cattle records are farmer-owned; agency dashboard is read/follow-up only.
- Detection scan images require first-scan storage notice acknowledgement.
- Real upload endpoint is `POST /api/media/uploads` with multipart image bytes.
- Old `POST /api/media` remains metadata-only compatibility path.
- Detection image bytes are stored through S3-compatible object storage.
- Local development object storage uses MinIO bucket `sapisehat-scan-images`.
- Agency image preview/download uses backend-issued signed URLs.
- Audit logs persist sensitive backend actions and admin-only read API is available at `GET /api/agency/audit-logs`.

## Dashboard-Relevant APIs

- `GET /api/agency/detection-monitoring` — jurisdiction-scoped review list.
- `GET /api/agency/risk-signals` — materialized cluster risk signals.
- `POST /api/agency/follow-ups` — agency follow-up status and notes.
- `GET /api/agency/media/{media_id}/download-url` — signed URL for private stored media.
- `GET /api/agency/audit-logs` — admin-only debug/ops audit log list.

Dashboard wording must keep results non-diagnostic: possible risk, review item, cluster signal; never confirmed diagnosis or outbreak declaration.

## Verification Commands

From repository root:

```bash
FASTAPI_ENV=test RATE_LIMIT_MAX_REQUESTS=1000 PYTEST_ADDOPTS='-p no:cacheprovider' python -m pytest tests -q
```

From `apps/backend`:

```bash
FASTAPI_ENV=test RATE_LIMIT_MAX_REQUESTS=1000 PYTEST_ADDOPTS='-p no:cacheprovider' python -m pytest tests -q
```

Real MinIO smoke:

```bash
bash apps/backend/scripts/start_minio_dev.sh
cd apps/backend
RUN_MINIO_SMOKE=1 python -m pytest tests/test_minio_media_smoke.py -q
```

## Migrated Backend Docs

- [Development guide](development.md)
- Image-specific legacy backend notes: [Team 1 backend](../../team-1-image/backend/README.md)
