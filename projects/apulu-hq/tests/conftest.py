"""Pytest fixtures — isolate every test in a temp data dir."""

from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Point apulu_hq at a fresh data directory + repo root for each test."""
    repo_root = Path(__file__).resolve().parents[3]
    monkeypatch.setenv("APULU_HQ_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APULU_HQ_REPO_ROOT", str(repo_root))
    monkeypatch.setenv("APULU_HQ_DISABLE_TAILERS", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # Force re-import so module-level singletons (settings, _conn) pick up env.
    for mod in [
        "apulu_hq.config",
        "apulu_hq.db",
        "apulu_hq.models",
        "apulu_hq.importer",
        "apulu_hq.events.bus",
        "apulu_hq.events.schema",
        "apulu_hq.events",
        "apulu_hq.chat",
        "apulu_hq.tailer",
        "apulu_hq.api.app",
        "apulu_hq.api",
    ]:
        if mod in list(__import__("sys").modules):
            del __import__("sys").modules[mod]
    yield
