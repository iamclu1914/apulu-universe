@echo off
REM Create only the engagement-related scheduled tasks

set PYTHON=C:\Users\rdyal\AppData\Local\Programs\Python\Python312\python.exe
set VAWN_DIR=C:\Users\rdyal\Vawn

echo Creating engagement scheduled tasks...

REM Delete any existing engagement tasks first
schtasks /delete /tn "Vawn\EngagementAgent" /f 2>nul
schtasks /delete /tn "Vawn\EngagementBot" /f 2>nul

REM Create EngagementAgent task - every 2 hours starting at 8:00am
schtasks /create /tn "Vawn\EngagementAgent" /tr "%PYTHON% %VAWN_DIR%\engagement_agent.py" /sc daily /st 08:00 /ri 120 /du 24:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] EngagementAgent task created - every 2 hours
) else (
    echo [ERROR] Failed to create EngagementAgent task
)

REM Create EngagementBot task - every 5 hours starting at 9:30am
schtasks /create /tn "Vawn\EngagementBot" /tr "%PYTHON% %VAWN_DIR%\engagement_bot.py" /sc daily /st 09:30 /ri 300 /du 24:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] EngagementBot task created - every 5 hours
) else (
    echo [ERROR] Failed to create EngagementBot task
)

echo.
echo Checking created tasks...
schtasks /query /tn "Vawn\EngagementAgent" /fo LIST
schtasks /query /tn "Vawn\EngagementBot" /fo LIST

pause