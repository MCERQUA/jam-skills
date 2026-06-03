"""fetch_discovery.py — Exhaustive brand-name SERP discovery ("grab everything").

This is the "what anyone types into Google" layer — and then some. It runs a few
BRAND-NAME SERP queries (`serp/google/organic/live/advanced`, server-side via DataForSEO,
never datacenter-blocked) and harvests the business's ENTIRE off-site web footprint:

  • social profiles  — Facebook, Instagram, LinkedIn, YouTube, X/Twitter, TikTok,
                        Pinterest, Nextdoor
  • directory/citation listings — Yelp, BBB, Angi, HomeAdvisor, Thumbtack, Houzz,
                        MapQuest, YellowPages, Manta, Foursquare, Chamber, BuildZoom,
                        Porch, Bizapedia, and any other recognizable citation site
  • review/reputation pages — Yelp, BBB, Angi, Trustpilot, Birdeye, Google reviews
  • Google Business / knowledge-panel presence (knowledge_graph / local_pack items)
  • video + press mentions

Goal (Mike, 2026-06-03): "we should be finding stuff that even the client maybe forgot
about... impressive is grabbing everything and anything." A report that lists every place
a business already appears online — including the BBB page or Yelp listing they forgot they
had — is what makes it credible. The old detectors (homepage HTML scrape + slug-guess HEAD
probe + exact my_business_info lookup) were fragile and routinely missed the obvious, making
the SAME report flip between "Facebook found / GMB 4.8★" and "no Facebook / no GMB" run to run.

ADDITIVE + AUTHORITATIVE: when these queries return nothing the legacy detectors stand
unchanged; when they find profiles/listings/GMB, they override the fragile probes (see
fetch_social.apply_discovery / fetch_brand.apply_discovery).
"""

import sys
from urllib.parse import urlparse
from .config import dfs_post, dfs_get_items

# ── Social platforms (feed the scored Social dimension) ───────────────────────
_PLATFORM_HOSTS = {
    "facebook":  ["facebook.com", "fb.com"],
    "instagram": ["instagram.com"],
    "linkedin":  ["linkedin.com"],
    "youtube":   ["youtube.com", "youtu.be"],
    "twitter":   ["twitter.com", "x.com"],
    "tiktok":    ["tiktok.com"],
    "pinterest": ["pinterest.com"],
    "nextdoor":  ["nextdoor.com"],
}

