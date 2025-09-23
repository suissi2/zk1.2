@echo off
setlocal ENABLEDELAYEDEXPANSION

pushd %~dp0

if not exist .scheduler.pid (
  echo [INFO] Aucun PID enregistré. Rien à arrêter.
  popd
  exit /b 0
)

for /f "usebackq delims=" %%p in (".scheduler.pid") do set PID=%%p
if not defined PID (
  echo [INFO] PID introuvable dans le fichier. Suppression du fichier.
  del /q .scheduler.pid >nul 2>&1
  popd
  exit /b 0
)

REM Tente d'arrêter le processus proprement puis force si besoin
taskkill /PID !PID! /T /F >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  echo [OK] Processus !PID! arrêté.
) else (
  echo [WARN] Impossible de tuer le processus !PID! ou déjà arrêté.
)

del /q .scheduler.pid >nul 2>&1

popd
exit /b 0

