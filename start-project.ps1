$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
function Test-Port([int]$port) { return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js 18+ is required.' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm is required.' }
if (-not (Test-Path (Join-Path $backend 'run-local.ps1'))) { throw 'backend/run-local.ps1 was not found.' }
if (-not (Test-Path (Join-Path $frontend 'package.json'))) { throw 'frontend/package.json was not found.' }
if (Test-Port 8080) { Write-Host 'Backend port 8080 is already in use; reusing it.' -ForegroundColor Yellow }
else { Start-Process powershell.exe -WorkingDirectory $backend -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File',(Join-Path $backend 'run-local.ps1')) -WindowStyle Normal; Write-Host 'Backend start command sent. Waiting for port 8080...' -ForegroundColor Green }
if (-not (Test-Port 8080)) {
  for ($i = 0; $i -lt 90; $i++) { if (Test-Port 8080) { break }; Start-Sleep -Seconds 1 }
}
if (-not (Test-Port 8080)) { Write-Host 'Backend did not start. Check the backend terminal for Maven or dependency errors.' -ForegroundColor Red }
if (Test-Port 5173) { Write-Host 'Frontend port 5173 is already in use; reusing it.' -ForegroundColor Yellow }
else { Start-Process cmd.exe -WorkingDirectory $frontend -ArgumentList @('/k','npm run dev -- --host 127.0.0.1') -WindowStyle Normal }
$ready = $false
for ($i = 0; $i -lt 60; $i++) { if (Test-Port 5173) { $ready = $true; break }; Start-Sleep -Seconds 1 }
if ($ready) {
  Start-Process 'http://localhost:5173'
  if (Test-Port 8080) { Write-Host 'Project is ready: http://localhost:5173 (backend: 8080)' -ForegroundColor Cyan }
  else { Write-Host 'Frontend is ready, but backend is not running. The page cannot call the review API.' -ForegroundColor Red }
}
else { Write-Host 'Frontend is not ready. Check the frontend terminal.' -ForegroundColor Yellow }
