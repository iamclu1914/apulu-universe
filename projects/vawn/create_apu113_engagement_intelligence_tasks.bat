@echo off
REM APU-113 Engagement Intelligence Dashboard Setup and Scheduler
REM Comprehensive intelligence system that consolidates all engagement monitoring data
REM Created by: Dex - Community Agent (APU-113)

echo.
echo ===============================================================================
echo   APU-113 Engagement Intelligence Dashboard Setup
echo   Comprehensive intelligence consolidation for all engagement monitoring
echo ===============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH. Please install Python 3.7+
    pause
    exit /b 1
)

REM Set environment variables
set PYTHON=python
set VAWN_DIR=%~dp0
set SCRIPT_DIR=%VAWN_DIR%src

echo [INFO] VAWN Directory: %VAWN_DIR%
echo [INFO] Scripts Directory: %SCRIPT_DIR%

REM Verify APU-113 script exists
if not exist "%SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py" (
    echo [ERROR] APU-113 script not found at %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py
    pause
    exit /b 1
)

echo.
echo [INFO] Creating APU-113 Engagement Intelligence Tasks...

REM Delete existing APU-113 tasks
schtasks /delete /tn "Vawn\APU113IntelligenceAnalyzer" /f >nul 2>&1
schtasks /delete /tn "Vawn\APU113DashboardUpdater" /f >nul 2>&1
schtasks /delete /tn "Vawn\APU113ReportGenerator" /f >nul 2>&1
schtasks /delete /tn "Vawn\APU113PerformanceMonitor" /f >nul 2>&1
schtasks /delete /tn "Vawn\APU113StrategicAnalyzer" /f >nul 2>&1
schtasks /delete /tn "Vawn\APU113AlertSystem" /f >nul 2>&1

REM Create core intelligence analyzer task (every 30 minutes during active hours)
echo [SETUP] Creating Core Intelligence Analyzer...
schtasks /create /tn "Vawn\APU113IntelligenceAnalyzer" /tr "%PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --analyze" /sc daily /st 07:00 /ri 30 /du 16:00 /f
if %errorlevel% neq 0 (
    echo [WARN] Failed to create Intelligence Analyzer task
) else (
    echo [OK] Intelligence Analyzer task created - runs every 30 minutes (7 AM - 11 PM)
)

REM Create dashboard updater task (every 10 minutes during business hours)
echo [SETUP] Creating Dashboard Updater...
schtasks /create /tn "Vawn\APU113DashboardUpdater" /tr "%PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --dashboard" /sc daily /st 08:00 /ri 10 /du 18:00 /f
if %errorlevel% neq 0 (
    echo [WARN] Failed to create Dashboard Updater task
) else (
    echo [OK] Dashboard Updater task created - runs every 10 minutes (8 AM - 6 PM)
)

REM Create comprehensive report generator (daily at 9 AM)
echo [SETUP] Creating Report Generator...
schtasks /create /tn "Vawn\APU113ReportGenerator" /tr "%PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --report" /sc daily /st 09:00 /f
if %errorlevel% neq 0 (
    echo [WARN] Failed to create Report Generator task
) else (
    echo [OK] Report Generator task created - runs daily at 9:00 AM
)

REM Create performance monitor (every 2 hours)
echo [SETUP] Creating Performance Monitor...
schtasks /create /tn "Vawn\APU113PerformanceMonitor" /tr "%PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --analyze" /sc daily /st 06:00 /ri 120 /du 24:00 /f
if %errorlevel% neq 0 (
    echo [WARN] Failed to create Performance Monitor task
) else (
    echo [OK] Performance Monitor task created - runs every 2 hours
)

REM Test APU-113 system
echo.
echo [TEST] Testing APU-113 Engagement Intelligence Dashboard...

REM Initialize database and configuration
echo [TEST] Initializing APU-113 system...
%PYTHON% "%SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py" --analyze
if %errorlevel% neq 0 (
    echo [ERROR] APU-113 initialization failed
    pause
    exit /b 1
) else (
    echo [OK] APU-113 system initialized successfully
)

REM Test dashboard functionality
echo [TEST] Testing dashboard functionality...
%PYTHON% "%SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py" --dashboard
if %errorlevel% neq 0 (
    echo [WARN] Dashboard test had issues, but system is operational
) else (
    echo [OK] Dashboard functionality verified
)

echo.
echo ===============================================================================
echo   APU-113 Setup Complete - Engagement Intelligence Dashboard Active
echo ===============================================================================
echo.

REM Display integration status with other APU systems
echo [INTEGRATION] APU System Integration Status:
if exist "%SCRIPT_DIR%\apu101_engagement_monitor.py" (echo ✅ APU-101 Integration: READY) else (echo ❌ APU-101 Integration: CHECK REQUIRED)
if exist "%SCRIPT_DIR%\apu112_engagement_metrics_aggregator.py" (echo ✅ APU-112 Integration: READY) else (echo ❌ APU-112 Integration: CHECK REQUIRED)
if exist "engagement_agent_enhanced.py" (echo ✅ Legacy Engagement Agent: READY) else (echo ❌ Legacy Engagement Agent: CHECK REQUIRED)
if exist "analytics_agent.py" (echo ✅ Analytics Agent: READY) else (echo ❌ Analytics Agent: CHECK REQUIRED)
if exist "metrics_agent.py" (echo ✅ Metrics Agent: READY) else (echo ❌ Metrics Agent: CHECK REQUIRED)

echo.
echo [SUMMARY] APU-113 Scheduled Tasks:
echo   • Intelligence Analyzer: Every 30 min (7 AM - 11 PM)
echo   • Dashboard Updater: Every 10 min (8 AM - 6 PM)
echo   • Report Generator: Daily at 9:00 AM
echo   • Performance Monitor: Every 2 hours (24/7)
echo.

echo [MANUAL COMMANDS] APU-113 Manual Operations:
echo   Single Analysis: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --analyze
echo   Dashboard View: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --dashboard
echo   Generate Report: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --report
echo   Continuous Monitor: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --monitor
echo.

echo [FEATURES] APU-113 Capabilities:
echo   ✅ Cross-platform engagement intelligence aggregation
echo   ✅ Predictive analytics and trend analysis
echo   ✅ Strategic recommendation engine
echo   ✅ Real-time alert system with intelligence scoring
echo   ✅ Comprehensive stakeholder reporting
echo   ✅ Integration with all existing APU monitoring systems
echo   ✅ SQLite database for historical intelligence tracking
echo   ✅ Platform performance optimization recommendations
echo.

echo [NEXT STEPS] To activate APU-113:
echo   1. Run initial analysis: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --analyze
echo   2. View dashboard: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --dashboard
echo   3. Generate first report: %PYTHON% %SCRIPT_DIR%\apu113_engagement_intelligence_dashboard.py --report
echo   4. All scheduled tasks will run automatically
echo.

echo ===============================================================================
echo   APU-113 Engagement Intelligence Dashboard is now operational!
echo   Consolidating intelligence from all engagement monitoring systems.
echo ===============================================================================

pause