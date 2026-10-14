# 不依赖全局 Path，直接调用本机 PostgreSQL 17 的 psql。
# 用法: .\scripts\psql.ps1 -U postgres -h 127.0.0.1 -c "SELECT version();"

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
if (-not (Test-Path $psql)) {
    Write-Error "未找到 $psql"
}
& $psql @Args
