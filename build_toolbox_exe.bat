@echo off
setlocal

cd /d "%~dp0"

echo.
echo === Creative Toolbox EXE build ===
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
echo Building EXE folder...
py -m PyInstaller ^
  --noconfirm ^
  --clean ^
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
echo Your app is here:
echo %CD%\dist\Creative Toolbox\Creative Toolbox.exe
echo.
echo Copy the whole folder "dist\Creative Toolbox" to your laptop.
echo.
pause
