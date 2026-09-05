<#
.SYNOPSIS
一键启动 Project Agent 中间件容器（Milvus standalone_embed + MinIO + MySQL 8 + Redis 7）
+ 建 Milvus 集合 + 建 MinIO bucket。

.DESCRIPTION
Windows PowerShell 脚本，3 步：
  1. docker compose up -d
  2. 等 4 个容器全部 healthy（最多 3min）
  3. 初始化 Milvus 集合（kb_item_names / kb_chunks）+ MinIO bucket（kb-files）

.EXAMPLE
  cd docker
  .\up.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "=" * 72 -ForegroundColor Cyan
Write-Host "🚀 Project Agent · 中间件一键启动（Windows PowerShell）" -ForegroundColor Cyan
Write-Host "=" * 72 -ForegroundColor Cyan

# 定位项目 docker 目录
$ScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
Set-Location $ScriptDir

# --- step 1: docker compose up -d ---
Write-Host "`n[1/3] docker compose up -d（4 个服务：milvus / minio / mysql / redis）" -ForegroundColor Yellow
docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "docker compose up 失败，见上" }

# --- step 2: 等 4 个健康检查 all passed ---
Write-Host "`n[2/3] 等 4 个容器 health=healthy（最长 180s）" -ForegroundColor Yellow
$timeoutAt = (Get-Date).AddSeconds(180)
$need = @("milvus-agent", "minio-agent", "mysql-agent", "redis-agent")
while ($true) {
    $raw  = docker ps --format '{{json .}}' | Out-String
    $containers = $raw -split "`r?`n" | Where-Object { $_ } | ForEach-Object { $_ | ConvertFrom-Json }
    $healthMap = @{}
    foreach ($c in $containers) { $healthMap[$c.Names] = $c.Status }
    $allOk = $need | ForEach-Object { $healthMap[$_] -match "\(healthy\)" } | Where-Object { $_ -eq $false }
    if (-not $allOk -or $allOk.Count -eq 0) {
        Write-Host "   ✅ 全部 healthy: $(($need | ForEach-Object { $healthMap[$_] }) -join ', ')" -ForegroundColor Green
        break
    }
    Write-Host "   ⏳ $(Get-Date -Format HH:mm:ss) waiting ... $($need | ForEach-Object { "$($_)=$($healthMap[$_] ?? 'missing')" })"
    if ((Get-Date) -gt $timeoutAt) { throw "等待健康检查超时，docker ps 检查状态" }
    Start-Sleep -Seconds 8
}

# --- step 3: 初始化 Milvus + MinIO（调用 python 初始化脚本） ---
Write-Host "`n[3/3] 初始化 Milvus 集合 / MinIO bucket" -ForegroundColor Yellow
Set-Location (Split-Path $ScriptDir -Parent)  # 项目根
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "   ⚠️  未找到 .venv\\Scripts\\python.exe，跳过自动初始化。" -ForegroundColor DarkYellow
    Write-Host "       请手动执行： uv run python -m project_agent.tools.init_infra  或 pip install 后运行。" -ForegroundColor DarkYellow
} else {
    & .venv\Scripts\python.exe -m project_agent.tools.init_infra
    if ($LASTEXITCODE -ne 0) { Write-Host "   ⚠️  初始化脚本返回非 0，见上" -ForegroundColor DarkYellow }
}

Write-Host "`n"
Write-Host "=" * 72 -ForegroundColor Green
Write-Host "✅ 启动完毕！接下来可以跑 演示：" -ForegroundColor Green
Write-Host "    1) 安装依赖：     uv pip install -e .  或  pip install -e ." -ForegroundColor White
Write-Host "    2) RAG 知识库-导入：   rag-import   (导入 data/samples/*.md 到 Milvus)" -ForegroundColor White
Write-Host "    3) RAG 知识库-问答：   rag-chat --presets  (跑 5 个演示预设问题)" -ForegroundColor White
Write-Host "    4) 代码助手-代码助手：copilot-run      (跑 5+1 节点，生成 Java 代码到 output/)" -ForegroundColor White
Write-Host "=" * 72 -ForegroundColor Green
