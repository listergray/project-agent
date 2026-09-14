#!/usr/bin/env bash
# Optional: export on a Mac source machine (same content as export-infra.ps1).
# On Windows source, keep using export-infra.ps1.
set -euo pipefail

HELPER_IMAGE="${HELPER_IMAGE:-redis:7-alpine}"
MYSQL_CONTAINER="${MYSQL_CONTAINER:-mysql-resume}"
MILVUS_VOLUME="${MILVUS_VOLUME:-docker_milvus_data}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-root123456}"
INCLUDE_OPTIONAL="${INCLUDE_OPTIONAL:-0}"
REDIS_VOLUME="${REDIS_VOLUME:-docker_redis_data}"
MINIO_VOLUME="${MINIO_VOLUME:-docker_minio_data}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -z "${1:-}" ]]; then
  :
fi
OUT_DIR="${1:-}"
if [[ -z "$OUT_DIR" ]]; then
  STAMP="$(date +%Y%m%d-%H%M%S)"
  OUT_DIR="$SCRIPT_DIR/backup/infra-$STAMP"
fi
mkdir -p "$OUT_DIR"

echo "==> export dir: $OUT_DIR"
echo "==> MySQL dump"
docker exec -i "$MYSQL_CONTAINER" \
  mysqldump -uroot "-p${MYSQL_ROOT_PASSWORD}" \
  --single-transaction --routines --triggers --events \
  --databases ry project_agent_meta project_agent_dw \
  2>"$OUT_DIR/mysql-dump.err" \
  | grep -v '^mysqldump: \[Warning\]' > "$OUT_DIR/mysql-biz.sql" || true
if [[ ! -s "$OUT_DIR/mysql-biz.sql" ]]; then
  cat "$OUT_DIR/mysql-dump.err" || true
  echo "mysqldump failed"
  exit 1
fi
echo "    OK mysql-biz.sql ($(wc -c < "$OUT_DIR/mysql-biz.sql") bytes)"

echo "==> Milvus volume tar: $MILVUS_VOLUME (helper=$HELPER_IMAGE)"
docker volume inspect "$MILVUS_VOLUME" >/dev/null
docker run --rm \
  -v "${MILVUS_VOLUME}:/data:ro" \
  -v "${OUT_DIR}:/backup" \
  --entrypoint sh \
  "$HELPER_IMAGE" \
  -c "tar czf /backup/milvus_data.tgz -C /data ."
echo "    OK milvus_data.tgz"

if [[ "$INCLUDE_OPTIONAL" == "1" ]]; then
  docker run --rm -v "${REDIS_VOLUME}:/data:ro" -v "${OUT_DIR}:/backup" --entrypoint sh "$HELPER_IMAGE" -c "tar czf /backup/redis_data.tgz -C /data ."
  docker run --rm -v "${MINIO_VOLUME}:/data:ro" -v "${OUT_DIR}:/backup" --entrypoint sh "$HELPER_IMAGE" -c "tar czf /backup/minio_data.tgz -C /data ."
fi

ZIP="$OUT_DIR.zip"
rm -f "$ZIP"
(
  cd "$OUT_DIR"
  zip -qr "$ZIP" .
)
echo
echo "DONE. Copy to the other machine:"
echo "  $ZIP"
