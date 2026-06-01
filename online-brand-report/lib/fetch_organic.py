"""fetch_organic.py — Ranked keywords, position distribution, avg position."""

import sys
from urllib.parse import urlparse
from .config import dfs_post, dfs_get_items, dfs_get_result0

def _pill(pos: int) -> str:
    if pos <= 3:  return "ok"
    if pos <= 10: return "ok"
    if pos <= 20: return "warn"
    if pos <= 50: return "warn"
    return "bad"

def fetch_organic(domain: str, location: str = "United States") -> dict:
    """Return ranked keywords data. Never raises."""
    out = {
        "kw_total": 0,
        "kw_top3": 0,
        "kw_4_10": 0,
        "kw_11_20": 0,
        "kw_21_50": 0,
        "kw_51_100": 0,
        "avg_position": 0.0,
        "top_keywords": [],   # list of {keyword, volume, position, url, pill}
        "top10_kw_labels": [],
        "top10_kw_volumes": [],
        # Bar widths (%) for the position-distribution bar UI
        "pos_bar_1_3_pct": 0,
        "pos_bar_4_10_pct": 0,
        "pos_bar_11_20_pct": 0,
        "pos_bar_21_50_pct": 0,
        "pos_bar_51_100_pct": 0,
    }

    try:
        result = dfs_post("dataforseo_labs/google/ranked_keywords/live", [
            {
                "target": domain,
                # location_code/language_code (Labs rejects location_name/language_name) + a high
                # limit so we capture ALL ranked keywords (was truncating at 100; ICA has 280).
                # (Fixed skill-wide 2026-06-01.)
                "location_code": 2840,
                "language_code": "en",
                "limit": 1000,
                "order_by": ["keyword_data.keyword_info.search_volume,desc"],
            }
        ])
        items = dfs_get_items(result)
        if not items:
            return out

        top3 = top4_10 = top11_20 = top21_50 = top51_100 = 0
        positions = []
        top_kws = []

        for item in items:
            kd = item.get("keyword_data") or {}
            ki = kd.get("keyword_info") or {}
            se = item.get("ranked_serp_element") or {}
            si = se.get("serp_item") or {}

            kw_text = kd.get("keyword", "")
            vol     = int(ki.get("search_volume") or 0)
            pos     = int(si.get("rank_absolute") or si.get("rank_group") or 0)
            url     = si.get("url") or ""
            # Shorten URL to path
            try:
                url_path = urlparse(url).path or "/"
            except Exception:
                url_path = url

            if pos <= 0:
                continue
            positions.append(pos)

            if pos <= 3:    top3 += 1
            elif pos <= 10: top4_10 += 1
            elif pos <= 20: top11_20 += 1
            elif pos <= 50: top21_50 += 1
            else:           top51_100 += 1

            top_kws.append({
                "keyword": kw_text,
                "volume": vol,
                "position": pos,
                "url": url_path,
                "pill": _pill(pos),
            })

        total = len(positions)
        out["kw_total"]   = total
        out["kw_top3"]    = top3
        out["kw_4_10"]    = top4_10
        out["kw_11_20"]   = top11_20
        out["kw_21_50"]   = top21_50
        out["kw_51_100"]  = top51_100
        out["avg_position"] = round(sum(positions) / len(positions), 1) if positions else 0.0

        # Bar widths (capped at 90% for visual clarity)
        def _pct(n):
            if total == 0: return 0
            return round(min(90, (n / total) * 100), 1)
        out["pos_bar_1_3_pct"]    = _pct(top3)
        out["pos_bar_4_10_pct"]   = _pct(top4_10)
        out["pos_bar_11_20_pct"]  = _pct(top11_20)
        out["pos_bar_21_50_pct"]  = _pct(top21_50)
        out["pos_bar_51_100_pct"] = _pct(top51_100)

        # Top 10 by volume for chart
        by_vol = sorted(top_kws, key=lambda x: x["volume"], reverse=True)[:10]
        out["top_keywords"]   = top_kws[:20]  # table: top 20 by volume
        out["top10_kw_labels"] = [k["keyword"][:40] for k in by_vol]
        out["top10_kw_volumes"]= [k["volume"] for k in by_vol]

    except Exception as e:
        print(f"[WARN] Organic fetch failed: {e}", file=sys.stderr)

    return out
