"""One-shot importer: Paperclip JSON → Apulu HQ SQLite.

Idempotent. Re-running will:
  - INSERT OR REPLACE agents by id (preserves UUIDs verbatim)
  - INSERT OR REPLACE routines by id (preserves UUIDs verbatim)
  - Leave dispatches/dlq/chat tables untouched

Reads:
  scripts/paperclip/agent_ids.json
  scripts/paperclip/routine_ids.json
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import settings
from .db import get_conn, tx
from .models import Agent, Routine, now_iso

# ---------------------------------------------------------------------------
# Agent metadata (derived from CLAUDE.md). IDs come from agent_ids.json.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentSeed:
    name: str
    department: str
    role: str
    adapter_type: str
    desk: tuple[int, int]
    system_prompt: str


AGENT_SEEDS: list[AgentSeed] = [
    AgentSeed(
        name="Clu",
        department="board",
        role="CEO & Creative Director",
        adapter_type="api",
        desk=(2, 2),
        system_prompt=(
            "You are Clu — but in HQ you ARE the user. This persona is reserved for the operator. "
            "If addressed directly, respond minimally and route back to the appropriate agent."
        ),
    ),
    AgentSeed(
        name="Nelly",
        department="cos",
        role="Chief of Staff",
        adapter_type="claude_local",
        desk=(4, 2),
        system_prompt=(
            "You are Nelly, Chief of Staff at Apulu Records. You coordinate across departments, "
            "synthesize the daily briefing, monitor health, and route artist work (Vawn now, "
            "extensible). Escalate to Clu only for budget overruns, creative gates, or system "
            "failures. Tone: calm, organized, terse. Always end with the next concrete action."
        ),
    ),
    AgentSeed(
        name="Oaklyn",
        department="marketing",
        role="Marketing Division President",
        adapter_type="claude_local",
        desk=(10, 4),
        system_prompt=(
            "You are Oaklyn, Marketing Division President. You own social presence, posting "
            "cadence, engagement quality, and analytics. Direct reports: Sage & Khari (content), "
            "Dex (engagement), Nova (analytics), Echo (press)."
        ),
    ),
    AgentSeed(
        name="Sage & Khari",
        department="marketing",
        role="Content & Visuals Team",
        adapter_type="process",
        desk=(12, 4),
        system_prompt=(
            "You are the Sage & Khari duo — content creation and visual content production for "
            "Vawn. You own posting across X, Bluesky, TikTok, Instagram, Threads. Also Remotion "
            "graphics (track-teaser) and lyric/video pipelines. Hand off to Onyx for any "
            "audio/master work."
        ),
    ),
    AgentSeed(
        name="Dex",
        department="marketing",
        role="Engagement",
        adapter_type="claude_local",
        desk=(14, 4),
        system_prompt=(
            "You are Dex, Engagement agent. You monitor comments and DMs across platforms and "
            "auto-reply with on-brand voice. You also run Bluesky-like activity on trending "
            "hip-hop posts to grow reach. Never reply with anything that contradicts Vawn's "
            "established voice."
        ),
    ),
    AgentSeed(
        name="Nova",
        department="marketing",
        role="Analytics",
        adapter_type="claude_local",
        desk=(16, 4),
        system_prompt=(
            "You are Nova, Analytics. You run content-performance-daily (11am) and the weekly "
            "analytics-digest (Sun 9am). Surface per-post metrics, identify outliers, and "
            "recommend the next week's content allocation."
        ),
    ),
    AgentSeed(
        name="Echo",
        department="marketing",
        role="Press & PR",
        adapter_type="claude_local",
        desk=(18, 4),
        system_prompt=(
            "You are Echo, Press & PR. You run the weekly press-opportunity-scan (Wed 2pm), "
            "track outlets and writers covering the bass-baritone cinematic lane, and draft "
            "pitch angles."
        ),
    ),
    AgentSeed(
        name="Aspyn",
        department="operations",
        role="Operations Division President (Analytics, Finance, Partnerships)",
        adapter_type="claude_local",
        desk=(10, 8),
        system_prompt=(
            "You are Aspyn, Operations Division President. You own analytics, finance, and "
            "partnerships. Direct reports: Nova (analytics), Cipher (finance), Vibe "
            "(partnerships). Run weekly-ops-digest (Sun 10pm)."
        ),
    ),
    AgentSeed(
        name="Cipher",
        department="operations",
        role="Finance & Royalties",
        adapter_type="claude_local",
        desk=(12, 8),
        system_prompt=(
            "You are Cipher, Finance & Royalties. You run streaming-revenue-check (Mon 12pm) "
            "and reconcile DSP revenue against expected payouts."
        ),
    ),
    AgentSeed(
        name="Vibe",
        department="operations",
        role="Partnerships & Sync Licensing",
        adapter_type="claude_local",
        desk=(14, 8),
        system_prompt=(
            "You are Vibe, Partnerships & Sync Licensing. You run sync-opportunity-scan "
            "(Mon 2pm) — film/TV/ad placement opportunities matching Vawn's bass-baritone "
            "cinematic catalog."
        ),
    ),
    AgentSeed(
        name="Rex",
        department="operations",
        role="Tech & Reliability",
        adapter_type="claude_local",
        desk=(4, 8),
        system_prompt=(
            "You are Rex, Tech & Reliability. You own the bulletproofing stack: retry wrapper, "
            "circuit breaker, DLQ, signature detection. You run system-health-check (daily 6am "
            "ET). You read STATUS.md and dispatch_log.jsonl first when diagnosing anything."
        ),
    ),
    AgentSeed(
        name="Rhythm",
        department="research",
        role="Research Director",
        adapter_type="claude_local",
        desk=(4, 12),
        system_prompt=(
            "You are Rhythm, Research Director. You run artist-discovery-scan (daily 9:30am), "
            "playlist-monitor (daily 1pm), and competitor-tracking (Fri 3pm). Surface signal, "
            "not noise."
        ),
    ),
    AgentSeed(
        name="Sable",
        department="cos",
        role="Artist Management",
        adapter_type="claude_local",
        desk=(6, 2),
        system_prompt=(
            "You are Sable, Artist Management for Vawn. You handle day-to-day scheduling, "
            "career arc, and artist development. You're the human-facing layer for the artist."
        ),
    ),
    AgentSeed(
        name="Camdyn",
        department="production",
        role="A&R + Creative Brief",
        adapter_type="claude_local",
        desk=(12, 12),
        system_prompt=(
            "You are Camdyn, A&R & Creative Brief. You read the cultural radar before every "
            "creative decision. You turn artist direction into briefs for Cole and the studio."
        ),
    ),
    AgentSeed(
        name="Cole",
        department="production",
        role="Music Production (Suno prompts)",
        adapter_type="claude_local",
        desk=(14, 12),
        system_prompt=(
            "You are Cole, Music Production. You turn Camdyn's briefs into Suno prompts and "
            "iterate to land the right vocal, tempo, and arrangement."
        ),
    ),
    AgentSeed(
        name="Onyx",
        department="post-prod",
        role="Mix / Master / QC",
        adapter_type="claude_local",
        desk=(16, 12),
        system_prompt=(
            "You are Onyx, Mix/Master/QC. You take stems through Vawn's mix engine and "
            "approve release-ready masters. Your QC gate is the last step before release."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Routine metadata. IDs from routine_ids.json. Schedules + assignees from
# scripts/paperclip/setup_marketing.py, add_remotion_routines.py, and CLAUDE.md.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoutineSeed:
    name: str
    agent_name: str
    cron: str
    description: str
    priority: str = "medium"
    enabled: bool = False
    disabled_reason: str | None = None


ROUTINE_SEEDS: list[RoutineSeed] = [
    # Content / Visuals — Sage & Khari
    RoutineSeed("hashtag-scan", "Sage & Khari", "0 6 * * *",
                "Generate trending hashtags for all platforms"),
    RoutineSeed("morning-early", "Sage & Khari", "0 8 * * *",
                "Post to X and Bluesky — morning energy", priority="high"),
    RoutineSeed("morning-main", "Sage & Khari", "15 9 * * *",
                "Post to TikTok, Instagram, Threads — morning", priority="high"),
    RoutineSeed("text-post-morning", "Sage & Khari", "30 10 * * *",
                "Text-only posts to X, Threads, Bluesky"),
    RoutineSeed("midday-early", "Sage & Khari", "0 12 * * *",
                "Post to X and Bluesky — midday swagger", priority="high"),
    RoutineSeed("midday-main", "Sage & Khari", "45 12 * * *",
                "Post to TikTok, Instagram, Threads — midday", priority="high"),
    RoutineSeed("text-post-afternoon", "Sage & Khari", "30 15 * * *",
                "Text-only posts + X thread from ideation"),
    RoutineSeed("evening-early", "Sage & Khari", "0 18 * * *",
                "Post to X, Bluesky, Instagram slideshow Reel", priority="high"),
    RoutineSeed("evening-main", "Sage & Khari", "15 20 * * *",
                "Post to TikTok, Threads — evening storytelling", priority="high"),
    RoutineSeed("recycle", "Sage & Khari", "0 14 * * 0",
                "Recycle top 30-day-old images with fresh captions", priority="low"),
    RoutineSeed("lyric-card", "Sage & Khari", "30 6 * * *",
                "Generate lyric card images for today",
                enabled=False,
                disabled_reason="Catalog data was fabricated; lyrics are off (2026-04-28)."),
    RoutineSeed("video-daily", "Sage & Khari", "45 6 * * *",
                "Create Ken Burns video from images"),
    RoutineSeed("video-cinematic", "Sage & Khari", "0 7 * * 0",
                "Create Higgsfield cinematic video (Sunday)",
                priority="low", enabled=False,
                disabled_reason="Cinematic video anchored on lyric prompt; lyrics are off (2026-04-28)."),
    RoutineSeed("track-teaser", "Sage & Khari", "0 19 * * 2",
                "Remotion TrackTeaser — waveform + track title (Tue, lyric pillar)"),
    # Engagement — Dex
    RoutineSeed("engagement-monitor", "Dex", "0 */2 * * *",
                "Monitor comments and auto-reply across platforms"),
    RoutineSeed("engagement-bot", "Dex", "0 */5 * * *",
                "Bluesky likes on trending hip-hop posts", priority="low"),
    # Analytics — Nova
    RoutineSeed("analytics-digest", "Nova", "0 9 * * 0",
                "Weekly analytics digest and recommendations", priority="low"),
    RoutineSeed("content-performance-daily", "Nova", "0 11 * * *",
                "Per-post metrics, surface outliers, recommend next-week allocation"),
    # Press — Echo
    RoutineSeed("press-opportunity-scan", "Echo", "0 14 * * 3",
                "Weekly press opportunity scan (Wed 2pm)", priority="low"),
    # Finance — Cipher
    RoutineSeed("streaming-revenue-check", "Cipher", "0 12 * * 1",
                "Mon 12pm DSP revenue reconciliation", priority="low"),
    # Partnerships — Vibe
    RoutineSeed("sync-opportunity-scan", "Vibe", "0 14 * * 1",
                "Mon 2pm sync licensing scan", priority="low"),
    # Research — Rhythm
    RoutineSeed("artist-discovery-scan", "Rhythm", "30 9 * * *",
                "Daily artist discovery scan"),
    RoutineSeed("playlist-monitor", "Rhythm", "0 13 * * *",
                "Daily playlist monitor"),
    RoutineSeed("competitor-tracking", "Rhythm", "0 15 * * 5",
                "Friday competitor tracking", priority="low"),
    # Ops digest — Aspyn
    RoutineSeed("weekly-ops-digest", "Aspyn", "0 22 * * 0",
                "Sunday 10pm weekly ops digest", priority="low"),
    # Tech health — Rex
    RoutineSeed("system-health-check", "Rex", "0 6 * * *",
                "Daily 6am ET system health check"),
]


def _load_legacy_json(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"Required Paperclip file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def import_all(*, repo_root: Path | None = None) -> dict[str, int]:
    """Run the import. Returns counts: {agents, routines}."""
    root = repo_root or settings.repo_root
    agent_ids_file = root / "scripts" / "paperclip" / "agent_ids.json"
    routine_ids_file = root / "scripts" / "paperclip" / "routine_ids.json"

    legacy_agents = _load_legacy_json(agent_ids_file)
    legacy_routines = _load_legacy_json(routine_ids_file)

    seen_agents: set[str] = set()
    seen_routines: set[str] = set()

    with tx() as conn:
        # ---- Agents ----
        for seed in AGENT_SEEDS:
            if seed.name not in legacy_agents:
                raise KeyError(
                    f"Agent '{seed.name}' missing from agent_ids.json — "
                    f"refusing to invent an ID"
                )
            agent_id = legacy_agents[seed.name]
            seen_agents.add(seed.name)

            existing = conn.execute(
                "SELECT created_at FROM agents WHERE id = ?", (agent_id,)
            ).fetchone()
            created = existing["created_at"] if existing else now_iso()

            agent = Agent(
                id=agent_id,
                legacy_id=agent_id,
                display_name=seed.name,
                department=seed.department,
                role=seed.role,
                adapter_type=seed.adapter_type,
                adapter_config={},
                model=None,
                provider="anthropic" if seed.adapter_type in {"claude_local", "api"} else None,
                system_prompt=seed.system_prompt,
                desk_x=seed.desk[0],
                desk_y=seed.desk[1],
                sprite_key=f"sprite_{seed.name.lower().replace(' & ', '_').replace(' ', '_')}",
                enabled=True,
                created_at=created,
                updated_at=now_iso(),
            )
            d = agent.to_db()
            conn.execute(
                """
                INSERT OR REPLACE INTO agents
                (id, legacy_id, display_name, department, role, adapter_type,
                 adapter_config, model, provider, system_prompt, desk_x, desk_y,
                 sprite_key, enabled, budget_monthly_usd, created_at, updated_at)
                VALUES
                (:id, :legacy_id, :display_name, :department, :role, :adapter_type,
                 :adapter_config, :model, :provider, :system_prompt, :desk_x, :desk_y,
                 :sprite_key, :enabled, :budget_monthly_usd, :created_at, :updated_at)
                """,
                d,
            )

        missing_agents = set(legacy_agents) - seen_agents
        if missing_agents:
            raise RuntimeError(
                f"Legacy agents not covered by AGENT_SEEDS: {sorted(missing_agents)}. "
                f"Add them to importer.py before re-running."
            )

        # ---- Routines ----
        for r in ROUTINE_SEEDS:
            if r.name not in legacy_routines:
                raise KeyError(
                    f"Routine '{r.name}' missing from routine_ids.json — "
                    f"refusing to invent an ID"
                )
            if r.agent_name not in legacy_agents:
                raise KeyError(
                    f"Routine '{r.name}' assigned to unknown agent '{r.agent_name}'"
                )
            rid = legacy_routines[r.name]
            agent_id = legacy_agents[r.agent_name]
            seen_routines.add(r.name)

            existing = conn.execute(
                "SELECT created_at FROM routines WHERE id = ?", (rid,)
            ).fetchone()
            created = existing["created_at"] if existing else now_iso()

            routine = Routine(
                id=rid,
                legacy_id=rid,
                display_name=r.name,
                agent_id=agent_id,
                cron_expr=r.cron,
                timezone="America/New_York",
                command="",
                args=[],
                description=r.description,
                priority=r.priority,
                enabled=r.enabled,
                disabled_reason=r.disabled_reason,
                created_at=created,
                updated_at=now_iso(),
            )
            d = routine.to_db()
            conn.execute(
                """
                INSERT OR REPLACE INTO routines
                (id, legacy_id, display_name, agent_id, cron_expr, timezone,
                 command, args, description, priority, enabled, disabled_reason,
                 created_at, updated_at)
                VALUES
                (:id, :legacy_id, :display_name, :agent_id, :cron_expr, :timezone,
                 :command, :args, :description, :priority, :enabled, :disabled_reason,
                 :created_at, :updated_at)
                """,
                d,
            )

        missing_routines = set(legacy_routines) - seen_routines
        if missing_routines:
            raise RuntimeError(
                f"Legacy routines not covered by ROUTINE_SEEDS: {sorted(missing_routines)}. "
                f"Add them to importer.py before re-running."
            )

    # Read-back counts for the caller.
    conn = get_conn()
    n_agents = conn.execute("SELECT COUNT(*) AS c FROM agents").fetchone()["c"]
    n_routines = conn.execute("SELECT COUNT(*) AS c FROM routines").fetchone()["c"]
    return {"agents": n_agents, "routines": n_routines}


if __name__ == "__main__":
    counts = import_all()
    print(f"Imported {counts['agents']} agents and {counts['routines']} routines.")
