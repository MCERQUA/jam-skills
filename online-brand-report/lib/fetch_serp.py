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


_NAME_SUFFIXES = (" llc", " inc", " ltd", " corp", " co.", " company", " & co")

def _brand_tokens(domain: str, name: str) -> list:
    """Return lowercase strings; if ANY appears in a SERP result title → mark is_client.
    Catches branded social/directory listings (Facebook, Yelp, Instagram) that carry
    the client's name but not their domain."""
    tokens = []
    # Domain label: 'examplefoam' from examplefoam.com
    label = (domain or "").replace("www.", "").split(".")[0].lower()
    if label and len(label) > 2:
        tokens.append(label)
    # Cleaned business name (drop corporate suffixes)
    n = (name or "").lower()
    for sfx in _NAME_SUFFIXES:
        n = n.replace(sfx, "")
    n = n.strip(" ,.")
    if n and len(n) > 3:
        tokens.append(n)
    return tokens


def _serp_for_query(keyword: str, city: str, state: str, client_domain: str,
                    location_code: int = 2840, location_coordinate: str = "",
                    brand_tokens: list | None = None) -> dict:
    results = []
    try:
        # Geo-target: the business's exact coordinate (the real LOCAL SERP a nearby
        # customer sees) when we have it from the GMB/Places listing, else the country
        # location_code (keyword carries the city). City-level location_name was
        # rejected by DFS for abbreviated states → coordinate is the reliable local lever.
        _loc = {"location_coordinate": location_coordinate} if location_coordinate \
               else {"location_code": location_code}
        result = dfs_post("serp/google/organic/live/advanced", [
            {
                "keyword": keyword,
                **_loc,
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
            title_norm = _norm(title)
            is_client = (bool(cd) and cd in _norm(dom)) or \
                        any(t in title_norm for t in (brand_tokens or []))
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

def fetch_serp(domain: str, service: str, city: str, state: str, extra_cities: list | None = None,
               location_code: int = 2840, location_coordinate: str = "",
               name: str = "") -> dict:
    """Fetch SERP snapshots for 2-3 key queries. Never raises.

    location_code: DataForSEO country code (2840 US / 2124 CA).
    location_coordinate: 'lat,lng' from the GMB/Places listing → geo-targeted LOCAL SERP.
    name: Business name — used to highlight branded social/directory listings (Yelp, FB, etc.)."""
    queries = []
    btokens = _brand_tokens(domain, name)
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
        block = _serp_for_query(kw, c, s, domain, location_code, location_coordinate, btokens)
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
