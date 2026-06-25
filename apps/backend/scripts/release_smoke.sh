#!/usr/bin/env bash
set -euo pipefail

export FASTAPI_ENV="${FASTAPI_ENV:-test}"
export RATE_LIMIT_MAX_REQUESTS="${RATE_LIMIT_MAX_REQUESTS:-1000}"
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p no:cacheprovider"

cd "$(dirname "$0")/.."

python -m alembic -c alembic.ini upgrade head
python -m pytest \
  tests/test_contract_examples.py \
  tests/test_surface_specific_auth.py \
  tests/test_media_object_storage.py \
  tests/test_audit_logs.py \
  tests/test_minio_media_smoke.py \
  tests/test_inference.py \
  -q
