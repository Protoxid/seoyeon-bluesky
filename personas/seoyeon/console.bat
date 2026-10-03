@echo off
REM ---------------------------------------------------------------------
REM  console.bat - start the Seo-yeon console.
REM
REM  Double-click this, not console.py. A double-clicked .py closes its own
REM  window the instant anything goes wrong, which is how a real error turns
REM  into "page not reachable" with nothing to read. This keeps the window.
REM
REM  cd /d %~dp0 means "the folder this .bat is in", so it works from the
REM  desktop, from a shortcut, from anywhere.
REM ---------------------------------------------------------------------
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   ! 'python' is not on your PATH.
  echo     Try 'py console.py' instead, or reinstall Python with
  echo     "Add python.exe to PATH" ticked.
  echo.
  pause
  exit /b 1
)

python console.py
echo.
echo   -- the console has stopped --
pause
