# Deployment Contracts

Shared deployment and operations docs live here.

Use this folder for FastAPI backend deployment, PostgreSQL, S3-compatible media storage, dashboard deployment, local development topology, and migration runbooks.

## Local Backend Services

Backend local object storage uses MinIO through the same S3-compatible settings planned for production buckets.

Start MinIO and create the default bucket:

```bash
bash apps/backend/scripts/start_minio_dev.sh
```

Default local values:

```text
S3_ENDPOINT_URL=http://localhost:9000
S3_BUCKET=sapisehat-scan-images
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
S3_FORCE_PATH_STYLE=true
```

MinIO console:

```text
http://localhost:9001
```

Run real upload and signed URL smoke after MinIO is ready:

```bash
cd apps/backend
RUN_MINIO_SMOKE=1 python -m pytest tests/test_minio_media_smoke.py -q
```

## Release Smoke

Backend release smoke runs migrations plus core contract/auth/media/audit/inference tests:

```bash
cd apps/backend
DATABASE_URL=sqlite:///./sapisehat_smoke.db FASTAPI_ENV=test RATE_LIMIT_MAX_REQUESTS=1000 bash scripts/release_smoke.sh
```

With MinIO included:

```bash
cd apps/backend
RUN_MINIO_SMOKE=1 DATABASE_URL=sqlite:///./sapisehat_smoke.db FASTAPI_ENV=test RATE_LIMIT_MAX_REQUESTS=1000 bash scripts/release_smoke.sh
```

## Backup / Export

Development SQLite backup:

```bash
cd apps/backend
DATABASE_URL=sqlite:///./sapisehat_dev.db BACKUP_DIR=./backups bash scripts/backup_export.sh
```

PostgreSQL backup:

```bash
cd apps/backend
DATABASE_URL=postgresql+psycopg://user:password@host:5432/database BACKUP_DIR=./backups bash scripts/backup_export.sh
```

The PostgreSQL path uses `pg_dump`; ensure it is installed in the runtime/container that performs backup.

## Production Config Guard

Production must not use development defaults:

- `JWT_SECRET` must be a strong production secret.
- `CORS_ORIGINS` must not contain wildcard in production.
- `S3_BUCKET` must be set.
- `S3_ACCESS_KEY_ID` and `S3_SECRET_ACCESS_KEY` must not use `minioadmin`.
- `GOOGLE_CLIENT_ID` must be set when Google auth is enabled.

## Migrated Deployment Docs

Backend migration docs live in [backend-migration](backend-migration/).
