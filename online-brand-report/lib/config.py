"""config.py — credentials helper + shared constants for online-brand-report skill."""

import os
import base64
import sys

# ── Load .platform-keys.env if env vars not already set ──────────────────────
_KEYS_FILE = "/mnt/system/base/.platform-keys.env"

def _load_platform_keys():
    if not os.path.exists(_KEYS_FILE):
        return
    with open(_KEYS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val

_load_platform_keys()

# ── DataForSEO credentials ────────────────────────────────────────────────────
DATAFORSEO_LOGIN    = os.environ.get("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "")

def dfs_auth_header() -> str:
    raw = f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}"
    return "Basic " + base64.b64encode(raw.encode()).decode()

def dfs_post(endpoint: str, payload: list, timeout: int = 60, retries: int = 2) -> dict:
    """POST to DataForSEO v3 endpoint. Returns parsed JSON, or {} after exhausting retries.

    Retries on TRANSIENT failures (timeout / connection / 5xx) — the live endpoints
    (notably on_page/lighthouse and backlinks/summary) intermittently error at the HTTP
    layer, which previously made the Brand Health Score swing run-to-run (a flaky call
    dropped a whole dimension). Task-level errors (e.g. an unsubscribed endpoint returning
    HTTP 200 with an error status_code) are NOT retried — they're deterministic, so retrying
    would just add latency. (Hardened 2026-06-01.)
    """
    import requests
    import time
    url = f"https://api.dataforseo.com/v3/{endpoint}"
    headers = {
        "Authorization": dfs_auth_header(),
        "Content-Type": "application/json",
    }
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            r.raise_for_status()
            result = r.json()
            # Log cost if present
            cost = 0.0
            for task in result.get("tasks", []):
                cost += task.get("cost", 0) or 0
            if cost:
                print(f"[COST] {endpoint}: ${cost:.4f}", file=sys.stderr)
            return result
        except Exception as e:
            if attempt < retries:
                print(f"[RETRY {attempt + 1}/{retries}] dfs_post {endpoint}: {e}", file=sys.stderr)
                time.sleep(1.0 * (attempt + 1))   # 1s, 2s backoff
                continue
            print(f"[ERROR] dfs_post {endpoint}: {e}", file=sys.stderr)
            return {}
    return {}

def dfs_get_items(result: dict) -> list:
    """Extract items from a DataForSEO task result safely."""
    try:
        return result["tasks"][0]["result"][0]["items"] or []
    except (KeyError, IndexError, TypeError):
        return []

def dfs_get_result0(result: dict) -> dict:
    """Extract result[0] from a DataForSEO task result safely."""
    try:
        return result["tasks"][0]["result"][0] or {}
    except (KeyError, IndexError, TypeError):
        return {}

# ── Ahrefs DR API (free endpoint) ────────────────────────────────────────────
# Get a free key at docs.ahrefs.com — set AHREFS_API_KEY in .platform-keys.env
AHREFS_API_KEY = os.environ.get("AHREFS_API_KEY", "")

# ── Social Dashboard (cc-backlinks) ──────────────────────────────────────────
CC_BACKLINKS_URL = "http://172.17.0.1:6350/api/seo/cc-backlinks"
