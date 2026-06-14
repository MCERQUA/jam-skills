"""fetch_serp.py — Live SERP snapshots for 3 key queries."""

import sys
from urllib.parse import urlparse
from .config import dfs_post, dfs_get_items

def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).hostname or url or ""
    except Exception:
        return url or ""


def _norm(s) -> str:
    """Null-safe lowercase — a SERP item with no url/domain used to crash
    `dom.lower()` (NoneType has no attribute 'lower') and kill the whole SERP block."""
    return (s or "").lower().replace("www.", "")

def _serp_for_query(keyword: str, city: str, state: str, client_domain: str) -> dict:
    results = []
    try:
        # location_code 2840 (US) + language_code — the old "City,AZ,United States" location_name
        # (abbreviated state) was rejected → empty SERP tables. The keyword carries the city, so
        # US-level returns the correct local results. (Fixed skill-wide 2026-06-01.)
        result = dfs_post("serp/google/organic/live/advanced", [
            {
                "keyword": keyword,
                "location_code": 2840,
                "language_code": "en",
                "depth": 15,
            }
        ])
        items = dfs_get_items(result)
        client_found = False
        for item in items:
            if item.get("type") != "organic":
                continue
            pos    = int(item.get("rank_absolute") or 0)
            url    = item.get("url") or ""
            title  = item.get("title") or ""
            dom    = _domain_from_url(url)
            cd     = _norm(client_domain)
            is_client = bool(cd) and cd in _norm(dom)
            if is_client:
                client_found = True
            results.append({
                "position": pos,
                "domain": dom,
                "title": title[:80],
                "is_client": is_client,
            })
            if len(results) >= 15:
                break
        if not client_found:
            # Try to find client in deeper results
            for item in items:
                dom = _domain_from_url(item.get("url", ""))
                cd  = _norm(client_domain)
                if cd and cd in _norm(dom):
                    pos = int(item.get("rank_absolute") or 0)
                    results.append({
                        "position": pos,
                        "domain": dom,
                        "title": (item.get("title") or "")[:80],
                        "is_client": True,
                    })
                    break
    except Exception as e:
        print(f"[WARN] SERP fetch for '{keyword}': {e}", file=sys.stderr)

    return {
        "query": keyword,
        "city": city,
        "results": results,
    }

def fetch_serp(domain: str, service: str, city: str, state: str, extra_cities: list | None = None) -> dict:
    """Fetch SERP snapshots for 2-3 key queries. Never raises."""
    queries = []
    cities_to_check = [c for c in ([city] + (extra_cities or [])[:2]) if c]

    # service/industry may not be known yet (it's captured later in onboarding).
    # Fall back to the brand (domain label) so the query is a real search, never a
    # leading-space location-only string like " Toronto ON" that returns nothing.
    svc = (service or "").strip()
    brand = (domain or "").strip().replace("www.", "").split(".")[0]
    head = svc or brand or "business"

    def _q(*parts):
        return " ".join(p.strip() for p in parts if p and p.strip())

    for c in (cities_to_check or [""])[:2]:
        queries.append((_q(head, c, state), c, state))
    # A second-angle query: a "near me" service query when we know the service,
    # otherwise the brand name itself (a brand-SERP check).
    queries.append((_q(svc, "near me") if svc else _q(brand), city, state))

    serp_blocks = []
    for (kw, c, s) in queries[:3]:
        block = _serp_for_query(kw, c, s, domain)
        serp_blocks.append(block)

    # Identify top recurring competitor
    competitor_counts: dict[str, int] = {}
    for block in serp_blocks:
        for r in block["results"]:
            if not r["is_client"]:
                dom = r["domain"]
                competitor_counts[dom] = competitor_counts.get(dom, 0) + 1
    top_competitor = max(competitor_counts, key=competitor_counts.get) if competitor_counts else ""

    return {
        "serp_blocks": serp_blocks,
        "top_serp_competitor": top_competitor,
    }
