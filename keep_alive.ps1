# AetherFin GPU Ops: 24/7 PowerShell Keep-Alive Script
# Runs a probe loop every 10 minutes to prevent Render free-tier sleep.

$BackendRoot = "https://aetherfin-gpu-ops-backend.onrender.com/"
$BackendNodes = "https://aetherfin-gpu-ops-backend.onrender.com/api/nodes"
$FrontendUrl = "https://frontend-sandy-seven-n9m6mrso9h.vercel.app"

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " AetherFin GPU Ops: 24/7 Keep-Alive Monitor" -ForegroundColor Green
Write-Host " Pinging every 10 minutes to prevent Render sleep" -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Cyan

function Probe-Url([string]$url, [string]$label) {
    try {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $resp = Invoke-WebRequest -Uri $url -Method Get -TimeoutSec 30 -UseBasicParsing
        $sw.Stop()
        Write-Host " [OK] $label - Status: $($resp.StatusCode) ($($sw.ElapsedMilliseconds)ms)" -ForegroundColor Green
    } catch {
        Write-Host " [FAIL] $label - Error: $_" -ForegroundColor Red
    }
}

while ($true) {
    $now = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "`n[$now] Probing live endpoints..." -ForegroundColor Gray
    Probe-Url $BackendRoot "Backend Root"
    Probe-Url $BackendNodes "Backend API Nodes"
    Probe-Url $FrontendUrl "Frontend Vercel"
    
    Write-Host "Sleeping 10 minutes until next probe..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 600
}

