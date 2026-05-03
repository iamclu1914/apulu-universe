# Infrastructure Runbooks

Quick reference for common failure patterns. When an alert arrives, find the signature in the table, follow the steps.

## Table of contents
- [Claude auth expired](#claude-auth-expired) — 11 agents blocked
- [Apulu Studio backend degraded](#apulu-studio-backend-degraded)
- [Bluesky posts failing with auth error](#bluesky-posts-failing-with-auth-error)
- [Gmail SMTP rejected (alerts not delivering)](#gmail-smtp-rejected)
- [Agent stuck in status=error](#agent-stuck-in-statuserror)
- [Dispatch failed with `missing_cron_arg`](#dispatch-failed-with-missing_cron_arg)
- [Dead-letter queue accumulating](#dead-letter-queue-accumulating)
- [Paperclip itself isn't running](#paperclip-itself-isnt-running)

---

## Claude auth expired

**Signature:** `claude_auth_expired` — stderr contains `Not logged in · Please run /login`

**What's blocked:** All 11 `claude_local` agents (Rex, Camdyn, Cole, Oaklyn, Aspyn, Sable, Onyx, Nelly, Vibe, Echo, Cipher, Rhythm). Any Paperclip routine assigned to these agents will fail.

**How you'll hear about it:** First failing routine triggers an email within 15 min via `paperclip_run_monitor.py`. Subject: `⚠️ Paperclip run failures — <agent> (claude_auth_expired)`.

**Fix:**
```bash
claude /login
```
Follow the OAuth flow in your terminal. Once re-authenticated, the fleet self-recovers on the next scheduled run. Verify with:
```bash
claude auth status
python C:\Users\rdyal\Vawn\claude_auth_probe.py
```

**Prevent recurrence:** OAuth tokens expire periodically (weeks). There's no elegant preventive — rely on signature detection.

---

## Apulu Studio backend degraded

**Signature:** `apulu_backend_5xx` or `BackendHealthProbe` alerts

**What's blocked:** Any slot touching Apulu Studio endpoints. X + Bluesky upload (`/api/posts/upload`). Instagram may still work via `/api/posts/{id}/publish`.

**First response:**
1. Read `C:\Users\rdyal\Vawn\backend_health.json` for the exact endpoints failing
2. `curl -s -o /dev/null -w "%{http_code}\n" https://apulustudio.onrender.com/` — is the root up?
3. If root is 200 but `/api/*` fails: backend handler bug. Check Render logs.
4. If everything fails: Render free-tier cold start or outright outage.

**Tool:**
```bash
python C:\Users\rdyal\Vawn\backend_health_probe.py  # Force-refresh
```

**Circuit breaker behavior:** While the backend is `degraded`, `post_vawn.py` exits 3 before generating Suno content. This saves tokens. Posts for affected platforms are lost for that slot but retry on the next one.

**Long-term fix:** Repo at github.com/iamclu1914/ApuluStudio. Common issues:
- Environment variable missing on Render after redeploy
- Storage backend (S3/Cloudinary) credentials expired
- Python dependency conflict after package update

---

## Bluesky posts failing with auth error

**Signature:** `bluesky_auth` — stderr contains "AuthenticationRequired" or "invalid creds"

**What's blocked:** Only Bluesky. X, IG, TikTok, Threads unaffected.

**Cause:** Bluesky app password in `C:\Users\rdyal\Vawn\credentials.json` is wrong or expired. The password format is **19 chars with hyphens** (e.g. `t3t4-aa2h-gzyl-364w`) — NOT the account password.

**Fix:**
1. Log in to bsky.app → Settings → Privacy and Security → App Passwords
2. Generate new password named "Apulu Records"
3. Edit `C:\Users\rdyal\Vawn\credentials.json`:
   ```json
   "bluesky_app_password": "xxxx-xxxx-xxxx-xxxx"
   ```
4. Test:
   ```bash
   python -c "from atproto import Client; c=Client(); print(c.login('therealvawn.bsky.social','<password>').handle)"
   ```

---

## Gmail SMTP rejected

**Signature:** `[ERR] Email failed: (535, b'5.7.8 Username and Password not accepted')` in any script's output. Also visible as growing `alert_fallback.jsonl`.

**What's blocked:** All alert emails. The failure is silent at the SMTP layer, so **the whole monitoring stack is flying blind** until this is fixed. Alerts accumulate in `alert_fallback.jsonl`.

**Cause:** Google revoked the app password, or the account password was changed (which invalidates all app passwords).

**Fix:**
1. Go to https://myaccount.google.com/apppasswords (signed in as `clu@apuluthegod.com`)
2. Generate new password named "Apulu Records" — copy the 16-char string, remove spaces
3. Either update `C:\Users\rdyal\Vawn\email_notify.py` line 22:
   ```python
   GMAIL_APP_PASSWORD = os.environ.get("APULU_GMAIL_APP_PASSWORD", "<new 16-char>")
   ```
   Or set env var `APULU_GMAIL_APP_PASSWORD` globally (code reads env first).
4. Test:
   ```bash
   cd C:\Users\rdyal\Vawn
   python -c "from email_notify import send_notification; print(send_notification('Test','<p>ok</p>'))"
   ```
5. Flush the queued alerts:
   ```bash
   python flush_alerts.py --clear-delivered
   ```

---

## Agent stuck in status=error

**Signature:** `PaperclipRunMonitor` alert with subject `🚨 Stuck agents (N) — not accepting issues`.

**What's blocked:** That specific agent won't pick up new issues until reset.

**Diagnose:** The alert email includes the agent name and how long it's been stuck. Check recent failures for that agent:
```bash
python C:\Users\rdyal\Vawn\paperclip_run_monitor.py --dry-run --window 240
```

**Fix root cause first**, then reset. Common causes:
- The underlying script has a bug or missing dep — fix the script
- Adapter config is wrong — fix the config (consider running `validate_adapters.py`)
- External service (Claude auth, Apulu Studio, etc.) is down — fix that

**Reset the agent** (only after root cause is addressed):
```bash
cd "C:/Users/rdyal/Apulu Universe/paperclip"
node -e "const{Client}=require('./node_modules/.pnpm/pg@8.18.0/node_modules/pg');const c=new Client({host:'127.0.0.1',port:54329,user:'paperclip',password:'paperclip',database:'paperclip'});c.connect().then(async()=>{const r=await c.query(\"UPDATE agents SET status='idle' WHERE name='<agent_name>' AND status='error' RETURNING name\");console.log(r.rows);await c.end()})"
```

**Do NOT auto-reset error-state agents** without fixing root cause — that masks real bugs.

---

## Dispatch failed with `missing_cron_arg`

**Signature:** stderr contains `required: --cron`. Alert subject: `🚨 Dispatch failed — <slot> (missing_cron_arg)`.

**Cause:** An agent's `adapter_config` invokes `post_vawn.py` directly without passing `--cron`. `post_vawn.py` requires `--cron morning|midday|evening`.

**Fix:** The adapter should invoke `marketing_dispatch.py`, NOT `post_vawn.py`:
```json
{
  "command": "cmd.exe",
  "args": ["/c", "python", "C:/Users/rdyal/Vawn/marketing_dispatch.py"],
  "cwd": "C:/Users/rdyal/Vawn"
}
```

`marketing_dispatch.py` reads the Paperclip issue title, looks up the slot in `DISPATCH_TABLE`, and invokes `post_vawn.py` with the correct args via the retry wrapper.

**Prevent recurrence:** `ValidateAdapters` WTS task (daily 5:45am) catches this class of bug before the 6am routines fire.

---

## Dead-letter queue accumulating

**Signature:** `STATUS.md` shows "N entries in dead-letter queue" or `dead_letter.jsonl` has more entries than yesterday.

**What it means:** Dispatches exhausted their retries (3 attempts with backoff) and couldn't recover. These are genuine failures, not transient.

**Inspect:**
```bash
python C:\Users\rdyal\Vawn\dlq.py list
python C:\Users\rdyal\Vawn\dlq.py stats              # Group by slot/signature
python C:\Users\rdyal\Vawn\dlq.py show <id>          # Full detail
```

**Replay a failed dispatch:**
```bash
python C:\Users\rdyal\Vawn\dlq.py replay <id>
```
Replay respects slot-locks by default (won't re-post if already shipped). Use `--force` to bypass.

**Clear after manual fix:**
```bash
python C:\Users\rdyal\Vawn\dlq.py clear <id>
python C:\Users\rdyal\Vawn\dlq.py clear --delivered          # Remove replayed
python C:\Users\rdyal\Vawn\dlq.py clear --all-older-than 30  # Bulk old cleanup
```

---

## Paperclip itself isn't running

**Signature:** `STATUS.md` fails to regenerate, or all WTS tasks start showing DB connection errors.

**Test:**
```bash
curl -s http://localhost:3100/api/companies -H "Accept: application/json" | head -c 200
```

**Start Paperclip:**
```bash
cd "C:/Users/rdyal/Apulu Universe/paperclip"
pnpm dev
```

Or re-run the `Paperclip` WTS task (it runs `pnpm dev` on a keepalive).

**Check Postgres separately:**
```bash
Get-Process postgres
```

Paperclip uses embedded Postgres on port 54329. If postgres isn't running, Paperclip can't start.

---

## Watchdog loop: "Paperclip unresponsive — launching via hidden starter"

**Signature:** Watchdog log repeats every 5 minutes with `Paperclip unresponsive — launching via hidden starter`, but service never comes back.

**What it means:** The auto-restart path is firing, but Paperclip is failing during startup (most commonly embedded Postgres never binds `54329`, or port `3100` is occupied by a stale process).

**Recovery (Windows):**
```powershell
# 1) Stop stale node/postgres processes
taskkill /F /IM node.exe
taskkill /F /IM postgres.exe

# 2) Verify port 3100 is free (kill reported PID if needed)
netstat -ano | findstr :3100

# 3) Remove stale Paperclip instance state
rmdir /S /Q "%USERPROFILE%\.paperclip-data\instances"

# 4) Start Paperclip from repo root helper
cd "C:\Users\rdyal\Apulu Universe"
start-paperclip.bat
```

**Fast health checks after restart:**
```powershell
curl -s http://localhost:3100/api/companies -H "Accept: application/json"
netstat -ano | findstr :54329
```

If the API is still down after one clean restart, inspect Paperclip startup logs first (before more watchdog cycles) to avoid repeated hidden-start retries masking the root error.
