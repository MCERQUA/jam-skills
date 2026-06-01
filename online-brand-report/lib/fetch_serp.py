"""fetch_serp.py — Live SERP snapshots for 3 key queries."""

import sys
from urllib.parse import urlparse
from .config import dfs_post, dfs_get_items

def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).hostname or url
    except Exception:
        return url

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
            is_client = client_domain.lower().replace("www.", "") in dom.lower()
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
                if client_domain.lower().replace("www.", "") in dom.lower():
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
    cities_to_check = [city] + (extra_cities or [])[:2]

    for c in cities_to_check[:2]:
        q = f"{service} {c} {state}" if state else f"{service} {c}"
        queries.append((q, c, state))
    # Add a "near me" type query
    queries.append((f"{service} contractor near me", city, state))

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
