#!/usr/bin/env bash
# Import backup (from Windows export-infra.ps1 / export-infra.sh) onto Mac.
#
# Defaults match project_agent compose (*-agent). Override if needed.
# Helper image: use local redis:7-alpine (already pulled with redis-agent) — NO alpine pull.
#
# Usage:
#   chmod +x import-infra.sh
#   ./import-infra.sh ~/Downloads/infra-xxxx.zip
#
# If volume name differs:
#   docker volume ls | grep milvus
#   MILVUS_VOLUME=实际卷名 ./import-infra.sh xxx.zip
#
set -euo pipefail

BACKUP_IN="${1:-}"

# New machine uses *-agent (old machine was *-resume)
MYSQL_CONTAINER="${MYSQL_CONTAINER:-mysql-agent}"
MILVUS_CONTAINER="${MILVUS_CONTAINER:-milvus-agent}"
REDIS_CONTAINER="${REDIS_CONTAINER:-redis-agent}"
MINIO_CONTAINER="${MINIO_CONTAINER:-minio-agent}"

# Compose project "docker" usually creates docker_*_data; override if docker volume ls differs
MILVUS_VOLUME="${MILVUS_VOLUME:-docker_milvus_data}"
REDIS_VOLUME="${REDIS_VOLUME:-docker_redis_data}"
MINIO_VOLUME="${MINIO_VOLUME:-docker_minio_data}"

MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-root123456}"
IMPORT_OPTIONAL="${IMPORT_OPTIONAL:-0}"

# Prefer an image already on the Mac (redis-agent pulls this). Avoid docker hub alpine pull.
HELPER_IMAGE="${HELPER_IMAGE:-redis:7-alpine}"

if [[ -z "$BACKUP_IN" ]]; then
  echo "Usage: $0 /path/to/infra-xxxx.zip|/path/to/dir"
  exit 1
fi
if [[ ! -e "$BACKUP_IN" ]]; then
  echo "Not found: $BACKUP_IN"
  exit 1
fi

pick_helper_image() {
  if docker image inspect "$HELPER_IMAGE" >/dev/null 2>&1; then
    echo "$HELPER_IMAGE"
    return
  fi
  # Fallbacks already common on this stack (no network pull)
  for img in "redis:7-alpine" "minio/minio:RELEASE.2024-10-02T17-50-41Z" "mysql:8.4"; do
    if docker image inspect "$img" >/dev/null 2>&1; then
      echo "$img"
      return
    fi
  done
  # Last resort: image of a running/local container
  for c in "$REDIS_CONTAINER" "$MINIO_CONTAINER" "$MYSQL_CONTAINER"; do
    img="$(docker inspect -f '{{.Config.Image}}' "$c" 2>/dev/null || true)"
    if [[ -n "$img" ]] && docker image inspect "$img" >/dev/null 2>&1; then
      echo "$img"
      return
    fi
  done
  echo ""
}

HELPER="$(pick_helper_image)"
if [[ -z "$HELPER" ]]; then
  echo "ERROR: no local helper image found (need tar/sh)."
  echo "  docker images"
  echo "Then: HELPER_IMAGE=<local-image> $0 $BACKUP_IN"
  exit 1
fi
echo "==> helper image (local, no pull): $HELPER"

WORKDIR="$(mktemp -d /tmp/infra-import.XXXXXX)"
cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

if [[ -f "$BACKUP_IN" ]]; then
  echo "==> unzip $BACKUP_IN"
  unzip -q "$BACKUP_IN" -d "$WORKDIR"
  if [[ -f "$WORKDIR/mysql-biz.sql" ]]; then
    BACKUP_DIR="$WORKDIR"
  else
    SQL_FOUND="$(find "$WORKDIR" -type f -name mysql-biz.sql -print -quit)"
    [[ -n "$SQL_FOUND" ]] || { echo "mysql-biz.sql not found inside zip"; exit 1; }
    BACKUP_DIR="$(dirname "$SQL_FOUND")"
  fi
