@echo off
setlocal ENABLEDELAYEDEXPANSION

pushd %~dp0

REM Vérifie l'existence du venv
if not exist .venv\Scripts\python.exe (
  echo [ERREUR] Environnement virtuel introuvable. Créez-le avec: python -m venv .venv
  popd
  exit /b 1
)

REM Vérifie si un PID est déjà enregistré et vivant
if exist .scheduler.pid (
  for /f "usebackq delims=" %%p in (".scheduler.pid") do set PID=%%p
  if defined PID (
    for /f "tokens=1" %%a in ('tasklist /FI "PID eq !PID!" ^| findstr /R /C:" !PID! "') do (
      echo [INFO] Scheduler déjà en cours (PID=!PID!).
      popd
      exit /b 0
    )
  )
)

REM Démarre main.py en arrière-plan et capture le PID via PowerShell
for /f "usebackq delims=" %%p in (`powershell -NoProfile -Command ^
  "$p = Start-Process -FilePath '.\\.venv\\Scripts\\python.exe' -ArgumentList 'main.py' -WorkingDirectory '.' -PassThru -WindowStyle Hidden; ^
   $p.Id"`) do set NEWPID=%%p

echo !NEWPID! > .scheduler.pid

echo [OK] Scheduler démarre. PID=!NEWPID!

popd
exit /b 0

