# 安装时未记住 postgres 密码时：临时改为 trust 本机登录并重设密码。
# 请以管理员身份运行 PowerShell：
#   cd D:\gwy-job-radar
#   .\scripts\reset-postgres-password.ps1 -NewPassword radar_secret

param(
    [string]$NewPassword = "radar_secret",
    [string]$PgData = "C:\Program Files\PostgreSQL\17\data"
)

$ErrorActionPreference = "Stop"
$hbaPath = Join-Path $PgData "pg_hba.conf"
$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
$pgCtl = "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe"
$serviceName = "postgresql-x64-17"

if (-not (Test-Path $hbaPath)) {
    Write-Error "未找到 $hbaPath"
}

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if (-not $isAdmin) {
    Write-Error "请右键 PowerShell -> 以管理员身份运行，再执行本脚本。"
}

$backup = "$hbaPath.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item -LiteralPath $hbaPath -Destination $backup -Force
Write-Host "已备份 pg_hba.conf -> $backup"

$originalLines = Get-Content -LiteralPath $hbaPath
$patchedLines = $originalLines | ForEach-Object {
    if ($_ -match "^\s*#" -or $_ -match "^\s*$") { $_ }
    elseif ($_ -match "scram-sha-256") { $_ -replace "scram-sha-256", "trust" }
    else { $_ }
}
[System.IO.File]::WriteAllLines($hbaPath, $patchedLines)

Restart-Service $serviceName -Force
Start-Sleep -Seconds 3

$escaped = $NewPassword.Replace("'", "''")
& $psql -U postgres -h 127.0.0.1 -p 5432 -v ON_ERROR_STOP=1 -c "ALTER USER postgres WITH PASSWORD '$escaped';"
Write-Host "postgres 超级用户密码已设置为: $NewPassword"

[System.IO.File]::WriteAllLines($hbaPath, $originalLines)
Restart-Service $serviceName -Force
Start-Sleep -Seconds 2
Write-Host "已恢复 scram-sha-256 认证。"

$env:PGPASSWORD = $NewPassword
& "$PSScriptRoot\setup-local-db.ps1"
Write-Host "完成。请将 DATABASE_URL 写入 .env.test"
