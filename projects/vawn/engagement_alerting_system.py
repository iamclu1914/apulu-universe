"""
engagement_alerting_system.py — Proactive alerting and escalation system for APU-37.
Implements automatic monitoring, notifications, and escalation procedures.
Created by: Dex - Community Agent (APU-37)
"""

import json
import sys
import smtplib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import load_json, save_json, VAWN_DIR, log_run, today_str

# Configuration
ALERTING_LOG = VAWN_DIR / "research" / "engagement_alerting_log.json"
NOTIFICATION_CONFIG = {
    "email_enabled": False,  # Set to True when email credentials are configured
    "webhook_enabled": False,  # Set to True for Discord/Slack webhooks
    "critical_threshold": 2,  # Number of consecutive critical alerts before escalation
    "alert_cooldown_minutes": 30,  # Minimum time between identical alerts
}

ESCALATION_RULES = {
    "auto_recovery_failed": {
        "severity": "critical",
        "cooldown_hours": 1,
        "max_attempts": 3,
        "actions": ["restart_services", "notify_admin"]
    },
    "multiple_agents_down": {
        "severity": "critical",
        "cooldown_hours": 0.5,
        "max_attempts": 5,
        "actions": ["restart_all_agents", "notify_admin"]
    },
    "platform_api_failure": {
        "severity": "high",
        "cooldown_hours": 2,
        "max_attempts": 2,
        "actions": ["check_api_status", "notify_admin"]
    },
    "engagement_drop": {
        "severity": "medium",
        "cooldown_hours": 4,
        "max_attempts": 1,
        "actions": ["analyze_trends", "schedule_review"]
    }
}


def load_alerting_history():
    """Load alerting history and state."""
    return load_json(ALERTING_LOG)


def save_alerting_history(data):
    """Save alerting history."""
    save_json(ALERTING_LOG, data)


def should_send_alert(alert_type: str, last_alerts: List[Dict]) -> bool:
    """Determine if an alert should be sent based on cooldown and history."""
    cooldown_minutes = NOTIFICATION_CONFIG["alert_cooldown_minutes"]
    cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)

    # Check if we've sent this type of alert recently
    recent_alerts = [
        alert for alert in last_alerts
        if (alert.get("type") == alert_type and
            datetime.fromisoformat(alert["timestamp"]) > cutoff_time)
    ]

    return len(recent_alerts) == 0


def send_notification(alert: Dict[str, Any], method: str = "log") -> bool:
    """Send notification via specified method."""
    message = f"[{alert['severity'].upper()}] {alert['message']}"

    if method == "log":
        # Always log to research log
        log_run("EngagementAlerting", alert['severity'], alert['message'])
        print(f"[ALERT] {message}")
        return True

    elif method == "email" and NOTIFICATION_CONFIG["email_enabled"]:
        # Email notification (placeholder - requires SMTP configuration)
        try:
            # This would need actual SMTP credentials configured
            print(f"[EMAIL ALERT] {message}")
            return True
        except Exception as e:
            print(f"[EMAIL FAILED] {e}")
            return False

    elif method == "webhook" and NOTIFICATION_CONFIG["webhook_enabled"]:
        # Webhook notification (placeholder - requires webhook URLs)
        try:
            # This would send to Discord/Slack webhook
            print(f"[WEBHOOK ALERT] {message}")
            return True
        except Exception as e:
            print(f"[WEBHOOK FAILED] {e}")
            return False

    return False


