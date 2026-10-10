$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root 'backend'
$frontend = Join-Path $root 'frontend'
$backendPort = 8080
$frontendPort = 5173

function Test-Port([int]$port) { return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw '未找到 Node.js。请先安装 Node.js 18 或更高版本。' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw '未找到 npm。请先安装 Node.js。' }
if (-not (Test-Path (Join-Path $backend 'run-local.ps1'))) { throw '未找到 backend/run-local.ps1。' }
if (-not (Test-Path (Join-Path $frontend 'package.json'))) { throw '未找到 frontend/package.json。' }

if (Test-Port $backendPort) { Write-Host "后端端口 $backendPort 已被占用，将复用当前后端。" -ForegroundColor Yellow }
else { Start-Process powershell.exe -WorkingDirectory $backend -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File',(Join-Path $backend 'run-local.ps1')) -WindowStyle Normal; Write-Host '后端启动命令已发送。' -ForegroundColor Green }
if (Test-Port $frontendPort) { Write-Host "前端端口 $frontendPort 已被占用，将复用当前前端。" -ForegroundColor Yellow }
else { Start-Process cmd.exe -WorkingDirectory $frontend -ArgumentList @('/k','npm run dev -- --host 127.0.0.1') -WindowStyle Normal; Write-Host '前端启动命令已发送。' -ForegroundColor Green }

$ready = $false
for ($i = 0; $i -lt 60; $i++) { if (Test-Port $frontendPort) { $ready = $true; break }; Start-Sleep -Seconds 1 }
if ($ready) { Start-Process "http://localhost:$frontendPort"; Write-Host "项目已启动：http://localhost:$frontendPort" -ForegroundColor Cyan }
else { Write-Host '前端尚未就绪。请查看前端终端窗口。' -ForegroundColor Yellow }
Write-Host '关闭项目：运行 停止项目.ps1，或关闭后端和前端终端窗口。' -ForegroundColor Gray
