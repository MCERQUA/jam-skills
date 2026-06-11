"""fetch_ahrefs.py — Ahrefs Domain Rating (DR) lookups.

Primary path: uses the FREE public endpoint — no API key, no cost.
  GET https://api.ahrefs.com/v3/public/domain-rating-free?target={domain}&output=json
  Response: {"domain_rating": {"domain_rating": 91.0}}

Optional enrichment: if AHREFS_API_KEY is set in the environment, also calls the
richer paid endpoint (site-explorer/domain-rating) to populate ahrefs_rank.

DR is a 0-100 logarithmic scale measuring domain authority based on the quantity
and quality of backlinks. More meaningful than DataForSEO's internal rank metric
for cross-domain authority comparison.
"""

import os
import sys
import time
import requests
from .config import _load_platform_keys

_load_platform_keys()

AHREFS_API_KEY = os.environ.get("AHREFS_API_KEY", "")
AHREFS_BASE = "https://api.ahrefs.com/v3"
AHREFS_FREE_ENDPOINT = f"{AHREFS_BASE}/public/domain-rating-free"
_cache: dict = {}  # domain → {"dr": float, "ahrefs_rank": int}


def _normalize(domain: str) -> str:
    """Strip scheme/path/www, return bare domain."""
    clean = domain.lower().strip().rstrip("/")
    for prefix in ("https://", "http://", "www."):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    return clean.split("/")[0]


def fetch_domain_rating(domain: str) -> dict:
    """Return {"dr": float, "ahrefs_rank": int} for a domain, or zeros on failure.

    Uses the free public endpoint as the primary DR source (no auth required).
    If AHREFS_API_KEY is set, also fetches ahrefs_rank from the paid endpoint.

    Results are cached within the process lifetime — safe to call per referring
    domain without hammering the rate limit.
    """
    clean = _normalize(domain)

    if clean in _cache:
        return _cache[clean]

    result = {"dr": 0, "ahrefs_rank": 0}

    # --- Primary: free public endpoint (no auth, no cost) ---
    try:
        r = requests.get(
            AHREFS_FREE_ENDPOINT,
            params={"target": clean, "output": "json"},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            dr_block = data.get("domain_rating") or {}
            result["dr"] = float(dr_block.get("domain_rating") or 0)
        elif r.status_code == 429:
            print("[WARN] Ahrefs DR (free): rate limit hit (429)", file=sys.stderr)
        else:
            print(f"[WARN] Ahrefs DR (free): {r.status_code} for {clean}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Ahrefs DR (free) fetch failed for {clean}: {e}", file=sys.stderr)

    # --- Optional enrichment: paid endpoint for ahrefs_rank ---
    if AHREFS_API_KEY:
        try:
            from datetime import date
            r2 = requests.get(
                f"{AHREFS_BASE}/site-explorer/domain-rating",
                headers={"Authorization": f"Bearer {AHREFS_API_KEY}"},
                params={"target": clean, "date": date.today().isoformat()},
                timeout=10,
            )
            if r2.status_code == 200:
                data2 = r2.json()
                result["ahrefs_rank"] = int(data2.get("ahrefs_rank") or 0)
                # Prefer paid DR if free returned 0 (edge case)
                if result["dr"] == 0:
                    result["dr"] = float(data2.get("domain_rating") or 0)
            elif r2.status_code == 403:
                print("[WARN] Ahrefs DR (paid): API key missing or invalid (403)", file=sys.stderr)
            elif r2.status_code == 429:
                print("[WARN] Ahrefs DR (paid): rate limit hit (429)", file=sys.stderr)
        except Exception as e:
            print(f"[WARN] Ahrefs DR (paid) fetch failed for {clean}: {e}", file=sys.stderr)

    _cache[clean] = result
    return result


def enrich_domains_with_dr(domains: list[str], delay_s: float = 0.2) -> dict[str, dict]:
    """Fetch DR for a list of domains, rate-limited.

    Returns {domain: {"dr": float, "ahrefs_rank": int}}.
    delay_s: seconds between uncached calls (conservative default; free endpoint
    has no published hard limit but 0.2s is courteous).
    """
    out = {}
    for domain in domains:
        clean = _normalize(domain)
        already_cached = clean in _cache
        result = fetch_domain_rating(domain)
        out[domain] = result
        if not already_cached:
            time.sleep(delay_s)
    return out
