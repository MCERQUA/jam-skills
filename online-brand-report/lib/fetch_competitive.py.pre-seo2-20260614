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
                # location_name/language_name removed: competitors_domain/live (Labs) rejects them →
                # 404. Labs endpoints take location_code/language_code or nothing (ica-voice 2026-06-01).
                "location_code": 2840,
                "language_code": "en",
                "limit": 25,
            }
        ])
        items = dfs_get_items(result)
        # Filter out the domain ITSELF + generic platforms/directories/social/video sites —
        # those aren't real local competitors (they rank for everything). Keep the first 5
        # genuine competitor domains. (Fixed 2026-06-01 — was showing self + youtube/yelp/angi.)
        _self = domain.lower().lstrip("www.")
        _BLOCK = (
            "youtube.com", "facebook.com", "instagram.com", "linkedin.com", "twitter.com",
            "x.com", "tiktok.com", "pinterest.com", "reddit.com", "yelp.com", "angi.com",
            "angieslist.com", "bbb.org", "homeadvisor.com", "thumbtack.com", "homeguide.com",
            "houzz.com", "nextdoor.com", "mapquest.com", "yellowpages.com", "manta.com",
            "homedepot.com", "lowes.com", "amazon.com", "wikipedia.org", "indeed.com",
            "glassdoor.com", "google.com", "apple.com", "bing.com", "porch.com", "buildzoom.com",
        )
        for item in items:
            dom = (item.get("domain") or "").lower().lstrip("www.")
            if not dom or dom == _self or dom in _BLOCK:
                continue
            competitors_raw.append({
                "domain": item.get("domain") or "",
                "keyword_count": int(item.get("avg_position") or 0),  # overwritten with traffic
                "intersections": int(item.get("intersections") or 0),
            })
            if len(competitors_raw) >= 5:
                break
    except Exception as e:
        print(f"[WARN] Competitors fetch failed: {e}", file=sys.stderr)

    # --- Bulk Traffic Estimation ---
    targets = [domain] + [c["domain"] for c in competitors_raw if c["domain"]]
    traffic_map = {}
    if targets:
        try:
            result = dfs_post("dataforseo_labs/google/bulk_traffic_estimation/live", [
                {"targets": targets[:10], "location_code": 2840, "language_code": "en"}
            ])
            items = dfs_get_items(result)
            for item in items:
                t = item.get("target") or ""
                # ETV lives at metrics.organic.etv (verified 2026-06-01) — the old flat
                # estimated_traffic_per_month/traffic fields don't exist → was always 0.
                m = item.get("metrics") or {}
                est = int((m.get("organic") or {}).get("etv") or 0)
                if not est:
                    est = int((m.get("paid") or {}).get("etv") or 0)
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
