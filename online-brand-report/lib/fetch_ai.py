"""fetch_ai.py — llms.txt presence + Google Knowledge Panel check."""

import sys
import requests
from .config import dfs_post, dfs_get_items

_UA = "Mozilla/5.0 (compatible; JamBot-BrandAudit/1.0)"

def fetch_ai(domain: str, brand_name: str) -> dict:
    """Return AI/LLM visibility data. Never raises."""
    out = {
        "llms_txt_present": False,
        "llms_txt_url": f"https://{domain}/llms.txt",
        "llms_txt_preview": "",
        "has_knowledge_panel": False,
        "brand_name_serp_position": None,
        "schema_present": False,
    }

    # --- llms.txt check ---
    try:
        r = requests.get(f"https://{domain}/llms.txt", headers={"User-Agent": _UA}, timeout=10)
        if r.status_code == 200 and len(r.text) > 10:
            out["llms_txt_present"] = True
            out["llms_txt_preview"] = r.text[:300].strip()
    except Exception as e:
        print(f"[INFO] llms.txt check: {e}", file=sys.stderr)

    # --- Google SERP for brand name → look for knowledge panel ---
    try:
        result = dfs_post("serp/google/organic/live/advanced", [
            {
                "keyword": brand_name,
                "location_name": "United States",
                "language_name": "English",
                "depth": 5,
            }
        ])
        items = dfs_get_items(result)
        for item in items:
            item_type = item.get("type", "")
            if item_type == "knowledge_graph":
                out["has_knowledge_panel"] = True
            elif item_type == "organic":
                url = item.get("url") or ""
                if domain.lower().replace("www.", "") in url.lower():
                    out["brand_name_serp_position"] = int(item.get("rank_absolute") or 0)
                    break
    except Exception as e:
        print(f"[WARN] Brand SERP check failed: {e}", file=sys.stderr)

    # --- Basic schema check (scrape homepage for JSON-LD) ---
    try:
        r = requests.get(f"https://{domain}", headers={"User-Agent": _UA}, timeout=10)
        if 'application/ld+json' in r.text or '"@type"' in r.text:
            out["schema_present"] = True
    except Exception as e:
        print(f"[INFO] Schema check: {e}", file=sys.stderr)

    return out