elif [[ -d "$BACKUP_IN" ]]; then
  BACKUP_DIR="$BACKUP_IN"
else
  echo "Need a .zip file or a directory"
  exit 1
fi

SQL="$BACKUP_DIR/mysql-biz.sql"
MILVUS_TGZ="$BACKUP_DIR/milvus_data.tgz"
[[ -f "$SQL" ]] || { echo "missing mysql-biz.sql in $BACKUP_DIR"; exit 1; }
[[ -f "$MILVUS_TGZ" ]] || { echo "missing milvus_data.tgz in $BACKUP_DIR"; exit 1; }

# Resolve milvus volume if default missing
if ! docker volume inspect "$MILVUS_VOLUME" >/dev/null 2>&1; then
  GUESS="$(docker volume ls -q | grep -E 'milvus' | head -n1 || true)"
  if [[ -n "$GUESS" ]]; then
    echo "==> default volume missing; using: $GUESS"
    MILVUS_VOLUME="$GUESS"
  else
    echo "ERROR: volume not found: $MILVUS_VOLUME"
    echo "  docker volume ls"
    exit 1
  fi
fi

vol_wipe() {
  local vol="$1"
  # busybox/redis alpine: tar+sh; mysql image also has sh/rm
  docker run --rm -v "${vol}:/data" --entrypoint sh "$HELPER" \
    -c 'rm -rf /data/* /data/.[!.]* /data/..?* 2>/dev/null; true'
}

vol_untar() {
  local vol="$1"
  local tgz="$2"
  local name
  name="$(basename "$tgz")"
  docker run --rm \
    -v "${vol}:/data" \
    -v "${BACKUP_DIR}:/backup" \
    --entrypoint sh \
    "$HELPER" \
    -c "tar xzf /backup/${name} -C /data"
}

echo "==> stop Milvus ($MILVUS_CONTAINER)"
docker stop "$MILVUS_CONTAINER" >/dev/null

echo "==> restore volume: $MILVUS_VOLUME"
vol_wipe "$MILVUS_VOLUME"
vol_untar "$MILVUS_VOLUME" "$MILVUS_TGZ"
echo "    Milvus volume restored"

echo "==> start Milvus"
docker start "$MILVUS_CONTAINER" >/dev/null

echo "==> import MySQL into $MYSQL_CONTAINER"
docker exec -i "$MYSQL_CONTAINER" \
  mysql -uroot "-p${MYSQL_ROOT_PASSWORD}" --default-character-set=utf8mb4 < "$SQL"

echo "==> verify"
docker exec "$MYSQL_CONTAINER" mysql -uroot "-p${MYSQL_ROOT_PASSWORD}" -N -e \
  "SHOW DATABASES LIKE 'ry'; SHOW DATABASES LIKE 'project_agent%'; SELECT COUNT(*) FROM ry.sys_user; SELECT COUNT(*) FROM ry.sys_menu;"

if [[ "$IMPORT_OPTIONAL" == "1" ]]; then
  if [[ -f "$BACKUP_DIR/redis_data.tgz" ]]; then
    echo "==> restore Redis"
    docker stop "$REDIS_CONTAINER" >/dev/null || true
    vol_wipe "$REDIS_VOLUME"
    vol_untar "$REDIS_VOLUME" "$BACKUP_DIR/redis_data.tgz"
    docker start "$REDIS_CONTAINER" >/dev/null
  fi
  if [[ -f "$BACKUP_DIR/minio_data.tgz" ]]; then
    echo "==> restore MinIO"
    docker stop "$MINIO_CONTAINER" >/dev/null || true
    vol_wipe "$MINIO_VOLUME"
    vol_untar "$MINIO_VOLUME" "$BACKUP_DIR/minio_data.tgz"
    docker start "$MINIO_CONTAINER" >/dev/null
  fi
fi

echo
echo "DONE."
echo "  1) docker ps"
echo "  2) optional: docker exec $REDIS_CONTAINER redis-cli FLUSHDB"
echo "  3) set INFRA_HOST to this Mac LAN IP in conf/.env"
echo "  4) re-login / test chat"
