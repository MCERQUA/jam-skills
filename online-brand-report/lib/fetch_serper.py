"""fetch_serper.py — Serper.dev Google Places enrichment (rich, verified GMB).

DataForSEO's brand SERP (fetch_discovery) proves a Google Business presence EXISTS and pulls
a rating off the knowledge panel, but its bare `knowledge_graph` item carries no address/phone/
category. Serper's `/places` endpoint (Google Maps) returns the FULL verified listing: exact
name, rating + review count, phone, street address, website, and category. That's the data the
report should lead with — and the field Mike's manual Serper test surfaced that the report was
missing (verified NAP, real review count, the phone that exposed a Yelp NAP mismatch).

Cheap + bounded: ONE /places call per report. Key loads from .openclaw-keys.env (where the
fleet's SERPER_API_KEY lives) or the environment. ADDITIVE + never raises: if the key is absent
or the call fails, the DataForSEO GMB data stands unchanged.
"""

import os
import sys
import json
import urllib.request
from urllib.parse import urlparse

from .fetch_discovery import (
    _brand_slugs, _matches_brand, _host,
    _PLATFORM_HOSTS, _DIRECTORY_SITES,
)

_SERPER_PLACES = "https://google.serper.dev/places"
_SERPER_SEARCH = "https://google.serper.dev/search"
_SERPER_URL = _SERPER_PLACES  # back-comat for the places call below
_OPENCLAW_KEYS = "/mnt/system/base/.openclaw-keys.env"


def _serper_key() -> str:
    key = os.environ.get("SERPER_API_KEY", "").strip()
    if key:
        return key
    # fall back to the fleet keys file (Serper lives there, not in .platform-keys.env)
    try:
        with open(_OPENCLAW_KEYS) as f:
            for line in f:
                line = line.strip()
                if line.startswith("SERPER_API_KEY="):
                    return line.partition("=")[2].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def _norm_phone(p: str) -> str:
    return "".join(ch for ch in (p or "") if ch.isdigit())[-10:]


