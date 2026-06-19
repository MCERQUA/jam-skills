#!/usr/bin/env python3
"""find-domain.py — deterministic Serper-backed domain finder for a business NAME.

The onboarding company turn often gives us a business NAME (and maybe a city)
but NO typed website. To run a REAL brand/SEO report we need the business's
actual website domain. This helper searches Google (via Serper /search) for the
name+location, filters out directories / socials / aggregators, and returns a
RANKED list of candidate domains plus a single `best` pick and a `confident`
flag.

Used from BOTH:
  • the host brand-report worker (jambot-brand-report-worker.sh) — when a
    company name is captured but no domain, it calls this and, on a confident
    hit, runs the REAL generate.py report (and remembers the domain).
  • the setup-host onboarding AI (the `claude -p` LLM dispatch on a messy
    company turn) — it infers/corrects the name, calls this, and either commits
    the discovered domain or asks the customer a clarifying question.

CONTRACT:
  Input : --name "<company>" [--city <city>] [--state <st>] [--num <n>]
  Output: ONE JSON object on stdout:
            {"query": "...",
             "candidates": [{"domain": "foamit.ca", "title": "...", "rank": 1}, ...],
             "best": "foamit.ca" | null,
             "confident": true | false}
  `confident` is true ONLY when the top non-directory candidate is a STRONG
  match — a distinctive brand token appears in the domain label OR the result
  title. A clearly-fake business returns best=null, confident=false.

FAIL-SOFT: any error (no key, network failure, bad JSON) → prints
  {"query": ..., "candidates": [], "best": null, "confident": false} and exits 0.
  Never raises, never blocks the caller. stdlib + the existing fetch_serper key
  loader only (no third-party imports).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from urllib.parse import urlparse

# Reuse the EXACT key loader + directory/social host lists already maintained for
# the brand report so this stays a single source of truth (no drift).
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from lib.fetch_serper import _serper_key as _serper_key_base, _serper_search  # type: ignore
    from lib.fetch_discovery import _PLATFORM_HOSTS, _DIRECTORY_SITES  # type: ignore
except Exception:  # pragma: no cover — import problems must not crash the caller
    _serper_key_base = None  # type: ignore
    _serper_search = None  # type: ignore
    _PLATFORM_HOSTS = {}  # type: ignore
    _DIRECTORY_SITES = {}  # type: ignore


# Extra key-file paths to try, on TOP of fetch_serper._serper_key's own lookup
# ($SERPER_API_KEY env + /mnt/system/base/.openclaw-keys.env). These cover the
# IN-CONTAINER case (setup-host mounts the platform keys at /config/.platform-keys.env
# and the skills tree at /mnt/shared-skills) where the host's .openclaw-keys.env
# path doesn't exist. Harmless when the key isn't in these files.
_EXTRA_KEY_FILES = (
    "/config/.platform-keys.env",
    "/mnt/system/base/.platform-keys.env",
    "/mnt/shared-skills/.openclaw-keys.env",
)


def _serper_key() -> str:
    """Serper key via the brand-report loader first, then container-local files."""
    if _serper_key_base is not None:
        try:
            k = _serper_key_base()
            if k:
                return k
        except Exception:
            pass
    env = os.environ.get("SERPER_API_KEY", "").strip()
    if env:
        return env
    for path in _EXTRA_KEY_FILES:
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SERPER_API_KEY="):
                        return line.partition("=")[2].strip().strip('"').strip("'")
        except Exception:
            continue
    return ""


def _gl(city: str, state: str) -> str:
    """Google country code for the Places query. Canada when the location text says so,
    else US default (Places still geo-resolves from the location in the query)."""
    t = f"{city} {state}".lower()
    ca = ("canada", "ontario", "quebec", "alberta", "british columbia", "manitoba",
          "saskatchewan", "nova scotia", "new brunswick", "newfoundland",
          "prince edward", " on ", " qc ", " bc ", " ab ")
    return "ca" if any(w in f" {t} " for w in ca) else "us"


def _serper_places(key: str, query: str, gl: str = "us"):
    """Authoritative business lookup via Google Places — returns the top place dict
    (carries the business's real 'website', 'title', 'address', 'rating') or None.
    The Places 'website' field is the AUTHORITATIVE own-site signal; far more reliable
    than guessing a domain from organic search (which mismatches generic names like
    'Talk of the Town' → a same-name shop in another city, or a delivery aggregator).
    Never raises."""
    import json as _json, urllib.request as _ur
    try:
        body = _json.dumps({"q": query, "gl": gl}).encode()
        req = _ur.Request("https://google.serper.dev/places", data=body,
                          headers={"X-API-KEY": key, "Content-Type": "application/json"})
        data = _json.loads(_ur.urlopen(req, timeout=20).read().decode("utf-8", "replace"))
        places = data.get("places") or []
        return places[0] if places else None
    except Exception:
        return None


# Extra aggregator / non-business hosts that aren't in the brand-report directory
# table but should never be returned as a business's OWN domain. Mirrors the spec
# exclusion intent (facebook, instagram, linkedin, yelp, yellowpages, bbb,
# mapquest, google, indeed, etc.). The directory/social tables above are unioned
# in on top of this at runtime.
_EXTRA_EXCLUDE_HOSTS = {
    "google.com", "google.ca", "goo.gl", "g.co", "bing.com", "duckduckgo.com",
    "indeed.com", "glassdoor.com", "ziprecruiter.com", "wikipedia.org",
    "wikidata.org", "amazon.com", "ebay.com", "etsy.com", "craigslist.org",
    "reddit.com", "quora.com", "medium.com", "blogspot.com", "wordpress.com",
    "youtube.com", "youtu.be", "facebook.com", "fb.com", "instagram.com",
    "linkedin.com", "twitter.com", "x.com", "tiktok.com", "pinterest.com",
    "yelp.com", "yelp.ca", "yellowpages.com", "yellowpages.ca", "yp.com",
    "bbb.org", "mapquest.com", "apple.com", "tripadvisor.com", "thumbtack.com",
    "angi.com", "angieslist.com", "homeadvisor.com", "houzz.com", "porch.com",
    "manta.com", "foursquare.com", "trustpilot.com", "birdeye.com",
    "nextdoor.com", "zoominfo.com", "crunchbase.com", "opencorporates.com",
    "dnb.com", "chamberofcommerce.com", "businessfinder.com",
    "expired.com", "godaddy.com", "namecheap.com", "wix.com", "squarespace.com",
    "weebly.com", "sites.google.com", "linktr.ee",
    # Food-delivery aggregators — a restaurant's DoorDash/UberEats page is NOT its
    # own site. (Talk of the Town, Bowmanville had NO website → find-domain wrongly
    # returned doordash.com 'confident', which would build a report about DoorDash.)
    "doordash.com", "ubereats.com", "skipthedishes.com", "grubhub.com",
    "seamless.com", "postmates.com", "menulog.com", "just-eat.com", "justeat.com",
    "deliveroo.com", "foodora.com", "ritual.co", "chownow.com", "order.online",
    # Menu / reservation / restaurant aggregators
    "opentable.com", "opentable.ca", "zomato.com", "allmenus.com", "menupix.com",
    "restaurantji.com", "sirved.com", "menupages.com", "yelp.ca", "ezcater.com",
    "toasttab.com", "spoton.com", "clover.com", "square.site", "tripadvisor.ca",
    # Local news / municipal directory hosts that surface for a business name but
    # are never the business's own domain (varied — these are the common Canadian
    # ones seen; the confident-match + greenfield fallback handles the long tail).
    "durhamregion.com", "newschannel5.com", "downtownsofdurham.ca", "blogto.com",
    "narcity.com", "cbc.ca", "ctvnews.ca", "thestar.com", "yahoo.com",
}


def _excluded_hosts() -> set[str]:
    """Union of social platform hosts + brand-report directory hosts + extras."""
    hosts: set[str] = set(_EXTRA_EXCLUDE_HOSTS)
    try:
        for hh in _PLATFORM_HOSTS.values():
            for h in hh:
                hosts.add(h)
    except Exception:
        pass
    try:
        for hh, _cat in _DIRECTORY_SITES.values():
            for h in hh:
                # directory table sometimes carries path-bearing hosts
                # ("google.com/maps") — keep only the bare host part.
                hosts.add(h.split("/", 1)[0])
    except Exception:
        pass
    return {h for h in hosts if h}


def _host(url: str) -> str:
    """Bare lowercase registrable host, no scheme/www/path."""
    try:
        h = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    except Exception:
        return ""
    if h.startswith("www."):
        h = h[4:]
    return h


def _is_excluded(host: str, excluded: set[str]) -> bool:
    if not host:
        return True
    # Exact host OR a true subdomain of an excluded host (e.g. members.sprayfoam.org,
    # m.yelp.com). Do NOT use a bare `e in host` substring test — that wrongly excludes
    # a legitimate business whose domain merely CONTAINS an aggregator string
    # (e.g. 'allstatesprayfoam.com' contains 'sprayfoam.com' → was thrown away →
    # the real report fell back to an empty greenfield build). The endswith("." + e)
    # clause already covers every real subdomain case.
    return any(host == e or host.endswith("." + e) for e in excluded)


_NONALNUM = re.compile(r"[^a-z0-9]+")


def _norm(s: str) -> str:
    return _NONALNUM.sub("", (s or "").lower())


# Generic service words that are NOT distinctive brand tokens. A match on one of
# these alone (e.g. "insulation" appearing in both the name and a competitor
# domain) must NOT count as a confident brand hit.
_GENERIC_WORDS = {
    "the", "and", "for", "inc", "llc", "ltd", "co", "company", "corp", "group",
    "services", "service", "solutions", "systems", "contracting", "contractors",
    "construction", "roofing", "plumbing", "insulation", "spray", "foam", "hvac",
    "electric", "electrical", "heating", "cooling", "landscaping", "cleaning",
    "painting", "remodeling", "renovation", "renovations", "home", "homes",
    "pro", "pros", "expert", "experts", "best", "local", "your", "our", "we",
    "of", "in", "at", "on", "a", "an",
}


def _brand_tokens(name: str) -> list[str]:
    """Distinctive (non-generic) lowercased word tokens from the company name."""
    toks = [t for t in _NONALNUM.sub(" ", (name or "").lower()).split() if t]
    distinctive = [t for t in toks if t not in _GENERIC_WORDS and len(t) >= 3]
    return distinctive or toks  # if everything was generic, fall back to all


def _name_slug(name: str) -> str:
    """Full normalized brand slug (alnum only) — e.g. 'Foamit' -> 'foamit'."""
    return _norm(name)


def _confident_match(name: str, domain: str, title: str) -> bool:
    """A STRONG match: a distinctive brand token (or the full name slug) appears
    in the domain LABEL or the result title."""
    label = _norm(domain.split(".")[0])
    title_n = _norm(title)
    full = _name_slug(name)
    # 1) full brand slug appears in the domain label or title
    if len(full) >= 4 and (full in label or full in title_n):
        return True
    # 2) a distinctive token appears in the domain label (domain wins trust)
    for tok in _brand_tokens(name):
        if len(tok) >= 4 and tok in label:
            return True
    # 3) ALL distinctive tokens appear in the title (full brand named on the page)
    toks = [t for t in _brand_tokens(name) if len(t) >= 3]
    if toks and all(t in title_n for t in toks) and len(toks) >= 2:
        return True
    return False


def find_domain(name: str, city: str = "", state: str = "", num: int = 20) -> dict:
    """Search + rank candidate domains. Never raises."""
    name = (name or "").strip()
    q_full = " ".join(p for p in (name, city, state) if p).strip()
    out = {"query": q_full, "candidates": [], "best": None, "confident": False}
    if not name or _serper_search is None:
        return out

    key = _serper_key()
    if not key:
        return out

    excluded = _excluded_hosts()

    # ── AUTHORITATIVE: Google Places 'website' field ──────────────────────────
    # Trust the business's actual listing before guessing from organic search.
    place = _serper_places(key, q_full or name, gl=_gl(city, state))
    if place is not None:
        site = (place.get("website") or "").strip()
        host = _host(site) if site else ""
        if host and not _is_excluded(host, excluded):
            out["candidates"] = [{"domain": host, "title": place.get("title") or name, "rank": 1}]
            out["best"] = host
            out["confident"] = True
            out["source"] = "places"
            out["gmb_found"] = True
            return out
        # The business EXISTS (found in Places) but has NO own website (or only an
        # aggregator listed) → GREENFIELD. Do NOT fall through to organic guessing,
        # which produces wrong-business / same-name-other-city / aggregator results.
        out["gmb_found"] = True
        out["no_website"] = True
        out["place_name"] = place.get("title") or name
        out["greenfield"] = True
        return out

    # ── Fallback: organic search (only when Places found NO listing at all) ────
    # Primary query: name + location. Fallback: bare name. Merge, keep order.
    organic: list = []
    seen_ids = set()
    queries = [q for q in (q_full, name) if q]
    # de-dup identical queries (name-only when no city/state)
    uniq_q = []
    for q in queries:
        if q not in uniq_q:
            uniq_q.append(q)
    for q in uniq_q:
        try:
            res = _serper_search(key, q, num=num) or []
        except Exception:
            res = []
        for o in res:
            link = (o or {}).get("link") or ""
            if not link or link in seen_ids:
                continue
            seen_ids.add(link)
            organic.append(o)

    if not organic:
        return out

    # Rank candidates by first (best) organic appearance; one entry per host.
    candidates: list[dict] = []
    by_host: dict[str, dict] = {}
    for idx, o in enumerate(organic):
        link = (o or {}).get("link") or ""
        host = _host(link)
        if _is_excluded(host, excluded):
            continue
        title = (o or {}).get("title") or ""
        if host in by_host:
            continue  # keep the highest-ranked result per host
        _conf = _confident_match(name, host, title)
        # City corroboration: a confident hit for a located business must reference
        # that city (in title or domain), else a same-name business in another city
        # (e.g. 'Talk of the Town' Overland Park KS vs Bowmanville ON) matches wrongly.
        if _conf and city:
            cnorm = _norm(city)
            if cnorm and cnorm not in _norm(title) and cnorm not in _norm(host):
                _conf = False
        entry = {
            "domain": host,
            "title": title[:120],
            "rank": len(by_host) + 1,
            "_serp_pos": idx,
            "_confident": _conf,
        }
        by_host[host] = entry
        candidates.append(entry)

    if not candidates:
        return out

    # Sort: confident hits first, then by SERP order. Re-number ranks.
    candidates.sort(key=lambda c: (0 if c["_confident"] else 1, c["_serp_pos"]))
    for i, c in enumerate(candidates, 1):
        c["rank"] = i

    top = candidates[0]
    confident = bool(top["_confident"])

    out["candidates"] = [
        {"domain": c["domain"], "title": c["title"], "rank": c["rank"]}
        for c in candidates[:10]
    ]
    out["best"] = top["domain"] if confident else None
    out["confident"] = confident
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Find a business's website domain via Serper.")
    ap.add_argument("--name", required=True, help="Company / business name")
    ap.add_argument("--city", default="", help="City (optional)")
    ap.add_argument("--state", default="", help="State / province / region (optional)")
    ap.add_argument("--num", type=int, default=20, help="Serper results per query")
    try:
        args = ap.parse_args(argv[1:])
    except SystemExit:
        # argparse already printed usage to stderr; still emit a fail-soft JSON
        print(json.dumps({"query": "", "candidates": [], "best": None, "confident": False}))
        return 0
    try:
        result = find_domain(args.name, args.city, args.state, args.num)
    except Exception as e:  # pragma: no cover — fail-soft contract
        sys.stderr.write(f"find-domain: unexpected error: {e!r}\n")
        result = {"query": (args.name or "").strip(), "candidates": [],
                  "best": None, "confident": False}
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
