@echo off
setlocal

cd /d "C:\appdevelopment\toolbox\codex"

set "SOURCE=C:\Users\Dell Optiplex\Documents\Codex\2026-06-20\ik-h\outputs\creative_toolbox.py"
set "TARGET=C:\appdevelopment\toolbox\codex\creative_toolbox.py"

echo Updating Creative Toolbox...

if not exist "%SOURCE%" (
    echo Source file not found:
    echo %SOURCE%
    pause
    exit /b 1
)

copy /Y "%SOURCE%" "%TARGET%" >nul
if errorlevel 1 (
    echo Could not copy the updated file.
    pause
    exit /b 1
)

echo Installing/checking dependencies...
py -m pip install openpyxl pillow psutil pycaw comtypes soundcard sounddevice numpy yt-dlp

if errorlevel 1 (
    echo Dependency install/check failed.
    pause
    exit /b 1
)

echo Starting Creative Toolbox...
py creative_toolbox.py

endlocal
pause