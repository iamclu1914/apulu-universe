@echo off
REM ============================================================
REM Fix Engagement Agents - Restart stale agent tasks
REM Created by: Dex - Community Agent (APU-23)
REM ============================================================

echo [INFO] Checking Windows Task Scheduler for engagement agents...

REM Check if EngagementAgent task exists and is running
schtasks /query /tn "Vawn\EngagementAgent" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] EngagementAgent task exists
    echo [INFO] Running EngagementAgent now...
    schtasks /run /tn "Vawn\EngagementAgent"
) else (
    echo [ERROR] EngagementAgent task not found in scheduler
    echo [FIX] Run setup_scheduler.bat as Administrator to recreate tasks
)

REM Check if EngagementBot task exists and is running
schtasks /query /tn "Vawn\EngagementBot" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] EngagementBot task exists
    echo [INFO] Running EngagementBot now...
    schtasks /run /tn "Vawn\EngagementBot"
) else (
    echo [ERROR] EngagementBot task not found in scheduler
    echo [FIX] Run setup_scheduler.bat as Administrator to recreate tasks
)

echo.
echo [INFO] Testing engagement monitor...
python "%~dp0engagement_monitor.py"

echo.
echo [DONE] Engagement agents restarted
pause