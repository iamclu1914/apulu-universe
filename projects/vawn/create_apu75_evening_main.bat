@echo off
echo ===============================================
echo   APU-75 Evening-Main Task Activation
echo ===============================================
echo.
echo This script enables the EveningMain scheduled task for:
echo  - TikTok + Threads posting at 8:15pm daily
echo  - "8pm prime time — storytelling, depth, J. Cole wordplay"
echo.
echo IMPORTANT: Run this as Administrator to enable the task.
echo.
pause

echo [1/3] Checking current EveningMain task status...
powershell.exe "Get-ScheduledTask -TaskName 'EveningMain' -TaskPath '\Vawn\' -ErrorAction SilentlyContinue | Format-Table TaskName,State,LastRunTime,NextRunTime"
echo.

echo [2/3] Enabling EveningMain task...
powershell.exe "Enable-ScheduledTask -TaskName 'EveningMain' -TaskPath '\Vawn\'"
if errorlevel 1 (
    echo [ERROR] Failed to enable EveningMain task.
    echo Please run this script as Administrator.
    echo Right-click this .bat file and select "Run as Administrator"
    pause
    exit /b 1
)
echo [OK] EveningMain task enabled successfully

echo.
echo [3/3] Verifying task configuration...
powershell.exe "Get-ScheduledTask -TaskName 'EveningMain' -TaskPath '\Vawn\' | Select-Object -ExpandProperty Actions | Format-List Execute,Arguments,WorkingDirectory"
echo.

echo ===============================================
echo SUCCESS: APU-75 Evening-Main Task Activated!
echo.
echo Task Details:
echo  - Target: TikTok + Threads
echo  - Schedule: 8:15pm daily
echo  - Command: python post_vawn.py --cron evening --platforms tiktok,threads
echo  - Content: Storytelling, depth, J. Cole wordplay vibe
echo.
echo Test the evening pipeline manually:
echo  python post_vawn.py --cron evening --platforms tiktok,threads
echo.
echo The evening posting automation is now active!
echo ===============================================
echo.
pause