# Verity Systems - Server Startup Script
# Ensures clean, consistent startup of all services

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Verity Systems - Starting Servers" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Set working directory
$projectRoot = "c:\Users\lawm\Desktop\verity-systems"
$pythonTools = "$projectRoot\python-tools"
$publicDir = "$projectRoot\public"

# Set encoding
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Step 1: Kill any existing Python processes
Write-Host "[1/5] Stopping existing Python processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Step 2: Free ports 8000 and 8081
Write-Host "[2/5] Freeing ports 8000 and 8081..." -ForegroundColor Yellow
$ports = @(8000, 8081)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        try {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "  - Freed port $port (PID: $($conn.OwningProcess))" -ForegroundColor Gray
        } catch {}
    }
}
Start-Sleep -Seconds 1

# Step 3: Start API Server
Write-Host "[3/5] Starting API Server on port 8081..." -ForegroundColor Yellow
$apiJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    $env:PYTHONIOENCODING = "utf-8"
    $env:PORT = "8081"
    python api_server_v4.py 2>&1
} -ArgumentList $pythonTools

Start-Sleep -Seconds 3

# Step 4: Start Frontend Server
Write-Host "[4/5] Starting Frontend Server on port 8000..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    param($dir)
    python -m http.server 8000 --directory $dir 2>&1
} -ArgumentList $publicDir

Start-Sleep -Seconds 2

# Step 5: Verify servers are running
Write-Host "[5/5] Verifying servers..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$apiRunning = $false
$frontendRunning = $false

# Check API server
try {
    $apiCheck = Invoke-WebRequest -Uri "http://localhost:8081/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($apiCheck.StatusCode -eq 200) {
        $apiRunning = $true
    }
} catch {}

# Check Frontend server
try {
    $frontendCheck = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($frontendCheck.StatusCode -eq 200) {
        $frontendRunning = $true
    }
} catch {}

# Report status
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Server Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($apiRunning) {
    Write-Host "  API Server:      [RUNNING] http://localhost:8081" -ForegroundColor Green
    Write-Host "  API Docs:        [RUNNING] http://localhost:8081/docs" -ForegroundColor Green
} else {
    Write-Host "  API Server:      [STARTING] http://localhost:8081" -ForegroundColor Yellow
}

if ($frontendRunning) {
    Write-Host "  Frontend:        [RUNNING] http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "  Frontend:        [STARTING] http://localhost:8000" -ForegroundColor Yellow
}

Write-Host "`n  New Features:" -ForegroundColor Cyan
Write-Host "  - Waitlist:      http://localhost:8000/waitlist.html" -ForegroundColor White
Write-Host "  - Misinfo Map:   http://localhost:8000/misinformation-map.html" -ForegroundColor White

Write-Host "`n========================================`n" -ForegroundColor Cyan

# Keep script running to show logs
Write-Host "Press Ctrl+C to stop servers`n" -ForegroundColor Gray

# Show job output
while ($true) {
    Receive-Job -Job $apiJob -ErrorAction SilentlyContinue
    Receive-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}
