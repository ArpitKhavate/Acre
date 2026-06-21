# Start Acre cloud API + web dashboard for LAN demo (Windows).
# Usage:  .\scripts\start_laptop_demo.ps1
# Then on QNX Pi:  export ACRE_BACKEND_URL=http://<this-PC-IP>:8000/api/sync

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch "^169" } |
    Select-Object -First 1).IPAddress
if (-not $ip) { $ip = "127.0.0.1" }

Write-Host ""
Write-Host "=== Acre laptop demo ===" -ForegroundColor Cyan
Write-Host "LAN IP:     $ip"
Write-Host "API:        http://${ip}:8000"
Write-Host "Web:        http://${ip}:3000"
Write-Host "Pi sync:    export ACRE_BACKEND_URL=http://${ip}:8000/api/sync"
Write-Host ""

# API env for web
$envFile = Join-Path $Root "web\.env.local"
@"
NEXT_PUBLIC_ACRE_API=http://${ip}:8000
NEXT_PUBLIC_ACRE_FARM=demo-farm-1
"@ | Set-Content -Encoding utf8 $envFile

Write-Host "Installing Python deps (if needed)..."
pip install -q -r requirements.txt -r cloud/requirements.txt
python -m cloud.seed | Out-Null

Write-Host "Starting API on 0.0.0.0:8000 ..."
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root'; uvicorn cloud.app.main:app --host 0.0.0.0 --port 8000"
)

Start-Sleep -Seconds 2

if (-not (Test-Path (Join-Path $Root "web\node_modules"))) {
    Write-Host "npm install (first run)..."
    Push-Location (Join-Path $Root "web")
    npm install
    Pop-Location
}

Write-Host "Starting web on 0.0.0.0:3000 ..."
Push-Location (Join-Path $Root "web")
npm run dev -- -H 0.0.0.0 -p 3000
Pop-Location
