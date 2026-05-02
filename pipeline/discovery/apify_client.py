"""
apify_client.py -- Thin wrapper around Apify API for running actors and fetching results.
No dependencies beyond requests.
"""

import os
import time
from datetime import date

import requests


APIFY_BASE = "https://api.apify.com/v2"

# Defaults overridable by env. Threshold is the % of monthly cap at which we
# refuse to start new actors so we never hard-stop discovery mid-run.
DEFAULT_MONTHLY_CAP_THRESHOLD_PCT = 85.0
DEFAULT_DAILY_BUDGET_USD = 7.0
# Pre-flight result is cached in-process for this many seconds so we don't
# hammer /users/me on every actor run inside one pipeline.
BUDGET_PREFLIGHT_TTL_SECONDS = 300


class ApifyBillingExhaustedError(RuntimeError):
    """Raised when Apify rejects calls with platform-feature-disabled (monthly cap hit).

    This is account-wide: when raised, every paid actor will fail until the cap
    is raised in the Apify console or the monthly cycle resets. Callers should
    short-circuit remaining Apify-backed work rather than retry.
    """


class ApifyBudgetNearCapError(ApifyBillingExhaustedError):
    """Raised pre-flight when monthly Apify usage is at/past the cap threshold.

    Subclass of ApifyBillingExhaustedError so existing skip-the-rest handlers
    in run_all.py still treat this as a hard short-circuit, but a separate
    type lets callers distinguish a self-imposed brake from an Apify-side
    refusal.
    """


class ApifyDailyBudgetExceededError(ApifyBillingExhaustedError):
    """Raised pre-flight when today's Apify spend has reached APIFY_DAILY_BUDGET_USD.

    Lets us cap daily burn before the monthly cap is even close, so a runaway
    actor or a flood of metrics pulls can't burn the budget in one bad day.
    """


