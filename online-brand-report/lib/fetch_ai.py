"""fetch_ai.py — llms.txt presence + Google Knowledge Panel check + AI Mode citations."""

import sys
import requests
from urllib.parse import urlparse
from .config import dfs_post, dfs_get_items

_UA = "Mozilla/5.0 (compatible; JamBot-BrandAudit/1.0)"

def _domain_clean(domain: str) -> str:
    return domain.lower().replace("www.", "")


def _fetch_ai_mode(brand_name: str, domain: str, location_code: int = 2840) -> dict:
    """Query DataForSEO AI Mode SERP and return citation presence data. Never raises."""
    out = {
        "ai_mode_cited": False,
        "ai_mode_query": brand_name,
        "ai_mode_references": [],
        "ai_mode_competitor_citations": [],
        "ai_mode_error": None,
    }
    try:
        result = dfs_post("serp/google/ai_mode/live/advanced", [
            {
                "keyword": brand_name,
                "location_code": location_code,
                "language_code": "en",
            }
        ])
        items = dfs_get_items(result)
        if not items:
            task_msg = ""
            try:
                task_msg = result.get("tasks", [{}])[0].get("status_message", "")
            except Exception:
                pass
            out["ai_mode_error"] = (
                f"no AI citations found (DFS: {task_msg})" if task_msg
                else "no AI citations found"
            )
            return out

        clean_domain = _domain_clean(domain)
        references = []

        for item in items:
            if item.get("type") != "ai_overview":
                continue
            for ref in (item.get("references") or []):
                ref_url   = ref.get("url") or ref.get("source_url") or ""
                ref_title = ref.get("title") or ""
                ref_dom   = ref.get("domain") or ""
                if not ref_dom and ref_url:
                    try:
                        ref_dom = urlparse(ref_url).hostname or ref_url
                    except Exception:
                        ref_dom = ref_url
                references.append({
                    "url":    ref_url,
                    "domain": ref_dom,
                    "title":  ref_title[:120],
                })
                rd = _domain_clean(ref_dom)
                if rd == clean_domain or rd.endswith("." + clean_domain):
                    out["ai_mode_cited"] = True

        out["ai_mode_references"] = references
        out["ai_mode_competitor_citations"] = [
            r["domain"] for r in references
            if _domain_clean(r["domain"]) != clean_domain
            and not _domain_clean(r["domain"]).endswith("." + clean_domain)
        ]
        if not references:
            out["ai_mode_error"] = "no AI citations found"

    except Exception as e:
        print(f"[WARN] AI Mode SERP check failed: {e}", file=sys.stderr)
        out["ai_mode_error"] = str(e)

    return out


def fetch_ai(domain: str, brand_name: str, location_code: int = 2840) -> dict:
    """Return AI/LLM visibility data. Never raises.

    location_code: DataForSEO country code threaded from generate.py (2840 US / 2124 CA)."""
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
                "location_code": location_code,
                "language_code": "en",
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

    # --- AI Mode citations (DataForSEO serp/google/ai_mode/live/advanced) ---
    out.update(_fetch_ai_mode(brand_name, domain, location_code))

    return out
