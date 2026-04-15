@echo off
echo ===============================================
echo   APU-128 Morning-Main Task Activation
echo ===============================================
echo.
echo This script enables the MorningMain scheduled task for:
echo  - TikTok + Instagram + Threads posting at 9:00am daily
echo  - "9am — sharp, intentional, quiet confidence"
echo.
echo IMPORTANT: Run this as Administrator to enable the task.
echo.
pause

echo [1/3] Checking current MorningMain task status...
powershell.exe "Get-ScheduledTask -TaskName 'MorningMain' -TaskPath '\Vawn\' -ErrorAction SilentlyContinue | Format-Table TaskName,State,LastRunTime,NextRunTime"
echo.

echo [2/3] Enabling MorningMain task...
powershell.exe "Enable-ScheduledTask -TaskName 'MorningMain' -TaskPath '\Vawn\'"
if errorlevel 1 (
    echo [ERROR] Failed to enable MorningMain task.
    echo Please run this script as Administrator.
    echo Right-click this .bat file and select "Run as Administrator"
    pause
    exit /b 1
)
echo [OK] MorningMain task enabled successfully

echo.
echo [3/3] Verifying task configuration...
powershell.exe "Get-ScheduledTask -TaskName 'MorningMain' -TaskPath '\Vawn\' | Select-Object -ExpandProperty Actions | Format-List Execute,Arguments,WorkingDirectory"
echo.

echo ===============================================
echo SUCCESS: APU-128 Morning-Main Task Activated!
echo.
echo Task Details:
echo  - Target: TikTok + Instagram + Threads
echo  - Schedule: 9:00am daily
echo  - Command: python post_vawn.py --cron morning --platforms tiktok,instagram,threads
echo  - Content: Sharp, intentional, quiet confidence vibe
echo.
echo Test the morning pipeline manually:
echo  python post_vawn.py --cron morning --platforms tiktok,instagram,threads
echo.
echo The morning posting automation is now active!
echo ===============================================
echo.
pause