"""Apulu HQ desktop shell.

Single-file launcher that:
  1. Spawns the FastAPI backend as a background subprocess on 127.0.0.1:8741
  2. Waits for /api/health to return 200
  3. Opens a native window via pywebview (uses Windows 11's WebView2)
     pointing at http://127.0.0.1:8741/ui
  4. Installs a system tray icon (Show/Hide, Restart Backend, Quit)
  5. Closing the window minimizes to tray; tray Quit shuts down both
     window and backend

Launch with `pythonw apulu_hq_shell.pyw` for no console window. Or use
the install_startup.ps1 helper to register at boot.
"""

from __future__ import annotations

import io
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pystray
import webview
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"
PORT = 8741
UI_URL = f"http://{HOST}:{PORT}/ui/"
HEALTH_URL = f"http://{HOST}:{PORT}/api/health"
WINDOW_TITLE = "Apulu HQ"

SHELL_DIR = Path(__file__).resolve().parent
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "apulu-hq" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "shell.log", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)
log = logging.getLogger("apulu-hq-shell")


# ---------------------------------------------------------------------------
# Backend lifecycle
# ---------------------------------------------------------------------------


class Backend:
    """Owns the FastAPI subprocess. Restart-safe, idempotent."""

    def __init__(self) -> None:
        self.proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def already_running(self) -> bool:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=0.5) as r:
                return r.status == 200
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            return False

    def start(self, timeout: float = 30.0) -> bool:
        with self._lock:
            if self.proc and self.proc.poll() is None:
                log.info("backend already managed (pid=%s)", self.proc.pid)
                return True
            if self.already_running():
                log.warning(
                    "backend on %s:%d is already running but not managed by this "
                    "shell — adopting it as-is (no restart)",
                    HOST, PORT,
                )
                return True

            log.info("starting backend on %s:%d", HOST, PORT)
            # Use the same Python that's running this shell (so it stays in
            # whatever venv the user activated)
            cmd = [
                sys.executable,
                "-m", "uvicorn",
                "apulu_hq.api:app",
                "--host", HOST,
                "--port", str(PORT),
                "--log-level", "info",
                "--no-access-log",
            ]
            creation_flags = 0
            if sys.platform == "win32":
                # CREATE_NO_WINDOW = 0x08000000
                creation_flags = 0x08000000

            self.proc = subprocess.Popen(
                cmd,
                cwd=str(SHELL_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
            log.info("backend pid=%s", self.proc.pid)

            deadline = time.time() + timeout
            while time.time() < deadline:
                if self.already_running():
                    log.info("backend ready")
                    return True
                if self.proc.poll() is not None:
                    log.error("backend exited prematurely with %s", self.proc.returncode)
                    return False
                time.sleep(0.4)
            log.error("backend health check timed out")
            return False

    def stop(self) -> None:
        with self._lock:
            if not self.proc:
                return
            if self.proc.poll() is None:
                log.info("stopping backend pid=%s", self.proc.pid)
                try:
                    if sys.platform == "win32":
                        self.proc.terminate()
                    else:
                        self.proc.send_signal(signal.SIGTERM)
                    try:
                        self.proc.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        log.warning("backend didn't exit; killing")
                        self.proc.kill()
                        self.proc.wait(timeout=4)
                except Exception:
                    log.exception("error stopping backend")
            self.proc = None

    def restart(self) -> bool:
        self.stop()
        return self.start()


# ---------------------------------------------------------------------------
# Tray icon
# ---------------------------------------------------------------------------


def _build_tray_image() -> Image.Image:
    """Procedural icon — gold A on warm dark background."""
    size = 128
    img = Image.new("RGBA", (size, size), (26, 20, 16, 255))
    d = ImageDraw.Draw(img)
    # rounded square frame
    d.rectangle([6, 6, size - 6, size - 6], outline=(200, 163, 91, 255), width=4)
    # big A
    try:
        font = ImageFont.truetype("arial.ttf", 84)
    except OSError:
        font = ImageFont.load_default()
    text = "A"
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1] - 4),
           text, fill=(200, 163, 91, 255), font=font)
    return img


class Tray:
    def __init__(self, on_show, on_quit, on_restart_backend) -> None:
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_restart_backend = on_restart_backend
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Show Apulu HQ", self._handle_show, default=True),
            pystray.MenuItem("Open in browser", self._handle_browser),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Restart backend", self._handle_restart),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._handle_quit),
        )
        self._icon = pystray.Icon(
            "apulu-hq",
            icon=_build_tray_image(),
            title="Apulu HQ",
            menu=menu,
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True, name="tray")
        self._thread.start()
        log.info("tray icon started")

    def _handle_show(self, icon, item) -> None:
        try:
            self.on_show()
        except Exception:
            log.exception("show failed")

    def _handle_browser(self, icon, item) -> None:
        import webbrowser
        webbrowser.open(UI_URL)

    def _handle_restart(self, icon, item) -> None:
        try:
            self.on_restart_backend()
        except Exception:
            log.exception("restart failed")

    def _handle_quit(self, icon, item) -> None:
        try:
            self.on_quit()
        finally:
            if self._icon:
                self._icon.stop()

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()


# ---------------------------------------------------------------------------
# Main wiring
# ---------------------------------------------------------------------------


def main() -> int:
    backend = Backend()
    if not backend.start():
        # Surface the error before the window opens so users see it
        log.error("backend failed to start — see %s", LOG_DIR / "shell.log")
        # Open a minimal failure window
        webview.create_window(
            "Apulu HQ — backend offline",
            html=(
                "<html><body style='background:#1a1410;color:#f4ecdf;font-family:sans-serif;"
                "padding:40px'><h1 style='color:#c8a35b'>Backend failed to start</h1>"
                f"<p>Check the log at <code>{LOG_DIR / 'shell.log'}</code></p></body></html>"
            ),
            width=600,
            height=400,
        )
        webview.start()
        return 1

    # Build the window but do NOT auto-show on launch if started minimized
    start_minimized = "--minimized" in sys.argv

    window = webview.create_window(
        WINDOW_TITLE,
        UI_URL,
        width=1440,
        height=900,
        resizable=True,
        hidden=start_minimized,
        background_color="#1a1410",
        text_select=True,
    )

    def show_window() -> None:
        try:
            window.show()
            window.restore()
        except Exception:
            log.exception("show_window")

    quit_event = threading.Event()

    def quit_all() -> None:
        log.info("quit requested")
        quit_event.set()
        backend.stop()
        try:
            window.destroy()
        except Exception:
            pass

    tray = Tray(
        on_show=show_window,
        on_quit=quit_all,
        on_restart_backend=backend.restart,
    )

    # When the user closes the window, hide to tray instead of quitting.
    def on_closing() -> bool:
        if quit_event.is_set():
            return True  # actually closing
        log.info("window close pressed — hiding to tray")
        window.hide()
        return False  # cancel close

    window.events.closing += on_closing

    tray.start()

    log.info("opening window")
    try:
        webview.start()
    finally:
        log.info("webview loop exited")
        backend.stop()
        tray.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
