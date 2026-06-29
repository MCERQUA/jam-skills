#!/usr/bin/env python3
"""
online-brand-report — generate a fully-populated SEO brand report HTML file.

Usage:
  python generate.py \
    --domain spartancoatingsystems.com \
    --name "Spartan Coating Systems" \
    --owner "Stephen Smith" \
    --city "Lawton" \
    --state "OK" \
    --phone "+1-580-555-0100" \
    --email "info@spartancoatingsystems.com" \
    --service "spray foam insulation" \
    --competitors "competitor1.com,competitor2.com" \
    --output /mnt/clients/test-dev/openvoiceui/canvas-pages/brand-report-spartan.html \
    [--tenant test-dev]
"""

import argparse
import os
import sys
import time
from datetime import datetime
import traceback
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SKILL_DIR))

from lib import (
    fetch_brand,
    fetch_web,
    fetch_organic,
    fetch_live_rankings,
    fetch_serp,
    fetch_local,
    fetch_backlinks,
    fetch_competitive,
    fetch_content,
    fetch_ai,
    fetch_social,
    fetch_discovery,
    fetch_serper,
    fetch_dnslytics,
    fetch_geo,
    score as score_mod,
    roadmap as roadmap_mod,
    render as render_mod,
    plan as plan_mod,
)

# Template ships WITH the skill (template.html alongside this script) so it resolves in
# ANY tenant container — not just test-dev's host canvas-pages, which isn't mounted in
# tenant containers. (Fixed 2026-06-03 — was hardcoded to test-dev's host path.)
TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")

# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="Generate an Online Brand Report HTML file.")
    p.add_argument("--domain",      default="",     help="Target domain (no https://). Empty = a no-website business: the SAME report renders, just sparse where there's no site (GMB + local SERP only).")
    p.add_argument("--name",        required=True,  help="Business name")
    p.add_argument("--owner",       default="",     help="Owner / contact name")
    p.add_argument("--city",        default="",     help="Primary city")
    p.add_argument("--state",       default="",     help="State abbreviation")
    p.add_argument("--phone",       default="",     help="Phone number")
    p.add_argument("--email",       default="",     help="Email address")
    p.add_argument("--service",     default="",     help="Primary service (drives keyword research, e.g. 'spray foam insulation')")
    p.add_argument("--services",    default="",     help="Comma-separated FULL service list for the service×area money-page matrix "
                                                         "(e.g. 'rim repair,curb rash,bent rim straightening'). If omitted, the "
                                                         "matrix expands only the primary --service across areas.")
    p.add_argument("--competitors", default="",     help="Comma-separated competitor domains")
    p.add_argument("--output",      default="",     help="Full output path for the HTML file")
    p.add_argument("--tenant",      default="test-dev", help="JamBot tenant name (for default output path)")
    p.add_argument("--publish-slug", default="",    help="Company slug for public publication at start.jam-bot.com/<slug>/. "
                                                         "If omitted, derived from --name (kebab-case). "
                                                         "Pass --no-publish to skip public copy.")
    p.add_argument("--no-publish",  action="store_true", help="Skip the start.jam-bot.com publication step")
    p.add_argument("--client-knowledge-path", default="", help="If set, writes brand_report_url and brand_report_generated_at back to this client-knowledge.json (for stager substitution)")
    return p.parse_args()


def slugify(text: str) -> str:
    """company-slug — kebab-case, ASCII-safe, matches nginx vhost regex ^[a-z0-9][a-z0-9-]{0,80}$"""
    import re
    s = text.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    s = re.sub(r'-+', '-', s)
    return s[:80] or 'unnamed'


def resolve_output(args) -> str:
    if args.output:
        return args.output
    # No-website business → derive the slug from the NAME (there's no domain). Same
    # report, just sparse on the on-site sections; the keyword research IS the build plan.
    slug = (args.domain.replace("www.", "").replace(".", "-").replace("_", "-").lower()
            if args.domain else slugify(args.name))
    fname = f"brand-report-{slug}.html"
    # Tenant openclaw containers mount the OVU canvas-pages at these IN-CONTAINER paths;
    # /mnt/clients is NOT mounted inside tenant containers. Prefer a mounted canvas-pages
    # dir, fall back to the host path for host-side runs. (Fixed 2026-06-03 — the otm
    # agent had to pass --output because the /mnt/clients default wasn't writable in-container.)
    for d in ("/home/node/.openclaw/workspace/canvas-pages",
              "/app/runtime/canvas-pages",
              f"/mnt/clients/{args.tenant}/openvoiceui/canvas-pages"):
        if os.path.isdir(d):
            return os.path.join(d, fname)
    return f"/mnt/clients/{args.tenant}/openvoiceui/canvas-pages/{fname}"


# ── Fetcher runner ────────────────────────────────────────────────────────────

def _run(label: str, fn, *a, **kw) -> dict:
    """Run a fetcher, catch exceptions, return empty dict on failure."""
    t0 = time.time()
    try:
        result = fn(*a, **kw)
        elapsed = time.time() - t0
        print(f"  [OK]  {label:<30} {elapsed:.1f}s", file=sys.stderr)
        return result
    except Exception:
        elapsed = time.time() - t0
        print(f"  [ERR] {label:<30} {elapsed:.1f}s", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {}


# ── Vertical / service auto-detection ─────────────────────────────────────────
# The keyword engine is seeded by `service` (fetch_content uses it as the literal
# keyword). When onboarding can't supply an industry, `--service` is empty and the
# report defaults to "your service" → it researches "your service in <city>" →
# an empty, useless report. But the report ALREADY fetches the two signals that
# reveal the real vertical: the GMB primary category (fetch_brand → gmb_categories)
# and the homepage <title>/<meta description>. This detector wires those existing
# signals into `service` so the report self-fills the vertical. Fail-open: returns
# "" when nothing reliable is found, so the caller keeps prior behavior.

_PLACEHOLDER_SERVICES = {"", "your service", "service", "services", "general", "n/a"}


def _clean_service(s: str) -> str:
    import re as _re
    s = _re.sub(r"\s+", " ", (s or "")).strip(" -|·•—,.\t")
    # trailing org/noise words add nothing to a keyword seed
    s = _re.sub(r"\b(shop|store|company|co|inc|llc|ltd|corp)\b\.?$", "", s, flags=_re.I).strip()
    return s


def _probe_homepage_meta(domain: str):
    """Return (title, meta_description) from the live homepage, or ("",""). Cheap,
    dependency-free, fail-soft (any error → empties → caller falls through)."""
    import re as _re, urllib.request as _u, html as _html
    # Realistic browser UA — bot-identifying UAs get 403'd by Cloudflare/WAF on many
    # real business sites (azrimrepair.com etc.), which silently breaks detection.
    _ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    for scheme in ("https://", "http://"):
        try:
            req = _u.Request(scheme + domain + "/", headers={"User-Agent": _ua})
            page = _u.urlopen(req, timeout=12).read(250000).decode("utf-8", "replace")
        except Exception:
            continue
        tm = _re.search(r"<title[^>]*>(.*?)</title>", page, _re.I | _re.S)
        dm = _re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
                        page, _re.I | _re.S)
        title = _html.unescape(_re.sub(r"\s+", " ", (tm.group(1) if tm else ""))).strip()
        desc = _html.unescape(_re.sub(r"\s+", " ", (dm.group(1) if dm else ""))).strip()
        if title or desc:
            return title, desc
    return "", ""