# ── Directory / citation / review sites (the "you forgot you had this" inventory) ──
# label -> (host substrings, category). category drives how it's framed in the report.
_DIRECTORY_SITES = {
    "Yelp":            (["yelp.com"],            "review"),
    "Better Business Bureau": (["bbb.org"],      "review"),
    "Angi":            (["angi.com", "angieslist.com"], "review"),
    "HomeAdvisor":     (["homeadvisor.com"],     "directory"),
    "Thumbtack":       (["thumbtack.com"],       "directory"),
    "Houzz":           (["houzz.com"],           "directory"),
    "Porch":           (["porch.com"],           "directory"),
    "BuildZoom":       (["buildzoom.com"],       "directory"),
    "MapQuest":        (["mapquest.com"],        "directory"),
    "YellowPages":     (["yellowpages.com", "yp.com"], "directory"),
    "Superpages":      (["superpages.com"],      "directory"),
    "Manta":           (["manta.com"],           "directory"),
    "Foursquare":      (["foursquare.com"],      "directory"),
    "Bizapedia":       (["bizapedia.com"],       "directory"),
    "Chamber of Commerce": (["chamberofcommerce.com"], "directory"),
    "Nextdoor":        (["nextdoor.com"],        "directory"),
    "Trustpilot":      (["trustpilot.com"],      "review"),
    "Birdeye":         (["birdeye.com"],         "review"),
    "Google Maps":     (["google.com/maps", "maps.google.com", "goo.gl/maps"], "directory"),
    "Bing Places":     (["bing.com/maps"],       "directory"),
    "Apple Maps":      (["maps.apple.com"],      "directory"),
    "Better Business Bureau (BBB)": (["bbb.org"], "review"),
    "Hotfrog":         (["hotfrog.com"],         "directory"),
    "Cylex":           (["cylex.us.com", "cylex-usa.com"], "directory"),
    "EZlocal":         (["ezlocal.com"],         "directory"),
    "Brownbook":       (["brownbook.net"],       "directory"),
    "Citysearch":      (["citysearch.com"],      "directory"),
    "iBegin":          (["ibegin.com"],          "directory"),
    "Local.com":       (["local.com"],           "directory"),
    "DexKnows":        (["dexknows.com"],         "directory"),
    "Bizcommunity":    (["bizcommunity.com"],    "directory"),
    "SprayFoam.org":   (["sprayfoam.org", "sprayfoam.com"], "industry"),
    "ZoomInfo":        (["zoominfo.com"],         "directory"),
    "Yahoo Local":     (["local.yahoo.com", "yahoo.com/local"], "directory"),
    "Procore":         (["procore.com"],          "directory"),
    "Movoto":          (["movoto.com"],           "directory"),
    "FMCSA (USDOT)":   (["fmcsa.dot.gov", "safer.fmcsa"], "directory"),
    "USDOT / Trucking": (["otrucking.com", "fleetseek.com", "carrier411.com"], "directory"),
    "Sunbiz (State Reg)": (["sunbiz.org"],        "directory"),
    "Wallist":         (["wallist.com"],          "review"),
    "BuildZoom Reviews": (["editorlistings.com"], "directory"),
}

# path first-segments that are NOT a profile (share buttons, generic nav, content permalinks)
_JUNK_FIRST = {
    "share", "sharer", "sharer.php", "intent", "tr", "plugins", "p", "dialog",
    "login", "signup", "register", "home", "help", "about", "privacy", "policy",
    "hashtag", "search", "embed", "l.php", "flx", "recover", "events",
}


def _norm(s: str) -> str:
    """Lowercase, strip to alphanumerics only — for slug containment matching."""
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def _brand_slugs(brand_name: str, domain: str) -> list[str]:
    """Distinctive brand slugs a real listing for THIS business would contain.

    Business names lead with the distinctive name and trail with the generic service
    ("On The Mark" + "Spray Foam"). So we take the full normalized slug and progressively
    drop trailing words, keeping every variant down to a floor (>=2 words AND >=7 chars).
    A look-alike competitor ("Mr Marks Spray Foam", "AGL Spray Foam") won't contain
    "onthemark", so it's correctly rejected — that keeps "grab everything" from grabbing
    the WRONG everything (which would re-break trust the other way). The domain slug is
    always included so a listing keyed to the site still matches.
    """
    slugs = set()
    dom_core = (domain or "").lower().replace("www.", "").split(".")[0]
    if len(dom_core) >= 6:
        slugs.add(_norm(dom_core))
    words = [w for w in (brand_name or "").split() if w.strip()]
    while words:
        slug = _norm(" ".join(words))
        # keep variants that are still distinctive enough to not match generic phrases
        if len(slug) >= 7 and (len(words) >= 2 or len(slug) >= 10):
            slugs.add(slug)
        if len(words) <= 2:
            break
        words = words[:-1]  # drop the trailing (most-generic) word
    return [s for s in slugs if s]


def _matches_brand(url: str, title: str, slugs: list[str]) -> bool:
    if not slugs:
        return True  # no brand name supplied — can't filter, keep everything
    blob = _norm(url) + " " + _norm(title)
    return any(s in blob for s in slugs)


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().replace("www.", "")
    except Exception:
        return ""


def _platform_for_host(host: str) -> str | None:
    for plat, hosts in _PLATFORM_HOSTS.items():
        if any(h in host for h in hosts):
            return plat
    return None


