$ErrorActionPreference = 'SilentlyContinue'
foreach ($port in @(8080, 5173)) { Get-NetTCPConnection -LocalPort $port -State Listen | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force; Write-Host "Stopped process $_ on port $port" -ForegroundColor Green } }
Write-Host 'Project services stopped.' -ForegroundColor Cyan
