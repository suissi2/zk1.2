@echo off
setlocal ENABLEDELAYEDEXPANSION

pushd %~dp0

REM Vérifie l'existence du venv
if not exist .venv\Scripts\python.exe (
  echo [ERREUR] Environnement virtuel introuvable. Créez-le avec: python -m venv .venv
  popd
  exit /b 1
)

set MODE=incremental
if /I "%~1"=="full" set MODE=full

REM Fixe l'encodage pour l'output Python
set PYTHONIOENCODING=utf-8

if /I "%MODE%"=="full" (
  echo [INFO] Import complet ^(non incrémental^)...
  ".venv\Scripts\python.exe" -c "from main import extract_access_to_csv; print(extract_access_to_csv(incremental=False))"
) else (
  echo [INFO] Import incrémental...
  ".venv\Scripts\python.exe" -c "from main import extract_access_to_csv; print(extract_access_to_csv(incremental=True))"
)

set EXITCODE=%ERRORLEVEL%
if %EXITCODE% NEQ 0 (
  echo [ERREUR] L'import a echoue avec le code %EXITCODE%.
) else (
  echo [OK] Import termine.
)

popd
exit /b %EXITCODE%
