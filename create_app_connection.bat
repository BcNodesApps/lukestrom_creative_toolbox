@echo off
setlocal EnableExtensions

set "SUPABASE_URL=https://kazkqusgrfisanohvcaw.supabase.co"

echo.
echo === LukeStrom app connection ===
echo.
echo This creates app_connection.json in this folder.
echo The publishable key is safe to ship with the desktop app.
echo Do NOT paste a database password or service role/admin key here.
echo.
echo Supabase URL:
echo %SUPABASE_URL%
echo.
set /p "SUPABASE_KEY=Paste Supabase publishable key: "

if "%SUPABASE_KEY%"=="" (
    echo.
    echo ERROR: No key entered.
    pause
    exit /b 1
)

> app_connection.json echo {
>> app_connection.json echo   "url": "%SUPABASE_URL%",
>> app_connection.json echo   "publishable_key": "%SUPABASE_KEY%"
>> app_connection.json echo }

echo.
echo Created:
echo %CD%\app_connection.json
echo.
pause
