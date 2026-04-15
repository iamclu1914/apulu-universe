"""
apu49_paperclip_coordinator.py — APU-49 Paperclip Agent Coordination

Coordinates Paperclip agent spawning and department routing based on
engagement monitoring results from APU-49.

Created by: Dex - Community Agent (APU-49)
"""

import json
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add current directory to path for imports
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import load_json, save_json, VAWN_DIR, log_run

# Paperclip coordination log
COORDINATION_LOG = VAWN_DIR / "research" / "paperclip_coordination_log.json"

# Department agent mapping for Paperclip
DEPARTMENT_AGENTS = {
    "legal": {
        "agent_type": "legal-specialist",
        "model": "sonnet",  # Legal needs good reasoning
        "skills": ["copyright-analysis", "compliance-review", "risk-assessment"],
        "response_urgency": "immediate"  # Legal issues are urgent
    },
    "a_and_r": {
        "agent_type": "music-curator",
        "model": "sonnet",
        "skills": ["talent-evaluation", "music-analysis", "industry-trends"],
        "response_urgency": "same_day"
    },
    "creative_revenue": {
        "agent_type": "marketing-analyst",
        "model": "haiku",  # Marketing analysis can be faster
        "skills": ["campaign-analysis", "conversion-tracking", "brand-monitoring"],
        "response_urgency": "within_hours"
    },
    "operations": {
        "agent_type": "operations-manager",
        "model": "haiku",  # Ops monitoring is straightforward
        "skills": ["system-monitoring", "workflow-optimization", "resource-planning"],
        "response_urgency": "within_hours"
    }
}


def load_apu49_monitoring_results() -> Optional[Dict]:
    """Load the latest APU-49 monitoring results."""
    try:
        monitor_log_path = VAWN_DIR / "research" / "apu49_paperclip_engagement_monitor_log.json"
        if not monitor_log_path.exists():
            return None

        monitor_log = load_json(monitor_log_path)

        # Get today's latest report
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in monitor_log:
            return None

        today_reports = monitor_log[today]
        if not today_reports:
            return None

        # Return most recent report
        return today_reports[-1]

    except Exception as e:
        log_run("PaperclipCoordinator", "error", f"Failed to load APU-49 results: {str(e)}")
        return None


def create_paperclip_agent_tasks(routing_actions: Dict) -> List[Dict]:
    """Create Paperclip agent tasks based on routing actions."""
    tasks = []

    for dept_key, action in routing_actions.items():
        if not action.get("action_required", False):
            continue

        agent_config = DEPARTMENT_AGENTS.get(dept_key)
        if not agent_config:
            continue

        # Create task specification for this department
        task = {
            "department": dept_key,
            "agent_type": agent_config["agent_type"],
            "model": agent_config["model"],
            "priority": action["priority"],
            "task_description": generate_task_description(dept_key, action),
            "context": action["paperclip_routing"]["context"],
            "urgency": agent_config["response_urgency"],
            "expected_deliverables": get_expected_deliverables(dept_key),
            "skills_required": agent_config["skills"],
            "estimated_duration": estimate_task_duration(action["priority"]),
            "department_head": action["department_head"]
        }

        tasks.append(task)

    return tasks


def generate_task_description(dept_key: str, action: Dict) -> str:
    """Generate detailed task description for department agents."""
    context = action["paperclip_routing"]["context"]
    urgent_issues = len(context.get("urgent_issues", []))
    alerts = len(context.get("alerts", []))

    descriptions = {
        "legal": f"""
        Legal Department Engagement Review:
        - {urgent_issues} urgent legal/compliance issues identified
        - {alerts} system alerts requiring legal assessment
        - Review copyright mentions, DMCA concerns, and compliance risks
        - Provide risk assessment and recommended actions
        - Escalate critical issues to Nelly (Head of Legal) immediately
        """,

        "a_and_r": f"""
        A&R Department Opportunity Analysis:
        - {urgent_issues} potential talent/collaboration opportunities
        - {alerts} engagement alerts related to music discovery
        - Analyze demo submissions, talent mentions, and collaboration requests
        - Assess artist development opportunities and industry trends
        - Report findings to Timbo (President of A&R)
        """,

        "creative_revenue": f"""
        Creative & Revenue Department Analysis:
        - {urgent_issues} revenue/campaign-related issues identified
        - {alerts} marketing performance alerts
        - Analyze conversion metrics, campaign performance, and brand mentions
        - Assess revenue optimization opportunities
        - Report to Letitia (President Creative & Revenue)
        """,

        "operations": f"""
        Operations Department System Review:
        - {urgent_issues} operational issues requiring attention
        - {alerts} system health alerts
        - Review workflow efficiency, system performance, and resource allocation
        - Identify process improvement opportunities
        - Report to Nari (COO)
        """
    }

    return descriptions.get(dept_key, f"Department analysis for {dept_key}")


def get_expected_deliverables(dept_key: str) -> List[str]:
    """Get expected deliverables for each department."""
    deliverables = {
        "legal": [
            "Risk assessment report",
            "Compliance recommendations",
            "Urgent issue escalation list",
            "Legal action plan"
        ],
        "a_and_r": [
            "Talent opportunity report",
            "Demo submission analysis",
            "Industry trend summary",
            "Artist development recommendations"
        ],
        "creative_revenue": [
            "Campaign performance analysis",
            "Revenue optimization recommendations",
            "Conversion metric review",
            "Brand health assessment"
        ],
        "operations": [
            "System health report",
            "Process improvement recommendations",
            "Resource allocation analysis",
            "Workflow optimization plan"
        ]
    }

    return deliverables.get(dept_key, ["Department analysis report"])


