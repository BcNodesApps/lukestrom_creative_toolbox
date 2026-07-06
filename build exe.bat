@echo off
setlocal EnableExtensions

echo.
echo Updating Git before EXE build...

cd /d "C:\appdevelopment\toolbox\codex"

for /f "tokens=2 delims==" %%V in ('findstr /B "APP_VERSION" creative_toolbox.py') do set "APPVER=%%~V"
set "APPVER=%APPVER:"=%"
set "APPVER=%APPVER: =%"

for /f "tokens=1-5 delims=/.:, " %%a in ("%DATE% %TIME%") do (
    set "NOW=%DATE% %TIME:~0,5%"
)

git add .

git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo No Git changes to commit.
) else (
    git commit -m "%NOW% %APPVER%"
)

git push

echo.
echo Git update done. Continuing EXE build...
echo.

REM hieronder laat je de bestaande build-code staan

@echo off
setlocal

cd /d "%~dp0"

echo.
echo === Creative Toolbox ONE-FILE EXE build ===
echo Working folder: %CD%
echo.

if not exist "creative_toolbox.py" (
    echo ERROR: creative_toolbox.py was not found in this folder.
    echo Copy this build file into C:\appdevelopment\toolbox\codex and run it there.
    pause
    exit /b 1
)

echo Installing/updating required Python packages...
py -m pip install -r requirements_toolbox.txt
if errorlevel 1 (
    echo.
    echo ERROR: Package installation failed.
    pause
    exit /b 1
)

if not exist "build_assets" mkdir "build_assets"

echo Creating app icon...
py -c "from pathlib import Path; from PIL import Image; src=Path(r'D:\OneDrive\Production\uploads\260414 logo lukestrom round.png'); out=Path('build_assets/lukestrom.ico'); (Image.open(src).convert('RGBA').save(out, sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)]) if src.exists() else print('Logo not found, building without custom icon'))"

set ICON_ARGS=
if exist "build_assets\lukestrom.ico" set ICON_ARGS=--icon "build_assets\lukestrom.ico"

set LOGO_ARGS=
if exist "D:\OneDrive\Production\uploads\260414 logo lukestrom round.png" set LOGO_ARGS=--add-data "D:\OneDrive\Production\uploads\260414 logo lukestrom round.png;."

set FFMPEG_ARGS=
if exist "C:\ffmpeg\bin\ffmpeg.exe" set FFMPEG_ARGS=--add-binary "C:\ffmpeg\bin\ffmpeg.exe;ffmpeg"

echo.
echo Building single EXE...
py -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name "Creative Toolbox" ^
  %ICON_ARGS% ^
  --add-data "13-song_analyzer\song_analyzer.py;13-song_analyzer" ^
  --add-data "8-youtube_dl\release notes.txt;8-youtube_dl" ^
  %LOGO_ARGS% ^
  %FFMPEG_ARGS% ^
  --collect-all yt_dlp ^
  --collect-all librosa ^
  --collect-all matplotlib ^
  --collect-all reportlab ^
  --collect-all openpyxl ^
  --collect-all numpy ^
  --collect-all scipy ^
  --collect-all sklearn ^
  --collect-all soundfile ^
  --collect-all audioread ^
  --collect-all numba ^
  --collect-all llvmlite ^
  --hidden-import PIL._tkinter_finder ^
  creative_toolbox.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo DONE.
echo Your one-file app is here:
echo %CD%\dist\Creative Toolbox.exe
echo.
echo You can copy just this EXE to your laptop.
echo Background images stay external and are read from:
echo D:\OneDrive\Production\creations
echo.
pause
