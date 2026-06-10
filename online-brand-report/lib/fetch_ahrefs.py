"""fetch_ahrefs.py — Ahrefs Domain Rating (DR) lookups via the free DR API endpoint.

Ahrefs made their DR endpoint free in 2026. Requires a free API key from
docs.ahrefs.com. Set AHREFS_API_KEY in .platform-keys.env.

DR is a 0-100 logarithmic scale measuring domain authority based on the
quantity and quality of backlinks. More meaningful than DataForSEO's internal
rank metric for cross-domain authority comparison.
"""

import os
import sys
import time
import requests
from datetime import date
from .config import _load_platform_keys

_load_platform_keys()

AHREFS_API_KEY = os.environ.get("AHREFS_API_KEY", "")
AHREFS_BASE = "https://api.ahrefs.com/v3"
_cache: dict = {}  # domain → {"dr": float, "ahrefs_rank": int}


def _headers() -> dict:
    return {"Authorization": f"Bearer {AHREFS_API_KEY}"}


def fetch_domain_rating(domain: str) -> dict:
    """Return {"dr": float, "ahrefs_rank": int} for a domain, or zeros on failure.

    Results are cached within the process lifetime — safe to call per referring
    domain without hammering the rate limit.
    """
    if not AHREFS_API_KEY:
        return {"dr": 0, "ahrefs_rank": 0}

    # Normalize: strip scheme/path, keep bare domain
    clean = domain.lower().strip().rstrip("/")
    for prefix in ("https://", "http://", "www."):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    clean = clean.split("/")[0]

    if clean in _cache:
        return _cache[clean]

    result = {"dr": 0, "ahrefs_rank": 0}
    try:
        r = requests.get(
            f"{AHREFS_BASE}/site-explorer/domain-rating",
            headers=_headers(),
            params={"target": clean, "date": date.today().isoformat()},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            result["dr"] = float(data.get("domain_rating") or 0)
            result["ahrefs_rank"] = int(data.get("ahrefs_rank") or 0)
        elif r.status_code == 403:
            print("[WARN] Ahrefs DR: API key missing or invalid (403)", file=sys.stderr)
        elif r.status_code == 429:
            print("[WARN] Ahrefs DR: rate limit hit (429) — add sleep between calls", file=sys.stderr)
        else:
            print(f"[WARN] Ahrefs DR: {r.status_code} for {clean}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Ahrefs DR fetch failed for {clean}: {e}", file=sys.stderr)

    _cache[clean] = result
    return result


def enrich_domains_with_dr(domains: list[str], delay_s: float = 0.2) -> dict[str, dict]:
    """Fetch DR for a list of domains, rate-limited.

    Returns {domain: {"dr": float, "ahrefs_rank": int}}.
    delay_s: seconds between uncached calls (60 req/min limit → 1s safe, 0.2s moderate).
    """
    out = {}
    for domain in domains:
        result = fetch_domain_rating(domain)
        out[domain] = result
        # Only sleep for uncached / actually-fetched domains
        if domain.lower().strip() not in _cache or _cache.get(domain.lower().strip()) == result:
            time.sleep(delay_s)
    return out