def _strip_geo_tail(s: str) -> str:
    """Remove a trailing location phrase from a service descriptor so the keyword
    seed isn't polluted with the city/region (which returns weaker keyword data).
    Generic — works for any location, not a hardcoded city list. Handles:
      'attic insulation in Toronto'        → 'attic insulation'
      'roof repair serving Dallas & Plano'  → 'roof repair'
      'screen printing Toronto & GTA'       → 'screen printing'
    Conservative: only strips when a connector (in/serving/near/…) precedes a
    Capitalized place, OR a trailing 'City & Area' / '& GTA' style region tag."""
    import re as _re
    s = (s or "").strip()
    # 1) connector + Capitalized place tail: 'in Toronto', 'serving Dallas & Plano'
    s = _re.sub(r"\b(?:in|serving|near|across|throughout|around|for)\s+[A-Z][\w .,'&-]*$",
                "", s).strip(" -|,&")
    # 2) trailing '& GTA' / '& Area' / '& Surrounding ...' region tag
    s = _re.sub(r"\s*&\s*(?:GTA|area|surrounding|region|county|counties)\b.*$",
                "", s, flags=_re.I).strip(" -|,&")
    return s


def _service_from_title(title: str) -> str:
    """Pull the service-descriptor chunk out of a homepage title — the part that
    isn't the brand name and isn't the geo tail. e.g.
    'PrintGuys - Custom Printed Merch & Company Apparel in Concord'
        → 'Custom Printed Merch & Company Apparel'."""
    import re as _re
    if not title:
        return ""
    best = ""
    for part in _re.split(r"\s*[\|\-–—:·•]\s*", title):
        p = _strip_geo_tail(part)
        if len(p.split()) >= 2 and len(p) > len(best):
            best = p
    return best


# Service-noun suffixes that mark a phrase as a real SEO head-term (the words a
# customer actually searches). Used to pick the clean keyword out of a homepage's
# meta description — e.g. 'Premium DTF printing, screen printing, embroidery' →
# 'screen printing'. Deterministic; NO LLM (Groq LLM is banned — TTS only).
_SERVICE_NOUNS = (
    "printing", "print", "repair", "repairs", "installation", "install", "cleaning",
    "removal", "restoration", "remediation", "roofing", "plumbing", "electrical",
    "hvac", "landscaping", "lawn care", "detailing", "insulation", "coating",
    "coatings", "painting", "paving", "concrete", "flooring", "remodeling",
    "renovation", "construction", "contracting", "fencing", "decking", "masonry",
    "welding", "towing", "embroidery", "apparel", "signage", "upholstery",
    "grooming", "training", "catering", "photography", "design", "marketing",
    "accounting", "bookkeeping", "consulting", "inspection", "pest control",
    "extermination", "waterproofing", "excavation", "drywall", "tiling",
    "windows", "gutters", "siding", "tree service", "junk removal", "moving",
    "locksmith", "glass", "appliance repair", "wraps", "tinting",
)

# Filler segments that look like a short phrase but aren't a service.
_META_FILLER = (
    "no minimums", "and more", "free quote", "free estimate", "fast turnaround",
    "near me", "call today", "family owned", "locally owned", "since", "serving",
    "best", "trusted", "affordable", "professional", "quality", "premium",
    "licensed", "insured", "guaranteed", "open", "available",
)


def _service_from_meta(desc: str) -> str:
    """Pull a clean SEO head-term out of a homepage meta description by scanning its
    comma/clause segments for a short (1-4 word) phrase ending in / containing a
    real service noun. Deterministic — no LLM. '' if nothing qualifies.
    e.g. '...Premium DTF printing, screen printing, embroidery...' → 'screen printing'."""
    import re as _re
    if not desc:
        return ""
    best = ""
    for seg in _re.split(r"[,.;:|–—\-]| and | & ", desc):
        s = _strip_geo_tail(_clean_service(seg))
        low = s.lower()
        if not s or low in _PLACEHOLDER_SERVICES:
            continue
        words = s.split()
        if not (1 <= len(words) <= 4):
            continue
        if any(f in low for f in _META_FILLER):
            continue
        if not any(_re.search(r"\b" + _re.escape(n) + r"s?\b", low) for n in _SERVICE_NOUNS):
            continue
        # Prefer a tight 2-word head-term ('screen printing') over a longer one.
        if not best or abs(len(words) - 2) < abs(len(best.split()) - 2):
            best = s
    return best


# Org / generic tail words that aren't part of the service descriptor in a business
# NAME ('Toronto SprayFoam parts' → drop 'parts'). Generic — no per-business hardcoding.
_NAME_ORG_NOISE = {
    "parts", "supply", "supplies", "service", "services", "solutions", "group",
    "shop", "store", "company", "co", "inc", "llc", "ltd", "corp", "the", "and",
    "of", "your", "pro", "pros", "experts", "expert", "specialists", "specialist",
}
# Service head-nouns that appear in business NAMES but aren't in _SERVICE_NOUNS
# (which targets homepage meta). 'foam' catches spray-foam businesses by name.
_NAME_SERVICE_NOUNS = set(_SERVICE_NOUNS) | {"foam", "spray foam"}