def _profile_quality(plat: str, url: str) -> int:
    """Higher = more profile-like (keep the best URL per platform; still COUNT weak signals)."""
    try:
        p = urlparse(url)
        segs = [s for s in (p.path or "").strip("/").split("/") if s]
        first = segs[0].lower() if segs else ""
        score = 50
        if not segs:
            return 10
        if first in _JUNK_FIRST:
            score -= 40
        if first in ("watch", "shorts", "media", "explore", "reel", "reels",
                     "posts", "photo", "video", "v", "pin", "p"):
            score -= 25
        if len(segs) == 1:
            score += 30
        if plat == "linkedin":
            score += 20 if first == "company" else (5 if first == "in" else 0)
        if plat == "youtube" and (first.startswith("@") or first in ("channel", "c", "user")):
            score += 25
        return score
    except Exception:
        return 0


def _harvest_social(items: list, slugs: list[str]) -> dict:
    """platform -> {"url", "signal":"profile"|"mention"} from SERP items.

    A clean vanity profile (single-segment) is kept on its own; a weaker content link
    (a video/location permalink) is only kept if it's clearly tied to THIS brand (slug
    match) — so we don't claim a YouTube channel off one unrelated video.
    """
    best: dict[str, dict] = {}
    for it in items:
        url = it.get("url") or ""
        host = _host(url)
        plat = _platform_for_host(host)
        if not url or not plat:
            continue
        q = _profile_quality(plat, url)
        if q <= 0:
            continue
        signal = "profile" if q >= 60 else "mention"
        if signal == "mention" and not _matches_brand(url, it.get("title") or "", slugs):
            continue  # weak signal not clearly tied to this business → skip
        prev = best.get(plat)
        if prev is None or q > prev["_q"]:
            best[plat] = {"url": url, "signal": signal, "_q": q}
    return {p: {"url": v["url"], "signal": v["signal"]} for p, v in best.items()}


def _harvest_directories(items: list, slugs: list[str]) -> dict:
    """label -> {"url", "category"} for directory/citation/review listings that are THIS business.

    Brand-slug match rejects look-alike competitor listings on the same directory
    (e.g. a different 'Mr Marks Spray Foam' Angi page) and generic category/discussion
    pages that merely contain the industry term.
    """
    found: dict[str, dict] = {}
    for it in items:
        url = it.get("url") or ""
        if not url:
            continue
        low = url.lower()
        host = _host(url)
        for label, (hosts, category) in _DIRECTORY_SITES.items():
            if any(h in low or h in host for h in hosts):
                if not _matches_brand(url, it.get("title") or "", slugs):
                    break  # listing on this directory, but not THIS business
                if label not in found:   # first (highest-ranked) hit per site
                    found[label] = {"url": url, "category": category}
                break
    return found


def _rating_from(it: dict) -> tuple[float, int]:
    r = it.get("rating") or {}
    try:
        val = float(r.get("value") or 0)
    except (TypeError, ValueError):
        val = 0.0
    try:
        votes = int(r.get("votes_count") or r.get("reviews_count") or 0)
    except (TypeError, ValueError):
        votes = 0
    return val, votes


def _harvest_gmb(items: list) -> dict:
    """Google Business / knowledge-panel presence — assert gmb_found even when my_business_info whiffs."""
    gmb = {"gmb_found": False, "gmb_name": "", "gmb_rating": 0.0,
           "gmb_review_count": 0, "gmb_address": "", "gmb_source": ""}
    PANEL_TYPES = {"knowledge_graph", "local_pack", "google_business_profile",
                   "map", "google_reviews", "local_services"}
    for it in items:
        if it.get("type") not in PANEL_TYPES:
            continue
        gmb["gmb_found"] = True
        title = (it.get("title") or "").strip()
        if title and not gmb["gmb_name"]:
            gmb["gmb_name"] = title
        val, votes = _rating_from(it)
        if val and val > gmb["gmb_rating"]:
            gmb["gmb_rating"] = val
        if votes and votes > gmb["gmb_review_count"]:
            gmb["gmb_review_count"] = votes
        addr = it.get("address") or ""
        if addr and not gmb["gmb_address"]:
            gmb["gmb_address"] = addr
        if not gmb["gmb_source"]:
            gmb["gmb_source"] = it.get("type")
    return gmb