class ApifyRunner:
    """Run Apify actors and retrieve results."""

    # Class-level cache so multiple ApifyRunner instances within one process
    # share a single budget snapshot. Keyed by token so multi-tenant isn't
    # cross-contaminated.
    _budget_cache: dict = {}

    def __init__(self, token):
        self.token = token
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    @staticmethod
    def _maybe_raise_billing_exhausted(resp):
        """Inspect a response for Apify's billing-cap signature and raise typed error."""
        if resp.status_code != 403:
            return
        try:
            err = (resp.json() or {}).get("error") or {}
        except ValueError:
            return
        if err.get("type") == "platform-feature-disabled" and "usage" in (err.get("message") or "").lower():
            raise ApifyBillingExhaustedError(err.get("message") or "Apify monthly usage limit hit")

    @staticmethod
    def _normalize_actor_id(actor_id):
        """Convert 'user/actor' to 'user~actor' for API URLs."""
        return actor_id.replace("/", "~")

    # ── Pre-flight budget check ─────────────────────────────────────────────

    def preflight_budget_check(self, force=False):
        """Block actor runs if we're over the monthly cap threshold or daily budget.

        Cached in-process for BUDGET_PREFLIGHT_TTL_SECONDS so we don't hammer
        /users/me on every actor invocation. If the budget API itself fails,
        we fail open (log a warning, return None) — apify_budget_monitor will
        catch monitor-side outages out-of-band.

        Returns the snapshot dict on success, None on monitor-fetch failure.
        Raises ApifyBudgetNearCapError or ApifyDailyBudgetExceededError if
        thresholds are breached.
        """
        now = time.time()
        cached = ApifyRunner._budget_cache.get(self.token)
        if cached and not force and (now - cached["ts"]) < BUDGET_PREFLIGHT_TTL_SECONDS:
            self._raise_if_over_budget(cached["snapshot"])
            return cached["snapshot"]

        snapshot = self._fetch_budget_snapshot()
        if snapshot is None:
            return None  # fail open
        ApifyRunner._budget_cache[self.token] = {"ts": now, "snapshot": snapshot}
        self._raise_if_over_budget(snapshot)
        return snapshot

    def _fetch_budget_snapshot(self):
        """GET /users/me/limits + /users/me/usage/monthly. Returns dict or None."""
        try:
            limits_resp = self.session.get(f"{APIFY_BASE}/users/me/limits", timeout=15)
            limits_resp.raise_for_status()
            ldata = (limits_resp.json() or {}).get("data") or {}
            usage_resp = self.session.get(f"{APIFY_BASE}/users/me/usage/monthly", timeout=15)
            usage_resp.raise_for_status()
            udata = (usage_resp.json() or {}).get("data") or {}
        except Exception as e:
            print(f"  [Apify] Budget pre-flight fetch failed (failing open): {e}")
            return None

        # Both endpoints expose monthly usage — prefer the explicit current.* path
        # from /limits when available, otherwise fall back to /usage/monthly.
        monthly_used = float(
            (ldata.get("current") or {}).get("monthlyUsageUsd")
            or udata.get("monthlyUsageUsd")
            or 0.0
        )
        monthly_cap = float(
            (ldata.get("limits") or {}).get("maxMonthlyUsageUsd")
            or (ldata.get("limits") or {}).get("monthlyUsageHardLimitUsd")
            or 0.0
        )

        today = date.today().isoformat()
        daily_used = 0.0
        for entry in (udata.get("dailyServiceUsages") or []):
            entry_date = str(entry.get("date") or "")[:10]
            if entry_date == today:
                daily_used = float(entry.get("totalUsageCreditsUsd") or 0.0)
                break

        return {
            "monthly_used": monthly_used,
            "monthly_cap": monthly_cap,
            "daily_used": daily_used,
            "today": today,
        }

    @staticmethod
    def _raise_if_over_budget(snapshot):
        threshold_pct = float(
            os.environ.get(
                "APIFY_MONTHLY_CAP_THRESHOLD_PCT",
                DEFAULT_MONTHLY_CAP_THRESHOLD_PCT,
            )
        ) / 100.0
        daily_budget = float(
            os.environ.get("APIFY_DAILY_BUDGET_USD", DEFAULT_DAILY_BUDGET_USD)
        )

        monthly_used = snapshot.get("monthly_used") or 0.0
        monthly_cap = snapshot.get("monthly_cap") or 0.0
        daily_used = snapshot.get("daily_used") or 0.0

        if monthly_cap > 0 and (monthly_used / monthly_cap) >= threshold_pct:
            pct = (monthly_used / monthly_cap) * 100.0
            raise ApifyBudgetNearCapError(
                f"Monthly Apify usage at {pct:.1f}% of cap "
                f"(${monthly_used:.2f} / ${monthly_cap:.2f}; "
                f"threshold {threshold_pct * 100:.0f}%). "
                f"Raise cap in Apify console or wait for cycle reset."
            )

        if daily_budget > 0 and daily_used >= daily_budget:
            raise ApifyDailyBudgetExceededError(
                f"Daily Apify spend ${daily_used:.4f} for {snapshot.get('today','today')} "
                f"meets/exceeds budget ${daily_budget:.2f} "
                f"(env APIFY_DAILY_BUDGET_USD)."
            )

    # ── Actor runner ────────────────────────────────────────────────────────

    def run_actor(self, actor_id, input_data, timeout=300, memory_mb=256, retries=1):
        """Start an actor run and wait for it to finish.

        Args:
            actor_id: Actor ID like "apidojo/tweet-scraper"
            input_data: Dict of input parameters for the actor
            timeout: Max seconds to wait (default 300)
            memory_mb: Memory allocation in MB (default 256)
            retries: Number of retry attempts on failure (default 1)

        Returns:
            List of result items from the default dataset.
        """
        # Pre-flight: if over budget we raise BEFORE billing the call. The
        # raised error subclasses ApifyBillingExhaustedError so existing
        # short-circuit logic in run_all.py still applies.
        self.preflight_budget_check()

        last_error = None
        for attempt in range(retries + 1):
            try:
                return self._run_actor_once(actor_id, input_data, timeout, memory_mb)
            except ApifyBillingExhaustedError:
                raise
            except Exception as e:
                last_error = e
                if attempt < retries:
                    print(f"  [Apify] {actor_id} failed (attempt {attempt+1}), retrying in 60s...")
                    time.sleep(60)
        raise last_error

    def _run_actor_once(self, actor_id, input_data, timeout, memory_mb):
        """Single attempt to run an actor."""
        slug = self._normalize_actor_id(actor_id)
        url = f"{APIFY_BASE}/acts/{slug}/runs"
        resp = self.session.post(
            url,
            json=input_data,
            params={"timeout": timeout, "memory": memory_mb},
        )
        self._maybe_raise_billing_exhausted(resp)
        resp.raise_for_status()
        run_data = resp.json()["data"]
        run_id = run_data["id"]
        print(f"  [Apify] Started {actor_id} (run: {run_id[:8]}...)")

        # Poll until finished
        start = time.time()
        while time.time() - start < timeout:
            status_url = f"{APIFY_BASE}/actor-runs/{run_id}"
            status_resp = self.session.get(status_url)
            status_resp.raise_for_status()
            status = status_resp.json()["data"]["status"]

            if status == "SUCCEEDED":
                break
            elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
                raise RuntimeError(f"Actor run {status}: {actor_id}")

            time.sleep(5)
        else:
            raise TimeoutError(f"Actor run timed out after {timeout}s: {actor_id}")

        # Fetch results from default dataset
        dataset_id = run_data["defaultDatasetId"]
        items_url = f"{APIFY_BASE}/datasets/{dataset_id}/items"
        items_resp = self.session.get(items_url, params={"format": "json"})
        items_resp.raise_for_status()
        items = items_resp.json()

        print(f"  [Apify] Got {len(items)} items from {actor_id}")
        return items

    def run_actor_sync(self, actor_id, input_data, timeout=300):
        """Run actor synchronously (waits for result in one call).

        Uses the synchronous run endpoint -- simpler but limited to 300s.
        """
        self.preflight_budget_check()

        slug = self._normalize_actor_id(actor_id)
        url = f"{APIFY_BASE}/acts/{slug}/run-sync-get-dataset-items"
        resp = self.session.post(
            url,
            json=input_data,
            params={"timeout": timeout},
            timeout=timeout + 30,
        )
        self._maybe_raise_billing_exhausted(resp)
        resp.raise_for_status()
        items = resp.json()
        print(f"  [Apify] Got {len(items)} items from {actor_id}")
        return items
