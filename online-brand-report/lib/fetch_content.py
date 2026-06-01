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
                "location_code": 2840,
                "language_code": "en",
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
                    "location_code": 2840,
                    "language_code": "en",
                    "limit": 100,
                    "order_by": ["keyword_data.keyword_info.search_volume,desc"],
                }
            ])
            items = dfs_get_items(result)
            # domain_intersection returns first_domain_serp_element (target1 = us) +
            # second_domain_serp_element (target2 = competitor). A content GAP = competitor
            # outranks us. The old code read ranked_serp_element.serp_item (wrong path) + an
            # invalid API filter → always empty. Filter in Python instead. (Fixed 2026-06-01.)
            for item in items:
                kd = item.get("keyword_data") or {}
                ki = kd.get("keyword_info") or {}
                our_pos  = int((item.get("first_domain_serp_element") or {}).get("rank_absolute") or 0)
                comp_pos = int((item.get("second_domain_serp_element") or {}).get("rank_absolute") or 0)
                if not comp_pos:
                    continue
                # gap: competitor ranks, and either we don't rank or we rank worse than them
                if our_pos == 0 or comp_pos < our_pos:
                    out["content_gaps"].append({
                        "keyword":        kd.get("keyword", ""),
                        "volume":         int(ki.get("search_volume") or 0),
                        "competitor_pos": comp_pos,
                        "your_pos":       our_pos or None,
                    })
                if len(out["content_gaps"]) >= 15:
                    break
            out["gap_count"] = len(out["content_gaps"])
        except Exception as e:
            print(f"[WARN] Domain intersection/gaps failed: {e}", file=sys.stderr)

    return out