def _other_mentions(items: list, client_domain: str, slugs: list[str]) -> list:
    """Notable non-social, non-directory, non-client organic results that are clearly about
    THIS business — press, blog features, partner pages, state registration: the 'grab
    everything' long tail. Brand-slug match keeps competitors (who merely share the industry
    term) out of the inventory."""
    cd = client_domain.lower().replace("www.", "")
    known = set()
    for hosts in _PLATFORM_HOSTS.values():
        known.update(hosts)
    for hosts, _c in _DIRECTORY_SITES.values():
        known.update(hosts)
    out, seen = [], set()
    for it in items:
        if it.get("type") != "organic":
            continue
        url = it.get("url") or ""
        host = _host(url)
        if not host or cd in host or any(k in host for k in known):
            continue
        title = (it.get("title") or "").strip()
        if not _matches_brand(url, title, slugs):
            continue
        if host in seen:
            continue
        seen.add(host)
        out.append({"url": url, "title": title[:90], "domain": host})
        if len(out) >= 12:
            break
    return out


def fetch_discovery(domain: str, brand_name: str, city: str = "", state: str = "") -> dict:
    """Run a few brand-name SERPs and harvest the FULL off-site footprint. Never raises.

    Returns:
        {
          "social_profiles": {platform: {"url","signal"}},
          "directories":     {label: {"url","category"}},
          "other_mentions":  [{"url","title","domain"}],
          "gmb": {gmb_found, gmb_name, gmb_rating, gmb_review_count, gmb_address, gmb_source},
          "discovery_query_count": int,
          "_discovery_available": bool,
        }
    """
    out = {"social_profiles": {}, "directories": {}, "other_mentions": [],
           "gmb": {}, "discovery_query_count": 0, "_discovery_available": False}

    if not (brand_name or domain):
        return out

    base = brand_name or domain
    loc = " ".join(p for p in (city, state) if p).strip()
    # A small fan-out of the queries a curious human would actually run.
    queries = []
    queries.append(f"{base} {loc}".strip())          # primary: brand + place
    queries.append(f"{base} reviews")                # surfaces Yelp/BBB/Angi/Trustpilot
    if loc:
        queries.append(base)                         # bare brand — catches national/forgotten listings
    # de-dup while preserving order
    seen_q = set()
    queries = [q for q in queries if q and not (q in seen_q or seen_q.add(q))]

    all_items: list = []
    for kw in queries:
        try:
            result = dfs_post("serp/google/organic/live/advanced", [
                {"keyword": kw, "location_code": 2840, "language_code": "en", "depth": 30}
            ])
            items = dfs_get_items(result)
            if items:
                all_items.extend(items)
                out["discovery_query_count"] += 1
        except Exception as e:
            print(f"[WARN] discovery query '{kw}' failed: {e}", file=sys.stderr)

    if not all_items:
        print("[INFO] discovery: no SERP items across brand queries", file=sys.stderr)
        return out

    slugs = _brand_slugs(brand_name, domain)
    out["social_profiles"] = _harvest_social(all_items, slugs)
    out["directories"]     = _harvest_directories(all_items, slugs)
    out["other_mentions"]  = _other_mentions(all_items, domain, slugs)
    out["gmb"]             = _harvest_gmb(all_items)
    out["_discovery_available"] = True

    socs = ", ".join(out["social_profiles"].keys()) or "none"
    dirs = ", ".join(out["directories"].keys()) or "none"
    print(f"[INFO] discovery ({out['discovery_query_count']} queries): "
          f"socials=[{socs}] directories=[{dirs}] "
          f"gmb_found={out['gmb'].get('gmb_found')} "
          f"mentions={len(out['other_mentions'])}", file=sys.stderr)
    return out
