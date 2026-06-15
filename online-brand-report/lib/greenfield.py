"""greenfield.py — Brand report for a business with NO website.

WHY THIS EXISTS
---------------
Many strong local businesses (restaurants, takeout, trades, salons) have a great
Google Maps / reviews presence but NO website. The real SEO engine (generate.py)
needs a domain to crawl, so for these prospects the onboarding worker used to
publish a near-empty placeholder.

This module builds a REAL, compelling, data-driven report whose story is:

    "You have a great reputation — 4.6★ from 523 reviews — but you're invisible
     in Google SEARCH because you have no website. Here's exactly who is taking
     your customers, and what a site would unlock."

It assembles the story from TWO live data sources (both already in the stack):

  1. Google Places via Serper   → the GMB strength + the exact coordinates
     (lib.fetch_serper.fetch_serper_gmb already does this).
  2. Geo-targeted live SERP via DataForSEO (serp/google/organic/live/advanced
     with location_coordinate=lat,lng) → for each category search a local
     customer would run, where the business ranks (or doesn't) and which
     competitors WITH their own website outrank it.

NEVER fabricates numbers. Every stat comes from the live API responses. If a
source is missing, the section degrades gracefully (it never raises).

Public API:
    build_greenfield_report(name, city, region, gl="us", places=None) -> dict
    render_greenfield(data) -> str   (standalone HTML)
"""

import os
import re
import sys
import html
import datetime
from urllib.parse import urlparse

from .config import dfs_post, dfs_get_items

# Reuse the aggregator/social/directory exclusion intent from find-domain.py so we
# only count REAL business websites as "competitors with a site". Import is
# best-effort — if find-domain isn't importable we fall back to a local set.
try:
    import importlib.util as _ilu
    _fd_path = os.path.join(os.path.dirname(__file__), "..", "find-domain.py")
    _spec = _ilu.spec_from_file_location("_b" + "rand_find_domain", _fd_path)
    _fd = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_fd)          # type: ignore
    _EXCLUDED_HOSTS = _fd._excluded_hosts()
except Exception as _e:                    # pragma: no cover - defensive
    print(f"[INFO] greenfield: find-domain exclusion import failed ({_e}); using local set",
          file=sys.stderr)
    _EXCLUDED_HOSTS = {
        "google.com", "google.ca", "bing.com", "facebook.com", "instagram.com",
        "linkedin.com", "twitter.com", "x.com", "tiktok.com", "pinterest.com",
        "yelp.com", "yelp.ca", "yellowpages.com", "yellowpages.ca", "tripadvisor.com",
        "tripadvisor.ca", "doordash.com", "ubereats.com", "skipthedishes.com",
        "grubhub.com", "opentable.com", "zomato.com", "wikipedia.org", "youtube.com",
        "reddit.com", "amazon.com", "blogto.com", "durhamregion.com",
    }

# Aggregator / social hosts that, when the TARGET business appears via one of them,
# mean "you only show up through a third party you don't own".
_THIRD_PARTY_PROFILE_HOSTS = {
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "yelp.com": "Yelp", "yelp.ca": "Yelp",
    "tripadvisor.com": "TripAdvisor", "tripadvisor.ca": "TripAdvisor",
    "doordash.com": "DoorDash", "ubereats.com": "Uber Eats",
    "skipthedishes.com": "SkipTheDishes", "grubhub.com": "Grubhub",
    "opentable.com": "OpenTable", "zomato.com": "Zomato",
    "yellowpages.com": "Yellow Pages", "yellowpages.ca": "Yellow Pages",
    "linktr.ee": "Linktree",
}

# DataForSEO country location_code (fallback when no coordinate).
_LOC_BY_GL = {"us": 2840, "ca": 2124, "gb": 2826, "uk": 2826, "au": 2036}


# ── small host helpers ────────────────────────────────────────────────────────
def _host(url: str) -> str:
    """Bare lowercase host, no scheme/www/path."""
    if not url:
        return ""
    try:
        h = (urlparse(url if "://" in url else "http://" + url).hostname or "").lower()
    except Exception:
        return ""
    if h.startswith("www."):
        h = h[4:]
    return h


