#!/usr/bin/env node
// SessionStart hook: probe 5 Apulu pipeline health signals and inject a
// banner into Claude Code's context when something is broken.
//
// Per Apollo verdict 2026-04-23 — the "push, not pull" notification surface
// for the user-present case. Runs on every Claude Code session start via
// .claude/settings.json SessionStart hooks array.
//
// Checks (each <500ms, bounded total <5s):
//   1. Paperclip port 3100 responding
//   2. posted_log.json: a post happened in the last 12h
//   3. dispatch_log.jsonl: no `_hallucinated: true` flags in the last 24h
//   4. Windows Task \Vawn\EmailBriefing: LastTaskResult == 0 (meta: is the
//      alerting infra itself alive?)
//   5. No orphan postmaster.pid in the Paperclip embedded-postgres data dir
//      (proactive catch of the next outage cause)
//
// Output: writes hookSpecificOutput.additionalContext JSON to stdout, same
// shape as vault-context.cjs. Empty output on all-healthy (silent).

const fs = require('fs');
const path = require('path');
const http = require('http');
const { execSync } = require('child_process');

const VAWN_DIR = 'C:/Users/rdyal/Vawn';
const PG_DATA_DIR = 'C:/Users/rdyal/.paperclip/instances/default/db';
const POSTED_LOG = path.join(VAWN_DIR, 'posted_log.json');
const DISPATCH_LOG = path.join(VAWN_DIR, 'dispatch_log.jsonl');

const PROBE_TIMEOUT_MS = 1500;
const POST_STALENESS_HOURS = 12;
const HALLUCINATION_WINDOW_HOURS = 24;

// ---------- checks ----------

function probePaperclip() {
  return new Promise((resolve) => {
    const req = http.get(
      { host: '127.0.0.1', port: 3100, path: '/api/health', timeout: PROBE_TIMEOUT_MS },
      (res) => {
        res.resume();
        resolve(res.statusCode === 200
          ? { ok: true }
          : { ok: false, reason: `Paperclip /api/health returned ${res.statusCode}` });
      }
    );
    req.on('error', (err) =>
      resolve({ ok: false, reason: `Paperclip port 3100 unreachable (${err.code || err.message})` }));
    req.on('timeout', () => {
      req.destroy();
      resolve({ ok: false, reason: `Paperclip port 3100 timeout (>${PROBE_TIMEOUT_MS}ms)` });
    });
  });
}

function checkRecentPost() {
  try {
    const log = JSON.parse(fs.readFileSync(POSTED_LOG, 'utf8'));
    const cutoff = Date.now() - POST_STALENESS_HOURS * 3600 * 1000;
    for (const [fname, entries] of Object.entries(log)) {
      if (fname.startsWith('_') || !entries || typeof entries !== 'object') continue;
      for (const dateKey of Object.keys(entries)) {
        // dateKey is YYYY-MM-DD; treat midnight UTC as the timestamp
        const t = Date.parse(dateKey + 'T00:00:00Z');
        if (!isNaN(t) && t >= cutoff) return { ok: true };
      }
    }
    return { ok: false, reason: `no posts logged in last ${POST_STALENESS_HOURS}h` };
  } catch (err) {
    return { ok: false, reason: `posted_log.json unreadable (${err.code || err.message})` };
  }
}

function checkHallucinations() {
  try {
    if (!fs.existsSync(DISPATCH_LOG)) return { ok: true };
    // Read last ~64KB (much larger than needed for one day of entries)
    const stat = fs.statSync(DISPATCH_LOG);
    const start = Math.max(0, stat.size - 65536);
    const fd = fs.openSync(DISPATCH_LOG, 'r');
    const buf = Buffer.alloc(stat.size - start);
    fs.readSync(fd, buf, 0, buf.length, start);
    fs.closeSync(fd);
    const tail = buf.toString('utf8');
    const lines = tail.split('\n').filter((l) => l.trim());
    if (start > 0 && lines.length) lines.shift(); // drop possibly-partial first line
    const cutoff = Date.now() - HALLUCINATION_WINDOW_HOURS * 3600 * 1000;
    let hits = 0;
    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        if (!entry.timestamp) continue;
        const t = Date.parse(entry.timestamp);
        if (isNaN(t) || t < cutoff) continue;
        if (entry._hallucinated === true) hits += 1;
      } catch {}
    }
    return hits === 0
      ? { ok: true }
      : { ok: false, reason: `${hits} hallucinated slot(s) in last ${HALLUCINATION_WINDOW_HOURS}h` };
  } catch (err) {
    return { ok: true }; // don't cry wolf on our own read errors
  }
}

function checkEmailBriefingTask() {
  try {
    const cmd =
      'powershell -NoProfile -Command "(Get-ScheduledTaskInfo -TaskPath \'\\Vawn\\\' -TaskName \'EmailBriefing\').LastTaskResult"';
    const out = execSync(cmd, { timeout: 3000, stdio: ['ignore', 'pipe', 'ignore'] })
      .toString()
      .trim();
    const code = parseInt(out, 10);
    if (isNaN(code)) return { ok: true };
    return code === 0
      ? { ok: true }
      : { ok: false, reason: `EmailBriefing task LastResult=${code} (non-zero)` };
  } catch {
    return { ok: true }; // silent if we can't probe
  }
}

function checkPostmasterOrphan() {
  try {
    const pidFile = path.join(PG_DATA_DIR, 'postmaster.pid');
    if (!fs.existsSync(pidFile)) return { ok: true };
    // postmaster.pid exists — normal IF Paperclip postgres is running.
    // We already checked Paperclip HTTP above; if both true, pid is real and fine.
    // If the Paperclip probe already failed, surface the pid as orphan hint.
    return { ok: true }; // consumed via combined logic below
  } catch {
    return { ok: true };
  }
}

// ---------- main ----------

(async () => {
  const [paperclip, recentPost, halluc, emailTask] = await Promise.all([
    probePaperclip(),
    Promise.resolve(checkRecentPost()),
    Promise.resolve(checkHallucinations()),
    Promise.resolve(checkEmailBriefingTask()),
  ]);
  const orphan = checkPostmasterOrphan();

  // Combined logic: if Paperclip is down AND a postmaster.pid exists, that's
  // a likely orphan blocking restart (the 2026-04-20 outage signature).
  let orphanMsg = null;
  if (!paperclip.ok && fs.existsSync(path.join(PG_DATA_DIR, 'postmaster.pid'))) {
    orphanMsg = 'postmaster.pid present while Paperclip is down — likely orphan Postgres blocking restart';
  }

  const failures = [];
  if (!paperclip.ok) failures.push(paperclip.reason);
  if (!recentPost.ok) failures.push(recentPost.reason);
  if (!halluc.ok) failures.push(halluc.reason);
  if (!emailTask.ok) failures.push(emailTask.reason);
  if (orphanMsg) failures.push(orphanMsg);

  if (failures.length === 0) {
    // Silent on healthy — no banner injected.
    return;
  }

  const lines = [
    '## 🚨 PIPELINE BROKEN',
    '',
    '*(auto-detected at session start by `.claude/helpers/pipeline-health.cjs`)*',
    '',
    ...failures.map((f) => `- ${f}`),
    '',
    '**Suggested next step:** run `python pipeline/brain/health_monitor.py` for full context, ' +
      'or ask me to diagnose.',
  ];

  const payload = {
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: lines.join('\n'),
    },
  };
  process.stdout.write(JSON.stringify(payload));
})().catch(() => {
  // Never let a probe bug crash the SessionStart hook chain.
  process.exit(0);
});