def _camel_split(s: str) -> str:
    """Insert a space at lower→Upper boundaries so 'SprayFoam' → 'Spray Foam'."""
    import re as _re
    return _re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s or "")


def _service_from_name(name: str, city: str = "", state: str = "") -> str:
    """Deterministic LAST-RESORT service seed derived from the business NAME — used when
    there's no website AND no GMB AND the LLM profile was unavailable, so the report is
    NEVER seeded with the 'your service' placeholder when a real name exists. Generic, no
    per-business hardcoding. Strategy:
      • camel-split + drop org/noise tail words and any token that matches the supplied
        city/state (geo), leaving the content words;
      • if a service head-noun is present, return it plus up to one preceding word
        ('Toronto SprayFoam parts' → 'spray foam'; 'Spartan Coating Systems' → 'spartan
        coating'); else fall back to the trailing 2-3 content words (a 'City Service Org'
        name puts the service after the city prefix)."""
    import re as _re
    if not (name or "").strip():
        return ""
    n = _strip_geo_tail(_camel_split(name))
    toks = _re.findall(r"[A-Za-z][A-Za-z'&-]*", n)
    geo = set()
    for g in (city, state):
        for w in _re.findall(r"[A-Za-z]+", (g or "").lower()):
            if len(w) >= 3:
                geo.add(w)
    content = [t.lower() for t in toks
               if t.lower() not in _NAME_ORG_NOISE and t.lower() not in geo]
    if not content:
        return ""
    joined = " ".join(content)
    # 1) service head-noun (longest match first so 'spray foam' beats 'foam').
    #    A MULTI-WORD noun is already a complete service term ('spray foam') → return it
    #    as-is. A SINGLE-WORD noun ('repair', 'insulation') takes one preceding qualifier
    #    word ('rim repair', 'foam insulation') — that word is the service modifier, not
    #    brand/geo noise in the common case.
    for noun in sorted(_NAME_SERVICE_NOUNS, key=len, reverse=True):
        multiword = " " in noun
        pat = (_re.escape(noun) if multiword
               else r"(?:\w+\s+)?" + _re.escape(noun)) + r"s?\b"
        m = _re.search(pat, joined)
        if m:
            phrase = _clean_service(m.group(0))
            if phrase and phrase.lower() not in _PLACEHOLDER_SERVICES and 3 <= len(phrase) <= 40:
                return phrase
    # 2) trailing 2-3 content words
    cand = _clean_service(" ".join(content[-3:]))
    if cand and cand.lower() not in _PLACEHOLDER_SERVICES and 3 <= len(cand) <= 50:
        return cand
    return ""


def detect_service(domain: str, brand_data: dict,
                   name: str = "", city: str = "", state: str = "") -> str:
    """Best-effort primary-service detection from signals the report already pulls.
    Fully DETERMINISTIC (no LLM — Groq LLM is banned). Order:
      (1) GMB primary category — authoritative ('Screen printing shop' → 'screen printing');
      (2) homepage meta head-term — a real service phrase from the description;
      (3) homepage title descriptor / first meta clause — last-resort seed;
      (4) business-NAME fallback — works even with NO website/GMB, so the report is never
          seeded with 'your service' when a real business name exists.
    Returns "" only when even the name yields nothing usable."""
    # 1) GMB primary category
    cats = (brand_data or {}).get("gmb_categories") or []
    if cats:
        cat = _clean_service(str(cats[0]))
        if cat and cat.lower() not in _PLACEHOLDER_SERVICES:
            return cat
    # Homepage signals (only when there's a domain to probe)
    title, desc = _probe_homepage_meta(domain) if domain else ("", "")
    if title or desc:
        # 2) meta head-term (clean keyword the engine can expand)
        meta_term = _service_from_meta(desc)
        if meta_term and 3 <= len(meta_term) <= 40:
            return meta_term
        # 3) title descriptor, then first meta clause (last resort)
        cand = _clean_service(_service_from_title(title))
        if not (cand and cand.lower() not in _PLACEHOLDER_SERVICES and 3 <= len(cand) <= 60):
            import re as _re
            first_clause = _re.split(r"[.;|–—\-]", desc)[0] if desc else ""
            cand = _clean_service(first_clause)
        if cand and cand.lower() not in _PLACEHOLDER_SERVICES and 3 <= len(cand) <= 70:
            return cand
    # 4) business-NAME fallback (no website / no GMB / LLM unavailable)
    return _service_from_name(name, city, state)


# ── Country / location_code resolver ──────────────────────────────────────────
# DataForSEO keyword/SERP endpoints take a numeric location_code. Every fetcher used
# to hardcode 2840 (United States), so Canadian (and any non-US) businesses got ZERO
# keyword data (printguys.ca, Concord ON → ranked_keywords: 0). This resolver maps the
# business location to the right country code. Conservative + fail-open: anything we
# can't positively identify as Canada falls back to the US default (2840) so existing
# US clients are unaffected.

DFS_LOCATION_US = 2840   # United States
DFS_LOCATION_CA = 2124   # Canada

