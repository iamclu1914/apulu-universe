"""Apulu HQ desktop shell.

Launches the FastAPI backend as a subprocess sidecar, then opens a pywebview
window pointing at http://127.0.0.1:8741.  A system-tray icon (pystray) lets
the operator show/hide the window, pause/resume all routines, and quit.

Entry point:  python -m apulu_hq.shell
              (or via run_shell.py in scripts/)

Behaviour:
  - If HQ backend is already running on :8741, the shell attaches to it and
    does NOT start a second uvicorn process.
  - Closing the window hides it to tray (does not kill the backend).
  - Quit from tray menu stops the backend sidecar (if we own it) and exits.
  - Window position/size are remembered in %LOCALAPPDATA%\\apulu-hq\\shell_prefs.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pystray
import webview
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HQ_URL = "http://127.0.0.1:8741"
HEALTH_URL = f"{HQ_URL}/api/health"
DATA_DIR = Path(os.environ.get("APULU_HQ_DATA_DIR", Path.home() / "AppData" / "Local" / "apulu-hq"))
PREFS_FILE = DATA_DIR / "shell_prefs.json"
LOG_FILE = DATA_DIR / "logs" / "shell.log"

DEFAULT_W, DEFAULT_H = 1440, 900
STARTUP_TIMEOUT = 20  # seconds to wait for backend


# ---------------------------------------------------------------------------
# Prefs (window geometry)
# ---------------------------------------------------------------------------

def _load_prefs() -> dict:
    try:
        return json.loads(PREFS_FILE.read_text())
    except Exception:
        return {}


def _save_prefs(prefs: dict) -> None:
    try:
        PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PREFS_FILE.write_text(json.dumps(prefs, indent=2))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Backend sidecar
# ---------------------------------------------------------------------------

def _backend_alive() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(HEALTH_URL, timeout=3)
        return True
    except Exception:
        return False


def _start_backend() -> subprocess.Popen | None:
    """Start uvicorn as a hidden sidecar. Returns the Popen object, or None
    if the backend was already running."""
    if _backend_alive():
        _log("backend already up — attaching")
        return None

    python = sys.executable
    project_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("HQ_DISPATCHER_SHADOW", "1")
    env.setdefault("APULU_HQ_DATA_DIR", str(DATA_DIR))

    log_path = DATA_DIR / "logs" / "hq.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_path, "a", encoding="utf-8")

    proc = subprocess.Popen(
        [
            python, "-m", "uvicorn",
            "apulu_hq.api:app",
            "--host", "127.0.0.1",
            "--port", "8741",
            "--log-level", "info",
        ],
        cwd=str(project_dir),
        stdout=log_fh,
        stderr=log_fh,
        env=env,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    _log(f"backend sidecar started PID={proc.pid}")

    # Wait for it to become healthy
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        if _backend_alive():
            _log("backend healthy")
            return proc
        time.sleep(0.5)

    _log("WARNING: backend did not become healthy within timeout")
    return proc


# ---------------------------------------------------------------------------
# Tray icon
# ---------------------------------------------------------------------------

def _make_tray_icon() -> Image.Image:
    """Generate a simple 64x64 tray icon programmatically (gold 'A' on dark)."""
    img = Image.new("RGBA", (64, 64), (28, 22, 18, 255))
    draw = ImageDraw.Draw(img)
    # Gold circle background
    draw.ellipse([4, 4, 60, 60], fill=(212, 175, 55, 255))
    # Dark 'A' letterform (simple triangle)
    pts = [(32, 10), (10, 54), (18, 54), (26, 36), (38, 36), (46, 54), (54, 54)]
    draw.polygon(pts, fill=(28, 22, 18, 255))
    draw.rectangle([24, 38, 40, 44], fill=(28, 22, 18, 255))
    return img


def _build_tray(window: webview.Window, sidecar: subprocess.Popen | None) -> pystray.Icon:
    icon_img = _make_tray_icon()

    def _show(_icon, _item):
        window.show()
        window.restore()

    def _hide(_icon, _item):
        window.hide()

    def _pause_all(_icon, _item):
        try:
            import urllib.request
            req = urllib.request.Request(f"{HQ_URL}/api/scheduler/reload", method="POST")
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass

    def _quit(_icon, _item):
        _log("quit from tray")
        _icon.stop()
        window.destroy()
        if sidecar and sidecar.poll() is None:
            sidecar.terminate()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Show Apulu HQ", _show, default=True),
        pystray.MenuItem("Hide", _hide),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _quit),
    )

    return pystray.Icon("ApuluHQ", icon_img, "Apulu HQ", menu)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[shell {ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prefs = _load_prefs()

    # 1. Start (or attach to) the backend
    sidecar = _start_backend()

    # 2. Create the pywebview window
    window = webview.create_window(
        title="Apulu HQ",
        url=HQ_URL,
        width=prefs.get("width", DEFAULT_W),
        height=prefs.get("height", DEFAULT_H),
        x=prefs.get("x", None),
        y=prefs.get("y", None),
        resizable=True,
        min_size=(800, 600),
        background_color="#1c1614",
    )

    def _on_closed():
        # Save geometry
        try:
            _save_prefs({
                "width": window.width,
                "height": window.height,
                "x": window.x,
                "y": window.y,
            })
        except Exception:
            pass

    window.events.closed += _on_closed

    # 3. Run tray in background thread
    tray = _build_tray(window, sidecar)
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    _log("opening window")

    # 4. Start webview (blocks until all windows closed)
    webview.start(debug=False)

    # On window close (X button) — hide to tray instead of quitting
    # pywebview doesn't natively support "hide on close"; we handle it by
    # hooking the closed event above and the tray provides the only quit path.

    _log("webview stopped")


if __name__ == "__main__":
    main()
