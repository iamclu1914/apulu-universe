"""Apulu HQ configuration.

Single source of truth for paths, ports, and environment-derived settings.
Reads `%LOCALAPPDATA%\\apulu-hq\\secrets.env` if present (KEY=VALUE per line).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_secrets_env() -> None:
    """Best-effort load of secrets.env into os.environ. No external deps."""
    candidates = []
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidates.append(Path(local_app) / "apulu-hq" / "secrets.env")
    candidates.append(Path.home() / ".apulu-hq" / "secrets.env")
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except OSError:
            pass


_load_secrets_env()


def _data_dir() -> Path:
    """%LOCALAPPDATA%\\apulu-hq on Windows, ~/.apulu-hq elsewhere."""
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        return Path(local_app) / "apulu-hq"
    return Path.home() / ".apulu-hq"


@dataclass
class Settings:
    data_dir: Path = field(default_factory=_data_dir)
    db_path: Path = field(init=False)
    log_dir: Path = field(init=False)

    host: str = "127.0.0.1"
    port: int = 8741

    anthropic_api_key: str | None = field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY")
    )
    default_chat_model: str = field(
        default_factory=lambda: os.environ.get(
            "APULU_HQ_DEFAULT_MODEL", "claude-sonnet-4-5"
        )
    )

    # Path to the universe repo root, used by the importer to locate the
    # Paperclip-era JSON files. Override via env when running outside the repo.
    repo_root: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "APULU_HQ_REPO_ROOT",
                str(Path(__file__).resolve().parents[3]),
            )
        )
    )

    def __post_init__(self) -> None:
        # Allow override of data dir via env.
        override = os.environ.get("APULU_HQ_DATA_DIR")
        if override:
            self.data_dir = Path(override)
        self.db_path = self.data_dir / "hq.db"
        self.log_dir = self.data_dir / "logs"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
