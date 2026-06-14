"""fetch_backlinks.py — Backlink summary, referring domains, anchor text, growth history."""

import sys
import requests
from datetime import date, timedelta
from .config import dfs_post, dfs_get_result0, dfs_get_items, CC_BACKLINKS_URL
from .fetch_ahrefs import fetch_domain_rating, enrich_domains_with_dr

def _fetch_bl_history(domain: str) -> dict:
    """Fetch 12-month backlink + referring-domain timeseries from DataForSEO. Never raises.

    Calls backlinks/history/live with a 365-day window and returns monthly snapshots
    sorted chronologically. Fields: month (YYYY-MM), backlinks, referring_domains,
    new_rd (new referring domains that month), lost_rd (lost referring domains).
    """
    out: dict = {"bl_history": [], "bl_history_error": None}
    try:
        today     = date.today()
        date_from = (today - timedelta(days=365)).strftime("%Y-%m-%d")
        date_to   = today.strftime("%Y-%m-%d")

        result = dfs_post("backlinks/history/live", [
            {
                "target":    domain,
                "date_from": date_from,
                "date_to":   date_to,
            }
        ])
        items = dfs_get_items(result)

        if not items:
            task_msg = ""
            try:
                task_msg = (result.get("tasks") or [{}])[0].get("status_message") or ""
            except Exception:
                pass
            out["bl_history_error"] = (
                f"no history data (DFS: {task_msg})" if task_msg
                else "no backlink history data"
            )
            return out

        history = []
        for item in items:
            month = (item.get("date") or "")[:7]   # "YYYY-MM"
            if not month:
                continue
            history.append({
                "month":             month,
                "backlinks":         int(item.get("backlinks")              or 0),
                "referring_domains": int(item.get("referring_domains")      or 0),
                "new_rd":            int(item.get("new_referring_domains")   or 0),
                "lost_rd":           int(item.get("lost_referring_domains")  or 0),
            })

        history.sort(key=lambda x: x["month"])
        out["bl_history"] = history
        if not history:
            out["bl_history_error"] = "no backlink history data"

    except Exception as e:
        print(f"[WARN] Backlink history fetch failed: {e}", file=sys.stderr)
        out["bl_history_error"] = str(e)

    # --- Backlink History (growth trend over the last 12 months) ---
    out.update(_fetch_bl_history(domain))

    return out


def fetch_backlinks(domain: str) -> dict:
    """Return backlink data. Never raises."""
    out = {
        "domain_rank": 0,
        "ahrefs_dr": 0,           # Ahrefs Domain Rating 0-100 (authoritative authority signal)
        "ahrefs_rank": 0,         # Ahrefs global rank
        "backlinks_total": 0,
        "referring_domains_total": 0,
        "dofollow_count": 0,
        "nofollow_count": 0,
        "top_referring_domains": [],  # list of {domain, rank, backlinks, dr}
        "anchor_text_dist": {         # for doughnut chart
            "labels": ["Branded", "Exact match", "Partial", "Generic", "Naked URL"],
            "data": [0, 0, 0, 0, 0],
        },
        "dofollow_pct": 0,
        # Availability flag for scoring: True only when the summary CALL succeeded (even if the
        # site genuinely has 0 backlinks — a real 0 must score low, not be excluded). Inferring
        # availability from value>0 made the Brand Health Score swing run-to-run. (Fixed 2026-06-01.)
        "_backlinks_available": False,
        "bl_history":            [],
        "bl_history_error":      None,
    }

    # --- Ahrefs Domain Rating (free API endpoint) ---
    try:
        ahrefs = fetch_domain_rating(domain)
        out["ahrefs_dr"]   = ahrefs["dr"]
        out["ahrefs_rank"] = ahrefs["ahrefs_rank"]
    except Exception as e:
        print(f"[INFO] Ahrefs DR fetch skipped: {e}", file=sys.stderr)

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
                "dr": 0,  # populated below
            })
    except Exception as e:
        print(f"[WARN] Referring domains fetch failed: {e}", file=sys.stderr)

    # --- Ahrefs DR enrichment for top referring domains ---
    try:
        rd_domains = [d["domain"] for d in out["top_referring_domains"] if d.get("domain")]
        if rd_domains:
            dr_map = enrich_domains_with_dr(rd_domains)
            for entry in out["top_referring_domains"]:
                entry["dr"] = dr_map.get(entry["domain"], {}).get("dr", 0)
    except Exception as e:
        print(f"[INFO] Ahrefs DR enrichment for referring domains skipped: {e}", file=sys.stderr)

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

    # --- Backlink History (growth trend over the last 12 months) ---
    out.update(_fetch_bl_history(domain))

    return out
