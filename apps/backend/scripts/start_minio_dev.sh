#!/usr/bin/env bash
set -euo pipefail

NETWORK_NAME="${NETWORK_NAME:-sapisehat-minio-net}"
MINIO_CONTAINER="${MINIO_CONTAINER:-sapisehat-minio-dev}"
BUCKET="${S3_BUCKET:-sapisehat-scan-images}"
ROOT_USER="${S3_ACCESS_KEY_ID:-minioadmin}"
ROOT_PASSWORD="${S3_SECRET_ACCESS_KEY:-minioadmin}"

docker network create "$NETWORK_NAME" >/dev/null 2>&1 || true
docker rm -f "$MINIO_CONTAINER" >/dev/null 2>&1 || true

docker run -d --name "$MINIO_CONTAINER" --network "$NETWORK_NAME" \
  -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER="$ROOT_USER" \
  -e MINIO_ROOT_PASSWORD="$ROOT_PASSWORD" \
  -v sapisehat-minio-data:/data \
  minio/minio:RELEASE.2025-09-07T16-13-09Z \
  server /data --console-address ":9001" >/dev/null

for _ in $(seq 1 30); do
  if docker run --rm --network "$NETWORK_NAME" minio/mc:RELEASE.2025-08-13T08-35-41Z \
    sh -c "mc alias set local http://$MINIO_CONTAINER:9000 '$ROOT_USER' '$ROOT_PASSWORD' >/dev/null && mc ready local >/dev/null"; then
    break
  fi
  sleep 1
done

docker run --rm --network "$NETWORK_NAME" minio/mc:RELEASE.2025-08-13T08-35-41Z \
  sh -c "mc alias set local http://$MINIO_CONTAINER:9000 '$ROOT_USER' '$ROOT_PASSWORD' >/dev/null && mc mb --ignore-existing local/$BUCKET"

cat <<EOF
MinIO ready.

Export for backend:
S3_ENDPOINT_URL=http://localhost:9000
S3_BUCKET=$BUCKET
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=$ROOT_USER
S3_SECRET_ACCESS_KEY=$ROOT_PASSWORD
S3_FORCE_PATH_STYLE=true

Console: http://localhost:9001
EOF
