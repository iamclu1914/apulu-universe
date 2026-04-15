@echo off
REM APU-127 Engagement Monitor Scheduler
REM Runs engagement monitoring with AI-powered auto-responses every 30 minutes

cd /d "C:\Users\rdyal\Vawn"

echo [%date% %time%] Starting APU-127 engagement monitor...

REM Run the engagement monitor
python engagement_monitor_apu127.py

if %ERRORLEVEL% equ 0 (
    echo [%date% %time%] APU-127 engagement monitor completed successfully
) else (
    echo [%date% %time%] APU-127 engagement monitor failed with error code %ERRORLEVEL%
)

echo.