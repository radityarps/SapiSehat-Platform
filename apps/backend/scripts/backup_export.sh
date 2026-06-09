#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="${BACKUP_DIR:-./backups}"
STAMP="${BACKUP_STAMP:-$(date +%Y%m%d-%H%M%S)}"
DATABASE_URL_VALUE="${DATABASE_URL:-sqlite:///./sapisehat_dev.db}"
mkdir -p "$OUT_DIR"

if [[ "$DATABASE_URL_VALUE" == postgresql* ]]; then
  echo "backup mode: postgres"
  pg_dump "$DATABASE_URL_VALUE" > "$OUT_DIR/sapisehat-$STAMP.sql"
  echo "postgres backup written: $OUT_DIR/sapisehat-$STAMP.sql"
else
  DB_PATH="${DATABASE_URL_VALUE#sqlite:///}"
  cp "$DB_PATH" "$OUT_DIR/sapisehat-$STAMP.db"
  echo "sqlite backup written: $OUT_DIR/sapisehat-$STAMP.db"
fi
