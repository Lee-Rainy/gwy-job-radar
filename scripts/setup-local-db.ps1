# Create application database on local PostgreSQL 17.
#
# Usage (postgres superuser):
#   $env:PGPASSWORD = "postgres"
#   .\scripts\setup-local-db.ps1
#
# Optional app user (default: postgres — no extra role):
#   .\scripts\setup-local-db.ps1 -AppUser radar -AppPassword radar_secret

param(
    [string]$PsqlUser = "postgres",
    [string]$AppUser = "postgres",
    [string]$AppPassword = "",
    [string]$DbName = "gd_job_radar"
)

$ErrorActionPreference = "Stop"
$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
if (-not (Test-Path $psql)) {
    Write-Error "psql not found at $psql"
}

if (-not $env:PGPASSWORD) {
    Write-Error "Set PGPASSWORD first, e.g. `$env:PGPASSWORD = 'postgres'"
}

$psqlArgs = @("-U", $PsqlUser, "-h", "127.0.0.1", "-p", "5432", "-w")

if ($AppUser -ne "postgres") {
    $exists = & $psql @psqlArgs -tAc "SELECT 1 FROM pg_roles WHERE rolname = '$AppUser';"
    if ($exists -ne "1") {
        if (-not $AppPassword) {
            Write-Error "AppPassword required when AppUser is not postgres"
        }
        $escaped = $AppPassword.Replace("'", "''")
        & $psql @psqlArgs -v ON_ERROR_STOP=1 -c "CREATE USER $AppUser WITH PASSWORD '$escaped';"
        Write-Host "Created role $AppUser"
    } else {
        Write-Host "Role $AppUser already exists"
    }
    $owner = $AppUser
} else {
    $owner = "postgres"
    Write-Host "Using PostgreSQL superuser postgres as database owner"
}

$dbExists = & $psql @psqlArgs -tAc "SELECT 1 FROM pg_database WHERE datname = '$DbName';"
if ($dbExists -ne "1") {
    & $psql @psqlArgs -v ON_ERROR_STOP=1 -c "CREATE DATABASE $DbName OWNER $owner;"
    Write-Host "Created database $DbName"
} else {
    Write-Host "Database $DbName already exists"
}

if ($AppUser -eq "postgres") {
    $urlPass = if ($env:PGPASSWORD) { $env:PGPASSWORD } else { "postgres" }
    $encoded = [uri]::EscapeDataString($urlPass)
    Write-Host ""
    Write-Host "DATABASE_URL=postgresql+psycopg://postgres:${encoded}@localhost:5432/${DbName}"
} else {
    $encoded = [uri]::EscapeDataString($AppPassword)
    Write-Host ""
    Write-Host "DATABASE_URL=postgresql+psycopg://${AppUser}:${encoded}@localhost:5432/${DbName}"
}
Write-Host "Add the line above to .env.test"
