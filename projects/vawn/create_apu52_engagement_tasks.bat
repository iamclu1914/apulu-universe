@echo off
REM APU-52 Unified Engagement Tasks - Coordinated scheduling for enhanced systems
REM Replaces basic engagement tasks with unified coordination system

set PYTHON=C:\Users\rdyal\AppData\Local\Programs\Python\Python312\python.exe
set VAWN_DIR=C:\Users\rdyal\Vawn

echo APU-52: Creating unified engagement monitoring tasks...
echo.

REM Delete existing basic engagement tasks
echo Removing old basic engagement tasks...
schtasks /delete /tn "Vawn\EngagementAgent" /f 2>nul
schtasks /delete /tn "Vawn\EngagementBot" /f 2>nul

REM Create enhanced engagement bot task (APU-50) - every 4 hours starting at 9:30am
echo Creating Enhanced Engagement Bot task (APU-50)...
schtasks /create /tn "Vawn\EnhancedEngagementBot" /tr "%PYTHON% %VAWN_DIR%\engagement_bot_enhanced.py" /sc daily /st 09:30 /ri 240 /du 24:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Enhanced Engagement Bot task created - every 4 hours starting 9:30am
) else (
    echo [ERROR] Failed to create Enhanced Engagement Bot task
)

REM Create unified engagement monitor task (APU-52) - runs 30 minutes after bot
echo Creating Unified Engagement Monitor task (APU-52)...
schtasks /create /tn "Vawn\UnifiedEngagementMonitor" /tr "%PYTHON% %VAWN_DIR%\src\apu52_unified_engagement_monitor.py" /sc daily /st 10:00 /ri 240 /du 24:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Unified Engagement Monitor task created - every 4 hours starting 10:00am
) else (
    echo [ERROR] Failed to create Unified Engagement Monitor task
)

REM Create engagement health check task - every 2 hours for API monitoring
echo Creating Engagement Health Check task...
schtasks /create /tn "Vawn\EngagementHealthCheck" /tr "%PYTHON% %VAWN_DIR%\engagement_bot_enhanced.py --health-only" /sc daily /st 08:00 /ri 120 /du 24:00 /f
if %ERRORLEVEL% EQU 0 (
    echo [OK] Engagement Health Check task created - every 2 hours starting 8:00am
) else (
    echo [ERROR] Failed to create Engagement Health Check task
)

echo.
echo APU-52 Task Schedule Summary:
echo ========================================
echo 08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00: Health Check
echo 09:30, 13:30, 17:30, 21:30: Enhanced Bot Execution
echo 10:00, 14:00, 18:00, 22:00: Unified Monitor Coordination
echo.

echo Verifying created tasks...
echo.
echo [Enhanced Engagement Bot]
schtasks /query /tn "Vawn\EnhancedEngagementBot" /fo LIST 2>nul
echo.
echo [Unified Engagement Monitor]
schtasks /query /tn "Vawn\UnifiedEngagementMonitor" /fo LIST 2>nul
echo.
echo [Engagement Health Check]
schtasks /query /tn "Vawn\EngagementHealthCheck" /fo LIST 2>nul

echo.
echo APU-52 unified engagement system ready!
echo.
echo Manual execution commands:
echo Enhanced Bot: python engagement_bot_enhanced.py
echo Health Check: python engagement_bot_enhanced.py --health-only
echo Unified Monitor: python src\apu52_unified_engagement_monitor.py
echo.

pause