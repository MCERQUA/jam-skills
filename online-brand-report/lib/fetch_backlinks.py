"""fetch_backlinks.py — Backlink summary, referring domains, anchor text."""

import sys
import requests
from .config import dfs_post, dfs_get_result0, dfs_get_items, CC_BACKLINKS_URL

def fetch_backlinks(domain: str) -> dict:
    """Return backlink data. Never raises."""
    out = {
        "domain_rank": 0,
        "backlinks_total": 0,
        "referring_domains_total": 0,
        "dofollow_count": 0,
        "nofollow_count": 0,
        "top_referring_domains": [],  # list of {domain, rank, backlinks}
        "anchor_text_dist": {         # for doughnut chart
            "labels": ["Branded", "Exact match", "Partial", "Generic", "Naked URL"],
            "data": [0, 0, 0, 0, 0],
        },
        "dofollow_pct": 0,
        # Availability flag for scoring: True only when the summary CALL succeeded (even if the
        # site genuinely has 0 backlinks — a real 0 must score low, not be excluded). Inferring
        # availability from value>0 made the Brand Health Score swing run-to-run. (Fixed 2026-06-01.)
        "_backlinks_available": False,
    }

    # --- DataForSEO Backlinks Summary ---
    try:
        result = dfs_post("backlinks/summary/live", [
            {"target": domain, "backlinks_status_type": "live"}
        ])
        r0 = dfs_get_result0(result)
        if r0:
            out["_backlinks_available"]  = True   # endpoint responded — data is real (incl. real zeros)
            out["domain_rank"]           = int(r0.get("rank") or 0)
            out["backlinks_total"]       = int(r0.get("backlinks") or 0)
            out["referring_domains_total"]= int(r0.get("referring_domains") or 0)
            out["dofollow_count"]        = int(r0.get("dofollow") or 0)
            out["nofollow_count"]        = int(r0.get("referring_links_types", {}).get("nofollow") or 0)
            total = max(1, out["backlinks_total"])
            out["dofollow_pct"] = round(out["dofollow_count"] / total * 100, 1)
    except Exception as e:
        print(f"[WARN] Backlinks summary failed: {e}", file=sys.stderr)

    # --- Referring Domains ---
    try:
        result = dfs_post("backlinks/referring_domains/live", [
            {
                "target": domain,
                "backlinks_status_type": "live",
                "limit": 20,
                "order_by": ["rank,desc"],
            }
        ])
        items = dfs_get_items(result)
        for item in items[:10]:
            out["top_referring_domains"].append({
                "domain": item.get("domain") or "",
                "rank": int(item.get("rank") or 0),
                "backlinks": int(item.get("backlinks") or 1),
            })
    except Exception as e:
        print(f"[WARN] Referring domains fetch failed: {e}", file=sys.stderr)

    # --- Anchor Text Distribution ---
    try:
        result = dfs_post("backlinks/anchors/live", [
            {"target": domain, "backlinks_status_type": "live", "limit": 100}
        ])
        items = dfs_get_items(result)
        branded = exact = partial = generic = naked = 0
        for item in items:
            anchor = (item.get("anchor") or "").lower().strip()
            cnt    = int(item.get("backlinks") or 1)
            if not anchor or anchor in ("click here", "here", "read more", "website", "link", ""):
                generic += cnt
            elif domain.lower().replace("www.", "").split(".")[0] in anchor:
                branded += cnt
            elif anchor.startswith("http") or anchor.startswith("www."):
                naked += cnt
            elif len(anchor.split()) <= 3:
                exact += cnt
            else:
                partial += cnt
        total_anchors = max(1, branded + exact + partial + generic + naked)
        out["anchor_text_dist"] = {
            "labels": ["Branded", "Exact match", "Partial", "Generic", "Naked URL"],
            "data": [branded, exact, partial, generic, naked],
        }
    except Exception as e:
        print(f"[WARN] Anchor text fetch failed: {e}", file=sys.stderr)

    # --- CC-Backlinks Supplement ---
    try:
        r = requests.get(CC_BACKLINKS_URL, params={"domain": domain, "limit": 50}, timeout=10)
        if r.status_code == 200:
            cc_data = r.json()
            cc_links = cc_data.get("backlinks") or []
            if cc_links and out["backlinks_total"] == 0:
                out["backlinks_total"] = len(cc_links)
            # Merge referring domains if not already fetched
            if not out["top_referring_domains"]:
                seen = set()
                for lnk in cc_links[:10]:
                    d = lnk.get("source_domain") or lnk.get("domain") or ""
                    if d and d not in seen:
                        seen.add(d)
                        out["top_referring_domains"].append({"domain": d, "rank": 0, "backlinks": 1})
    except Exception as e:
        print(f"[INFO] CC-backlinks supplement skipped: {e}", file=sys.stderr)

    return out
