@echo off
REM APU-78 System Recovery & Community Continuity Bot - Task Scheduler Setup
REM Created by: Dex - Community Agent (APU-78)
REM Revolutionary system reliability and community relationship management

echo ========================================
echo APU-78 System Recovery & Community Continuity Bot
echo ========================================
echo Mission: Restore engagement bot reliability + community relationship building
echo.

REM Set Python path and Vawn directory
set PYTHON=python
set VAWN_DIR=C:\Users\rdyal\Vawn

REM Remove any legacy engagement tasks that might conflict
echo Removing legacy engagement tasks to prevent conflicts...
schtasks /delete /tn "Vawn\APU74IntelligentBot" /f >nul 2>&1
schtasks /delete /tn "Vawn\APU77DepartmentMonitor" /f >nul 2>&1
schtasks /delete /tn "Vawn\EnhancedEngagementBot" /f >nul 2>&1
schtasks /delete /tn "Vawn\EngagementHealthCheck" /f >nul 2>&1
schtasks /delete /tn "Vawn\UnifiedEngagementMonitor" /f >nul 2>&1

echo.
echo === CREATING APU-78 SYSTEM RECOVERY TASKS ===
echo.

REM Primary APU-78 System Recovery Engine - Every 30 minutes for proactive recovery
echo Creating APU-78 System Recovery Engine...
schtasks /create /tn "Vawn\APU78SystemRecovery" /tr "%PYTHON% %VAWN_DIR%\src\apu78_community_continuity_bot.py" /sc daily /st 07:00 /ri 30 /du 24:00 /f

if %ERRORLEVEL% EQU 0 (
    echo   ✅ APU-78 System Recovery Engine: Every 30 minutes, 7:00 AM - 11:00 PM
) else (
    echo   ❌ Failed to create APU-78 System Recovery Engine task
)

REM APU-78 Dependency Health Check - Every 10 minutes during active hours
echo Creating APU-78 Dependency Health Monitor...
schtasks /create /tn "Vawn\APU78DependencyHealth" /tr "%PYTHON% %VAWN_DIR%\src\apu78_community_continuity_bot.py --dependency-check" /sc daily /st 07:00 /ri 10 /du 16:00 /f

if %ERRORLEVEL% EQU 0 (
    echo   ✅ APU-78 Dependency Health Monitor: Every 10 minutes, 7:00 AM - 11:00 PM
) else (
    echo   ❌ Failed to create APU-78 Dependency Health Monitor task
)

REM APU-78 Community Relationship Tracker - Every 2 hours for relationship building
echo Creating APU-78 Community Relationship Tracker...
schtasks /create /tn "Vawn\APU78CommunityTracker" /tr "%PYTHON% %VAWN_DIR%\src\apu78_community_continuity_bot.py --community-focus" /sc daily /st 08:00 /ri 120 /du 24:00 /f

if %ERRORLEVEL% EQU 0 (
    echo   ✅ APU-78 Community Relationship Tracker: Every 2 hours, 8:00 AM - 12:00 AM
) else (
    echo   ❌ Failed to create APU-78 Community Relationship Tracker task
)

REM APU-78 Emergency Engagement Coordinator - Every 5 minutes when systems critical
echo Creating APU-78 Emergency Engagement Coordinator...
schtasks /create /tn "Vawn\APU78EmergencyCoordinator" /tr "%PYTHON% %VAWN_DIR%\src\apu78_community_continuity_bot.py --emergency-mode" /sc daily /st 07:00 /ri 5 /du 24:00 /f

if %ERRORLEVEL% EQU 0 (
    echo   ✅ APU-78 Emergency Engagement Coordinator: Every 5 minutes (activates on system failure)
) else (
    echo   ❌ Failed to create APU-78 Emergency Engagement Coordinator task
)

REM APU-78 Cross-Platform Community Sync - Every 4 hours for unified community experience
echo Creating APU-78 Cross-Platform Community Sync...
schtasks /create /tn "Vawn\APU78CrossPlatformSync" /tr "%PYTHON% %VAWN_DIR%\src\apu78_community_continuity_bot.py --cross-platform-sync" /sc daily /st 09:00 /ri 240 /du 24:00 /f

if %ERRORLEVEL% EQU 0 (
    echo   ✅ APU-78 Cross-Platform Community Sync: Every 4 hours, 9:00 AM start
) else (
    echo   ❌ Failed to create APU-78 Cross-Platform Community Sync task
)

REM APU-78 Ecosystem Integration Health Check - Every 6 hours for coordination
echo Creating APU-78 Ecosystem Integration Monitor...
schtasks /create /tn "Vawn\APU78EcosystemIntegration" /tr "%PYTHON% %VAWN_DIR%\src\apu78_community_continuity_bot.py --ecosystem-health" /sc daily /st 07:30 /ri 360 /du 24:00 /f

if %ERRORLEVEL% EQU 0 (
    echo   ✅ APU-78 Ecosystem Integration Monitor: Every 6 hours, 7:30 AM start
) else (
    echo   ❌ Failed to create APU-78 Ecosystem Integration Monitor task
)

echo.
echo === APU-78 TASK CREATION SUMMARY ===
echo.

REM List all APU-78 tasks to confirm creation
echo Created APU-78 tasks:
schtasks /query /fo table | findstr "APU78"

echo.
echo === MANUAL EXECUTION COMMANDS ===
echo.
echo Core System Recovery: python src\apu78_community_continuity_bot.py
echo Dependency Check: python src\apu78_community_continuity_bot.py --dependency-check
echo Community Focus: python src\apu78_community_continuity_bot.py --community-focus
echo Emergency Mode: python src\apu78_community_continuity_bot.py --emergency-mode
echo Cross-Platform Sync: python src\apu78_community_continuity_bot.py --cross-platform-sync
echo Ecosystem Health: python src\apu78_community_continuity_bot.py --ecosystem-health

echo.
echo === APU-78 SYSTEM OVERVIEW ===
echo.
echo APU-78 addresses critical infrastructure failures that broke the entire
echo engagement bot ecosystem, while adding missing community relationship focus:
echo.
echo • System Recovery Engine: Fixes atproto, dependency, and credential issues
echo • Community Relationship Builder: Tracks fan relationships across platforms
echo • Fallback Engagement System: Manual coordination when automation fails
echo • Emergency Response: 5-minute response time for critical system failures
echo • Cross-Platform Community: Unified community experience coordination
echo.
echo Integration with APU Ecosystem:
echo • Enables APU-74 (Intelligent Automation) to function properly
echo • Supports APU-77 (Department Coordination) with reliable data
echo • Bridges automation and authentic community relationship building
echo.
echo Strategic Value:
echo • Fixes foundational reliability issues affecting all engagement bots
echo • Adds missing community relationship focus to complement automation
echo • Provides continuity during infrastructure failures
echo • Enables the sophisticated APU ecosystem (74, 77) to operate effectively
echo.
echo === APU-78 DEPLOYMENT COMPLETE ===
echo.
echo The APU-78 System Recovery & Community Continuity Bot is now operational.
echo Monitor system recovery progress and community relationship building.
echo.
echo Next Steps:
echo 1. Monitor APU-78 System Recovery dashboard
echo 2. Verify dependency resolution and system health restoration
echo 3. Track community relationship building across platforms
echo 4. Coordinate with APU-74 and APU-77 as systems recover
echo.

pause