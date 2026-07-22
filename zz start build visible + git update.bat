@echo off
if /I "%~1"=="_run" goto run

start "Creative Toolbox build + GitHub release" cmd /k ""%~f0" _run"
exit /b

:run
setlocal EnableExtensions
cd /d "C:\appdevelopment\toolbox\codex"

echo.
echo === Creative Toolbox build + GitHub release ===
echo.

set "NO_PAUSE=1"
call "build exe.bat"
if errorlevel 1 (
    echo.
    echo Build failed. GitHub release was not published.
    echo.
    pause
    exit /b 1
)

echo.
echo Publishing GitHub release...
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\publish_github_release.ps1"
if errorlevel 1 (
    echo.
    echo GitHub release failed.
    echo.
    pause
    exit /b 1
)

echo.
echo All done.
echo.
pause
exit /b 0
