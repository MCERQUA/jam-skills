"""fetch_live_rankings.py — LIVE Google SERP rank check for a candidate keyword set.

WHY THIS EXISTS
---------------
`fetch_organic.py` reads DataForSEO **Labs** `ranked_keywords/live` — a periodic crawl
DB that UNDER-reports rankings for small / new / non-US domains. For printguys.ca
(Concord, ON) the Labs lookup returned just 1 ranked keyword, even though the business
genuinely ranks on Google's first page for several terms.

This module queries Google LIVE (serp/google/organic/live/advanced) for a candidate
keyword set RIGHT NOW and records where the domain ACTUALLY ranks, then `generate.py`
folds those into the existing `organic_data` so every section reflects the live truth.

Mirrors the call shape of `fetch_serp._serp_for_query`. Submits ONE keyword per
`dfs_post` (because `dfs_get_items` only returns tasks[0] — batching loses all but the
first). Never raises — every call is try/except wrapped.
"""

import sys
from urllib.parse import urlparse
from .config import dfs_post, dfs_get_items


# ── pill bucket — IDENTICAL to fetch_organic._pill ───────────────────────────
def _pill(pos: int) -> str:
    if pos <= 3:  return "ok"
    if pos <= 10: return "ok"
    if pos <= 20: return "warn"
    if pos <= 50: return "warn"
    return "bad"


def _norm(s) -> str:
    """Null-safe lowercase domain compare (mirrors fetch_serp._norm)."""
    return (s or "").lower().replace("www.", "")


def _domain_from_url(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).hostname or url or ""
    except Exception:
        return url or ""


def _url_path(url: str) -> str:
    try:
        return urlparse(url).path or "/"
    except Exception:
        return url or "/"


def _serp_loc(location_code: int, location_coordinate: str) -> dict:
    """Geo-target a SERP query: prefer the business's exact coordinate (real LOCAL
    results a nearby customer sees), else the country location_code. 'lat,lng' from
    the GMB/Places listing → far more accurate for local businesses than national."""
    if location_coordinate:
        return {"location_coordinate": location_coordinate}
    return {"location_code": location_code}


def _live_rank_for_keyword(keyword: str, client_domain: str,
                           location_code: int = 2840, depth: int = 20,
                           location_coordinate: str = "") -> dict | None:
    """Run ONE live Google SERP for `keyword`; return the BEST (lowest rank_absolute)
    organic result that belongs to `client_domain`, or None if the domain doesn't appear.

    Returns {"keyword", "position", "url"} (url = path) on a hit. Never raises."""
    try:
        result = dfs_post("serp/google/organic/live/advanced", [
            {
                "keyword": keyword,
                **_serp_loc(location_code, location_coordinate),
                "language_code": "en",
                "depth": depth,
            }
        ])
        items = dfs_get_items(result)
        cd = _norm(client_domain)
        best_pos = None
        best_url = ""
        for item in items:
            if item.get("type") != "organic":
                continue
            dom = _domain_from_url(item.get("url") or "")
            if not (cd and cd in _norm(dom)):
                continue
            pos = int(item.get("rank_absolute") or item.get("rank_group") or 0)
            if pos <= 0:
                continue
            if best_pos is None or pos < best_pos:
                best_pos = pos
                best_url = item.get("url") or ""
        if best_pos is None:
            return None
        return {
            "keyword": keyword,
            "position": best_pos,
            "url": _url_path(best_url),
        }
    except Exception as e:
        print(f"[WARN] Live SERP rank check for '{keyword}': {e}", file=sys.stderr)
        return None


def fetch_live_rankings(domain: str, candidates: list, location_code: int = 2840,
                        max_checks: int = 18, volumes: dict | None = None,
                        location_coordinate: str = "") -> dict:
    """Live-check `candidates` against Google and record where `domain` actually ranks.

    Loops candidate keywords (dedup case-insensitively, cap at `max_checks` to control
    cost), runs a live SERP per keyword, and records the BEST rank where the domain
    appears. Never raises.

    Returns:
        {
          "live_rankings": [{keyword, position, page, volume, url}, …]  (sorted by position asc),
          "live_ranked_count": N,
          "live_first_page_count": M,
          "checked": K,
        }
    `page = (position-1)//10 + 1`; `volume` looked up from `volumes` (keyed lowercased
    keyword) else 0.
    """
    volumes = volumes or {}

    # Dedup case-insensitively, preserve order, drop empties, cap to max_checks.
    seen = set()
    queue = []
    for kw in candidates or []:
        kw = (kw or "").strip()
        if not kw:
            continue
        low = kw.lower()
        if low in seen:
            continue
        seen.add(low)
        queue.append(kw)
        if len(queue) >= max_checks:
            break

    live_rankings = []
    checked = 0
    for kw in queue:
        checked += 1
        hit = _live_rank_for_keyword(kw, domain, location_code=location_code, depth=20,
                                     location_coordinate=location_coordinate)
        if not hit:
            continue
        pos = hit["position"]
        live_rankings.append({
            "keyword": hit["keyword"],
            "position": pos,
            "page": (pos - 1) // 10 + 1,
            "volume": int(volumes.get(hit["keyword"].lower(), 0) or 0),
            "url": hit["url"],
        })

    live_rankings.sort(key=lambda x: x["position"])
    first_page = sum(1 for r in live_rankings if r["position"] <= 10)

    return {
        "live_rankings": live_rankings,
        "live_ranked_count": len(live_rankings),
        "live_first_page_count": first_page,
        "checked": checked,
    }


