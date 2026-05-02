---
date: 2026-04-27
incident: STORAGE_QUOTA_AND_LYRICS_CUTOVER
severity: P1
duration_outage: ~96h (2026-04-24 → 2026-04-28)
duration_silent: ~72h
status: resolved
tags:
  - incident
  - postmortem
  - infrastructure
  - posting
  - content-quality
---

# Storage quota + Supabase SDK regression + fabricated lyrics catalog

## TL;DR

Vawn social posting was silently broken for ~4 days (2026-04-24 → 2026-04-28). Three stacked failures kept the whole stack reporting healthy while zero posts shipped:

1. **Apulu Studio backend** — Supabase Storage hit its 1 GB free-tier quota and started returning 500 with `exceed_storage_size_quota`.
2. **Supabase Python SDK** — A `.text`-on-dict regression in recent `storage3` versions caught the storage error but couldn't render it, surfacing instead as `'dict' object has no attribute 'text'`.
3. **Vawn dispatcher** — Treated `exit 0 + apulu_backend_5xx signature` as success, so dispatch_log, heartbeat_runs, and STATUS.md all said "healthy." No human signal until Aspyn's weekly digest noticed `posted_log` empties two days in.

While unwinding the silent-failure problem we also discovered that **the entire `catalog_local.py` lyrics database was AI-generated**. Every lyric card and every "anchor_line" feeding the captions for at least the past week was a hallucinated bar attributed to Vawn. That triggered a separate cutover: the lyric pipeline is now disabled at every layer until a real catalog gets seeded.

Net: 9+ structural defenses shipped. No lyric content can leak into posts. Future incidents in this class will surface within ~10 minutes via the new outcome verification chain.

## Timeline (UTC)

| When | What |
|---|---|
| 2026-04-17 | Earlier backend outage. 11 `evening-early` dispatches landed in DLQ. (Not part of this incident — context for the staleness flagged repeatedly in subsequent reports.) |
| 2026-04-24 ~00:00 | Apulu Studio uploads start returning 500. Supabase Storage quota threshold tripped. SDK `.text` regression activates. Dispatcher records `exit 0 + apulu_backend_5xx signature` as success — silent failure mode begins. |
| 2026-04-24, 25, 26 | All Vawn posting slots (morning-early, morning-main, midday-early, midday-main, evening-early, evening-main) ship 0 posts. Heartbeat_runs reports 100% success. `posted_log.json` records empty `[]` arrays for every image. No alerts fire. |
| 2026-04-26 ~22:00 | Rex's daily health note (`journals/vawn/health/2026-04-26-health.md`) flags the silent-failure pattern: signature detected but no escalation. |
| 2026-04-27 ~14:00 | Aspyn's weekly ops digest surfaces "0/15 platform-posts" three days running. Diagnosis kicks off. |
| 2026-04-27 ~14:30 | Bug A diagnosed: `dispatch_runner.py:245-248` returns 0 immediately on `proc.returncode == 0` without checking for high-severity signature. |
| 2026-04-27 ~15:00 | Bug A + Bug B fixes shipped to `dispatch_runner.py` and `post_vawn.py`. Marketing dispatcher picker fix also shipped (was picking arbitrary issue from a 109-deep stale queue). |
| 2026-04-27 ~16:00 | Structural observability work: `posted_log_invariant.py`, real-traffic upload probe extension, `paperclip_watchdog_notify.py`, `cleanup_stale_issues.py`. All verified end-to-end. |
| 2026-04-27 22:04 | Live evening-early fire: dispatch_log shows `exit=1, sig=apulu_backend_5xx, success=False, final=True`. Bug A and Bug B fixes confirmed working in production. |
| 2026-04-27 ~23:18 | Codex (parallel rescue) lands `a1f4032` to ApuluStudio main: replaces broken Supabase SDK upload with direct httpx POST to Storage REST API. Same approach as our PR #3, which gets closed as duplicate. |
| 2026-04-28 ~01:00 | Render redeploys with Codex's fix. The `.text` error stops. Real upload now returns 500 with the actual underlying error: `Service for this project is restricted due to the following violations: exceed_storage_size_quota`. |
| 2026-04-28 ~14:25 | Clu upgrades Supabase plan. Storage quota lifts. `real_upload` probe flips to `ok(200)`. |
| 2026-04-28 ~14:35 | Manual fire of `midday-early` slot: `Posted: ['x', 'bluesky'] | Failed: []`. End-to-end recovery confirmed. |
| 2026-04-28 ~15:00 | First public post reveals second class of problem: the caption uses banned generic-rapper-talk ("the real ones," "drop a comment if you felt that"), and the lyric card renders a hallucinated bar. |
| 2026-04-28 ~15:30 | Investigation reveals `pipeline/brain/catalog_local.py` is loading from a `catalog/lyrics.json` containing 11 fabricated tracks with 0 real Vawn bars. Every track name and every bar is AI-generated prose — none of it matches the canonical catalog at `catalogs/vawn-lyrics.md`. |
| 2026-04-28 ~16:00 | Lyrics cutover: every layer that emits or consumes lyrics is disabled. `lyric-card` and `video-cinematic` Paperclip routines disabled, `Vawn\LyricAnnotation` WTS task disabled, source `lyrics.json` files deleted, `anchor_line` plumbing severed in `post_vawn.py`/`text_post_agent.py`/`captions.py`/`content_agent.py`/`catalog_agent.py`/`video_agent.py`/`lyric_annotation_agent.py`, generic-rapper-talk ban list added to caption prompt. |

