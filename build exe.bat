@echo off
setlocal EnableExtensions

set "SOURCE=C:\Users\Dell Optiplex\Documents\Codex\2026-06-20\ik-h\outputs\creative_toolbox.py"
set "TARGET_DIR=C:\appdevelopment\toolbox\codex"
set "TARGET=%TARGET_DIR%\creative_toolbox.py"

cd /d "%TARGET_DIR%"

echo.
echo === Creative Toolbox build ===
echo Working folder: %CD%
echo.

echo Updating source from Codex outputs...
if not exist "%SOURCE%" (
    echo ERROR: Source file not found:
    echo %SOURCE%
    goto fail
)

copy /Y "%SOURCE%" "%TARGET%" >nul
if errorlevel 1 (
    echo ERROR: Could not copy latest creative_toolbox.py.
    goto fail
)

if not exist "creative_toolbox.py" (
    echo ERROR: creative_toolbox.py was not found.
    goto fail
)

echo Reading app version...
for /f "tokens=2 delims==" %%V in ('findstr /B "APP_VERSION" creative_toolbox.py') do set "APPVER=%%~V"
set "APPVER=%APPVER:"=%"
set "APPVER=%APPVER: =%"
if "%APPVER%"=="" set "APPVER=V?"
echo Version: %APPVER%

echo.
echo Updating Git before EXE build...
for /f "tokens=1-5 delims=/.:, " %%a in ("%DATE% %TIME%") do set "NOW=%DATE% %TIME:~0,5%"

git add .
if errorlevel 1 goto fail

git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo No Git changes to commit.
) else (
    git commit -m "%NOW% %APPVER%"
    if errorlevel 1 goto fail
)

git push
if errorlevel 1 goto fail

echo.
echo Installing/updating required Python packages...
py -m pip install -r requirements_toolbox.txt
if errorlevel 1 goto fail

if not exist "build_assets" mkdir "build_assets"

echo.
echo Creating app icon...
py -c "from pathlib import Path; from PIL import Image; src=Path(r'D:\OneDrive\Production\uploads\260414 logo lukestrom round.png'); out=Path('build_assets/lukestrom.ico'); (Image.open(src).convert('RGBA').save(out, sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)]) if src.exists() else print('Logo not found, building without custom icon'))"

set ICON_ARGS=
if exist "build_assets\lukestrom.ico" set ICON_ARGS=--icon "build_assets\lukestrom.ico"

set LOGO_ARGS=
if exist "D:\OneDrive\Production\uploads\260414 logo lukestrom round.png" set LOGO_ARGS=--add-data "D:\OneDrive\Production\uploads\260414 logo lukestrom round.png;."

set FFMPEG_ARGS=
if exist "C:\ffmpeg\bin\ffmpeg.exe" set FFMPEG_ARGS=--add-binary "C:\ffmpeg\bin\ffmpeg.exe;ffmpeg"

echo.
echo Building one-file EXE...
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

if errorlevel 1 goto fail

echo.
echo Build done.
echo EXE:
echo %CD%\dist\Creative Toolbox.exe
echo.

if "%NO_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:fail
echo.
echo ERROR: Build failed.
echo.
if "%NO_PAUSE%"=="1" exit /b 1
pause
exit /b 1
