# Called by Windows task "douyin-auto-daily-publish" every day at 19:00.
# The service also has an in-process timer; the API claims the day once, so only one publish runs.
$ErrorActionPreference = "Stop"
try {
    Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:12500/api/publish/next" -TimeoutSec 60 | Out-Null
} catch {
    exit 1
}