# ccTLD → (DataForSEO location_code, country name). The domain TLD is the strongest
# GENERIC country signal — this is what makes the report work for a business ANYWHERE,
# not just US/CA. Country-ambiguous gTLDs (.com/.net/.org/.io/.co/.biz) are NOT here →
# they fall through to location-text detection, then the US default.
_TLD_COUNTRY = {
    "ca": (2124, "Canada"),
    "uk": (2826, "United Kingdom"), "co.uk": (2826, "United Kingdom"),
    "au": (2036, "Australia"), "com.au": (2036, "Australia"),
    "ie": (2372, "Ireland"),
    "nz": (2554, "New Zealand"), "co.nz": (2554, "New Zealand"),
    "in": (2356, "India"), "co.in": (2356, "India"),
    "de": (2276, "Germany"), "fr": (2250, "France"), "nl": (2528, "Netherlands"),
    "es": (2724, "Spain"), "it": (2380, "Italy"),
    "za": (2710, "South Africa"), "co.za": (2710, "South Africa"),
    "sg": (2702, "Singapore"), "ae": (2784, "United Arab Emirates"),
    "mx": (2484, "Mexico"), "com.mx": (2484, "Mexico"),
    "br": (2076, "Brazil"), "com.br": (2076, "Brazil"),
}
_COUNTRY_NAME = {
    2840: "United States", 2124: "Canada", 2826: "United Kingdom", 2036: "Australia",
    2372: "Ireland", 2554: "New Zealand", 2356: "India", 2276: "Germany",
    2250: "France", 2528: "Netherlands", 2724: "Spain", 2380: "Italy",
    2710: "South Africa", 2702: "Singapore", 2784: "United Arab Emirates",
    2484: "Mexico", 2076: "Brazil",
}


def _country_from_tld(domain: str):
    """(location_code, country_name) from the domain's ccTLD, or None for a generic gTLD."""
    d = (domain or "").lower().strip().strip("/").split("/")[0]
    parts = d.split(".")
    if len(parts) >= 2:
        if ".".join(parts[-2:]) in _TLD_COUNTRY:      # 'co.uk', 'com.au'
            return _TLD_COUNTRY[".".join(parts[-2:])]
        if parts[-1] in _TLD_COUNTRY:                 # 'ca', 'de'
            return _TLD_COUNTRY[parts[-1]]
    return None


def country_name_for(location_code: int) -> str:
    return _COUNTRY_NAME.get(location_code, "United States")


# location_code → Serper `gl` country code (for the Places coordinate lookup).
_GL_FOR_CODE = {2840: "us", 2124: "ca", 2826: "gb", 2036: "au", 2372: "ie",
                2554: "nz", 2356: "in", 2276: "de", 2250: "fr", 2528: "nl",
                2724: "es", 2380: "it", 2710: "za", 2702: "sg", 2784: "ae",
                2484: "mx", 2076: "br"}


def business_coordinate(name: str, city: str, region: str, location_code: int) -> str:
    """The business's 'lat,lng' from its Google Places listing, for geo-targeted LOCAL
    SERPs (what a nearby customer actually sees). '' if not found. Never raises —
    geo-targeting is a precision upgrade, never a hard dependency."""
    import json as _json, urllib.request as _u
    key = os.environ.get("SERPER_API_KEY", "").strip()
    q = " ".join(p for p in (name, city, region) if p).strip()
    if not key or not q:
        return ""
    gl = _GL_FOR_CODE.get(location_code, "us")
    try:
        body = _json.dumps({"q": q, "gl": gl}).encode()
        req = _u.Request("https://google.serper.dev/places", data=body,
                         headers={"X-API-KEY": key, "Content-Type": "application/json"})
        data = _json.loads(_u.urlopen(req, timeout=20).read().decode("utf-8", "replace"))
        p = (data.get("places") or [{}])[0]
        lat, lng = p.get("latitude"), p.get("longitude")
        if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
            return f"{lat},{lng}"
    except Exception:
        pass
    return ""

# Canadian province/territory abbreviations + full names (lowercased, matched against
# --state, then --city/region text as a fallback).
_CA_PROVINCE_ABBR = {
    "on", "qc", "bc", "ab", "mb", "sk", "ns", "nb", "nl", "pe", "nt", "nu", "yt",
}
_CA_PROVINCE_NAMES = {
    "ontario", "quebec", "québec", "british columbia", "alberta", "manitoba",
    "saskatchewan", "nova scotia", "new brunswick", "newfoundland",
    "newfoundland and labrador", "labrador", "prince edward island",
    "northwest territories", "nunavut", "yukon",
}


def _looks_canadian(text: str) -> bool:
    """True if the given location text positively identifies a Canadian province/territory
    (by 2-letter abbreviation or full name). Word-boundary aware so 'ON' only matches as a
    standalone token, never inside another word."""
    import re as _re
    t = (text or "").strip().lower()
    if not t:
        return False
    if t in _CA_PROVINCE_ABBR or t in _CA_PROVINCE_NAMES:
        return True
    tokens = set(_re.findall(r"[a-zà-ÿ]+", t))
    if tokens & _CA_PROVINCE_ABBR:
        return True
    # full-name match (handles multi-word names embedded in a larger string)
    for name in _CA_PROVINCE_NAMES:
        if _re.search(r"\b" + _re.escape(name) + r"\b", t):
            return True
    return False


def resolve_location_code(state: str, city: str = "", domain: str = "") -> int:
    """Map the business to a DataForSEO country location_code. Signals, in order:
      1. domain ccTLD (.ca/.co.uk/.com.au/.de/… — strongest generic 'anywhere' signal)
      2. a Canadian province in --state / --city text
      3. US default (2840) — for ambiguous gTLDs (.com) with no other signal.
    Fail-open: an unidentifiable location is treated as US so existing US clients
    are unaffected."""
    tld = _country_from_tld(domain)
    if tld:
        return tld[0]
    if _looks_canadian(state) or _looks_canadian(city):
        return DFS_LOCATION_CA
    return DFS_LOCATION_US


# Province / region full-name → 2-letter abbreviation, for region-granularity GMB
# confirmation (a GMB address writes 'ON', not 'Ontario').
_PROV_ABBR = {
    "ontario": "on", "quebec": "qc", "québec": "qc", "british columbia": "bc",
    "alberta": "ab", "manitoba": "mb", "saskatchewan": "sk", "nova scotia": "ns",
    "new brunswick": "nb", "newfoundland and labrador": "nl", "newfoundland": "nl",
    "prince edward island": "pe", "northwest territories": "nt", "nunavut": "nu",
    "yukon": "yt",
}
# Country / filler words that must NOT count as a location-confirmation token (a bare
# 'Canada' match would confirm ANY Canadian listing → re-opens cross-city contamination).
_GEO_STOPWORDS = {"canada", "usa", "united", "states", "america", "the", "and"}


