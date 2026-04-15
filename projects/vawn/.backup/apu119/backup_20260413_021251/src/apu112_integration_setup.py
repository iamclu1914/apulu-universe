"""
apu112_integration_setup.py — APU-112 Integration Setup Script

Script to integrate APU-112 engagement metrics aggregation system with existing Flask applications.
Provides easy setup for adding real-time metrics to review_ui.py or other Flask apps.

Created by: Backend API Agent (APU-112)
Usage:
    python apu112_integration_setup.py --target review_ui.py
    python apu112_integration_setup.py --standalone --port 5556
"""

import argparse
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from apu112_engagement_metrics_aggregator import APU112EngagementAggregator
from apu112_flask_integration import init_metrics_integration, metrics_bp

def integrate_with_existing_app(target_file: str, config_path: str = None):
    """Integrate APU-112 metrics with existing Flask application."""

    print(f"\n[APU-112] Integrating with existing Flask app: {target_file}")

    # Import the target Flask app
    target_path = Path(target_file)
    if not target_path.exists():
        print(f"[ERROR] Target file not found: {target_file}")
        return False

    # Read the existing Flask app file
    app_content = target_path.read_text(encoding="utf-8")

    # Check if already integrated
    if "apu112_flask_integration" in app_content:
        print(f"[WARNING] APU-112 integration already exists in {target_file}")
        return True

    # Create backup
    backup_path = target_path.with_suffix(f"{target_path.suffix}.apu112_backup")
    backup_path.write_text(app_content, encoding="utf-8")
    print(f"[BACKUP] Created backup: {backup_path}")

    # Add integration imports
    import_insertion_point = app_content.find("from flask import")
    if import_insertion_point == -1:
        print(f"[ERROR] Could not find Flask import in {target_file}")
        return False

    integration_imports = """
# APU-112 Real-Time Engagement Metrics Integration
try:
    from src.apu112_flask_integration import init_metrics_integration
    APU112_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] APU-112 metrics integration not available: {e}")
    APU112_INTEGRATION_AVAILABLE = False
"""

    # Find app creation point
    app_creation_point = app_content.find("app = Flask(__name__)")
    if app_creation_point == -1:
        print(f"[ERROR] Could not find Flask app creation in {target_file}")
        return False

    # Find the end of app creation section to add integration
    lines = app_content.split('\n')
    app_line_idx = -1
    for i, line in enumerate(lines):
        if "app = Flask(__name__)" in line:
            app_line_idx = i
            break

    if app_line_idx == -1:
        print(f"[ERROR] Could not locate app creation line")
        return False

    # Insert integration code after app creation
    integration_code = """
# Initialize APU-112 engagement metrics integration
if APU112_INTEGRATION_AVAILABLE:
    try:
        apu112_aggregator = init_metrics_integration(app)
        print("[APU-112] ✅ Real-time engagement metrics integration initialized")
        print("[APU-112] 📊 Dashboard: http://localhost:5555/api/v1/metrics/live-dashboard")
        print("[APU-112] 🔗 API docs: http://localhost:5555/api/v1/metrics/dashboard")
    except Exception as e:
        print(f"[APU-112] ⚠️ Integration failed: {e}")
        APU112_INTEGRATION_AVAILABLE = False
else:
    print("[APU-112] ❌ Integration not available - install requirements")
"""

    # Insert the integration code
    lines.insert(app_line_idx + 1, integration_code)

    # Add import at the top (after existing Flask imports)
    flask_import_idx = -1
    for i, line in enumerate(lines):
        if "from flask import" in line:
            flask_import_idx = i
            break

    if flask_import_idx != -1:
        lines.insert(flask_import_idx + 1, integration_imports)

    # Write the modified content back
    modified_content = '\n'.join(lines)
    target_path.write_text(modified_content, encoding="utf-8")

    print(f"[SUCCESS] ✅ APU-112 integration added to {target_file}")
    print(f"[NEXT STEPS]")
    print(f"  1. Install required dependencies: pip install flask-socketio numpy")
    print(f"  2. Run your Flask app as usual")
    print(f"  3. Access metrics dashboard at: /api/v1/metrics/live-dashboard")
    print(f"  4. Use API endpoints at: /api/v1/metrics/*")

    return True

