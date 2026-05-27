"""fetch_content.py — Keyword suggestions + content gaps vs top competitor."""

import sys
from .config import dfs_post, dfs_get_items

def fetch_content(domain: str, service: str, location: str, top_competitor: str = "") -> dict:
    """Return content/keyword gap data. Never raises."""
    out = {
        "keyword_suggestions": [],  # list of {keyword, volume, difficulty, cpc}
        "content_gaps": [],         # list of {keyword, volume, competitor_pos}
        "kw_suggestions_count": 0,
        "gap_count": 0,
    }

    # --- Keyword Suggestions ---
    try:
        result = dfs_post("dataforseo_labs/google/keyword_suggestions/live", [
            {
                "keyword": service,
                "location_name": location,
                "language_name": "English",
                "limit": 30,
                "order_by": ["keyword_info.search_volume,desc"],
            }
        ])
        items = dfs_get_items(result)
        for item in items[:20]:
            kd = item.get("keyword_data") or item
            ki = kd.get("keyword_info") or {}
            out["keyword_suggestions"].append({
                "keyword": kd.get("keyword") or item.get("keyword", ""),
                "volume":     int(ki.get("search_volume") or 0),
                "difficulty": int((kd.get("keyword_properties") or {}).get("keyword_difficulty") or 0),
                "cpc":        round(float(ki.get("cpc") or 0), 2),
            })
        out["kw_suggestions_count"] = len(out["keyword_suggestions"])
    except Exception as e:
        print(f"[WARN] Keyword suggestions failed: {e}", file=sys.stderr)

    # --- Content Gaps (domain intersection with top competitor) ---
    if top_competitor:
        try:
            result = dfs_post("dataforseo_labs/google/domain_intersection/live", [
                {
                    "target1": domain,
                    "target2": top_competitor,
                    "location_name": location,
                    "language_name": "English",
                    "limit": 30,
                    "filters": [
                        ["ranked_serp_element.serp_item.rank_absolute", ">", 20],
                    ],
                    "order_by": ["keyword_data.keyword_info.search_volume,desc"],
                }
            ])
            items = dfs_get_items(result)
            for item in items[:15]:
                kd = item.get("keyword_data") or {}
                ki = kd.get("keyword_info") or {}
                # Find the competitor (target2) ranked position
                serp_data = item.get("ranked_serp_element") or {}
                si = serp_data.get("serp_item") or {}
                competitor_pos = int(si.get("rank_absolute") or 0)
                # Gap: competitor ranks in top 20, we rank > 20 (filtered above)
                out["content_gaps"].append({
                    "keyword":      kd.get("keyword", ""),
                    "volume":       int(ki.get("search_volume") or 0),
                    "competitor_pos": competitor_pos,
                })
            out["gap_count"] = len(out["content_gaps"])
        except Exception as e:
            print(f"[WARN] Domain intersection/gaps failed: {e}", file=sys.stderr)

    return out