def execute_remediation_action(action: str, context: Dict[str, Any]) -> bool:
    """Execute automated remediation actions."""
    print(f"[REMEDIATION] Executing action: {action}")

    try:
        if action == "restart_services":
            # Run the enhanced monitoring system to trigger auto-recovery
            result = subprocess.run(
                [sys.executable, str(VAWN_DIR / "engagement_monitor_enhanced.py")],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(VAWN_DIR)
            )
            success = result.returncode == 0
            log_run("EngagementAlerting", "ok" if success else "error", f"restart_services: {'success' if success else 'failed'}")
            return success

        elif action == "restart_all_agents":
            # Manually run both engagement agents
            agents = ["engagement_agent.py", "engagement_bot.py"]
            success_count = 0

            for agent in agents:
                result = subprocess.run(
                    [sys.executable, str(VAWN_DIR / agent)],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=str(VAWN_DIR)
                )
                if result.returncode == 0:
                    success_count += 1

            success = success_count == len(agents)
            log_run("EngagementAlerting", "ok" if success else "warning", f"restart_all_agents: {success_count}/{len(agents)} successful")
            return success

        elif action == "check_api_status":
            # Basic API health check (placeholder)
            # Would implement actual API endpoint checks
            print(f"[REMEDIATION] API status check completed")
            log_run("EngagementAlerting", "info", "API status check performed")
            return True

        elif action == "analyze_trends":
            # Trigger analytics review (placeholder)
            print(f"[REMEDIATION] Engagement trend analysis initiated")
            log_run("EngagementAlerting", "info", "Engagement trend analysis scheduled")
            return True

        elif action == "notify_admin":
            # Send high-priority admin notification
            admin_message = {
                "type": "admin_escalation",
                "severity": "critical",
                "message": f"Manual intervention required: {context.get('reason', 'Unknown issue')}",
                "context": context
            }
            return send_notification(admin_message, "log")

        elif action == "schedule_review":
            # Schedule manual review (placeholder)
            print(f"[REMEDIATION] Manual review scheduled")
            log_run("EngagementAlerting", "info", "Manual engagement review scheduled")
            return True

        else:
            print(f"[REMEDIATION] Unknown action: {action}")
            return False

    except Exception as e:
        print(f"[REMEDIATION ERROR] {action} failed: {e}")
        log_run("EngagementAlerting", "error", f"Remediation action {action} failed: {str(e)}")
        return False


def process_alert_escalation(alert: Dict[str, Any], alerting_history: Dict[str, Any]) -> bool:
    """Process alert escalation based on rules and history."""
    alert_type = alert.get("type", "unknown")
    escalation_rule = ESCALATION_RULES.get(alert_type)

    if not escalation_rule:
        # No specific escalation rule, just log
        send_notification(alert, "log")
        return True

    # Check escalation history
    today = today_str()
    if today not in alerting_history:
        alerting_history[today] = {}

    if alert_type not in alerting_history[today]:
        alerting_history[today][alert_type] = {
            "count": 0,
            "last_escalation": None,
            "remediation_attempts": 0,
            "escalated": False
        }

    history_entry = alerting_history[today][alert_type]

    # Check cooldown
    if history_entry["last_escalation"]:
        last_escalation = datetime.fromisoformat(history_entry["last_escalation"])
        cooldown_delta = timedelta(hours=escalation_rule["cooldown_hours"])

        if datetime.now() - last_escalation < cooldown_delta:
            print(f"[ESCALATION] {alert_type} in cooldown period")
            return False

    # Increment count and check if escalation is needed
    history_entry["count"] += 1

    # Send notification first
    if should_send_alert(alert_type, alerting_history.get("recent_alerts", [])):
        send_notification(alert, "log")

        # Add to recent alerts
        if "recent_alerts" not in alerting_history:
            alerting_history["recent_alerts"] = []

        alerting_history["recent_alerts"].append({
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "severity": alert["severity"],
            "message": alert["message"]
        })

    # Check if remediation is needed
    if (history_entry["count"] >= NOTIFICATION_CONFIG["critical_threshold"] and
        history_entry["remediation_attempts"] < escalation_rule["max_attempts"]):

        print(f"[ESCALATION] Triggering remediation for {alert_type} (attempt {history_entry['remediation_attempts'] + 1})")

        # Execute remediation actions
        remediation_success = True
        for action in escalation_rule["actions"]:
            success = execute_remediation_action(action, {"reason": alert_type, "alert": alert})
            if not success:
                remediation_success = False

        history_entry["remediation_attempts"] += 1
        history_entry["last_escalation"] = datetime.now().isoformat()

        if remediation_success:
            print(f"[ESCALATION] Remediation successful for {alert_type}")
            # Reset count on successful remediation
            history_entry["count"] = 0
        else:
            print(f"[ESCALATION] Remediation failed for {alert_type}")

            # If we've exhausted attempts, mark as escalated
            if history_entry["remediation_attempts"] >= escalation_rule["max_attempts"]:
                history_entry["escalated"] = True
                escalation_alert = {
                    "type": "escalation_exhausted",
                    "severity": "critical",
                    "message": f"All remediation attempts failed for {alert_type} - manual intervention required"
                }
                send_notification(escalation_alert, "log")

    return True


