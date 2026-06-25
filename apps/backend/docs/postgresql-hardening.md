# PostgreSQL hardening

Status: implemented and verified for Milestone 4. Targeted backend tests cover the hardening migration, DB constraint/index audit, agency seed documentation, and backup/export script contract.

## Migration discipline

- All production schema changes must be represented by an Alembic revision under `alembic/versions`.
- Run migrations with `alembic -c alembic.ini upgrade head` before deploying API code that depends on new columns, constraints, or indexes.
- Never edit applied revisions. Add a new revision instead.
- Constraints and indexes are PostgreSQL-first. SQLite is only a local developer fallback.

## Deterministic agency seed flow

- Seed records use stable IDs, emails, phone numbers, jurisdiction IDs, and role names.
- Seed commands must be idempotent: rerun updates or skips existing seed rows instead of creating duplicates.
- Document demo credentials in `.env.example` only; never commit real credentials.
- Run seed after migrations so FK/check constraints protect bad fixture data.

## Backup/export approach

Production backup baseline:

```bash
pg_dump "$DATABASE_URL" --format=custom --file=backups/sapisehat-$(date +%Y%m%d%H%M).dump
```

Restore drill:

```bash
createdb sapisehat_restore
pg_restore --dbname=sapisehat_restore backups/<dump-file>.dump
alembic -c alembic.ini upgrade head
```

Operational rules:

- Keep at least daily backups for production.
- Test restore before each release gate.
- Store dumps outside app containers and encrypt storage at rest.
- Export selected tables with `COPY` only for audited support workflows.

## Verification

Targeted verification command:

```bash
python -m pytest \
  tests/test_postgresql_hardening_migration.py \
  tests/test_backup_export_script.py \
  tests/test_db_constraints_and_indexes.py \
  tests/test_farmer_area_advisory_api.py \
  -q
```

Expected result: all tests pass.