def fetch_serper_gmb(domain: str, brand_name: str, city: str = "", state: str = "",
                     cli_phone: str = "") -> dict:
    """Return rich, verified GMB data from Serper Places. Never raises.

    Returns:
        {
          "available": bool,
          "gmb_found": bool,
          "gmb_name", "gmb_rating", "gmb_review_count", "gmb_phone",
          "gmb_address", "gmb_website", "gmb_category",
          "nap_phone_mismatch": bool,   # CLI/site phone vs the verified GMB phone
        }
    """
    out = {"available": False, "gmb_found": False}
    key = _serper_key()
    if not key:
        print("[INFO] Serper enrichment skipped — no SERPER_API_KEY", file=sys.stderr)
        return out

    q = " ".join(p for p in (brand_name, city, state) if p).strip()
    if not q:
        return out

    try:
        body = json.dumps({"q": q, "gl": "us"}).encode()
        req = urllib.request.Request(
            _SERPER_URL, data=body, method="POST",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        print(f"[WARN] Serper places fetch failed: {e}", file=sys.stderr)
        return out

    out["available"] = True
    places = data.get("places") or []
    if not places:
        print(f"[INFO] Serper places: no listing for '{q}'", file=sys.stderr)
        return out

    # Prefer the place whose website matches the client domain; else the top result.
    dom = (domain or "").lower().replace("www.", "")
    pick = None
    for p in places:
        site = (p.get("website") or "").lower()
        if dom and dom in site:
            pick = p
            break
    pick = pick or places[0]

    out["gmb_found"]        = True
    out["gmb_name"]         = pick.get("title") or brand_name
    try:
        out["gmb_rating"]   = float(pick.get("rating") or 0)
    except (TypeError, ValueError):
        out["gmb_rating"]   = 0.0
    try:
        out["gmb_review_count"] = int(pick.get("ratingCount") or 0)
    except (TypeError, ValueError):
        out["gmb_review_count"] = 0
    out["gmb_phone"]        = pick.get("phoneNumber") or ""
    out["gmb_address"]      = pick.get("address") or ""
    out["gmb_website"]      = pick.get("website") or ""
    out["gmb_category"]     = pick.get("category") or ""

    # NAP cross-check: a caller-supplied phone that disagrees with the verified GMB phone
    # is a real, actionable finding (the Yelp/GMB mismatch Mike caught by hand).
    if cli_phone and out["gmb_phone"]:
        out["nap_phone_mismatch"] = _norm_phone(cli_phone) != _norm_phone(out["gmb_phone"])
    else:
        out["nap_phone_mismatch"] = False

    print(f"[INFO] Serper GMB: {out['gmb_name']} — {out['gmb_rating']}★ "
          f"({out['gmb_review_count']} reviews) {out['gmb_phone']} | {out['gmb_address']}"
          + ("  [NAP PHONE MISMATCH]" if out['nap_phone_mismatch'] else ""), file=sys.stderr)
    return out


def _serper_search(key: str, query: str, num: int = 30) -> list:
    """POST to Serper /search; return the organic results list (each: link/title/snippet)."""
    try:
        body = json.dumps({"q": query, "gl": "us", "num": num}).encode()
        req = urllib.request.Request(
            _SERPER_SEARCH, data=body, method="POST",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode())
        return data.get("organic") or []
    except Exception as e:
        print(f"[WARN] Serper search '{query}': {e}", file=sys.stderr)
        return []


def fetch_connected_and_mentions(domain: str, brand_name: str, phone: str = "",
                                 address: str = "", gmb_phone: str = "") -> dict:
    """Find supporting/leadgen/DBA sites + every brand mention, via Serper search.

    Two things the brand-SERP discovery can't do on its own:
      1) Catch a DBA / leadgen site whose URL+title DON'T contain the brand (e.g.
         tampasprayfoaminsulation.com) — we catch it because Google indexes the brand name
         in its on-page CONTENT (the result SNIPPET), which the discovery's URL/title filter
         misses. A non-directory, non-social domain that publishes the brand name on its own
         pages is a strong "owned/affiliated site" candidate.
      2) Reverse the verified phone/address — domains that share the exact NAP are connected.

    Serper is the search lane Mike wants for this now (DataForSEO can be layered in later).
    Returns:
        {
          "available": bool,
          "connected_sites": [{domain, url, title, signals:[...]}],  # candidates to verify
          "mentions":        [{domain, url, title}],                  # full mention inventory
        }
    """
    out = {"available": False, "connected_sites": [], "mentions": []}
    key = _serper_key()
    if not key:
        return out

    slugs = _brand_slugs(brand_name, domain)
    primary = (domain or "").lower().replace("www.", "")
    phones = {_norm_phone(p) for p in (phone, gmb_phone) if _norm_phone(p)}
    known_dir_hosts = set()
    for hosts, _c in _DIRECTORY_SITES.values():
        known_dir_hosts.update(hosts)
    social_hosts = set()
    for hosts in _PLATFORM_HOSTS.values():
        social_hosts.update(hosts)

    # Query fan-out — prefer Serper search. Brand (+place), bare phone, address.
    loc = " ".join(p for p in (address,) if p).strip()
    queries = [q for q in [
        brand_name,
        f'"{phone}"' if phone else "",
        f'"{gmb_phone}"' if gmb_phone and _norm_phone(gmb_phone) not in {_norm_phone(phone)} else "",
        f'"{address}"' if address else "",
    ] if q]

    organic = []
    for q in queries:
        organic.extend(_serper_search(key, q))
    if not organic:
        return out
    out["available"] = True

    connected: dict[str, dict] = {}
    mentions: dict[str, dict] = {}
    for o in organic:
        link = o.get("link") or ""
        host = _host(link)
        if not host or host == primary or primary in host:
            continue
        if any(h in host for h in social_hosts):
            continue  # socials handled elsewhere
        title = o.get("title") or ""
        snippet = o.get("snippet") or ""
        blob_url_title = link + " " + title
        blob_full = blob_url_title + " " + snippet

        is_dir = any(h in host for h in known_dir_hosts)
        # brand match on the FULL text incl. snippet (this is what catches the DBA site)
        brand_hit = _matches_brand(link, title + " " + snippet, slugs)
        phone_hit = bool(phones) and any(p in _norm_phone(blob_full) or p in "".join(ch for ch in blob_full if ch.isdigit()) for p in phones)

        # every non-directory brand mention goes in the inventory
        if brand_hit and not is_dir and host not in mentions:
            mentions[host] = {"domain": host, "url": link, "title": title[:90]}

        # connected candidate = a non-directory site that publishes the brand name OR shares the NAP
        if (brand_hit or phone_hit) and not is_dir:
            sig = []
            if brand_hit:
                sig.append("publishes-brand-name")
            if phone_hit:
                sig.append("shares-phone")
            prev = connected.get(host)
            if prev is None:
                connected[host] = {"domain": host, "url": link, "title": title[:90], "signals": sig}
            else:
                prev["signals"] = sorted(set(prev["signals"]) | set(sig))

    out["connected_sites"] = list(connected.values())[:12]
    out["mentions"] = list(mentions.values())[:15]
    cs = ", ".join(c["domain"] for c in out["connected_sites"]) or "none"
    print(f"[INFO] Serper connected/mentions: connected=[{cs}] mentions={len(out['mentions'])}",
          file=sys.stderr)
    return out


def apply_serper_gmb(brand_out: dict, serper: dict) -> dict:
    """Overlay Serper Places GMB onto brand_data — AUTHORITATIVE for the verified listing.

    Serper Places is the richest, most reliable GMB source we have (full NAP + real review
    count), so when present it WINS over the my_business_info / SERP-panel values for the
    listing fields. Existence is union (any source finding it = found).
    """
    if not serper or not serper.get("gmb_found"):
        return brand_out
    brand_out["gmb_found"] = True
    if serper.get("gmb_name"):         brand_out["gmb_name"] = serper["gmb_name"]
    if serper.get("gmb_rating"):       brand_out["gmb_rating"] = serper["gmb_rating"]
    if serper.get("gmb_review_count"): brand_out["gmb_review_count"] = serper["gmb_review_count"]
    if serper.get("gmb_phone"):        brand_out["gmb_phone"] = serper["gmb_phone"]
    if serper.get("gmb_address"):      brand_out["gmb_address"] = serper["gmb_address"]
    if serper.get("gmb_website"):      brand_out["gmb_website"] = serper["gmb_website"]
    if serper.get("gmb_category"):     brand_out["gmb_categories"] = [serper["gmb_category"]]
    brand_out["gmb_source"] = "serper-places"
    brand_out["nap_phone_mismatch"] = serper.get("nap_phone_mismatch", False)
    return brand_out
