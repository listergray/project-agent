<#
.SYNOPSIS
一键跑通演示（冒烟单测 + 代码助手 流水线 + 可选 RAG 知识库 预设问答）

.EXAMPLE
  cd e:\ai-pro\project-agent
  .\scripts\run.ps1
  .\scripts\run.ps1 -WithRAG   # 需 Docker 中间件已启动
#>
param(
    [switch]$WithRAG
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    Write-Host "未找到 .venv，请先执行：" -ForegroundColor Yellow
    Write-Host "  py -3.12 -m venv .venv" -ForegroundColor White
    Write-Host "  .\.venv\Scripts\pip install -e `".[dev]`"" -ForegroundColor White
    exit 1
}

$env:PYTHONUTF8 = "1"
Write-Host "== pytest 冒烟单测 ==" -ForegroundColor Cyan
& $Py -m pytest tests/test_smoke_project_agent.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n== 代码助手 流水线 ==" -ForegroundColor Cyan
& $Py -m project_agent.copilot.cli
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($WithRAG 知识库) {
    Write-Host "`n== RAG 知识库 导入样例文档 ==" -ForegroundColor Cyan
    & (Join-Path $Root ".venv\Scripts\rag-import.exe")
    Write-Host "`n== RAG 知识库 预设 5 问 ==" -ForegroundColor Cyan
    & (Join-Path $Root ".venv\Scripts\rag-chat.exe") --presets
}

Write-Host "`n全部完成。" -ForegroundColor Green