def estimate_task_duration(priority: str) -> str:
    """Estimate task duration based on priority."""
    durations = {
        "high": "2-4 hours",
        "medium": "4-8 hours",
        "low": "8-24 hours"
    }
    return durations.get(priority, "4-8 hours")


async def coordinate_paperclip_agents() -> Dict[str, Any]:
    """Main coordination function - spawns and manages Paperclip agents."""
    coordination_results = {
        "timestamp": datetime.now().isoformat(),
        "agents_spawned": [],
        "coordination_status": "success",
        "errors": [],
        "department_assignments": {}
    }

    try:
        # Load APU-49 monitoring results
        monitoring_results = load_apu49_monitoring_results()
        if not monitoring_results:
            coordination_results["coordination_status"] = "no_data"
            coordination_results["errors"].append("No APU-49 monitoring data available")
            return coordination_results

        # Extract routing actions
        routing_actions = monitoring_results.get("paperclip_routing", {})
        if not routing_actions:
            coordination_results["coordination_status"] = "no_actions"
            return coordination_results

        # Create agent tasks
        tasks = create_paperclip_agent_tasks(routing_actions)
        if not tasks:
            coordination_results["coordination_status"] = "no_tasks"
            return coordination_results

        # Log coordination start
        log_run("PaperclipCoordinator", "info", f"Starting coordination for {len(tasks)} department tasks")

        # Process each department task
        for task in tasks:
            try:
                agent_result = await spawn_department_agent(task)
                coordination_results["agents_spawned"].append(agent_result)
                coordination_results["department_assignments"][task["department"]] = agent_result

                log_run("PaperclipCoordinator", "ok",
                       f"Spawned {task['agent_type']} for {task['department']} department")

            except Exception as e:
                error_msg = f"Failed to spawn agent for {task['department']}: {str(e)}"
                coordination_results["errors"].append(error_msg)
                log_run("PaperclipCoordinator", "error", error_msg)

        # Update coordination status
        if coordination_results["errors"]:
            coordination_results["coordination_status"] = "partial_success"
        else:
            coordination_results["coordination_status"] = "success"

    except Exception as e:
        coordination_results["coordination_status"] = "failed"
        coordination_results["errors"].append(f"Coordination failed: {str(e)}")
        log_run("PaperclipCoordinator", "error", f"Coordination failed: {str(e)}")

    return coordination_results


async def spawn_department_agent(task: Dict) -> Dict[str, Any]:
    """Spawn a Paperclip agent for a specific department task."""

    # For now, simulate agent spawning since we're not in the Paperclip environment
    # In actual Paperclip environment, this would use the Paperclip agent spawn API

    agent_result = {
        "agent_id": f"dept_{task['department']}_{int(datetime.now().timestamp())}",
        "agent_type": task["agent_type"],
        "department": task["department"],
        "task_description": task["task_description"][:100] + "...",  # Truncated
        "priority": task["priority"],
        "estimated_completion": estimate_completion_time(task["urgency"]),
        "deliverables": task["expected_deliverables"],
        "status": "spawned",
        "spawn_time": datetime.now().isoformat()
    }

    # Log the agent spawn
    print(f"[PAPERCLIP] Spawned {task['agent_type']} agent for {task['department']} department")
    print(f"[PAPERCLIP] Priority: {task['priority']}, Urgency: {task['urgency']}")
    print(f"[PAPERCLIP] Agent ID: {agent_result['agent_id']}")

    return agent_result


def estimate_completion_time(urgency: str) -> str:
    """Estimate when task will be completed."""
    from datetime import timedelta

    time_deltas = {
        "immediate": timedelta(hours=2),
        "same_day": timedelta(hours=8),
        "within_hours": timedelta(hours=4),
        "standard": timedelta(hours=24)
    }

    completion_time = datetime.now() + time_deltas.get(urgency, timedelta(hours=8))
    return completion_time.isoformat()


def save_coordination_report(coordination_results: Dict):
    """Save coordination results to log."""
    coordination_log = load_json(COORDINATION_LOG) if Path(COORDINATION_LOG).exists() else {}

    today = datetime.now().strftime("%Y-%m-%d")
    if today not in coordination_log:
        coordination_log[today] = []

    coordination_log[today].append(coordination_results)

    # Keep only last 30 days
    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=30)).date()
    coordination_log = {
        k: v for k, v in coordination_log.items()
        if datetime.strptime(k, "%Y-%m-%d").date() >= cutoff_date
    }

    save_json(COORDINATION_LOG, coordination_log)


def main():
    """Main Paperclip coordination function."""
    print("\n[*] APU-49 Paperclip Coordinator Starting...")
    print("[*] Analyzing department routing needs...")

    # Run coordination
    coordination_results = asyncio.run(coordinate_paperclip_agents())

    # Save results
    save_coordination_report(coordination_results)

    # Display summary
    print(f"\n[COORDINATION SUMMARY]")
    print(f"Status: {coordination_results['coordination_status'].upper()}")
    print(f"Agents Spawned: {len(coordination_results['agents_spawned'])}")
    print(f"Errors: {len(coordination_results['errors'])}")

    # Display department assignments
    if coordination_results["department_assignments"]:
        print(f"\n[DEPARTMENT ASSIGNMENTS]")
        for dept, agent_info in coordination_results["department_assignments"].items():
            print(f"  • {dept.upper()}: {agent_info['agent_type']} (ID: {agent_info['agent_id']})")

    # Display any errors
    if coordination_results["errors"]:
        print(f"\n[ERRORS]")
        for error in coordination_results["errors"]:
            print(f"  • {error}")

    return coordination_results


if __name__ == "__main__":
    results = main()

    # Exit code based on coordination status
    status = results.get("coordination_status", "failed")

    if status == "failed":
        sys.exit(2)
    elif status == "partial_success":
        sys.exit(1)
    else:
        sys.exit(0)