# ── Merge / recompute helpers ────────────────────────────────────────────────

def _bucket_of(pos: int) -> str:
    if pos <= 3:    return "kw_top3"
    if pos <= 10:   return "kw_4_10"
    if pos <= 20:   return "kw_11_20"
    if pos <= 50:   return "kw_21_50"
    return "kw_51_100"


def merge_live_into_organic(organic_data: dict, live_rankings: list) -> dict:
    """Fold live rankings into organic_data, ADDITIVELY. The live check can only
    ADD coverage, never remove it.

    CRITICAL: fetch_organic's `kw_total` and the kw_* buckets count ALL ranked
    keywords (up to 1000), but `top_keywords` holds only the top-by-volume DISPLAY
    sample (~20). So we must NOT recompute totals from `top_keywords` — that would
    clobber an established domain's real total (foamit: 206 ranked → wrongly 22).
    Instead we INCREMENT the existing totals by the genuinely net-new live finds
    (keywords not already in the display set) and add them to the display table.

    Mutates and returns `organic_data`."""
    organic_data = organic_data or {}
    top_keywords = list(organic_data.get("top_keywords") or [])
    by_kw = {(r.get("keyword") or "").lower(): r for r in top_keywords}

    net_new = 0
    bucket_adds = {"kw_top3": 0, "kw_4_10": 0, "kw_11_20": 0, "kw_21_50": 0, "kw_51_100": 0}

    for lr in live_rankings or []:
        kw = lr.get("keyword", "")
        low = kw.lower()
        pos = int(lr.get("position") or 0)
        if pos <= 0 or not low:
            continue
        existing = by_kw.get(low)
        if existing:
            # Already shown → keep the BETTER position; do NOT bump totals (not net-new).
            old_pos = int(existing.get("position") or 0)
            if old_pos <= 0 or pos < old_pos:
                existing["position"] = pos
                existing["url"] = lr.get("url", "") or existing.get("url", "")
                existing["pill"] = _pill(pos)
                if not existing.get("volume"):
                    existing["volume"] = int(lr.get("volume") or 0)
        else:
            row = {"keyword": kw, "volume": int(lr.get("volume") or 0), "position": pos,
                   "url": lr.get("url", ""), "pill": _pill(pos), "live": True}
            top_keywords.append(row)
            by_kw[low] = row
            net_new += 1
            bucket_adds[_bucket_of(pos)] += 1

    # INCREMENT the real totals (never recompute-from-sample → never decrease).
    organic_data["kw_total"] = int(organic_data.get("kw_total") or 0) + net_new
    for b, add in bucket_adds.items():
        if add:
            organic_data[b] = int(organic_data.get(b) or 0) + add

    # Refresh the display table (top by volume, cap 20) + the top10 chart arrays.
    by_vol = sorted(top_keywords, key=lambda x: int(x.get("volume") or 0), reverse=True)
    organic_data["top_keywords"]     = by_vol[:20]
    organic_data["top10_kw_labels"]  = [(k.get("keyword") or "")[:40] for k in by_vol[:10]]
    organic_data["top10_kw_volumes"] = [int(k.get("volume") or 0) for k in by_vol[:10]]

    # Recompute the position-distribution bar widths from the (now-correct) totals.
    total = int(organic_data.get("kw_total") or 0)
    def _pct(n):
        return 0 if total == 0 else round(min(90, (int(n) / total) * 100), 1)
    organic_data["pos_bar_1_3_pct"]    = _pct(organic_data.get("kw_top3"))
    organic_data["pos_bar_4_10_pct"]   = _pct(organic_data.get("kw_4_10"))
    organic_data["pos_bar_11_20_pct"]  = _pct(organic_data.get("kw_11_20"))
    organic_data["pos_bar_21_50_pct"]  = _pct(organic_data.get("kw_21_50"))
    organic_data["pos_bar_51_100_pct"] = _pct(organic_data.get("kw_51_100"))
    return organic_data

    return organic_data
