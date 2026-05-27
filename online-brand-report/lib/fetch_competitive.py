"""fetch_competitive.py — Competitor domains, traffic estimates, keyword overlap."""

import sys
from .config import dfs_post, dfs_get_items, dfs_get_result0

def fetch_competitive(domain: str, location: str = "United States") -> dict:
    """Return competitor data. Never raises."""
    out = {
        "competitors": [],      # list of {domain, traffic_estimate, keyword_count, overlap_pct}
        "client_traffic": 0,    # estimated monthly visits
        "top_competitor": "",
        # For radar chart: normalized 0-100 values vs top competitor
        "radar_client": [0, 0, 0, 0, 0, 0],
        "radar_competitor": [100, 100, 100, 100, 100, 100],
        "radar_labels": ["Traffic", "Keywords", "Top-10 KW", "Backlinks", "Authority", "Pages"],
        "radar_comp_name": "",
    }

    competitors_raw = []

    # --- Competitors ---
    try:
        result = dfs_post("dataforseo_labs/google/competitors_domain/live", [
            {
                "target": domain,
                "location_name": location,
                "language_name": "English",
                "limit": 5,
            }
        ])
        items = dfs_get_items(result)
        for item in items[:5]:
            competitors_raw.append({
                "domain": item.get("domain") or "",
                "keyword_count": int(item.get("avg_position") or 0),  # we'll overwrite with traffic
                "intersections": int(item.get("intersections") or 0),
            })
    except Exception as e:
        print(f"[WARN] Competitors fetch failed: {e}", file=sys.stderr)

    # --- Bulk Traffic Estimation ---
    targets = [domain] + [c["domain"] for c in competitors_raw if c["domain"]]
    traffic_map = {}
    if targets:
        try:
            result = dfs_post("dataforseo_labs/google/bulk_traffic_estimation/live", [
                {"targets": targets[:10]}
            ])
            items = dfs_get_items(result)
            for item in items:
                t = item.get("target") or ""
                est = int(item.get("estimated_traffic_per_month") or item.get("traffic") or 0)
                traffic_map[t] = est
        except Exception as e:
            print(f"[WARN] Traffic estimation failed: {e}", file=sys.stderr)

    out["client_traffic"] = traffic_map.get(domain, 0)

    # Build competitors output list
    for c in competitors_raw:
        dom = c["domain"]
        traffic = traffic_map.get(dom, 0)
        out["competitors"].append({
            "domain": dom,
            "traffic_estimate": traffic,
            "keyword_count": c.get("intersections", 0),
            "overlap_pct": 0,
        })

    if out["competitors"]:
        out["top_competitor"] = out["competitors"][0]["domain"]
        out["radar_comp_name"] = out["top_competitor"]

        # Build radar: client vs top competitor (values relative to competitor max)
        top_traffic = max(1, out["competitors"][0]["traffic_estimate"])
        client_traffic = max(0, out["client_traffic"])
        top_kw   = max(1, out["competitors"][0]["keyword_count"])
        client_kw = 0  # filled in by orchestrator from organic data if available

        def _norm(val, max_val):
            return min(100, round((val / max_val) * 100, 1)) if max_val > 0 else 0

        out["radar_client"] = [
            _norm(client_traffic, top_traffic),
            0,   # keywords — filled in by orchestrator
            0,   # top-10 kw — filled in by orchestrator
            0,   # backlinks — filled in by orchestrator
            0,   # authority (DR) — filled in by orchestrator
            0,   # pages — filled in by orchestrator
        ]

    return out
