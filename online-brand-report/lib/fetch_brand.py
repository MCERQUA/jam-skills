"""fetch_brand.py — Logo URL detection + GMB profile fetch."""

import sys
import requests
from .config import dfs_post, dfs_get_items

# A REALISTIC browser UA — many real business sites sit behind Cloudflare/WAF and
# 403 any UA that self-identifies as a bot (e.g. azrimrepair.com blocked our old
# "JamBot-BrandAudit/1.0" → no logo/GMB). Look like a normal Chrome visitor.
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

def _abs(domain: str, href: str) -> str:
    """Resolve a possibly-relative href to an absolute URL (so the logo doesn't
    break inside the canvas iframe)."""
    href = (href or "").strip()
    if href.startswith("http"):
        return href
    if href.startswith("//"):
        return f"https:{href}"
    return f"https://{domain}/{href.lstrip('/')}"


def _unwrap_next_image(src: str, domain: str) -> str:
    """Next.js (and similar) proxy the real asset via /_next/image?url=<encoded>&w=…
    Decode the inner `url=` back to the underlying asset so we embed the actual logo
    file, not an optimizer URL. Other proxies / plain srcs pass through unchanged."""
    import urllib.parse as _up
    if "/_next/image" in src and "url=" in src:
        q = _up.parse_qs(_up.urlparse(src).query)
        if q.get("url"):
            return _up.unquote(q["url"][0])
    return src


