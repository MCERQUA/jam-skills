"""fetch_social.py — Social profile existence checks."""

import sys
import re
import requests

_UA = "Mozilla/5.0 (compatible; JamBot-BrandAudit/1.0)"

_PLATFORMS = {
    "facebook":  "https://www.facebook.com/{slug}",
    "instagram": "https://www.instagram.com/{slug}/",
    "linkedin":  "https://www.linkedin.com/company/{slug}/",
    "youtube":   "https://www.youtube.com/@{slug}",
    "twitter":   "https://twitter.com/{slug}",
    "tiktok":    "https://www.tiktok.com/@{slug}",
}

_SOCIAL_LINK_RE = re.compile(
    r'href=["\']https?://(?:www\.)?'
    r'(facebook\.com|instagram\.com|linkedin\.com|youtube\.com|twitter\.com|x\.com|tiktok\.com)'
    r'/([^"\'?\s]+)',
    re.I
)

def _slug_from_domain(domain: str) -> str:
    """Best-guess slug from domain: strip TLD, take first word."""
    base = domain.lower().replace("www.", "").split(".")[0]
    # Remove common separators
    return re.sub(r"[^a-z0-9]", "", base)

def _check_social_url(url: str) -> bool:
    try:
        r = requests.head(url, headers={"User-Agent": _UA}, timeout=8, allow_redirects=True)
        # 200 or 302 to the same domain = exists; 404/410 = not found
        # Some platforms always return 200 even for missing profiles, so check final URL
        if r.status_code in (404, 410):
            return False
        # If redirected to a login/signup page, treat as not found
        final = r.url.lower()
        if any(x in final for x in ["login", "signup", "register", "not-found"]):
            return False
        return r.status_code < 400
    except Exception:
        return False

def fetch_social(domain: str, brand_name: str) -> dict:
    """Return social presence data. Never raises."""
    out = {
        "platforms": {},  # platform -> {exists, url, status}
        "platforms_claimed": 0,
        "platforms_total": len(_PLATFORMS),
    }

    slug = _slug_from_domain(domain)

    # --- Scrape homepage for social links first (more reliable) ---
    found_from_site: dict[str, str] = {}
    try:
        r = requests.get(f"https://{domain}", headers={"User-Agent": _UA}, timeout=12, allow_redirects=True)
        for m in _SOCIAL_LINK_RE.finditer(r.text):
            site_domain = m.group(1).lower()
            path = m.group(2).strip("/")
            if not path or path in ("share", "sharer", "intent"):
                continue
            for plat, url_tmpl in _PLATFORMS.items():
                if plat in site_domain or (plat == "twitter" and "x.com" in site_domain):
                    url = f"https://{site_domain}/{path}"
                    found_from_site[plat] = url
    except Exception as e:
        print(f"[INFO] Social homepage scrape: {e}", file=sys.stderr)

    # --- Check each platform ---
    claimed = 0
    for platform, url_tmpl in _PLATFORMS.items():
        url_from_site = found_from_site.get(platform)
        if url_from_site:
            out["platforms"][platform] = {
                "exists": True,
                "url": url_from_site,
                "status": "active",
            }
            claimed += 1
            continue

        # Probe with slug
        probe_url = url_tmpl.format(slug=slug)
        exists = _check_social_url(probe_url)
        out["platforms"][platform] = {
            "exists": exists,
            "url": probe_url if exists else None,
            "status": "active" if exists else "absent",
        }
        if exists:
            claimed += 1

    out["platforms_claimed"] = claimed
    return out