## Root causes

### Cause 1 — Supabase Storage quota exceeded (the underlying real problem)

The `media` bucket on the Apulu Studio Supabase project hit its 1 GB free-tier limit. Likely contributors: cumulative upload from all artist content, cropped variants per platform per post, no retention policy.

Why it stayed undetected: Supabase's response is sticky — once the violation is flagged, even a quota check that's now under-limit doesn't auto-clear. The error explicitly told us to "reach out to Supabase support."

### Cause 2 — Supabase Python SDK regression on storage upload

`supabase>=2.3.0` (unpinned upper bound in `requirements.txt`) pulls a `storage3` version where the upload response handler does `response.text` on what's now a dict-like `UploadResponse`. Throws `AttributeError: 'dict' object has no attribute 'text'`. The backend's `try/except Exception` block caught this and surfaced the AttributeError string as the response body, masking the actual quota error underneath.

Codex's fix: replace `self.client.storage.from_(BUCKET).upload(...)` with a direct httpx POST to `{SUPABASE_URL}/storage/v1/object/{bucket}/{path}`. SDK-version-independent. Shipped as ApuluStudio commit `a1f4032`.

### Cause 3 — Vawn dispatcher swallowed the 500s as success

`dispatch_runner.py` line 245-248 (in the original code):

```python
if last_exit == 0:
    print(f"[dispatcher] Success on attempt {attempt} ({duration:.1f}s)")
    log_outcome(slot, attempt, max_retries, last_exit, duration, signature, final=True)
    return 0
```

The `signature` parameter (which correctly identified `apulu_backend_5xx`) was logged but ignored. Subprocess exited 0 because `post_vawn.py`'s broad `except Exception` blocks per-platform swallowed the upload error and the script printed the exception to stdout (matching the `apulustudio.onrender.com.*50[0-9]` regex) but exited cleanly. Net: dispatch_log records `success: true` with `signature: apulu_backend_5xx` — the paradoxical state.

Compounded by:

- **Bug B**: `post_vawn.py` had no aggregate exit-code logic. If all attempted platforms failed, the script still exited 0.
- **Bug C**: `marketing_dispatch.py:resolve_slot_from_issues` picked `candidates[0]` from the API's issue list with no explicit ordering. Every process-adapter agent had a 100+ deep backlog of stale `todo` `routine_execution` issues (Sage 109, Dex 130, Nova 12, Rex 9, Rhythm 12) because nothing in the platform PATCHes them to `done` after run. Result: routines fired correctly, but the dispatcher kept picking stale issues, causing slot mislabels (e.g., hashtag-scan firing at 10:00 ET ran the midday-main script).

### Cause 4 — Health probes never exercised the failing path

`backend_health_probe.py` did `POST /api/posts/upload` **without auth and without a body**. Returned 401. Probe coded 401 as "ok." So the probe could go green for days while every real upload failed.

### Cause 5 — Catalog data was fabricated (separate, but co-discovered)

`catalog_local.py` reads from `catalog/lyrics.json`. That file contained 11 tracks with names like "THE VERSION THAT SURVIVED," "I KNOW WHAT THIS IS," "BOTH CITIES" — all AI-generated. Bars had no rhyme schemes, no rap cadence, were generic introspective prose. The canonical Vawn catalog (24 tracks, 210 bars) sits in `catalogs/vawn-lyrics.md` as artist-provided reference but was never synced into `lyrics.json`. Whoever populated the JSON did it from an LLM, not from the markdown.

