"""
apify_client.py -- Thin wrapper around Apify API for running actors and fetching results.
No dependencies beyond requests.
"""

import time
import requests


APIFY_BASE = "https://api.apify.com/v2"


class ApifyRunner:
    """Run Apify actors and retrieve results."""

    def __init__(self, token):
        self.token = token
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    @staticmethod
    def _normalize_actor_id(actor_id):
        """Convert 'user/actor' to 'user~actor' for API URLs."""
        return actor_id.replace("/", "~")

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
        last_error = None
        for attempt in range(retries + 1):
            try:
                return self._run_actor_once(actor_id, input_data, timeout, memory_mb)
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
        slug = self._normalize_actor_id(actor_id)
        url = f"{APIFY_BASE}/acts/{slug}/run-sync-get-dataset-items"
        resp = self.session.post(
            url,
            json=input_data,
            params={"timeout": timeout},
            timeout=timeout + 30,
        )
        resp.raise_for_status()
        items = resp.json()
        print(f"  [Apify] Got {len(items)} items from {actor_id}")
        return items