def _logo_from_header(domain: str) -> str | None:
    """Return the logo <img> the site shows in its HEADER/NAV — the actual brand
    logo a visitor sees in the menu bar (Mike's rule: 'whatever logo on the website
    in the menu header should be the logo'). Order:
      1. an <img> inside <header>/<nav> whose alt/class/id/src mentions 'logo'
      2. else the first <img> inside <header>/<nav>
      3. else any page <img> whose alt/class/id/src mentions 'logo'
    Resolves srcset + Next.js/_next/image proxies and returns an absolute URL."""
    def _attrblob(img):
        return " ".join(str(img.get(a, "")) for a in ("alt", "class", "id", "src")).lower()
    try:
        from bs4 import BeautifulSoup
        r = requests.get(f"https://{domain}", headers={"User-Agent": _UA}, timeout=12, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")

        def pick(imgs):
            for img in imgs:                      # prefer one that says 'logo'
                if "logo" in _attrblob(img):
                    return img
            return imgs[0] if imgs else None       # else first img in the container

        img = None
        for tag in ("header", "nav"):
            container = soup.find(tag)
            if container:
                img = pick(container.find_all("img"))
                if img:
                    break
        if img is None:                            # page-wide: any img that says 'logo'
            img = pick([i for i in soup.find_all("img") if "logo" in _attrblob(i)])
        if img is None:
            return None

        src = img.get("src") or ""
        if not src and img.get("srcset"):          # take the first srcset candidate
            src = img["srcset"].split(",")[0].strip().split(" ")[0]
        if not src:
            return None
        return _abs(domain, _unwrap_next_image(src, domain))
    except Exception as e:
        print(f"[WARN] header-logo scrape failed: {e}", file=sys.stderr)
    return None


def _logo_from_site(domain: str) -> str | None:
    """Find the site's real brand mark: an apple-touch-icon, then a non-tiny
    rel=icon. DELIBERATELY does NOT use og:image — that's the social-share image,
    which on most sites is a hero/article/product photo, NOT the logo (it was the
    source of the 'wrong logo from an article' bug). A missing-but-real logo is
    handled downstream by the Clearbit-by-domain fallback + initials badge."""
    try:
        from bs4 import BeautifulSoup
        r = requests.get(f"https://{domain}", headers={"User-Agent": _UA}, timeout=12, allow_redirects=True)
        soup = BeautifulSoup(r.text, "html.parser")
        # apple-touch-icon — usually 180x180, a proper brand mark
        icon = soup.find("link", rel=lambda v: v and "apple-touch-icon" in " ".join(v))
        if icon and icon.get("href"):
            return _abs(domain, icon["href"])
        # a sized rel=icon that isn't a tiny 16/32 favicon (those scale up ugly)
        for link in soup.find_all("link", rel=lambda v: v and "icon" in " ".join(v).lower()):
            href = link.get("href")
            sizes = (link.get("sizes") or "").lower()
            if href and sizes and not any(t in sizes for t in ("16x16", "32x32")):
                return _abs(domain, href)
    except Exception as e:
        print(f"[WARN] logo scrape failed: {e}", file=sys.stderr)
    return None

def _check_url(url: str) -> bool:
    try:
        r = requests.head(url, headers={"User-Agent": _UA}, timeout=8, allow_redirects=True)
        return r.status_code < 400
    except Exception:
        return False

def fetch_brand(domain: str, brand_name: str, city: str, state: str,
                country: str = "United States") -> dict:
    """Return brand/GMB data dict. Never raises. `country` is the business's
    country name ('United States' / 'Canada'), threaded from generate.py's
    location resolver so the GMB lookup targets the RIGHT country (a Canadian
    business was never found under the old hardcoded 'United States')."""
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

    # --- Logo detection (the ACTUAL logo the site shows, in priority order) ---
    # 1. the logo <img> in the site's header/menu — what a visitor sees (Mike's rule).
    out["logo_url"] = _logo_from_header(domain)
    # 2. common logo file paths.
    if not out["logo_url"]:
        for url in (f"https://{domain}/logo.png",
                    f"https://{domain}/logo.svg",
                    f"https://{domain}/images/logo.png",
                    f"https://{domain}/wp-content/uploads/logo.png",
                    f"https://{domain}/wp-content/themes/logo.png"):
            if _check_url(url):
                out["logo_url"] = url
                break
    # 3. apple-touch-icon / sized icon (brand mark — NOT og:image, which is a
    #    social-share/article photo). If still nothing → render falls to the
    #    initials badge. (Clearbit's free logo API is dead — DNS no longer resolves.)
    if not out["logo_url"]:
        out["logo_url"] = _logo_from_site(domain)

    # --- GMB via DataForSEO business_data (country-aware) ---
    keyword = f"{brand_name} {city} {state}"
    location = f"{city},{state},{country}"
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


def apply_discovery(brand_out: dict, gmb_serp: dict) -> dict:
    """Backfill GMB presence from the brand SERP knowledge panel (AUTHORITATIVE for existence).

    `gmb_serp` = fetch_discovery()["gmb"]. The strict my_business_info/live lookup needs a
    valid keyword + city,state location_name; a missing/wrong --state makes it return nothing
    → false "no Google Business Profile". But if the brand-name SERP shows a knowledge_graph /
    local_pack panel, the business DEMONSTRABLY has a Google presence — so assert gmb_found and
    fill any field the strict lookup didn't. Never overwrites a real value already fetched.
    """
    if not gmb_serp:
        return brand_out
    if gmb_serp.get("gmb_found"):
        brand_out["gmb_found"] = True
        if not brand_out.get("gmb_name") and gmb_serp.get("gmb_name"):
            brand_out["gmb_name"] = gmb_serp["gmb_name"]
        if not brand_out.get("gmb_rating") and gmb_serp.get("gmb_rating"):
            brand_out["gmb_rating"] = gmb_serp["gmb_rating"]
        if not brand_out.get("gmb_review_count") and gmb_serp.get("gmb_review_count"):
            brand_out["gmb_review_count"] = gmb_serp["gmb_review_count"]
        if not brand_out.get("gmb_address") and gmb_serp.get("gmb_address"):
            brand_out["gmb_address"] = gmb_serp["gmb_address"]
        brand_out.setdefault("gmb_source", gmb_serp.get("gmb_source") or "serp")
    return brand_out