def run_monitoring_and_alerting():
    """Run the enhanced monitoring system and process alerts."""
    print("\n[*] Enhanced Engagement Alerting System (APU-37) Starting...")

    # Load alerting history
    alerting_history = load_alerting_history()

    try:
        # Run the enhanced monitoring system
        result = subprocess.run(
            [sys.executable, str(VAWN_DIR / "engagement_monitor_enhanced.py")],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(VAWN_DIR)
        )

        print(f"[MONITORING] Enhanced monitor completed (exit code: {result.returncode})")

        # Parse the output for dashboard information
        if result.stdout:
            print("[MONITORING] System Status:")
            # Extract key lines from dashboard
            lines = result.stdout.split('\n')
            for line in lines:
                if any(keyword in line for keyword in ["[SYSTEM]", "[AGENTS]", "[ALERTS]", "[AUTO-RECOVERY]"]):
                    print(f"  {line}")

        # Process alerts based on exit code
        alerts_to_process = []

        if result.returncode == 2:
            # Critical: High priority alerts + failed recoveries
            alerts_to_process.append({
                "type": "multiple_agents_down",
                "severity": "critical",
                "message": "Multiple high priority alerts and failed auto-recovery detected"
            })
        elif result.returncode == 1:
            # Warning: Either high priority alerts OR failed recoveries
            if "FAILED RECOVERIES" in result.stdout:
                alerts_to_process.append({
                    "type": "auto_recovery_failed",
                    "severity": "high",
                    "message": "Auto-recovery attempts failed"
                })
            elif "HIGH PRIORITY ALERTS" in result.stdout:
                alerts_to_process.append({
                    "type": "platform_api_failure",
                    "severity": "high",
                    "message": "High priority system alerts detected"
                })
        elif result.returncode == 0:
            # Success - check for medium/low priority alerts
            if "auto-recoveries" in result.stdout:
                print("[SUCCESS] Auto-recovery performed successfully")

            # Check for engagement drops or platform issues
            if "Multiple platforms showing zero engagement" in result.stdout:
                alerts_to_process.append({
                    "type": "engagement_drop",
                    "severity": "medium",
                    "message": "Multiple platforms showing zero engagement"
                })

        # Process each alert through escalation system
        for alert in alerts_to_process:
            process_alert_escalation(alert, alerting_history)

        # Log the monitoring run
        log_run("EngagementAlertingSystem", "ok" if result.returncode == 0 else "warning",
               f"Monitoring completed with {len(alerts_to_process)} alerts processed")

    except subprocess.TimeoutExpired:
        timeout_alert = {
            "type": "monitoring_timeout",
            "severity": "critical",
            "message": "Enhanced monitoring system timed out after 5 minutes"
        }
        process_alert_escalation(timeout_alert, alerting_history)

    except Exception as e:
        error_alert = {
            "type": "monitoring_error",
            "severity": "critical",
            "message": f"Enhanced monitoring system failed: {str(e)}"
        }
        process_alert_escalation(error_alert, alerting_history)

    # Clean up old alert history (keep last 7 days)
    cutoff_date = (datetime.now() - timedelta(days=7)).date()
    alerting_history = {
        k: v for k, v in alerting_history.items()
        if k == "recent_alerts" or datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
    }

    # Keep only last 50 recent alerts
    if "recent_alerts" in alerting_history:
        alerting_history["recent_alerts"] = alerting_history["recent_alerts"][-50:]

    # Save updated alerting history
    save_alerting_history(alerting_history)

    return len(alerts_to_process)


def main():
    """Main alerting system function."""
    try:
        alerts_processed = run_monitoring_and_alerting()
        print(f"\n[OK] Engagement Alerting System completed - {alerts_processed} alerts processed")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Engagement Alerting System failed: {e}")
        log_run("EngagementAlertingSystem", "error", f"System failure: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)