def _is_excluded_host(host: str) -> bool:
    """True if host is an aggregator/social/directory (NOT a real business site)."""
    if not host:
        return True
    return any(host == e or host.endswith("." + e) or e in host for e in _EXCLUDED_HOSTS)


def _third_party_label(host: str) -> str:
    """If host is a known third-party profile platform, return its display name."""
    for h, label in _THIRD_PARTY_PROFILE_HOSTS.items():
        if host == h or host.endswith("." + h):
            return label
    return ""


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _name_tokens(name: str) -> set:
    """Distinctive lowercased tokens from the business name (drop tiny stopwords)."""
    stop = {"the", "and", "of", "a", "an", "to", "in", "on", "co", "inc", "ltd", "llc"}
    toks = {t for t in _TOKEN_RE.findall((name or "").lower()) if len(t) > 1 and t not in stop}
    return toks


def _name_match(business_name: str, *texts) -> bool:
    """True if a SERP result's title/host plausibly belongs to the business — at
    least half of the distinctive name tokens (min 1) appear in the combined text."""
    toks = _name_tokens(business_name)
    if not toks:
        return False
    blob = " ".join((t or "").lower() for t in texts)
    hits = sum(1 for t in toks if t in blob)
    # require a real overlap, not a single common word
    need = max(1, (len(toks) + 1) // 2)
    return hits >= need


# ── query derivation ──────────────────────────────────────────────────────────
def _derive_queries(category: str, city: str) -> list:
    """Derive 3-5 local-customer search queries from the Places category + city.

    Generic + category-driven (NOT hardcoded to restaurants). For a takeout
    restaurant in Bowmanville this yields:
        takeout restaurant bowmanville
        best restaurant bowmanville          (plural-stripped + 'best')
        restaurant near me
        restaurant delivery bowmanville       (food/restaurant verticals only)
        restaurant bowmanville
    """
    cat = (category or "").strip().lower()
    city_l = (city or "").strip().lower()
    # Singularize the head noun lightly for the "best <x>" form.
    cat_words = cat.split()
    head_noun = cat_words[-1] if cat_words else "business"
    singular = head_noun[:-1] if head_noun.endswith("s") and len(head_noun) > 3 else head_noun

    queries = []

    def add(q):
        q = re.sub(r"\s+", " ", (q or "")).strip()
        if q and q not in queries:
            queries.append(q)

    if cat and city_l:
        add(f"{cat} {city_l}")
    if city_l:
        add(f"best {singular} {city_l}")
        add(f"best {cat or singular}s {city_l}")
    if cat:
        add(f"{cat} near me")
    elif singular:
        add(f"{singular} near me")

    # Food / restaurant verticals also lose huge volume to delivery aggregators.
    if any(w in cat for w in ("restaurant", "takeout", "food", "pizza", "cafe",
                              "diner", "deli", "bakery", "bar", "grill")):
        if city_l:
            add(f"food delivery {city_l}")

    # Always a plain category+city as a baseline.
    if cat and city_l:
        add(f"{cat} {city_l}")

    return queries[:5]


# ── live geo-targeted SERP for one query ──────────────────────────────────────
def _serp_for_query(keyword: str, business_name: str, location_coordinate: str,
                    location_code: int, depth: int = 12) -> dict:
    """Run ONE geo-targeted live SERP. Return a structured analysis of where the
    business stands for `keyword`:

        {
          "query": keyword,
          "found": "organic" | "third_party" | "not_at_all",
          "found_via": "Facebook" | "" ,          # platform name if third_party
          "found_position": int | None,
          "competitors": [{"position", "domain", "title"}],  # real-website rivals above
          "local_pack": [{"title", "url", "has_site": bool}],
          "error": "" | "<msg>",
        }
    """
    out = {
        "query": keyword, "found": "not_at_all", "found_via": "",
        "found_position": None, "competitors": [], "local_pack": [], "error": "",
    }
    loc = {"location_coordinate": location_coordinate} if location_coordinate \
        else {"location_code": location_code}
    try:
        result = dfs_post("serp/google/organic/live/advanced", [
            {"keyword": keyword, **loc, "language_code": "en", "depth": depth}
        ])
        items = dfs_get_items(result)
    except Exception as e:                 # dfs_post already swallows, belt+suspenders
        out["error"] = str(e)
        return out

    competitors = []
    seen_comp_hosts = set()
    for item in items:
        itype = item.get("type") or ""
        # ── local pack / map results ──
        if itype in ("local_pack", "map", "google_maps", "maps_search"):
            title = (item.get("title") or "").strip()
            url = item.get("url") or item.get("domain") or ""
            lp_host = _host(url)
            has_site = bool(lp_host) and not _is_excluded_host(lp_host)
            out["local_pack"].append({
                "title": title[:80],
                "url": url,
                "has_site": has_site,
                "is_business": _name_match(business_name, title, lp_host),
            })
            # If our business is in the local pack but with NO own site, that's
            # still "visible on maps, invisible in search" — record found via maps
            # only if we haven't found a stronger (organic) signal.
            if _name_match(business_name, title, lp_host) and out["found"] == "not_at_all":
                out["found"] = "third_party"
                out["found_via"] = "Google Maps listing"
            continue

        if itype != "organic":
            continue

        pos = int(item.get("rank_absolute") or item.get("rank_group") or 0)
        url = item.get("url") or ""
        title = (item.get("title") or "").strip()
        host = _host(url)

        # Is THIS the target business?
        tp_label = _third_party_label(host)
        if _name_match(business_name, title, host):
            # Found — distinguish own-organic (impossible: no site) from third-party.
            if tp_label:
                if out["found"] != "organic":
                    out["found"] = "third_party"
                    out["found_via"] = tp_label
                    if out["found_position"] is None:
                        out["found_position"] = pos
            else:
                # Some non-excluded host carrying the name (rare for no-site biz) —
                # treat as a genuine organic appearance.
                out["found"] = "organic"
                out["found_via"] = host
                out["found_position"] = pos
            continue

        # Competitor with their OWN website ranking above (or anywhere on page 1).
        if host and not _is_excluded_host(host) and host not in seen_comp_hosts:
            seen_comp_hosts.add(host)
            competitors.append({"position": pos, "domain": host, "title": title[:80]})

    competitors.sort(key=lambda c: c["position"] or 999)
    out["competitors"] = competitors[:5]
    return out


# ── main assembler ────────────────────────────────────────────────────────────
def build_greenfield_report(name, city, region, gl="us", places=None) -> dict:
    """Assemble the greenfield report data dict. Never raises.

    Args:
        name:   business name.
        city:   city.
        region: state/province.
        gl:     "us" | "ca" | … (Serper geo + DataForSEO country fallback).
        places: optional pre-fetched Serper place dict (from fetch_serper_gmb-style
                call). If None, this fetches it via fetch_serper.fetch_serper_gmb.

    Returns a dict consumed by render_greenfield().
    """
    name = (name or "").strip()
    city = (city or "").strip()
    region = (region or "").strip()
    gl = (gl or "us").strip().lower()
    location_code = _LOC_BY_GL.get(gl, 2840)

    # ── 1. GMB strength + coordinates (Serper Places) ──────────────────────────
    gmb = {
        "name": name, "category": "", "address": "", "phone": "",
        "rating": 0.0, "review_count": 0, "price_level": "",
        "latitude": None, "longitude": None, "found": False,
    }
    if places:
        p = places
    else:
        p = {}
        try:
            from .fetch_serper import fetch_serper_gmb
            serper = fetch_serper_gmb("", name, city, region) or {}
            if serper.get("gmb_found"):
                p = {
                    "title": serper.get("gmb_name"),
                    "category": serper.get("gmb_category"),
                    "address": serper.get("gmb_address"),
                    "phoneNumber": serper.get("gmb_phone"),
                    "rating": serper.get("gmb_rating"),
                    "ratingCount": serper.get("gmb_review_count"),
                    "website": serper.get("gmb_website"),
                }
            # fetch_serper_gmb doesn't return coordinates/priceLevel → raw call
            p2 = _raw_serper_place(name, city, region, gl)
            if p2:
                # prefer the richer raw place (has lat/lng/priceLevel)
                p = {**p, **{k: v for k, v in p2.items() if v not in (None, "")}}
        except Exception as e:
            print(f"[WARN] greenfield: Serper GMB fetch failed: {e}", file=sys.stderr)

    if p:
        gmb["found"] = True
        gmb["name"] = (p.get("title") or name) or name
        gmb["category"] = p.get("category") or ""
        gmb["address"] = p.get("address") or ""
        gmb["phone"] = p.get("phoneNumber") or p.get("phone") or ""
        try:
            gmb["rating"] = float(p.get("rating") or 0)
        except (TypeError, ValueError):
            gmb["rating"] = 0.0
        try:
            gmb["review_count"] = int(p.get("ratingCount") or p.get("reviews") or 0)
        except (TypeError, ValueError):
            gmb["review_count"] = 0
        gmb["price_level"] = p.get("priceLevel") or ""
        lat, lng = p.get("latitude"), p.get("longitude")
        try:
            if lat is not None and lng is not None:
                gmb["latitude"], gmb["longitude"] = float(lat), float(lng)
        except (TypeError, ValueError):
            pass

    coord = ""
    if gmb["latitude"] is not None and gmb["longitude"] is not None:
        coord = f"{gmb['latitude']},{gmb['longitude']}"

    # ── 2. derive queries + run geo-targeted live SERP for each ────────────────
    queries = _derive_queries(gmb["category"], city)
    if not queries:
        # last resort: brand + city, brand near me
        if name and city:
            queries = [f"{name} {city}".strip()]

    query_results = []
    for kw in queries:
        block = _serp_for_query(kw, gmb["name"], coord, location_code)
        query_results.append(block)

    # ── 3. verdict / aggregate ─────────────────────────────────────────────────
    total = len(query_results)
    invisible = sum(1 for q in query_results if q["found"] == "not_at_all")
    third_party = sum(1 for q in query_results if q["found"] == "third_party")
    organic = sum(1 for q in query_results if q["found"] == "organic")

    # Unique website-having competitors across all queries (the ones taking clicks).
    comp_seen = {}
    for q in query_results:
        for c in q["competitors"]:
            d = c["domain"]
            if d and d not in comp_seen:
                comp_seen[d] = c
    top_competitors = sorted(comp_seen.values(), key=lambda c: c["position"] or 999)[:8]

    # Verdict line — truthful, derived from the counts.
    missing = invisible + third_party     # not ranking with an owned site
    if total == 0:
        verdict = (f"We couldn't pull live local search results for {gmb['name'] or name} — "
                   f"but with no website, you can't rank in Google search at all.")
    elif missing == 0:
        verdict = (f"{gmb['name'] or name} shows up for these searches — but only through "
                   f"profiles you don't own. A website is what captures that traffic as yours.")
    else:
        verdict = (f"Invisible (or only via third-party listings) for {missing} of {total} "
                   f"key local searches — competitors WITH websites are taking those clicks.")

    data = {
        "name": gmb["name"] or name,
        "city": city,
        "region": region,
        "gl": gl,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "coordinate": coord,
        "gmb": gmb,
        "queries": query_results,
        "summary": {
            "total_queries": total,
            "invisible": invisible,
            "third_party_only": third_party,
            "organic": organic,
            "missing": missing,
        },
        "top_competitors": top_competitors,
        "verdict": verdict,
    }
    return data


def _raw_serper_place(name, city, region, gl) -> dict:
    """Direct Serper /places call to get the RICH place (lat/lng/priceLevel that
    fetch_serper_gmb doesn't surface). Returns places[0] or {} — never raises."""
    import json as _json
    import urllib.request
    try:
        from .fetch_serper import _serper_key
        key = _serper_key()
    except Exception:
        key = os.environ.get("SERPER_API_KEY", "").strip()
    if not key:
        return {}
    q = " ".join(p for p in (name, city, region) if p).strip()
    if not q:
        return {}
    try:
        body = _json.dumps({"q": q, "gl": gl or "us"}).encode()
        req = urllib.request.Request(
            "https://google.serper.dev/places", data=body, method="POST",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=25) as r:
            d = _json.loads(r.read().decode())
        places = d.get("places") or []
        return places[0] if places else {}
    except Exception as e:
        print(f"[WARN] greenfield: raw Serper places failed: {e}", file=sys.stderr)
        return {}


# ── renderer ──────────────────────────────────────────────────────────────────
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "template.html")


