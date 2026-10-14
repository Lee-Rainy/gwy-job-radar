# Run one crawl + email, then exit.
#   .\start-once.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Run: python -m venv .venv && pip install -r requirements.txt"
}

$env:PYTHONPATH = $PSScriptRoot
if (-not $env:ENV_FILE) { $env:ENV_FILE = ".env.test" }
$env:COLLECTOR_SOURCES = "gz_rsj"

& $python -m app.main init-db
& $python -m app.main run-now --period evening --sources gz_rsj
