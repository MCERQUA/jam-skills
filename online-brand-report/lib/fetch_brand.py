"""fetch_brand.py — Logo URL detection + GMB profile fetch."""

import sys
import requests
from .config import dfs_post, dfs_get_items

_UA = "Mozilla/5.0 (compatible; JamBot-BrandAudit/1.0)"

def _try_logo_from_meta(domain: str) -> str | None:
    """Scrape og:image or link[rel=icon] from homepage."""
    try:
        from bs4 import BeautifulSoup
        r = requests.get(f"https://{domain}", headers={"User-Agent": _UA}, timeout=12, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        # og:image first — resolve relative URLs to absolute (else the logo breaks inside
        # the canvas iframe). Matches the apple-touch-icon branch below (ica-voice 2026-06-01).
        og = soup.find("meta", property="og:image")
        if og and og.get("content"):
            href = og["content"].strip()
            if href.startswith("http"):
                return href
            if href.startswith("//"):
                return f"https:{href}"
            return f"https://{domain}/{href.lstrip('/')}"
        # apple-touch-icon
        icon = soup.find("link", rel=lambda v: v and "apple-touch-icon" in " ".join(v))
        if icon and icon.get("href"):
            href = icon["href"]
            if href.startswith("http"):
                return href
            return f"https://{domain}{href}"
    except Exception as e:
        print(f"[WARN] logo scrape failed: {e}", file=sys.stderr)
    return None

def _check_url(url: str) -> bool:
    try:
        r = requests.head(url, headers={"User-Agent": _UA}, timeout=8, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False

def fetch_brand(domain: str, brand_name: str, city: str, state: str) -> dict:
    """Return brand/GMB data dict. Never raises."""
    out = {
        "logo_url": None,
        "gmb_name": brand_name,
        "gmb_phone": "",
        "gmb_address": "",
        "gmb_website": domain,
        "gmb_rating": 0.0,
        "gmb_review_count": 0,
        "gmb_categories": [],
        "gmb_found": False,
    }

    # --- Logo detection ---
    candidates = [
        f"https://{domain}/logo.png",
        f"https://{domain}/logo.svg",
        f"https://{domain}/images/logo.png",
        f"https://{domain}/wp-content/uploads/logo.png",
        f"https://{domain}/wp-content/themes/logo.png",
    ]
    for url in candidates:
        if _check_url(url):
            out["logo_url"] = url
            break
    if not out["logo_url"]:
        out["logo_url"] = _try_logo_from_meta(domain)

    # --- GMB via DataForSEO business_data ---
    keyword = f"{brand_name} {city} {state}"
    location = f"{city},{state},United States"
    try:
        result = dfs_post("business_data/google/my_business_info/live", [
            {"keyword": keyword, "location_name": location}
        ])
        items = dfs_get_items(result)
        if items:
            item = items[0]
            out["gmb_found"] = True
            out["gmb_name"]         = item.get("title") or brand_name
            out["gmb_phone"]        = item.get("phone") or ""
            out["gmb_address"]      = item.get("address") or f"{city}, {state}"
            out["gmb_website"]      = item.get("domain") or domain
            out["gmb_rating"]       = float(item.get("rating", {}).get("value") or 0)
            out["gmb_review_count"] = int(item.get("rating", {}).get("votes_count") or 0)
            cats = item.get("category") or ""
            out["gmb_categories"]   = [cats] if cats else []
    except Exception as e:
        print(f"[WARN] GMB fetch failed: {e}", file=sys.stderr)

    return out
