@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

rem Detect current branch name
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>NUL') do set BRANCH=%%b
if not defined BRANCH (
  echo [git] Impossible de déterminer la branche courante. Assurez-vous d'etre dans un depot Git.
  exit /b 1
)

rem Optional commit message from arguments
set USER_MSG=%*
if not defined USER_MSG set USER_MSG=

rem Stage changes
git add -A

rem Check if there is anything to commit
git diff-index --quiet HEAD -- 2>NUL
if errorlevel 1 (
  rem There are staged/working changes; create a commit
  git commit -m "sync: %DATE% %TIME% %USER_MSG%" || goto :error
) else (
  echo [git] Aucun changement a committer.
)

rem Rebase on latest upstream before pushing
echo [git] Pull --rebase depuis origin/%BRANCH% ...
git pull --rebase origin %BRANCH% || goto :error

rem Push current branch
echo [git] Push vers origin/%BRANCH% ...
git push origin %BRANCH% || goto :error

echo [git] Synchronisation terminee avec succes.
exit /b 0

:error
echo [git] Erreur pendant la synchronisation. Consultez les messages ci-dessus.
exit /b 1