def run_standalone_server(port: int, config_path: str = None):
    """Run standalone APU-112 metrics server."""

    print(f"\n[APU-112] Starting standalone engagement metrics server on port {port}")

    from flask import Flask
    from flask_socketio import SocketIO

    # Create Flask app
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'apu112-metrics-secret'

    # Initialize APU-112 integration
    try:
        aggregator = init_metrics_integration(app, config_path)
        print(f"[APU-112] ✅ Metrics aggregation system initialized")

        # Add basic routes
        @app.route('/')
        def index():
            return f"""
            <h1>APU-112 Engagement Metrics Server</h1>
            <p>Real-time engagement metrics aggregation system is running.</p>
            <ul>
                <li><a href="/api/v1/metrics/live-dashboard">📊 Live Dashboard</a></li>
                <li><a href="/api/v1/metrics/dashboard">📈 Metrics API</a></li>
                <li><a href="/api/v1/metrics/real-time">⚡ Real-time Data</a></li>
                <li><a href="/api/v1/metrics/alerts">🚨 Current Alerts</a></li>
            </ul>
            """

        @app.route('/health')
        def health_check():
            return {"status": "healthy", "service": "apu112-metrics", "port": port}

        # Start background metrics collection
        print(f"[APU-112] 🔄 Starting background metrics collection...")

        # Run the Flask app with SocketIO
        from flask_socketio import SocketIO
        socketio = SocketIO(app, cors_allowed_origins="*")

        print(f"[APU-112] 🚀 Server starting...")
        print(f"[APU-112] 📊 Dashboard: http://localhost:{port}/api/v1/metrics/live-dashboard")
        print(f"[APU-112] 🔗 API: http://localhost:{port}/api/v1/metrics/dashboard")
        print(f"[APU-112] ❤️ Health: http://localhost:{port}/health")

        socketio.run(app, host='0.0.0.0', port=port, debug=False)

    except Exception as e:
        print(f"[ERROR] Failed to start standalone server: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    required_packages = ['flask', 'numpy', 'sqlite3']
    missing = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"[WARNING] Missing required packages: {', '.join(missing)}")
        print(f"[INSTALL] Run: pip install {' '.join(missing)}")
        return False

    # Check optional dependencies
    optional_packages = ['flask_socketio']
    missing_optional = []

    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)

    if missing_optional:
        print(f"[INFO] Optional packages for real-time features: {', '.join(missing_optional)}")
        print(f"[INSTALL] Run: pip install {' '.join(missing_optional)}")

    return True

def validate_config(config_path: str = None):
    """Validate APU-112 configuration."""
    if config_path and not Path(config_path).exists():
        print(f"[ERROR] Configuration file not found: {config_path}")
        return False

    try:
        # Test aggregator initialization
        aggregator = APU112EngagementAggregator(config_path)
        print(f"[VALIDATION] ✅ Configuration is valid")
        print(f"[VALIDATION] 📊 Platforms: {', '.join(aggregator.config['collection']['platforms'])}")
        print(f"[VALIDATION] ⏱️ Collection interval: {aggregator.config['collection']['real_time_interval_seconds']}s")
        return True

    except Exception as e:
        print(f"[VALIDATION] ❌ Configuration error: {e}")
        return False

def main():
    """Main function for APU-112 integration setup."""

    parser = argparse.ArgumentParser(description="APU-112 Engagement Metrics Integration Setup")
    parser.add_argument("--target", help="Target Flask app file to integrate with (e.g., review_ui.py)")
    parser.add_argument("--standalone", action="store_true", help="Run standalone metrics server")
    parser.add_argument("--port", type=int, default=5556, help="Port for standalone server")
    parser.add_argument("--config", help="Path to custom configuration file")
    parser.add_argument("--validate-only", action="store_true", help="Only validate configuration")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies")

    args = parser.parse_args()

    print("=" * 80)
    print("[*] APU-112 Real-Time Engagement Metrics Aggregation System")
    print("[*] Integration Setup and Configuration Tool")
    print("=" * 80)

    # Check dependencies
    if args.check_deps or not check_dependencies():
        if args.check_deps:
            return 0
        print("[ERROR] Required dependencies not available")
        return 1

    # Validate configuration
    if not validate_config(args.config):
        print("[ERROR] Configuration validation failed")
        return 1

    if args.validate_only:
        print("[SUCCESS] Configuration validation passed")
        return 0

    # Integration modes
    if args.target:
        # Integrate with existing Flask app
        success = integrate_with_existing_app(args.target, args.config)
        return 0 if success else 1

    elif args.standalone:
        # Run standalone server
        try:
            run_standalone_server(args.port, args.config)
            return 0
        except KeyboardInterrupt:
            print(f"\n[APU-112] Server stopped by user")
            return 0
        except Exception as e:
            print(f"[ERROR] Server failed: {e}")
            return 1

    else:
        # Show usage
        parser.print_help()
        print(f"\nExamples:")
        print(f"  # Integrate with existing Flask app")
        print(f"  python {Path(__file__).name} --target review_ui.py")
        print(f"")
        print(f"  # Run standalone metrics server")
        print(f"  python {Path(__file__).name} --standalone --port 5556")
        print(f"")
        print(f"  # Validate configuration only")
        print(f"  python {Path(__file__).name} --validate-only --config custom_config.json")

        return 0

if __name__ == "__main__":
    exit(main())