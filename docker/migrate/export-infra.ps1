#Requires -Version 5.1
<#
.SYNOPSIS
  Export must-migrate data from *-resume containers (MySQL biz DBs + Milvus).

.DESCRIPTION
  MUST migrate:
    - MySQL: ry / project_agent_meta / project_agent_dw
    - Milvus: vector KB volume tar
  SKIP by default:
    - Redis: cache/session (rebuild OK)
    - MinIO: currently empty; use -IncludeOptional to export

  Source PC:
    cd ...\docker\migrate
    .\export-infra.ps1

  Copy backup\infra-*.zip to the other PC, then run import-infra.ps1
#>
param(
  [string]$OutDir = "",
  [string]$MysqlContainer = "mysql-resume",
  [string]$MilvusVolume = "docker_milvus_data",
  [string]$MysqlRootPassword = "root123456",
  [switch]$IncludeOptional,
  [string]$RedisVolume = "docker_redis_data",
  [string]$MinioVolume = "docker_minio_data",
  # Use local redis image so Mac/China network need not pull alpine
  [string]$HelperImage = "redis:7-alpine"
)

$ErrorActionPreference = "Stop"

if (-not $OutDir) {
  $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $OutDir = Join-Path $PSScriptRoot "backup\infra-$stamp"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$OutDir = (Resolve-Path $OutDir).Path

Write-Host "==> export dir: $OutDir"

# --- MySQL logical dump (portable) ---
$dbs = @("ry", "project_agent_meta", "project_agent_dw")
$mysqlSql = Join-Path $OutDir "mysql-biz.sql"
$mysqlErr = Join-Path $OutDir "mysql-dump.err"
Write-Host "==> MySQL dump: $($dbs -join ', ')"
$dumpArgs = @(
  "exec", "-i", $MysqlContainer,
  "mysqldump", "-uroot", "-p$MysqlRootPassword",
  "--single-transaction", "--routines", "--triggers", "--events",
  "--databases"
) + $dbs
$proc = Start-Process -FilePath "docker" -ArgumentList $dumpArgs -NoNewWindow -Wait -PassThru `
  -RedirectStandardOutput $mysqlSql -RedirectStandardError $mysqlErr
if ($proc.ExitCode -ne 0) {
  if (Test-Path $mysqlErr) { Get-Content $mysqlErr }
  throw "mysqldump failed, exit=$($proc.ExitCode)"
}
$lines = Get-Content $mysqlSql -Encoding UTF8
$lines = $lines | Where-Object { $_ -notmatch '^mysqldump:\s*\[Warning\]' }
$lines | Set-Content -Path $mysqlSql -Encoding UTF8
$sqlSize = (Get-Item $mysqlSql).Length
Write-Host "    OK mysql-biz.sql ($([math]::Round($sqlSize/1KB,1)) KB)"

# --- Milvus volume tar (fastest for same major version) ---
$milvusTgz = Join-Path $OutDir "milvus_data.tgz"
Write-Host "==> Milvus volume tar: $MilvusVolume (helper=$HelperImage)"
docker volume inspect $MilvusVolume | Out-Null
if (-not (docker image inspect $HelperImage 2>$null)) {
  Write-Host "WARN: $HelperImage not local; docker will try to pull it"
}
docker run --rm `
  -v "${MilvusVolume}:/data:ro" `
  -v "${OutDir}:/backup" `
  --entrypoint sh `
  $HelperImage `
  -c "tar czf /backup/milvus_data.tgz -C /data ."
if (-not (Test-Path $milvusTgz)) { throw "milvus_data.tgz missing" }
$mvSize = (Get-Item $milvusTgz).Length
Write-Host "    OK milvus_data.tgz ($([math]::Round($mvSize/1MB,1)) MB)"

if ($IncludeOptional) {
  Write-Host "==> Optional: Redis + MinIO volumes"
  docker run --rm -v "${RedisVolume}:/data:ro" -v "${OutDir}:/backup" --entrypoint sh $HelperImage -c "tar czf /backup/redis_data.tgz -C /data ."
  docker run --rm -v "${MinioVolume}:/data:ro" -v "${OutDir}:/backup" --entrypoint sh $HelperImage -c "tar czf /backup/minio_data.tgz -C /data ."
}

$manifest = @{
  exported_at   = (Get-Date).ToString("o")
  must          = @("mysql-biz.sql", "milvus_data.tgz")
  mysql_dbs     = $dbs
  milvus_volume = $MilvusVolume
  note          = "Need same major images: mysql:8.4 / milvus:v2.4.x"
}
$manifest | ConvertTo-Json | Set-Content (Join-Path $OutDir "manifest.json") -Encoding UTF8

$zip = "$OutDir.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Write-Host "==> zip $zip"
Compress-Archive -Path (Join-Path $OutDir "*") -DestinationPath $zip -Force

Write-Host ""
Write-Host "DONE. Copy this file to the other PC:"
Write-Host "  $zip"
Write-Host "Then run:"
Write-Host ("  .\import-infra.ps1 -BackupZip `"{0}`"" -f $zip)
