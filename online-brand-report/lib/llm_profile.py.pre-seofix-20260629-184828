#!/usr/bin/env python3
"""
llm_profile — LLM-powered business-profile reader for the online-brand-report engine.

WHY THIS EXISTS
The report seeds keyword research from a `service` string. Historically that was
derived by regex from the homepage title/meta (`generate.py:detect_service`), which
produces garbage on many sites (azrimrepair.com → "restoration including cracks"
instead of "rim repair" — it's an auto rim/wheel repair shop). This module instead
asks Claude to READ the homepage and return an accurate, structured business profile.

DESIGN PRINCIPLES
  • Quality over cost — uses `--model sonnet` (the capable, client-facing tier).
  • NEVER Groq — Groq LLM is BANNED on this server (TTS only).
  • Fail-OPEN at every layer — any fetch error / claude-unavailable / timeout /
    non-JSON / placeholder result → return {} so the caller falls back to the
    existing deterministic `detect_service` regex path. Claude may be UNAVAILABLE
    inside tenant containers, so this MUST never crash a report run.
  • Additive — does not modify or replace `detect_service`; it runs FIRST and the
    regex stays as the fallback.

The Claude call is made through the sanctioned headless OAuth path:
    source /home/mike/MIKE-AI/scripts/with-claude-env.sh
    printf '%s' "$PROMPT" | claude -p --model sonnet
"""

import sys
import json
import re
import subprocess

import requests

# Reuse the report's existing normalizers so the LLM's primary_service is cleaned and
# geo-stripped exactly like the regex path would be (single source of truth).
try:
    import generate as _gen  # generate.py lives alongside the skill (on sys.path)
    _clean_service = _gen._clean_service
    _strip_geo_tail = _gen._strip_geo_tail
    _PLACEHOLDER_SERVICES = _gen._PLACEHOLDER_SERVICES
except Exception:  # pragma: no cover — fail-soft if import shape changes
    _PLACEHOLDER_SERVICES = {"", "your service", "service", "services", "general", "n/a"}

    def _clean_service(s: str) -> str:
        s = re.sub(r"\s+", " ", (s or "")).strip(" -|·•—,.\t")
        s = re.sub(r"\b(shop|store|company|co|inc|llc|ltd|corp)\b\.?$", "", s, flags=re.I).strip()
        return s

    def _strip_geo_tail(s: str) -> str:
        s = (s or "").strip()
        s = re.sub(r"\b(?:in|serving|near|across|throughout|around|for)\s+[A-Z][\w .,'&-]*$",
                   "", s).strip(" -|,&")
        s = re.sub(r"\s*&\s*(?:GTA|area|surrounding|region|county|counties)\b.*$",
                   "", s, flags=re.I).strip(" -|,&")
        return s


_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

CLAUDE_ENV_WRAPPER = "/home/mike/MIKE-AI/scripts/with-claude-env.sh"


# ── Homepage fetch ────────────────────────────────────────────────────────────
def fetch_homepage_text(domain: str) -> dict:
    """Fetch a domain's homepage and return its readable content for the LLM.

    Returns a dict:
        {"title", "meta_description", "headings":[...], "nav_links":[...], "body_excerpt"}
    Tries https then http, follows redirects, browser UA, ~15s timeout.
    Strips <script>/<style>. Fail-soft → {} on any error.
    """
    html = ""
    for scheme in ("https://", "http://"):
        try:
            r = requests.get(scheme + domain.lstrip("/"),
                             headers={"User-Agent": _UA},
                             timeout=15, allow_redirects=True)
            if r.status_code < 400 and r.text:
                html = r.text
                break
        except Exception:
            continue
    if not html:
        return {}

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content tags so the body excerpt is real visible text.
        for tag in soup(["script", "style", "noscript", "template", "svg"]):
            tag.decompose()

        title = ""
        if soup.title and soup.title.string:
            title = re.sub(r"\s+", " ", soup.title.string).strip()

        meta_description = ""
        md = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        if md and md.get("content"):
            meta_description = re.sub(r"\s+", " ", md["content"]).strip()
        if not meta_description:  # OG fallback
            ogd = soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
            if ogd and ogd.get("content"):
                meta_description = re.sub(r"\s+", " ", ogd["content"]).strip()

        headings = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            txt = re.sub(r"\s+", " ", h.get_text(" ", strip=True)).strip()
            if txt and txt not in headings:
                headings.append(txt)
            if len(headings) >= 25:
                break

        nav_links = []
        nav_containers = soup.find_all(["nav", "header"]) or [soup]
        for cont in nav_containers:
            for a in cont.find_all("a"):
                txt = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                if txt and 1 <= len(txt) <= 40 and txt.lower() not in (n.lower() for n in nav_links):
                    nav_links.append(txt)
            if len(nav_links) >= 30:
                break
        nav_links = nav_links[:30]

        body_text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
        body_excerpt = body_text[:2000]

        return {
            "title": title,
            "meta_description": meta_description,
            "headings": headings,
            "nav_links": nav_links,
            "body_excerpt": body_excerpt,
        }
    except Exception:
        return {}


