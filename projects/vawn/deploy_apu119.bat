@echo off
REM APU-119 Real-Time Community Response Optimization System Deployment
REM Quick deployment script for Windows
REM Created by: Dex - Community Agent (APU-119)

echo.
echo ===============================================================================
echo   APU-119 Real-Time Community Response Optimization System
echo   Deployment and Validation Script
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
set SCRIPT_DIR=%VAWN_DIR%

echo [INFO] VAWN Directory: %VAWN_DIR%
echo [INFO] Python: %PYTHON%

REM Verify deployment script exists
if not exist "%SCRIPT_DIR%deploy_apu119.py" (
    echo [ERROR] Deployment script not found: %SCRIPT_DIR%deploy_apu119.py
    pause
    exit /b 1
)

echo [INFO] Starting APU-119 deployment...
echo.

REM Run the deployment script
%PYTHON% "%SCRIPT_DIR%deploy_apu119.py"

set DEPLOY_EXIT_CODE=%errorlevel%

echo.
if %DEPLOY_EXIT_CODE% equ 0 (
    echo ✅ APU-119 deployment completed successfully!
    echo.
    echo 🎯 Quick Test:
    echo    To test the system, run: python src\apu119_engagement_monitor.py
    echo.
    echo 📊 Integration Test:
    echo    To test integration, run: python src\apu119_system_integration.py
    echo.
    echo 🔍 Monitoring Test:
    echo    To test monitoring, run: python src\apu119_monitoring_alerts.py
) else (
    echo ❌ APU-119 deployment failed. Check the logs for details.
    echo.
    echo 📋 Troubleshooting:
    echo    1. Check Python version: python --version
    echo    2. Review deployment log: research\apu119_deployment_log.json
    echo    3. Check validation results: research\apu119_validation_results.json
)

echo.
echo Press any key to exit...
pause >nul
exit /b %DEPLOY_EXIT_CODE%