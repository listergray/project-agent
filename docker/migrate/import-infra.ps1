#Requires -Version 5.1
<#
.SYNOPSIS
  Import backup created by export-infra.ps1 (Windows helper; Mac use import-infra.sh).

.DESCRIPTION
  Defaults: *-agent containers, helper image redis:7-alpine (local, no alpine pull).
#>
param(
  [string]$BackupZip = "",
  [string]$BackupDir = "",
  [string]$MysqlContainer = "mysql-agent",
  [string]$MilvusContainer = "milvus-agent",
  [string]$MilvusVolume = "docker_milvus_data",
  [string]$MysqlRootPassword = "root123456",
  [switch]$ImportOptional,
  [string]$RedisContainer = "redis-agent",
  [string]$MinioContainer = "minio-agent",
  [string]$RedisVolume = "docker_redis_data",
  [string]$MinioVolume = "docker_minio_data",
  [string]$HelperImage = "redis:7-alpine"
)

$ErrorActionPreference = "Stop"

if (-not $BackupDir) {
  if (-not $BackupZip) { throw "Need -BackupZip or -BackupDir" }
  if (-not (Test-Path $BackupZip)) { throw "Not found: $BackupZip" }
  $BackupDir = Join-Path $env:TEMP ("infra-import-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
  Write-Host "==> unzip $BackupZip -> $BackupDir"
  Expand-Archive -Path $BackupZip -DestinationPath $BackupDir -Force
}
$BackupDir = (Resolve-Path $BackupDir).Path

$sql = Join-Path $BackupDir "mysql-biz.sql"
$milvusTgz = Join-Path $BackupDir "milvus_data.tgz"
if (-not (Test-Path $sql)) { throw "missing mysql-biz.sql" }
if (-not (Test-Path $milvusTgz)) { throw "missing milvus_data.tgz" }

Write-Host "==> helper image: $HelperImage"
Write-Host "==> stop Milvus ($MilvusContainer)"
docker stop $MilvusContainer | Out-Null

Write-Host "==> restore volume: $MilvusVolume"
docker run --rm -v "${MilvusVolume}:/data" --entrypoint sh $HelperImage -c "rm -rf /data/* /data/.[!.]* /data/..?* 2>/dev/null; true"
docker run --rm `
  -v "${MilvusVolume}:/data" `
  -v "${BackupDir}:/backup" `
  --entrypoint sh `
  $HelperImage `
  -c "tar xzf /backup/milvus_data.tgz -C /data"
Write-Host "    Milvus volume restored"

Write-Host "==> start Milvus"
docker start $MilvusContainer | Out-Null

Write-Host "==> import MySQL into $MysqlContainer"
Get-Content $sql -Raw -Encoding UTF8 | docker exec -i $MysqlContainer `
  mysql -uroot "-p$MysqlRootPassword" --default-character-set=utf8mb4
if ($LASTEXITCODE -ne 0) { throw "mysql import failed" }

Write-Host "==> verify"
docker exec $MysqlContainer mysql -uroot "-p$MysqlRootPassword" -N -e "SHOW DATABASES LIKE 'ry'; SHOW DATABASES LIKE 'project_agent%'; SELECT COUNT(*) FROM ry.sys_user; SELECT COUNT(*) FROM ry.sys_menu;"

if ($ImportOptional) {
  $redisTgz = Join-Path $BackupDir "redis_data.tgz"
  $minioTgz = Join-Path $BackupDir "minio_data.tgz"
  if (Test-Path $redisTgz) {
    Write-Host "==> restore Redis"
    docker stop $RedisContainer | Out-Null
    docker run --rm -v "${RedisVolume}:/data" --entrypoint sh $HelperImage -c "rm -rf /data/* /data/.[!.]* 2>/dev/null; true"
    docker run --rm -v "${RedisVolume}:/data" -v "${BackupDir}:/backup" --entrypoint sh $HelperImage -c "tar xzf /backup/redis_data.tgz -C /data"
    docker start $RedisContainer | Out-Null
  }
  if (Test-Path $minioTgz) {
    Write-Host "==> restore MinIO"
    docker stop $MinioContainer | Out-Null
    docker run --rm -v "${MinioVolume}:/data" --entrypoint sh $HelperImage -c "rm -rf /data/* /data/.[!.]* 2>/dev/null; true"
    docker run --rm -v "${MinioVolume}:/data" -v "${BackupDir}:/backup" --entrypoint sh $HelperImage -c "tar xzf /backup/minio_data.tgz -C /data"
    docker start $MinioContainer | Out-Null
  }
}

Write-Host ""
Write-Host "DONE."
Write-Host "  1) docker ps"
Write-Host "  2) optional: docker exec $RedisContainer redis-cli FLUSHDB"
Write-Host "  3) set INFRA_HOST to new machine IP in conf/.env"
Write-Host "  4) re-login / test chat"