# ── JSON extraction ───────────────────────────────────────────────────────────
def _extract_json_object(text: str):
    """Pull the first balanced {...} object out of arbitrary model output (which may
    wrap JSON in ```json fences or add stray prose). Returns a dict or None."""
    if not text:
        return None
    # strip code fences first
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        # find first '{' and walk to the matching '}'
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_str = False
        esc = False
        end = -1
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
        if end == -1:
            return None
        candidate = text[start:end + 1]
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _as_str_list(v, limit):
    """Coerce a value into a clean list of short non-empty strings, capped at `limit`."""
    if not isinstance(v, list):
        return []
    out = []
    for item in v:
        if not isinstance(item, str):
            continue
        s = re.sub(r"\s+", " ", item).strip()
        if s and s.lower() not in {x.lower() for x in out}:
            out.append(s)
        if len(out) >= limit:
            break
    return out


# ── LLM business profile ──────────────────────────────────────────────────────
def llm_business_profile(domain: str, page: dict = None, gmb_categories=None,
                         timeout: int = 70, name: str = "", city: str = "",
                         region: str = "") -> dict:
    """Read a company's homepage with Claude and return a structured business profile.

    Returns the validated profile dict on success, or {} on ANY failure (fetch error,
    claude unavailable, timeout, non-JSON, placeholder/empty primary_service). The
    caller (generate.py) falls back to the deterministic `detect_service` regex on {}.

    Schema (all keys present on success):
        primary_service : str  — single best 2-3 word SEO keyword (lowercase, no brand/city)
        services        : list — up to 8 distinct services
        keyword_seeds   : list — 5-10 search phrases (some with intent like 'X near me')
        industry        : str  — short vertical label
        city            : str  — city if clearly on the page, else ''
        region          : str  — state/province if clearly on the page, else ''
    """
    try:
        if page is None and domain:
            page = fetch_homepage_text(domain)
        page = page or {}
        have_page = bool(page.get("title") or page.get("body_excerpt") or page.get("headings"))
        cats = gmb_categories or []
        cats_txt = ", ".join(str(c)[:60] for c in cats[:6]) if cats else "(none)"

        if have_page:
            # ── Has a website → read it (the accurate, preferred path). ──
            title = (page.get("title") or "")[:300]
            meta = (page.get("meta_description") or "")[:500]
            headings_txt = " | ".join(h[:120] for h in (page.get("headings") or [])[:20])[:1500]
            nav_txt = ", ".join(n[:40] for n in (page.get("nav_links") or [])[:30])[:800]
            body = (page.get("body_excerpt") or "")[:2000]
            prompt = f"""You are analyzing a local-business website to seed SEO keyword research.
Read the page content below and identify what this business actually does — the
service a real customer would type into Google to find them. Do NOT guess from the
brand name alone; use the headings, navigation, and body copy.

DOMAIN: {domain}
GOOGLE BUSINESS CATEGORIES (if any): {cats_txt}

PAGE TITLE: {title}
META DESCRIPTION: {meta}
HEADINGS (h1/h2/h3): {headings_txt}
NAVIGATION LINKS: {nav_txt}
BODY TEXT EXCERPT: {body}

Return ONLY a single JSON object (no prose, no markdown fences) with EXACTLY these keys:
{{
  "primary_service": "<the single best 2-3 word SEO search keyword a customer types, lowercase, no brand/city, e.g. 'rim repair', 'spray foam insulation', 'screen printing'>",
  "services": ["<up to 8 distinct services they offer, short phrases>"],
  "keyword_seeds": ["<5-10 search phrases (include a couple service+intent like 'X near me') to research, lowercase, no city>"],
  "industry": "<short vertical label, e.g. 'auto wheel repair', 'insulation contractor'>",
  "city": "<city if clearly stated on the page, else ''>",
  "region": "<state/province if clearly stated on the page, else ''>"
}}"""
        elif (name or "").strip():
            # ── NO website → infer the vertical from the business NAME + GMB category
            #    + city. This is what keeps the no-website report's keyword research
            #    RICH — that research IS the foundation/plan for the site we'll build. ──
            print(f"[llm_profile] no homepage — inferring from name '{name}' "
                  f"({city} {region}), GMB cats: {cats_txt}", file=sys.stderr)
            prompt = f"""A local business has NO website yet. From its NAME, location, and Google
Business category, infer what it most likely does — the service a real customer would
type into Google — so we can build SEO keyword research that becomes the plan for their
NEW website. Be reasonable and concrete; do not invent obscure services.

BUSINESS NAME: {name}
LOCATION: {city} {region}
GOOGLE BUSINESS CATEGORIES (if any): {cats_txt}

Return ONLY a single JSON object (no prose, no markdown fences) with EXACTLY these keys:
{{
  "primary_service": "<the single best 2-3 word SEO search keyword a customer types, lowercase, no brand/city, e.g. 'rim repair', 'custom apparel printing', 'screen printing'>",
  "services": ["<up to 8 distinct services they likely offer, short phrases>"],
  "keyword_seeds": ["<5-10 search phrases (include a couple with intent like 'X near me') to research, lowercase, no city>"],
  "industry": "<short vertical label, e.g. 'custom apparel printing', 'insulation contractor'>",
  "city": "{city}",
  "region": "{region}"
}}"""
        else:
            print("[llm_profile] unavailable, falling back "
                  "(no homepage and no business name)", file=sys.stderr)
            return {}

        try:
            proc = subprocess.run(
                ["bash", "-lc",
                 f"source {CLAUDE_ENV_WRAPPER} 2>/dev/null; claude -p --model sonnet"],
                input=prompt, capture_output=True, text=True, timeout=timeout)
        except Exception as e:
            print(f"[llm_profile] unavailable, falling back (claude call failed: {e})",
                  file=sys.stderr)
            return {}

        if proc.returncode != 0 or not (proc.stdout or "").strip():
            print(f"[llm_profile] unavailable, falling back "
                  f"(rc={proc.returncode}, empty/err output)", file=sys.stderr)
            return {}

        obj = _extract_json_object(proc.stdout)
        if not obj:
            print("[llm_profile] unavailable, falling back (no JSON in output)",
                  file=sys.stderr)
            return {}

        # Validate + normalize primary_service through the report's own cleaners.
        raw_ps = obj.get("primary_service")
        if not isinstance(raw_ps, str):
            raw_ps = ""
        ps = _clean_service(_strip_geo_tail(raw_ps)).lower().strip()
        if not ps or ps in _PLACEHOLDER_SERVICES:
            print("[llm_profile] unavailable, falling back "
                  "(empty/placeholder primary_service)", file=sys.stderr)
            return {}

        services = _as_str_list(obj.get("services"), 8)
        keyword_seeds = _as_str_list(obj.get("keyword_seeds"), 10)
        industry = obj.get("industry") if isinstance(obj.get("industry"), str) else ""
        industry = re.sub(r"\s+", " ", industry).strip()
        city = obj.get("city") if isinstance(obj.get("city"), str) else ""
        city = re.sub(r"\s+", " ", city).strip()
        region = obj.get("region") if isinstance(obj.get("region"), str) else ""
        region = re.sub(r"\s+", " ", region).strip()

        profile = {
            "primary_service": ps,
            "services": services,
            "keyword_seeds": keyword_seeds,
            "industry": industry,
            "city": city,
            "region": region,
        }
        print(f"[llm_profile] {domain} → primary_service='{ps}' "
              f"({len(services)} services, {len(keyword_seeds)} seeds)", file=sys.stderr)
        return profile
    except Exception as e:
        print(f"[llm_profile] unavailable, falling back (unexpected: {e})", file=sys.stderr)
        return {}


# ── CLI smoke-test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    doms = sys.argv[1:] or ["azrimrepair.com"]
    for d in doms:
        print(d, json.dumps(llm_business_profile(d)))
