@echo off
setlocal

REM Usage:
REM   export_to_sheets.bat [test|prod] [host] [port] [path]
REM   - mode: test (defaut, 5679) | prod (5678)
REM   - host: defaut localhost
REM   - port: surcharge manuelle si besoin
REM   - path: chemin du webhook (defaut: export)

set MODE=%1
if "%MODE%"=="" set MODE=test

set HOST=%2
if "%HOST%"=="" set HOST=localhost

set TEST_PORT=5679
set PROD_PORT=5678

if /I "%MODE%"=="prod" (
	set PORT=%PROD_PORT%
) else (
	set PORT=%TEST_PORT%
)

if not "%3"=="" set PORT=%3

set PATH_SEG=%4
if "%PATH_SEG%"=="" set PATH_SEG=export

set URL=http://%HOST%:%PORT%/webhook/%PATH_SEG%
set OUT_FILE=%~dp0export_response.json
set TMP_HTTP=%TEMP%\export_http_code.tmp

echo Mode: %MODE%
echo URL: %URL%

where curl.exe >NUL 2>&1
if errorlevel 1 (
	echo Erreur: curl.exe introuvable dans le PATH.
	echo Alternative PowerShell:
	echo   Invoke-RestMethod -Method Post -Uri "%URL%" -Body '{}' -ContentType 'application/json' ^| ConvertTo-Json ^| Out-File -Encoding utf8 "%OUT_FILE%"
	exit /b 1
)

del /f /q "%TMP_HTTP%" >NUL 2>&1

echo Envoi de la requete...
curl.exe --fail-with-body -sS -X POST "%URL%" ^
	-H "Content-Type: application/json" ^
	-d "{}" ^
	-o "%OUT_FILE%" ^
	-w "%%{http_code}" > "%TMP_HTTP%"
set ERR=%ERRORLEVEL%

set HTTP_CODE=
if exist "%TMP_HTTP%" set /p HTTP_CODE=<"%TMP_HTTP%"
del /f /q "%TMP_HTTP%" >NUL 2>&1

echo HTTP: %HTTP_CODE%

if not %ERR%==0 goto :error

REM Si curl a reussi, on verifie le code HTTP (2xx attendu)
if "%HTTP_CODE%"=="" goto :error
if "%HTTP_CODE:~0,1%"=="2" goto :ok

goto :error

:ok
echo Reponse enregistree dans: %OUT_FILE%
exit /b 0

:error
echo La requete a echoue.
echo - Code HTTP: %HTTP_CODE%
echo - Mode utilise: %MODE% (test=5679, prod=5678)
echo - URL visee: %URL%
echo.
echo Causes probables:
echo   1) Port 5679: le workflow n'est pas en mode test ^(bouton "Execute Workflow" actif^) dans n8n.
echo   2) Sinon utilisez le mode prod avec workflow active: .\export_to_sheets.bat prod
echo   3) n8n n'est pas demarre, ou hote/port/chemin incorrects.
echo.
if exist "%OUT_FILE%" (
	echo Corps de reponse ^(si present^):
	type "%OUT_FILE%"
)
exit /b 1

endlocal
