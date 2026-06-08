#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-sapisehat-backend-test}"
NETWORK_NAME="${NETWORK_NAME:-sapisehat-test-net}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-sapisehat-postgres-test}"
DATABASE_URL="postgresql+psycopg://sapisehat:sapisehat@${POSTGRES_CONTAINER}:5432/sapisehat_test"
export MSYS_NO_PATHCONV=1
export FASTAPI_ENV=test
export RATE_LIMIT_MAX_REQUESTS=1000
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:-} -p no:cacheprovider"

cd "$(dirname "$0")/.."

docker build -t "$IMAGE_NAME" .
docker network create "$NETWORK_NAME" >/dev/null 2>&1 || true
docker rm -f "$POSTGRES_CONTAINER" >/dev/null 2>&1 || true
docker run -d --name "$POSTGRES_CONTAINER" --network "$NETWORK_NAME" \
  -e POSTGRES_USER=sapisehat \
  -e POSTGRES_PASSWORD=sapisehat \
  -e POSTGRES_DB=sapisehat_test \
  postgres:16-alpine >/dev/null

cleanup() {
  docker rm -f "$POSTGRES_CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in $(seq 1 30); do
  if docker exec "$POSTGRES_CONTAINER" pg_isready -U sapisehat -d sapisehat_test >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

docker exec "$POSTGRES_CONTAINER" pg_isready -U sapisehat -d sapisehat_test >/dev/null

docker run --rm --network "$NETWORK_NAME" -w /app \
  -e FASTAPI_ENV="$FASTAPI_ENV" \
  -e RATE_LIMIT_MAX_REQUESTS="$RATE_LIMIT_MAX_REQUESTS" \
  -e PYTEST_ADDOPTS="$PYTEST_ADDOPTS" \
  -e DATABASE_URL="$DATABASE_URL" "$IMAGE_NAME" \
  python -m alembic -c alembic.ini upgrade head

docker run --rm --network "$NETWORK_NAME" -w /app \
  -e FASTAPI_ENV="$FASTAPI_ENV" \
  -e RATE_LIMIT_MAX_REQUESTS="$RATE_LIMIT_MAX_REQUESTS" \
  -e PYTEST_ADDOPTS="$PYTEST_ADDOPTS" \
  -e DATABASE_URL="$DATABASE_URL" "$IMAGE_NAME" \
  python -m pytest \
    tests/test_surface_specific_auth.py \
    tests/test_farmer_account_tracer.py \
    tests/test_cattle_profile_tracer.py \
    tests/test_cattle_timeline_tracer.py \
    tests/test_offline_detection_sync_tracer.py \
    tests/test_follow_up_status_tracer.py \
    tests/test_authorization_tracer.py \
    -q
