$ErrorActionPreference = 'Stop'

Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONIOENCODING = 'utf-8'

Write-Host "[INFO] Exécution de import_all_to_onedrive.bat depuis $PSScriptRoot" -ForegroundColor Cyan

& cmd /c ".\import_all_to_onedrive.bat"

if ($LASTEXITCODE -ne 0) {
  Write-Host "[ERREUR] Script batch retourne le code $LASTEXITCODE" -ForegroundColor Red
  exit $LASTEXITCODE
}

Write-Host "[OK] Import terminé via PowerShell wrapper." -ForegroundColor Green
