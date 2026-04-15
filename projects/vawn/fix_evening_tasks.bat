@echo off
echo ============================================================
echo   APU-47 Evening-Main Fix - Enable Disabled Evening Tasks
echo ============================================================
echo.
echo This script will enable the disabled evening posting tasks.
echo Make sure to run this as Administrator.
echo.
pause

echo [1/2] Enabling EveningEarly task (6:00pm)...
powershell.exe "Enable-ScheduledTask -TaskName 'EveningEarly' -TaskPath '\Vawn\'"
if errorlevel 1 (
    echo [ERROR] Failed to enable EveningEarly task. Make sure you're running as Administrator.
    pause
    exit /b 1
)
echo [OK] EveningEarly task enabled

echo.
echo [2/2] Enabling EveningMain task (8:15pm)...
powershell.exe "Enable-ScheduledTask -TaskName 'EveningMain' -TaskPath '\Vawn\'"
if errorlevel 1 (
    echo [ERROR] Failed to enable EveningMain task. Make sure you're running as Administrator.
    pause
    exit /b 1
)
echo [OK] EveningMain task enabled

echo.
echo ============================================================
echo SUCCESS: Evening posting tasks have been re-enabled!
echo.
echo EveningEarly: 6:00pm daily (X + Bluesky + IG slideshow)
echo EveningMain:  8:15pm daily (TikTok + Threads)
echo.
echo The evening posting pipeline should now work automatically.
echo ============================================================
echo.
pause