def _extract_head_and_style(template_path: str) -> tuple:
    """Pull the <head> inner + the full <style> block from the real template so the
    greenfield report visually matches the real brand reports. (Mirrors
    render._extract_css_and_static.) Fail-soft to minimal styling."""
    try:
        with open(template_path) as f:
            t = f.read()
        head_match = re.search(r"<head>(.*?)</head>", t, re.DOTALL)
        head_inner = head_match.group(1) if head_match else ""
        style_match = re.search(r"(<style>.*?</style>)", t, re.DOTALL)
        style_block = style_match.group(1) if style_match else "<style></style>"
        return head_inner, style_block
    except Exception as e:
        print(f"[WARN] greenfield: template head extraction failed: {e}", file=sys.stderr)
        return "", "<style></style>"


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _initials(name: str) -> str:
    toks = [t for t in _TOKEN_RE.findall((name or "").lower()) if t not in
            {"the", "and", "of", "a", "an"}]
    if not toks:
        toks = _TOKEN_RE.findall((name or "X").lower()) or ["x"]
    letters = "".join(t[0] for t in toks[:3]).upper()
    return letters or "?"


def _found_cell(q: dict) -> str:
    """HTML for the 'where you rank' cell."""
    f = q.get("found")
    if f == "organic":
        pos = q.get("found_position")
        return (f'<span class="gf-rank gf-rank-warn">#{_esc(pos)}</span>'
                if pos else '<span class="gf-rank gf-rank-warn">listed</span>')
    if f == "third_party":
        via = q.get("found_via") or "a third-party listing"
        pos = q.get("found_position")
        pos_txt = f" (#{_esc(pos)})" if pos else ""
        return (f'<span class="gf-rank gf-rank-warn">via {_esc(via)}{pos_txt}</span>'
                f'<div class="gf-sub">not your own site</div>')
    return '<span class="gf-rank gf-rank-bad">Not found</span>'