This wasn't part of the outage — it's a separate, deeper content-quality bug that was hiding behind the silent-posting issue. Once posting recovered, it became visible in the first published caption.

## What we shipped

### Code-side fixes (live in production)

| File | Change | Repo |
|---|---|---|
| `dispatch_runner.py` | Treat `exit_code=0 + critical/high signature` as failure: enter retry, write dead_letter, send alert, return non-zero. Update success-flag logic to factor in signature severity. | Vawn |
| `post_vawn.py` | At end of `main()`: if any platforms attempted and all failed, `sys.exit(1)`. | Vawn |
| `marketing_dispatch.py` | `resolve_slot_from_issues` sorts candidates by `createdAt` DESC. Failure cooldown (10 min) now applies to retryable failures too, preventing alert flood. | Vawn |
| `backend_health_probe.py` | Added `real_upload` probe: authenticated tiny-PNG POST that exercises the full upload handler path. Critical-tier — flips overall to degraded if upload 5xxs. | Vawn |
| `run_paperclip_watchdog.cmd` | Routes up/down state through `paperclip_watchdog_notify.py`. | Vawn |
| `paperclip_watchdog_notify.py` (new) | Threshold-based downtime alerting: emails Clu after 10 min sustained downtime; recovery email when service comes back. | Vawn |
| `posted_log_invariant.py` (new) | Outcome verification: cross-checks `dispatch_log.jsonl` slot fires against `posted_log.json` results hourly. Alerts on `none_landed` / `never_recorded`. | Vawn |
| `cleanup_stale_issues.py` (new) | Daily DB cleanup: cancels routine_execution todos older than 24h with empty `started_at`. Prevents queue-depth growth. | Vawn |
| `apulustudio/storage_service.py` (commit `a1f4032`) | Direct httpx POST to Supabase Storage REST API. Bypasses SDK regression. Includes pytest regression test. | ApuluStudio |

### Lyrics cutover (separate, also live)

Every layer that emitted or consumed lyrics is disabled:

| Layer | Action |
|---|---|
| Paperclip routine `lyric-card` (6:30 AM ET daily) | `routine_triggers.enabled = false` |
| Paperclip routine `video-cinematic` (Sun 7 AM ET) | `routine_triggers.enabled = false` |
| WTS task `Vawn\LyricAnnotation` (Wed 10 AM weekly) | Disabled via `schtasks` |
| `pipeline/output/vawn/catalog/lyrics.json` | Deleted |
| `research/vawn/catalog/lyrics.json` | Deleted |
| `pipeline/brain/catalog_local.py` | Fail-safe (returns 0 tracks when source missing) |
| `agents_research/catalog_agent.py` | Early-return clears `daily_brief.catalog_lines` and writes `[]` |
| `agents_research/content_agent.py` | Schema removed `anchor_line`/`anchor_track`; system prompt bans lyric refs |
| `post_vawn.py`, `text_post_agent.py` | Anchor_line/anchor_track forced to `""`; ANCHOR LINE block removed from prompts |
| `captions.py` | `_build_context_block` no longer injects anchor_line/track. Generic-rapper-talk ban list added (20 phrases including "the real ones", "for real for real", "drop a comment", "is something else"). |
| `post_vawn.py` `CTA_POOL` | Removed "drop a comment if you felt that"; 4/6 entries blank now (~67% empty CTA) |
| `video_agent.py:cinematic_video()` | Early-return guard |
| `lyric_annotation_agent.py:main()` | Early-return guard |
| `research/content_calendar.json` | 21 stale anchor_line entries cleared |
| `research/daily_brief.json` | 3 stale catalog_lines cleared |
| `catalogs/vawn-lyrics.md` | Archived banner added; flagged as not connected to live pipeline |

## What was right

The 2026-04-16 bulletproofing build (retry wrapper, signature detection, DLQ, watchdog) **did its job within the silent-failure constraint**. It caught the failure signature correctly, retried within each invocation, and would have escalated — except the dispatcher's exit-code logic short-circuited the escalation path. Once that was fixed, the existing alert pipeline + dead-letter writing + retry backoff all worked first try.

