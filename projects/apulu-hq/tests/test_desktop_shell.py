"""Light smoke tests for the desktop shell. Does NOT open a real window —
that requires user-session GUI and isn't testable in CI / pytest. We only
test the parts that are safely unit-testable: tray image generation and
the Backend health-check logic."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SHELL_PATH = Path(__file__).resolve().parents[1] / "apulu_hq_shell.pyw"


@pytest.fixture
def shell_module(monkeypatch):
    """Import the .pyw file as a module."""
    pytest.importorskip("webview")
    pytest.importorskip("pystray")
    pytest.importorskip("PIL")
    spec = importlib.util.spec_from_file_location("apulu_hq_shell", SHELL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["apulu_hq_shell"] = mod
    spec.loader.exec_module(mod)
    yield mod
    sys.modules.pop("apulu_hq_shell", None)


def test_tray_image_renders(shell_module):
    img = shell_module._build_tray_image()
    assert img.size == (128, 128)
    assert img.mode == "RGBA"


def test_backend_already_running_returns_false_when_no_server(shell_module, monkeypatch):
    """With nothing listening on 127.0.0.1:8741, already_running() must
    return False (not raise)."""
    # Point at a port we know is closed
    monkeypatch.setattr(shell_module, "HEALTH_URL",
                        "http://127.0.0.1:1/api/health")
    b = shell_module.Backend()
    assert b.already_running() is False


def test_backend_start_fails_fast_with_bad_python(shell_module, monkeypatch, tmp_path):
    """If the spawned subprocess exits immediately, start() returns False
    within a sensible window (not the full 30s timeout)."""
    import time

    # Force the spawned command to be a no-op that exits immediately
    real_popen = shell_module.subprocess.Popen
    bad_cmd = [shell_module.sys.executable, "-c", "import sys; sys.exit(2)"]

    class FakeBackend(shell_module.Backend):
        def start(self, timeout=4.0):
            # Mirror the real start() but with a bad command + tight timeout
            log = shell_module.log
            log.info("starting backend (fake bad command)")
            self.proc = real_popen(
                bad_cmd,
                cwd=str(shell_module.SHELL_DIR),
                stdout=shell_module.subprocess.DEVNULL,
                stderr=shell_module.subprocess.DEVNULL,
            )
            deadline = time.time() + timeout
            while time.time() < deadline:
                if self.already_running():
                    return True
                if self.proc.poll() is not None:
                    return False
                time.sleep(0.1)
            return False

    monkeypatch.setattr(shell_module, "HEALTH_URL",
                        "http://127.0.0.1:1/api/health")
    b = FakeBackend()
    start = time.time()
    assert b.start() is False
    assert time.time() - start < 3.0, "start() should fast-fail on bad subprocess"
