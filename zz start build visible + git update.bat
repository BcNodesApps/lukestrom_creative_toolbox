@echo off
if /I "%~1"=="_run" goto run

start "Creative Toolbox build + GitHub release" cmd /k ""%~f0" _run"
exit /b

:run
setlocal EnableExtensions
cd /d "C:\appdevelopment\toolbox\codex"

set "LOGDIR=%USERPROFILE%\Downloads"
if not exist "%LOGDIR%" set "LOGDIR=%TEMP%"
for /f "tokens=1-5 delims=/.:, " %%a in ("%DATE% %TIME%") do set "STAMP=%DATE:/=-%_%TIME::=-%"
set "STAMP=%STAMP: =_%"
set "STAMP=%STAMP:,=_%"
set "LOGFILE=%LOGDIR%\lukestrom_build_%STAMP%.log"

echo.
echo === Creative Toolbox build + GitHub release ===
echo Log file:
echo %LOGFILE%
echo.
echo === Creative Toolbox build + GitHub release === > "%LOGFILE%"
echo Started: %DATE% %TIME% >> "%LOGFILE%"
echo Working folder: %CD% >> "%LOGFILE%"
echo. >> "%LOGFILE%"

set "NO_PAUSE=1"
call "build exe.bat" 2>&1 | powershell -NoProfile -ExecutionPolicy Bypass -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
if errorlevel 1 (
    echo.
    echo Build failed. GitHub release was not published.
    echo Log file: %LOGFILE%
    echo. >> "%LOGFILE%"
    echo Build failed. GitHub release was not published. >> "%LOGFILE%"
    echo Finished: %DATE% %TIME% >> "%LOGFILE%"
    echo.
    pause
    exit /b 1
)

echo.
echo Publishing GitHub release...
echo. >> "%LOGFILE%"
echo Publishing GitHub release... >> "%LOGFILE%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\publish_github_release.ps1" 2>&1 | powershell -NoProfile -ExecutionPolicy Bypass -Command "$input | Tee-Object -FilePath '%LOGFILE%' -Append"
if errorlevel 1 (
    echo.
    echo GitHub release failed.
    echo Log file: %LOGFILE%
    echo. >> "%LOGFILE%"
    echo GitHub release failed. >> "%LOGFILE%"
    echo Finished: %DATE% %TIME% >> "%LOGFILE%"
    echo.
    pause
    exit /b 1
)

echo.
echo All done.
echo Log file: %LOGFILE%
echo. >> "%LOGFILE%"
echo All done. >> "%LOGFILE%"
echo Finished: %DATE% %TIME% >> "%LOGFILE%"
echo.
pause
exit /b 0