The new circuit breaker in `post_vawn.py` (added with backend_health.json check) also worked correctly during the outage: it refused to fire morning slots on 2026-04-28 once the probe flipped to degraded, conserving Suno tokens.

## What was wrong (process, not code)

- **Stale items repeated across reports.** DLQ-stale-9-days was flagged in 3 consecutive health reports between 2026-04-17 and 2026-04-26. Nothing in the org assigned ownership or a deadline. Same pattern for "daily briefings frozen at 04-14" (12 days unaddressed by close of incident) and "ideation pipeline silent since 04-19" (8 days unaddressed).
- **No outcome verification existed.** Heartbeat_runs counts "did the script run" not "did the work happen." No invariant said "if a posting slot fired, posted_log must reflect a successful platform."
- **Two source-of-truth lists for the same data.** `CTA_POOL` was hardcoded in `post_vawn.py` AND in `pipeline/config/content_rules.json:cta_rotation`. They drifted. The hardcoded one was actually used. Same DRY violation applied to humanizer rules (inlined as string literals in `captions.py`, also exists in JSON).
- **Bare-endpoint probes on POST endpoints.** Auth-only probes that never sent a body. Looked healthy because they returned 401. Real failures only appeared with body.
- **No incident postmortems.** Same class of bug (silent posting failures) hit the system multiple times. No prior postmortem captured the failure mode for future operators. **This document is the start of `journals/vawn/incidents/`.**
- **Trust drift on data sources.** Catalog data was loaded into JSON without anyone verifying the JSON matched the markdown reference. The trust chain "Vawn told me his lyrics" → "I wrote them in markdown" → "agent extracted to JSON" had a silent break between markdown and JSON.

## What to monitor going forward

If any of these alert, treat as a signal of regression toward this incident class:

- `posted_log_invariant.py` exits non-zero (now hourly via `Vawn\PostedLogInvariant` WTS task)
- `backend_health_probe.real_upload` flips to `fail`
- `paperclip_watchdog_notify` alert fires (Paperclip down >10 min)
- `dispatch_log.jsonl` shows `signature: not null` AND `success: true` on the same entry (paradox state — should be impossible after Bug A fix; if it appears, the fix has regressed)
- `cleanup_stale_issues.py` reports >50 stale issues during daily run (means the underlying Paperclip-platform "no PATCH on completion" issue is back)

## Open follow-ups

The cutover stopped the bleeding. Several deeper items remain:

- **Reseed a real Vawn lyrics catalog** if you want lyric cards / cinematic videos / lyric-anchored captions back. Would parse `catalogs/vawn-lyrics.md` into a clean `lyrics.json` with proper validation. Estimated 30 min if the markdown is canonical.
- **Fix the Paperclip platform issue-status leak.** Process-adapter agents never PATCH issues to `done` after run. The `cleanup_stale_issues.py` cron is a symptom-level fix; the structural fix is wiring each adapter (or the heartbeat layer) to PATCH on success/cancel. Owner: Paperclip codebase, separate workspace.
- **Pin Supabase SDK version in `apulustudio/requirements.txt`** to avoid future surprise regressions. Codex's httpx-direct fix sidesteps the issue but the rest of the SDK is still on `>=2.3.0` unpinned.
- **Storage retention policy** on the Supabase `media` bucket. Without a TTL or pruning job, it'll grow until the next quota event.
- **Sole-source-of-truth pass on content rules.** `pipeline/config/content_rules.json` should be the only source; `post_vawn.py:CTA_POOL` and `captions.py` humanizer-rules string literal should both load from it at runtime.
- **Carry-list with owners and ETAs.** Anything Aspyn flags in the weekly digest needs to either land in `journals/vawn/incidents/` (if it warrants an incident) or in a per-item ticket with assignee + deadline.

## Cross-references

- Health note that surfaced the diagnosis: `journals/vawn/health/2026-04-26-health.md`
- Aspyn's weekly digest: `research/vawn/ops-digest/2026-04-26-weekly-ops.md`
- Closed PR (duplicate of Codex's fix): https://github.com/iamclu1914/ApuluStudio/pull/3
- Shipped backend fix: `iamclu1914/ApuluStudio` commit `a1f4032`
- Infrastructure hub: [[../../wiki/infrastructure/_index]]
- Paperclip-operations hub: [[../../wiki/paperclip-operations/_index]]
- Archived catalog: [[../../catalogs/vawn-lyrics]]