def gmb_city_confirmed(city: str, state: str, gmb_addr: str) -> bool:
    """True when a GMB address plausibly belongs to the requested location, WITHOUT the
    over-strict 'whole city string must be a literal substring' test that dropped valid
    GMB data for region-granularity inputs (e.g. city='Ontario Canada', a province, never
    appears verbatim in '…, Toronto, ON M5H, Canada'). Still guards cross-city
    contamination: requires a real geo-token overlap, not just a same name. Confirms when:
      • the full city string is a substring of the address (original strict path), OR
      • any city/state word ≥4 chars (excluding country/filler words) appears as a token, OR
      • the input names a province/region and the address carries that province's
        2-letter abbreviation as a standalone token (region-level confirmation)."""
    import re as _re
    addr = (gmb_addr or "").lower()
    if not addr:
        return False
    city_l = (city or "").lower().strip()
    if city_l and city_l in addr:
        return True
    addr_tokens = set(_re.findall(r"[a-zà-ÿ]+", addr))
    want = set()
    for g in (city, state):
        for w in _re.findall(r"[a-zà-ÿ]+", (g or "").lower()):
            if len(w) >= 4 and w not in _GEO_STOPWORDS:
                want.add(w)
    if want & addr_tokens:
        return True
    combo = f"{city_l} {(state or '').lower()}"
    for full, ab in _PROV_ABBR.items():
        if full in combo and _re.search(r"\b" + ab + r"\b", addr):
            return True
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    domain    = args.domain.replace("https://", "").replace("http://", "").rstrip("/")
    name      = args.name
    owner     = args.owner
    city      = args.city
    state     = args.state
    phone     = args.phone
    email     = args.email
    service   = args.service
    tenant    = args.tenant
    output    = resolve_output(args)

    competitors_raw = [c.strip() for c in args.competitors.split(",") if c.strip()]

    # Resolve the DataForSEO country location_code from the business location so non-US
    # (e.g. Canadian) businesses get real keyword/SERP data instead of an empty US lookup.
    location_code = resolve_location_code(state, city, domain)
    # Geo-target SERPs to the business's real location (what a nearby customer sees),
    # not just the country. Looked up once from Google Places; '' → country-level.
    location_coordinate = business_coordinate(name, city, state, location_code)
    if location_coordinate:
        print(f"    Geo-target: {location_coordinate} (local SERP) [Places]", file=sys.stderr)
    _loc_label = country_name_for(location_code)
    print(f"    Location code: {location_code} ({_loc_label}) "
          f"[from domain='{domain}' state='{state}' city='{city}']", file=sys.stderr)

    print(f"\n=== Online Brand Report: {name} ({domain}) ===", file=sys.stderr)
    print(f"    Output: {output}", file=sys.stderr)
    print(f"    Tenant: {tenant}", file=sys.stderr)
    print(f"\n--- Fetching data ---", file=sys.stderr)

    t_start = time.time()

    # ── Run all fetchers ──────────────────────────────────────────────────────
    # GMB + homepage first — they carry the vertical signals the keyword engine needs.
    brand_data      = _run("brand/GMB",         fetch_brand.fetch_brand,       domain, name, city, state, country=_loc_label)
    web_data        = _run("web/Lighthouse",    fetch_web.fetch_web,           domain)

    # AUTO-DETECT the service/vertical when none was supplied (or it's a placeholder),
    # so the keyword research is seeded with the REAL business, not "your service".
    # Uses signals already fetched above (GMB category) + a cheap homepage probe.
    detected_service = ""
    llm_profile_data = {}
    if service.strip().lower() in _PLACEHOLDER_SERVICES:
        # PREFERRED: LLM reads the homepage and returns an accurate structured profile
        # (replaces fragile regex that produced garbage like azrimrepair.com →
        # "restoration including cracks" instead of "rim repair"). Fail-OPEN: claude may
        # be unavailable inside tenant containers → returns {} → we fall back to the
        # deterministic detect_service() regex below.
        try:
            from lib import llm_profile as _llm_profile
            # name/city/region let it infer the vertical from the BUSINESS NAME + GMB
            # when there's no website — so a no-site company still gets full keyword
            # research (the foundation/plan for the site we'll build them).
            llm_profile_data = _llm_profile.llm_business_profile(
                domain, gmb_categories=brand_data.get("gmb_categories"),
                name=name, city=city, region=state) or {}
        except Exception as _llm_e:
            print(f"    LLM profile errored (non-fatal): {_llm_e}", file=sys.stderr)
            llm_profile_data = {}

        if llm_profile_data.get("primary_service"):
            detected_service = llm_profile_data["primary_service"]
            service = detected_service
            print(f"    Auto-detected service/vertical (LLM): '{service}' "
                  f"(was empty/placeholder) → seeds keyword research", file=sys.stderr)
        else:
            # FALLBACK: deterministic detection from GMB/homepage signals, then the
            # business NAME (so a no-website prospect whose LLM call failed still gets a
            # real vertical seed instead of the 'your service' placeholder).
            detected_service = detect_service(domain, brand_data,
                                              name=name, city=city, state=state)
            if detected_service:
                service = detected_service
                print(f"    Auto-detected service/vertical (regex/name): '{service}' "
                      f"(LLM gave nothing; was empty/placeholder) → seeds keyword research",
                      file=sys.stderr)
            else:
                print("    Service auto-detect: no reliable vertical found "
                      "(LLM + GMB/homepage/name gave nothing) — proceeding without seed",
                      file=sys.stderr)

    organic_data    = _run("organic/keywords",  fetch_organic.fetch_organic,   domain, location_code=location_code)
    serp_data       = _run("serp/results",      fetch_serp.fetch_serp,         domain, service, city, state, location_code=location_code, location_coordinate=location_coordinate)
    local_data      = _run("local/reviews+map", fetch_local.fetch_local,       name, service, city, state, domain, location_code=location_code)
    backlink_data   = _run("backlinks",         fetch_backlinks.fetch_backlinks, domain)
    comp_data       = _run("competitive",       fetch_competitive.fetch_competitive, domain, competitors_raw, location_code=location_code)
    content_data    = _run("content/gaps",      fetch_content.fetch_content,   domain, service, city,
                                                                                comp_data.get("top_competitor", ""), location_code=location_code)
    ai_data         = _run("AI/llms.txt",       fetch_ai.fetch_ai,             domain, name, location_code=location_code)
    social_data     = _run("social",            fetch_social.fetch_social,     domain, name)
    geo_data        = _run("geo/city-volumes",  fetch_geo.fetch_geo,           service, city, state, location_code=location_code)

    # ── Brand-name SERP discovery — "what anyone Googles" (grab everything) ─────
    # ONE source of ground truth for the obvious stuff the fragile probes miss: the real
    # social profiles, the full directory/citation footprint, and Google Business presence.
    # Applied AUTHORITATIVELY over the homepage-scrape/HEAD-probe/exact-GMB-lookup results so
    # the report never again falsely says "no Facebook / no GMB" for a business that's trivially
    # findable on Google. (2026-06-03 — Mike: "missing the obvious stuff anyone can find".)
    discovery_data  = _run("discovery/brand-serp", fetch_discovery.fetch_discovery, domain, name, city, state, location_code=location_code)
    if discovery_data.get("_discovery_available"):
        fetch_social.apply_discovery(social_data, discovery_data.get("social_profiles", {}))
        fetch_brand.apply_discovery(brand_data,  discovery_data.get("gmb", {}))

    # Serper Places enrichment — the richest verified GMB (full NAP + real review count +
    # category) and a NAP phone cross-check. Authoritative for the listing fields when present.
    serper_gmb      = _run("serper/places-GMB", fetch_serper.fetch_serper_gmb, domain, name, city, state, phone)
    if serper_gmb.get("gmb_found"):
        fetch_serper.apply_serper_gmb(brand_data, serper_gmb)

    # Connected/supporting sites + full brand-mention inventory via Serper search ("find
    # everything connected to this brand"). Uses the VERIFIED GMB phone/address for the
    # NAP-reverse. (2026-06-03 — Mike: find supporting/leadgen sites + every brand mention.)
    serper_web      = _run("serper/connected+mentions", fetch_serper.fetch_connected_and_mentions,
                           domain, name, phone, serper_gmb.get("gmb_address", ""), serper_gmb.get("gmb_phone", ""))

    # Reverse-analytics — the operator's HIDDEN site network via shared GA/AdSense ID (catches
    # JS-rendered DBA/leadgen sites that target other keywords, which search can't find). No-key-
    # safe: skips the headless render entirely without DNSLYTICS_API_KEY. (2026-06-03.)
    dns_net         = _run("dnslytics/reverse-analytics", fetch_dnslytics.fetch_connected_via_analytics,
                           domain, name)

    # ── LIVE SERP rank check ──────────────────────────────────────────────────
    # DataForSEO **Labs** ranked_keywords UNDER-reports rankings for small / new /
    # non-US domains (printguys.ca: Labs returned 1 keyword while the business ranks
    # page-1 for several). Query Google LIVE for a candidate keyword set NOW and fold
    # the real rankings into organic_data so every section reflects the live truth.
    _brand_token = (domain.split(".")[0] if domain else "").strip()
    _kw_sugg = content_data.get("keyword_suggestions", []) or []
    _kw_sugg_by_vol = sorted(_kw_sugg, key=lambda k: int(k.get("volume") or 0), reverse=True)
    _candidates = [
        service,
        f"{service} {city}".strip() if service else "",
        f"{service} near me".strip() if service else "",
        f"{service} {state}".strip() if service else "",
        _brand_token,
    ] + [k.get("keyword", "") for k in _kw_sugg_by_vol[:12]]
    # Fold the LLM-identified real services + keyword seeds into the live-SERP candidate
    # set so the rank check tests the terms the business ACTUALLY ranks for, not just
    # regex guesses. Dedup happens below (case-insensitive). Empty when no LLM profile.
    _candidates += (llm_profile_data.get("keyword_seeds") or [])
    _candidates += (llm_profile_data.get("services") or [])
    _candidates = [c.strip() for c in _candidates if c and c.strip()]
    # case-insensitive dedup, preserving order
    _seen = set()
    _candidates = [c for c in _candidates
                   if not (c.lower() in _seen or _seen.add(c.lower()))]
    _kw_volumes = {k["keyword"].lower(): int(k.get("volume") or 0)
                   for k in _kw_sugg if k.get("keyword")}
    live_rank_data = _run("organic/live-rank-check", fetch_live_rankings.fetch_live_rankings,
                          domain, _candidates, location_code=location_code, volumes=_kw_volumes,
                          location_coordinate=location_coordinate)
    if live_rank_data.get("checked"):
        print(f"    Live SERP rank check: {live_rank_data.get('checked', 0)} queries → "
              f"{live_rank_data.get('live_ranked_count', 0)} ranked "
              f"({live_rank_data.get('live_first_page_count', 0)} first-page)", file=sys.stderr)
        _kw_total_before = organic_data.get("kw_total", 0)
        fetch_live_rankings.merge_live_into_organic(
            organic_data, live_rank_data.get("live_rankings", []))
        print(f"    Merged live rankings into organic data: "
              f"kw_total {_kw_total_before} → {organic_data.get('kw_total', 0)}", file=sys.stderr)

    t_fetch = time.time() - t_start
    print(f"\n    Total fetch time: {t_fetch:.1f}s", file=sys.stderr)

    # ── Merge into single data dict ───────────────────────────────────────────
    data: dict = {}
    for d in (brand_data, web_data, organic_data, serp_data, local_data,
              backlink_data, comp_data, content_data, ai_data, social_data, geo_data):
        data.update(d)

    # Stash the raw live-rank findings so render/plan and seo-plan.json can surface them
    # (live_rankings / live_ranked_count / live_first_page_count / checked).
    if live_rank_data:
        data.update(live_rank_data)

    # Off-site footprint inventory (directories/citations + long-tail mentions) — the
    # "you forgot you had this" section. Kept under explicit keys so render/plan can surface it.
    # Merge the long-tail mention inventory from both lanes (DataForSEO discovery + Serper
    # search), de-duped by domain. Serper's are brand-snippet-verified; mark phone-sharers.
    _mentions = {}
    for m in discovery_data.get("other_mentions", []):
        _mentions[m.get("domain", "")] = {**m, "shares_phone": False}
    for m in (serper_web.get("connected_sites", []) if serper_web else []):
        dom = m.get("domain", "")
        prev = _mentions.get(dom, {})
        _mentions[dom] = {
            "domain": dom, "url": m.get("url", "") or prev.get("url", ""),
            "title": m.get("title", "") or prev.get("title", ""),
            "shares_phone": ("shares-phone" in (m.get("signals") or [])) or prev.get("shares_phone", False),
        }
    for m in (serper_web.get("mentions", []) if serper_web else []):
        _mentions.setdefault(m.get("domain", ""), {**m, "shares_phone": False})
    _mentions.pop("", None)

    data["web_footprint"] = {
        "directories":    discovery_data.get("directories", {}),
        "other_mentions": list(_mentions.values()),
        "social_profiles": discovery_data.get("social_profiles", {}),
        "query_count":    discovery_data.get("discovery_query_count", 0),
        # Reverse-analytics: domains sharing the brand's GA/AdSense ID = same operator.
        "connected_network": (dns_net.get("connected", []) if dns_net else []),
        "tracking_ids":      (dns_net.get("tracking_ids", {}) if dns_net else {}),
    }

    # ── GMB confirmation gate (authoritative) ───────────────────────────────────
    # Trust a GMB and its reviews ONLY when a location-validated source confirmed the
    # listing in the requested city. For a generic business name, Google's knowledge panel /
    # map results surface the most prominent SAME-NAMED business (often out of area) — the
    # "EZ Roofing" cross-city contamination. A confirmed GMB's address contains the city; an
    # unconfirmed name-collision panel does not. No confirmation → honest "no local presence":
    # drop the inherited rating/review data before it reaches the score.
    _gmb_addr = (data.get("gmb_address") or "").lower()
    # Token/region-aware confirmation — a literal whole-city substring test dropped valid
    # GMB data whenever the location was given at province/region granularity (e.g.
    # 'Ontario Canada'). gmb_city_confirmed() still requires a real geo overlap so the
    # 'EZ Roofing' cross-city contamination stays blocked. (Fixed 2026-06-29.)
    # A DOMAIN-VERIFIED GMB (the listing's own website IS the client domain) is confirmed
    # unconditionally — the strongest possible proof it's theirs — so the city-token gate
    # never zeroes a real listing whose GMB municipality differs from the marketing city
    # (e.g. markets as 'Toronto', GMB address reads 'North York'). (Added 2026-06-29.)
    _gmb_domain_verified = bool(data.get("gmb_domain_verified"))
    _gmb_city_ok = bool(city) and gmb_city_confirmed(city, state, _gmb_addr)
    _gmb_confirmed = _gmb_domain_verified or _gmb_city_ok
    if _gmb_domain_verified and not _gmb_city_ok:
        print(f"    [INFO] GMB confirmed by DOMAIN match (website = {domain}); GMB municipality "
              f"in address differs from input city '{city}' — kept (no false zero)", file=sys.stderr)
    if not _gmb_confirmed:
        _dropped = data.get("gmb_review_count", 0) or data.get("review_count", 0)
        if _dropped:
            print(f"    [INFO] No GMB confirmed in {city} {state} — discarding name-collision "
                  f"review data ({_dropped} reviews from a same-named out-of-area listing)", file=sys.stderr)
        data["gmb_found"]        = False
        data["gmb_rating"]       = 0.0
        data["gmb_review_count"] = 0
        data["review_avg"]       = 0.0
        data["review_count"]     = 0

    # If fetch_local couldn't get reviews, fall back to the CONFIRMED GMB rating only.
    if data.get("review_avg", 0) == 0 and data.get("gmb_rating", 0) > 0:
        data["review_avg"]   = data["gmb_rating"]
        data["review_count"] = data.get("gmb_review_count", 0)
        print(f"    [INFO] Using GMB rating as review fallback: {data['review_avg']}★ ({data['review_count']} reviews)", file=sys.stderr)

    # Inject CLI-supplied identity fields (override if fetchers set them)
    data.update({
        "domain":       domain,
        "brand_name":   name,
        "owner_name":   owner,
        "city":         city,
        "state":        state,
        "service":      service,
        "tenant":       tenant,
    })
    # phone / email: CLI WINS when supplied, else keep what the GMB fetcher found
    # (fetch_local sets data["phone"]/["address"] from my_business_info). Non-clobbering
    # so a report still shows the real NAP when the caller didn't pass --phone. (ica-voice 2026-06-01)
    if phone:
        data["phone"] = phone
    if email:
        data["email"] = email

    # Full service list → drives the service×area money-page matrix (plan.py reads data["services"]).
    # Without it the matrix expands only the single primary service across areas (core-only).
    services_list = [s.strip() for s in args.services.split(",") if s.strip()]
    # When the caller didn't pass --services, use the FULL service list the LLM read
    # off the site so the money-page matrix is complete (not just the one primary
    # service). The onboarding worker never passes --services, so this is the path
    # that actually fires for real clients.
    if not services_list and llm_profile_data.get("services"):
        services_list = [s.strip() for s in llm_profile_data["services"]
                         if isinstance(s, str) and s.strip()][:8]
        if services_list:
            print(f"    [INFO] Service matrix from LLM profile ({len(services_list)} services)", file=sys.stderr)
    if services_list:
        data["services"] = services_list
        print(f"    [INFO] Service matrix: {', '.join(services_list)}", file=sys.stderr)

    # ── Score + Roadmap ───────────────────────────────────────────────────────
    print("\n--- Scoring ---", file=sys.stderr)
    score_result = score_mod.calculate_score(data)
    print(f"    Brand Health Score: {score_result['total']}/100  Grade: {score_result['grade']}  ({score_result['grade_desc']})", file=sys.stderr)
    print(f"    Breakdown: {score_result['breakdown']}", file=sys.stderr)

    print("\n--- Roadmap ---", file=sys.stderr)
    roadmap = roadmap_mod.generate_roadmap(data, score_result)
    print(f"    P1 items: {len(roadmap['p1'])}   P2: {len(roadmap['p2'])}   P3: {len(roadmap['p3'])}", file=sys.stderr)

    # ── Build plan (the meat) — machine-readable spec for the website builder ──
    print("\n--- Build Plan ---", file=sys.stderr)
    plan = plan_mod.build_plan(data)
    s = plan["summary"]
    print(f"    {s['keyword_gaps']} gaps · {s['quick_wins']} quick-wins · "
          f"{s['recommended_pages']} pages · {s['content_articles']} articles", file=sys.stderr)

    # ── Render ────────────────────────────────────────────────────────────────
    print("\n--- Rendering HTML ---", file=sys.stderr)

    # Ensure output directory exists
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the machine-readable plan next to the HTML report (builder consumes this).
    import json as _json2
    plan_path = out_path.with_name("seo-plan.json")
    plan_path.write_text(_json2.dumps(plan, indent=2))
    print(f"    seo-plan.json → {plan_path}", file=sys.stderr)

    # Write the human-readable background plan (gold-standard style) alongside it.
    try:
        from lib import plan_md as plan_md_mod
        identity = {"name": name, "owner": owner, "city": city, "state": state,
                    "phone": phone, "email": email, "brand_name": name}
        md = plan_md_mod.render_plan_md(plan, identity, score_result, roadmap,
                                        generated_at=datetime.utcnow().strftime("%Y-%m-%d"))
        md_path = out_path.with_name("website-plan.md")
        md_path.write_text(md)
        print(f"    website-plan.md → {md_path}", file=sys.stderr)
    except Exception as _md_e:
        print(f"    website-plan.md FAILED: {_md_e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    render_mod.render(
        data=data,
        score_result=score_result,
        roadmap=roadmap,
        output_path=str(out_path),
        plan=plan,
    )

    t_total = time.time() - t_start
    file_kb = out_path.stat().st_size // 1024

    # ── Publish to start.jam-bot.com/<slug>/ ─────────────────────────────────
    public_url = ""
    if not args.no_publish:
        publish_slug = args.publish_slug or slugify(name)
        public_dir = Path("/var/www/start-jam-bot") / publish_slug
        try:
            public_dir.mkdir(parents=True, exist_ok=True)
            # Copy as index.html so nginx pretty-URL /<slug>/ serves it
            import shutil
            shutil.copyfile(str(out_path), str(public_dir / "index.html"))
            public_url = f"https://start.jam-bot.com/{publish_slug}/"
            print(f"    Published:   {public_url}", file=sys.stderr)
        except Exception as e:
            print(f"    Publish FAILED: {e}", file=sys.stderr)

    # ── Writeback to client-knowledge.json ────────────────────────────────────
    # Runs whenever a client-knowledge path is given — NOT gated on publish, so
    # the auto-detected industry lands even on no-publish runs. brand_report_url
    # is written only when we actually published (have a public_url).
    if args.client_knowledge_path:
        try:
            import json as _json
            ckp = Path(args.client_knowledge_path)
            ck = _json.loads(ckp.read_text()) if ckp.exists() else {}
            if public_url:
                ck["brand_report_url"] = public_url
                ck["brand_report_generated_at"] = datetime.utcfromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%SZ")
            # If the report auto-detected the vertical, write it back as
            # company.industry (only when onboarding hasn't already got one) so the
            # onboarding flow SKIPS the industry question — the report found it,
            # the prospect never gets asked.
            if detected_service:
                co = ck.get("company")
                if not isinstance(co, dict):
                    co = {}; ck["company"] = co
                if not (co.get("industry") or "").strip():
                    # Prefer the LLM's richer vertical label over the bare service term
                    # when we have one (e.g. 'auto wheel repair' vs 'rim repair').
                    _ind = (llm_profile_data.get("industry") or "").strip() or detected_service
                    _ind_src = ("brand-report-llm-profile"
                                if (llm_profile_data.get("industry") or "").strip()
                                else "brand-report-autodetect")
                    co["industry"] = _ind
                    ck["industry_source"] = _ind_src
                    print(f"    Wrote company.industry='{_ind}' "
                          f"({_ind_src}) to {ckp}", file=sys.stderr)
            ckp.write_text(_json.dumps(ck, indent=2))
            if public_url:
                print(f"    Wrote brand_report_url to {ckp}", file=sys.stderr)
            # Persist the machine + human plan NEXT TO client-knowledge.json so the
            # onboarding agent can read THIS prospect's plan later — the shared
            # canvas-pages copy (out_path.with_name) is overwritten by the next
            # prospect's report. (2026-06-19 — onboarding phase1-build-review turn.)
            try:
                import shutil as _sh
                for _pf in ("seo-plan.json", "website-plan.md"):
                    _src = out_path.with_name(_pf)
                    if _src.exists() and _src.resolve() != (ckp.parent / _pf).resolve():
                        _sh.copyfile(str(_src), str(ckp.parent / _pf))
                        print(f"    Persisted {_pf} → {ckp.parent / _pf}", file=sys.stderr)
            except Exception as _pf_e:
                print(f"    Plan persist to prospect dir FAILED: {_pf_e}", file=sys.stderr)
        except Exception as _wb_e:
            print(f"    Writeback FAILED: {_wb_e}", file=sys.stderr)

    print(f"\n=== DONE ===", file=sys.stderr)
    print(f"    File:        {output}  ({file_kb}KB)", file=sys.stderr)
    print(f"    Total time:  {t_total:.1f}s", file=sys.stderr)
    print(f"    Score:       {score_result['total']}/100  {score_result['grade']} — {score_result['grade_desc']}", file=sys.stderr)
    print(f"    Roadmap:     {len(roadmap['p1'])} P1 / {len(roadmap['p2'])} P2 / {len(roadmap['p3'])} P3 items", file=sys.stderr)

    # Stdout: machine-readable result for openclaw skill invocation
    print(f"Report generated: {output}")
    print(f"Score: {score_result['total']}/100 ({score_result['grade']} — {score_result['grade_desc']})")
    print(f"Roadmap: {len(roadmap['p1'])} P1 / {len(roadmap['p2'])} P2 / {len(roadmap['p3'])} P3 action items")
    print(f"Canvas URL: /canvas/{out_path.name}")
    if public_url:
        print(f"Public URL: {public_url}")


if __name__ == "__main__":
    main()
