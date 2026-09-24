$ErrorActionPreference = 'Stop'
$mvn = Get-Command mvn -ErrorAction SilentlyContinue
if ($mvn) { & $mvn.Source spring-boot:run; exit $LASTEXITCODE }
$candidates = @(
  "$env:USERPROFILE\.m2\wrapper\dists\apache-maven-3.9.10-bin\53h08a94dg6djh6umvruv7q564\apache-maven-3.9.10\bin\mvn.cmd",
  "$env:USERPROFILE\.m2\wrapper\dists\apache-maven-3.9.16\*\apache-maven-3.9.16\bin\mvn.cmd"
)
$found = $candidates | ForEach-Object { Get-Item $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
if (-not $found) { throw 'Maven was not found. Install Maven 3.9+ or configure it in VS Code.' }
& $found.FullName spring-boot:run
exit $LASTEXITCODE
