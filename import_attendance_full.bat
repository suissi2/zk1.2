@echo off
setlocal ENABLEDELAYEDEXPANSION

pushd %~dp0

if not exist .venv\Scripts\python.exe (
  echo [ERREUR] Environnement virtuel introuvable. Créez-le avec: python -m venv .venv
  popd
  exit /b 1
)

set PYTHONIOENCODING=utf-8

echo [INFO] Import complet ^(non incremental^)...
".venv\Scripts\python.exe" -c "from main import extract_access_to_csv; print(extract_access_to_csv(incremental=False))"

set EXITCODE=%ERRORLEVEL%
if %EXITCODE% NEQ 0 (
  echo [ERREUR] L'import complet a echoue avec le code %EXITCODE%.
) else (
  echo [OK] Import complet termine.
)

popd
exit /b %EXITCODE%

