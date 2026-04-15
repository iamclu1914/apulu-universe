"""
integrate_apu112_metrics.py — APU-112 Quick Integration Script

Quick integration script to add real-time engagement metrics to the existing review_ui.py
Flask application. This script provides a simple way to enhance the existing UI with
comprehensive analytics capabilities.

Created by: Backend API Agent (APU-112)
Usage: python integrate_apu112_metrics.py
"""

import sys
from pathlib import Path

def main():
    """Main integration function."""
    print("=" * 80)
    print("[*] APU-112 Real-Time Engagement Metrics Integration")
    print("[*] Quick Setup for Vawn Review UI Enhancement")
    print("=" * 80)

    # Check if review_ui.py exists
    review_ui_path = Path("review_ui.py")
    if not review_ui_path.exists():
        print("❌ review_ui.py not found in current directory")
        print("💡 Please run this script from the Vawn root directory")
        return 1

    print("✅ Found review_ui.py")

    # Check if integration already exists
    review_ui_content = review_ui_path.read_text(encoding="utf-8")
    if "apu112_flask_integration" in review_ui_content:
        print("⚠️ APU-112 integration already exists in review_ui.py")
        print("🚀 You can access the metrics dashboard at:")
        print("   📊 http://localhost:5555/api/v1/metrics/live-dashboard")
        print("   🔗 http://localhost:5555/api/v1/metrics/dashboard")
        return 0

    print("🔧 Setting up APU-112 integration...")

    # Create backup
    backup_path = Path("review_ui_backup.py")
    backup_path.write_text(review_ui_content, encoding="utf-8")
    print(f"📁 Created backup: {backup_path}")

    # Add integration code
    try:
        # Find the Flask app initialization
        lines = review_ui_content.split('\n')

        # Find import section
        import_index = -1
        for i, line in enumerate(lines):
            if "from flask import" in line:
                import_index = i
                break

        if import_index == -1:
            print("❌ Could not find Flask imports in review_ui.py")
            return 1

        # Add APU-112 import
        apu112_import = """
# APU-112 Real-Time Engagement Metrics Integration
try:
    from src.apu112_flask_integration import init_metrics_integration
    APU112_AVAILABLE = True
    print("[APU-112] ✅ Metrics integration module loaded")
except ImportError as e:
    APU112_AVAILABLE = False
    print(f"[APU-112] ⚠️ Metrics integration not available: {e}")"""

        lines.insert(import_index + 1, apu112_import)

        # Find app creation
        app_index = -1
        for i, line in enumerate(lines):
            if "app = Flask(__name__)" in line:
                app_index = i
                break

        if app_index == -1:
            print("❌ Could not find Flask app creation in review_ui.py")
            return 1

        # Add APU-112 initialization
        apu112_init = """
# Initialize APU-112 Real-Time Engagement Metrics
if APU112_AVAILABLE:
    try:
        apu112_aggregator = init_metrics_integration(app)
        print("[APU-112] 🚀 Real-time engagement metrics system active!")
        print("[APU-112] 📊 Dashboard: http://localhost:5555/api/v1/metrics/live-dashboard")
        print("[APU-112] 🔗 API endpoints: http://localhost:5555/api/v1/metrics/dashboard")
        print("[APU-112] ⚡ Real-time data: http://localhost:5555/api/v1/metrics/real-time")
        print("[APU-112] 🚨 Alerts: http://localhost:5555/api/v1/metrics/alerts")
    except Exception as e:
        print(f"[APU-112] ❌ Failed to initialize metrics: {e}")
        APU112_AVAILABLE = False
else:
    print("[APU-112] ❌ Metrics integration disabled (missing dependencies)")"""

        lines.insert(app_index + 1, apu112_init)

        # Add metrics dashboard route to main app
        dashboard_route = """
@app.route("/metrics")
def metrics_dashboard():
    \"\"\"Redirect to APU-112 metrics dashboard.\"\"\"
    if APU112_AVAILABLE:
        return redirect("/api/v1/metrics/live-dashboard")
    else:
        return \"\"\"
        <h1>APU-112 Metrics Dashboard</h1>
        <p>Real-time engagement metrics are not available.</p>
        <p>To enable metrics:</p>
        <ol>
            <li>Install dependencies: <code>pip install flask-socketio numpy</code></li>
            <li>Restart the application</li>
        </ol>
        <a href="/">← Back to Main Dashboard</a>
        \"\"\""""

        # Find a good place to add the route (after other routes)
        route_added = False
        for i, line in enumerate(lines):
            if line.strip().startswith('@app.route("/")'):
                # Insert before the main route
                lines.insert(i, dashboard_route)
                lines.insert(i, "")  # Add blank line
                route_added = True
                break

        if not route_added:
            # Add at the end before main execution
            for i, line in enumerate(lines):
                if line.strip().startswith('if __name__ == "__main__"'):
                    lines.insert(i, dashboard_route)
                    lines.insert(i, "")
                    break

        # Write the modified content
        modified_content = '\n'.join(lines)
        review_ui_path.write_text(modified_content, encoding="utf-8")

        print("✅ Successfully integrated APU-112 metrics into review_ui.py!")

    except Exception as e:
        print(f"❌ Integration failed: {e}")
        # Restore backup
        review_ui_path.write_text(review_ui_content, encoding="utf-8")
        print("🔄 Restored original review_ui.py from backup")
        return 1

    # Installation instructions
    print("\n" + "=" * 50)
    print("[NEXT STEPS]")
    print("=" * 50)

    print("1. 📦 Install required dependencies:")
    print("   pip install flask-socketio numpy")
    print("")

    print("2. 🚀 Start your Flask application as usual:")
    print("   python review_ui.py")
    print("")

    print("3. 📊 Access the enhanced dashboards:")
    print("   • Main Review UI: http://localhost:5555/")
    print("   • Metrics Dashboard: http://localhost:5555/metrics")
    print("   • Live Metrics: http://localhost:5555/api/v1/metrics/live-dashboard")
    print("   • API Data: http://localhost:5555/api/v1/metrics/dashboard")
    print("")

    print("4. 🔍 Available Features:")
    print("   • Real-time engagement metrics collection")
    print("   • Cross-platform data normalization")
    print("   • Trend analysis and insights")
    print("   • Hashtag performance correlation")
    print("   • Growth funnel tracking")
    print("   • Live WebSocket updates")
    print("   • Automated alerts for viral content")
    print("")

    print("5. 🛠️ Configuration:")
    print("   • Edit: config/apu112_metrics_config.json")
    print("   • Customize collection intervals, weights, and thresholds")
    print("")

    print("6. 📈 Integration Benefits:")
    print("   • Unified view of engagement across all platforms")
    print("   • Real-time performance insights")
    print("   • Data-driven content optimization")
    print("   • Historical trend analysis")
    print("   • Predictive viral content detection")

    print("\n🎉 APU-112 integration complete!")
    print("💡 For detailed documentation, see: docs/APU112_ENGAGEMENT_METRICS_SYSTEM.md")

    return 0

if __name__ == "__main__":
    exit(main())