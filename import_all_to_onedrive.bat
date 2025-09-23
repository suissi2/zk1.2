@echo off
setlocal ENABLEDELAYEDEXPANSION

pushd %~dp0

REM Vérifie OneDrive
if "%OneDrive%"=="" (
  echo [ERREUR] La variable d'environnement OneDrive n'est pas definie.
  echo Veuillez vous connecter a OneDrive puis reessayer.
  popd
  exit /b 1
)

REM Crée le dossier OneDrive cible si besoin
set TARGET=%OneDrive%\Attendance\exports
if not exist "%TARGET%" (
  mkdir "%TARGET%" 2>nul
)

REM Vérifie l'existence du venv
if not exist .venv\Scripts\python.exe (
  echo [ERREUR] Environnement virtuel introuvable. Creez-le avec: python -m venv .venv
  popd
  exit /b 1
)

REM S'assure que config.ini existe
if not exist config.ini (
  if exist config.ini.template (
    copy /Y config.ini.template config.ini >nul
  ) else (
    echo [ERREUR] config.ini et config.ini.template introuvables.
    popd
    exit /b 1
  )
)

REM Met a jour output_directory dans config.ini vers OneDrive (remplace la ligne existante)
set TMPFILE=%TEMP%\config_%RANDOM%.tmp
>"%TMPFILE%" (
  for /f "usebackq delims=" %%L in ("config.ini") do (
    set "LINE=%%L"
    echo !LINE! | findstr /R /I "^output_directory\s*=" >nul
    if !ERRORLEVEL! EQU 0 (
      echo output_directory = %%OneDrive%%\Attendance\exports\
    ) else (
      echo !LINE!
    )
  )
)
move /Y "%TMPFILE%" config.ini >nul

REM Fixe l'encodage pour l'output Python
set PYTHONIOENCODING=utf-8

echo [INFO] Import complet vers OneDrive: "%TARGET%"
".venv\Scripts\python.exe" -c "from main import extract_access_to_csv; print(extract_access_to_csv(incremental=False))"
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% NEQ 0 (
  echo [ERREUR] Import complet a echoue ^(%EXITCODE%^).
) else (
  echo [OK] Import complet termine. Fichiers dans: "%TARGET%"
)

popd
exit /b %EXITCODE%
