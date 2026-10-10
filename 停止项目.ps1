$ErrorActionPreference = 'SilentlyContinue'
foreach ($port in @(8080, 5173)) {
  Get-NetTCPConnection -LocalPort $port -State Listen | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force; Write-Host "已停止端口 $port 的进程 $_" -ForegroundColor Green }
}
Write-Host '项目服务已停止。' -ForegroundColor Cyan