def render_greenfield(data: dict) -> str:
    """Build a polished standalone HTML report from build_greenfield_report() data.

    Reuses the real template's <head> + <style> so it looks consistent, then adds a
    focused greenfield-specific body + a small scoped style block. Never raises."""
    data = data or {}
    gmb = data.get("gmb") or {}
    name = data.get("name") or gmb.get("name") or "Your Business"
    city = data.get("city") or ""
    region = data.get("region") or ""
    queries = data.get("queries") or []
    summary = data.get("summary") or {}
    competitors = data.get("top_competitors") or []
    verdict = data.get("verdict") or ""

    head_inner, style_block = _extract_head_and_style(_TEMPLATE_PATH)

    rating = gmb.get("rating") or 0
    reviews = gmb.get("review_count") or 0
    category = gmb.get("category") or ""
    address = gmb.get("address") or ""
    phone = gmb.get("phone") or ""
    price = gmb.get("price_level") or ""
    location = ", ".join(p for p in (city, region) if p)

    # ── hero reputation line ──
    if rating and reviews:
        rep_stat = f'{rating:g}★ from {reviews:,} reviews'
        rep_lead = (f'<span class="gf-big">{rating:g}★</span> '
                    f'<span class="gf-big-sub">{reviews:,} reviews</span>')
    elif reviews:
        rep_stat = f'{reviews:,} reviews'
        rep_lead = f'<span class="gf-big">{reviews:,}</span> <span class="gf-big-sub">reviews</span>'
    else:
        rep_stat = "a real local reputation"
        rep_lead = f'<span class="gf-big">{_esc(name)}</span>'

    # ── per-query table rows ──
    rows = []
    for q in queries:
        comp_html = ""
        comps = q.get("competitors") or []
        if comps:
            chips = "".join(
                f'<span class="gf-comp">{_esc(c["domain"])}'
                + (f' <em>#{_esc(c["position"])}</em>' if c.get("position") else "")
                + "</span>"
                for c in comps[:4]
            )
            comp_html = f'<div class="gf-comps">{chips}</div>'
        else:
            comp_html = '<span class="gf-muted">—</span>'
        rows.append(
            f'<tr><td class="gf-q">“{_esc(q.get("query"))}”</td>'
            f'<td>{_found_cell(q)}</td>'
            f'<td>{comp_html}</td></tr>'
        )
    rows_html = "\n".join(rows) or (
        '<tr><td colspan="3" class="gf-muted">Live local search data unavailable — '
        'but with no website you cannot appear in Google\'s organic results.</td></tr>'
    )

    # ── competitor list (gap section) ──
    if competitors:
        comp_items = "".join(
            f'<li><strong>{_esc(c["domain"])}</strong>'
            + (f' — ranking #{_esc(c["position"])}' if c.get("position") else "")
            + (f'<div class="gf-sub">{_esc(c["title"])}</div>' if c.get("title") else "")
            + "</li>"
            for c in competitors[:6]
        )
        comp_block = f'<ul class="gf-list">{comp_items}</ul>'
    else:
        comp_block = ('<p class="gf-muted">We could not isolate website-owning rivals in this '
                      'run, but the search results above are dominated by businesses and '
                      'aggregators — not by you.</p>')

    total = summary.get("total_queries") or 0
    missing = summary.get("missing") or 0

    # ── facts row ──
    facts = []
    if category:
        facts.append(("Category", category))
    if location:
        facts.append(("Location", location))
    if price:
        facts.append(("Price", price))
    if phone:
        facts.append(("Phone", phone))
    facts_html = "".join(
        f'<div class="gf-fact"><span class="gf-fact-k">{_esc(k)}</span>'
        f'<span class="gf-fact-v">{_esc(v)}</span></div>'
        for k, v in facts
    )

    gen_at = (data.get("generated_at") or "")[:10]

    scoped_css = """
<style>
  .gf-wrap{max-width:860px;margin:0 auto;padding:28px 22px 60px;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;
    color:#0f172a;line-height:1.6;}
  .gf-hero{background:linear-gradient(135deg,#0b3d2e 0%,#11603f 55%,#1f8a5b 100%);
    color:#fff;border-radius:20px;padding:34px 30px;margin:0 0 26px;
    box-shadow:0 18px 40px -18px rgba(13,80,55,.55);}
  .gf-hero .gf-badge{width:64px;height:64px;border-radius:16px;background:rgba(255,255,255,.16);
    display:flex;align-items:center;justify-content:center;font-weight:800;font-size:24px;
    letter-spacing:.5px;margin-bottom:16px;border:1px solid rgba(255,255,255,.25);}
  .gf-hero h1{margin:0 0 4px;font-size:30px;line-height:1.15;font-weight:800;}
  .gf-hero .gf-loc{opacity:.85;margin:0 0 18px;font-size:15px;}
  .gf-big{font-size:40px;font-weight:800;}
  .gf-big-sub{font-size:18px;opacity:.9;font-weight:600;}
  .gf-hero .gf-line{font-size:18px;margin:14px 0 0;font-weight:600;max-width:56ch;}
  .gf-hero .gf-line strong{color:#ffe08a;}
  .gf-facts{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 28px;}
  .gf-fact{background:#f1f5f4;border:1px solid #dbe7e2;border-radius:10px;padding:8px 14px;
    display:flex;flex-direction:column;}
  .gf-fact-k{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#5b7a6f;font-weight:700;}
  .gf-fact-v{font-size:15px;font-weight:600;color:#11342a;}
  .gf-sec{margin:34px 0;}
  .gf-sec h2{font-size:21px;font-weight:800;margin:0 0 6px;color:#0b3d2e;}
  .gf-sec .gf-intro{color:#475569;margin:0 0 16px;font-size:15px;}
  .gf-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e2e8e5;
    border-radius:14px;overflow:hidden;font-size:14.5px;}
  .gf-table th{background:#0b3d2e;color:#fff;text-align:left;padding:12px 14px;font-size:12px;
    text-transform:uppercase;letter-spacing:.05em;}
  .gf-table td{padding:13px 14px;border-top:1px solid #eef2f0;vertical-align:top;}
  .gf-q{font-weight:700;color:#11342a;}
  .gf-rank{display:inline-block;padding:3px 10px;border-radius:999px;font-weight:700;font-size:13px;}
  .gf-rank-bad{background:#fde2e2;color:#b42318;}
  .gf-rank-warn{background:#fef3cd;color:#9a6700;}
  .gf-sub{font-size:12px;color:#64748b;margin-top:3px;}
  .gf-comps{display:flex;flex-wrap:wrap;gap:6px;}
  .gf-comp{background:#eef5f1;border:1px solid #d6e6dd;border-radius:8px;padding:3px 9px;
    font-size:12.5px;color:#0b3d2e;font-weight:600;}
  .gf-comp em{color:#1f8a5b;font-style:normal;font-weight:700;}
  .gf-muted{color:#94a3b8;}
  .gf-verdict{background:#fff7ed;border:1px solid #fed7aa;border-left:5px solid #ea580c;
    border-radius:12px;padding:18px 20px;font-size:16px;font-weight:600;color:#7c2d12;margin:8px 0 0;}
  .gf-gap{background:#0b3d2e;color:#eafff5;border-radius:16px;padding:26px 26px;margin:34px 0;}
  .gf-gap h2{color:#fff;margin-top:0;}
  .gf-list{margin:8px 0 0;padding-left:20px;}
  .gf-list li{margin:8px 0;}
  .gf-list .gf-sub{color:#a7d8c4;}
  .gf-unlock{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:16px;}
  .gf-card{background:#fff;border:1px solid #e2e8e5;border-radius:14px;padding:18px;}
  .gf-card h3{margin:0 0 6px;font-size:16px;color:#0b3d2e;}
  .gf-card p{margin:0;font-size:14px;color:#475569;}
  .gf-foot{margin-top:40px;color:#94a3b8;font-size:12px;text-align:center;}
</style>
"""

    unlock_cards = [
        ("Rank for the searches you're missing",
         f"You're absent (or only third-party) for {missing} of {total} key local searches. "
         f"A website is what lets Google rank YOU — not just the aggregators."
         if total else
         "A website is what lets Google rank you in organic search — right now you can't appear at all."),
        ("Own your brand search",
         f"When someone searches “{_esc(name)}”, a site you control is the first result — "
         "your hours, menu, and booking, not a third party's version of you."),
        ("Capture the delivery / aggregator margin",
         "Aggregators charge a cut and own the customer. Your own site (with ordering/booking) "
         "keeps the margin and the relationship."),
        ("Turn reputation into bookings",
         f"You already have {rep_stat}. A website turns that trust into a direct path to call, "
         "order, or book — instead of sending clicks to a competitor with a site."),
    ]
    unlock_html = "".join(
        f'<div class="gf-card"><h3>{_esc(t)}</h3><p>{b}</p></div>'
        for t, b in unlock_cards
    )

    body = f"""
<div class="gf-wrap">

  <div class="gf-hero">
    <div class="gf-badge">{_esc(_initials(name))}</div>
    <h1>{_esc(name)}</h1>
    <p class="gf-loc">{_esc(location)}{(' · ' + _esc(category)) if category else ''}</p>
    <div>{rep_lead}</div>
    <p class="gf-line">A genuine local reputation — and <strong>invisible on Google search</strong>
       because you have no website.</p>
  </div>

  {f'<div class="gf-facts">{facts_html}</div>' if facts_html else ''}

  <div class="gf-sec">
    <h2>What customers see when they search for you</h2>
    <p class="gf-intro">These are the real searches a nearby customer runs — checked live at your
       exact location. Here's where you show up, and who's showing up instead.</p>
    <table class="gf-table">
      <thead><tr><th>Search</th><th>Where you rank</th><th>Sites ranking instead</th></tr></thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
    <div class="gf-verdict">{_esc(verdict)}</div>
  </div>

  <div class="gf-gap">
    <h2>The gap: you have the reputation, not the visibility</h2>
    <p>People already trust {_esc(name)} — {_esc(rep_stat)}. But trust only converts when people
       can FIND you. Today, the businesses winning these searches all have one thing you don't:
       a website. These are the rivals capturing clicks that should be yours:</p>
    {comp_block}
  </div>

  <div class="gf-sec">
    <h2>What a website unlocks</h2>
    <p class="gf-intro">A site is the one missing piece between your reputation and the customers
       searching right now.</p>
    <div class="gf-unlock">
      {unlock_html}
    </div>
  </div>

  <div class="gf-foot">
    Brand snapshot for {_esc(name)} · generated {_esc(gen_at)} · live local search data.
  </div>

</div>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
{head_inner}
{style_block}
{scoped_css}
<title>{_esc(name)} — Brand Snapshot</title>
</head>
<body>
{body}
</body>
</html>"""
