# One-click local start (scheduler). Run in PowerShell:
#   cd D:\gwy-job-radar
#   .\start.ps1
#
# First time only:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#   .\.venv\Scripts\python.exe -m pip install -r requirements.txt

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "Missing .venv. Run: python -m venv .venv"
    Write-Host "Then: .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}

if (-not (Test-Path (Join-Path $PSScriptRoot ".env.test"))) {
    Write-Host "Missing .env.test. Run: copy .env.example .env.test"
    exit 1
}

$env:PYTHONPATH = $PSScriptRoot
if (-not $env:ENV_FILE) { $env:ENV_FILE = ".env.test" }
if (-not $env:COLLECTOR_SOURCES) { $env:COLLECTOR_SOURCES = "gz_rsj" }
if (-not $env:RUN_JOB_ON_START) { $env:RUN_JOB_ON_START = "true" }

Write-Host "Starting gd-job-radar (serve). Press Ctrl+C to stop."
Write-Host "PYTHON=$python"
& $python -m app.main serve
