# Add PostgreSQL 17 to the current user PATH (run from repo root).
# Usage: .\scripts\configure-postgres-env.ps1

$ErrorActionPreference = "Stop"

$pgRoot = "C:\Program Files\PostgreSQL\17"
$pgBin = Join-Path $pgRoot "bin"
$pgData = Join-Path $pgRoot "data"

if (-not (Test-Path (Join-Path $pgBin "psql.exe"))) {
    Write-Error "psql not found at $pgBin"
}

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$parts = @()
if ($userPath) {
    $parts = $userPath -split ';' | Where-Object { $_.Trim() -ne "" }
}
if ($parts -notcontains $pgBin) {
    $parts += $pgBin
    [Environment]::SetEnvironmentVariable("Path", ($parts -join ';'), "User")
    Write-Host "Added to user Path: $pgBin"
} else {
    Write-Host "Path already contains: $pgBin"
}

[Environment]::SetEnvironmentVariable("PGROOT", $pgRoot, "User")
[Environment]::SetEnvironmentVariable("PGDATA", $pgData, "User")
Write-Host "PGROOT=$pgRoot"
Write-Host "PGDATA=$pgData"

$env:PGROOT = $pgRoot
$env:PGDATA = $pgData
if ($env:Path -notlike "*$pgBin*") {
    $env:Path = $env:Path + ';' + $pgBin
}

Write-Host ""
& (Join-Path $pgBin "psql.exe") --version
Write-Host ""
Write-Host "Open a NEW terminal, then run: psql --version"
Write-Host 'Example: $env:PGPASSWORD="your_postgres_password"; psql -U postgres -h 127.0.0.1'
