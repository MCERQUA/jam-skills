#!/usr/bin/env python3
"""
stitch-finalize.py — Final post-conversion fixups that the deterministic pipeline
needs to produce a complete site:

  1. Rewrite remote image URLs (e.g. src.jam-bot.com/uploads/*, lh3.googleusercontent
     /aida-public/*) → local /images/intake/<sha8>.<ext>. Downloads if missing.

  2. Inject logo <img> into navbars: replace the Stitch wordmark <span> at the top of
     each page with an <img src="<local logo>" alt="<businessName>"> wrapped in a
     Link to "/".

  3. Build a Services dropdown in the navbar linking to every /services/<service>
     OR every top-level service-* route discovered under src/app/.

  4. Rewrite footer Service Areas list links from href="#" to /<city-slug> (where the
     city has a built page) — leaves text-only otherwise.

Generic. Runs after content-layer. No project/client hardcoding.

Usage:
  stitch-finalize.py --intake <intake.json> --project <project-root>
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


SERVICE_HINT_PAT = re.compile(r"^(pvc|composite|cedar|membrane|custom-curved|deck-railing|"
                              r"pergolas?|deck-repair|outdoor-living|trex|vinyl|wood)",
                              re.IGNORECASE)

# Reserved navbar/system slugs that are NOT location pages even if they sit at
# top-level src/app/. Anything else at top-level that has page.tsx and isn't a
# service is treated as a location candidate (validated against intake.targetMarkets
# when available).
RESERVED_SLUGS = {
    "about", "services", "gallery", "contact", "faq", "blog",
    "privacy", "terms", "api", "og", "sitemap", "robots",
    "deck-cost-seattle",  # cost guides — covered by their own link if added later
}


def detect_ext(url: str) -> str:
    p = urlparse(url).path.lower()
    for cand in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"):
        if p.endswith(cand):
            return ".jpg" if cand == ".jpeg" else cand
    return ".jpg"


def download_to_intake(url: str, project: Path) -> str | None:
    if not url.startswith(("http://", "https://")):
        return url
    images_dir = project / "public" / "images" / "intake"
    images_dir.mkdir(parents=True, exist_ok=True)
    sha8 = hashlib.sha1(url.encode()).hexdigest()[:8]
    ext = detect_ext(url)
    local_name = f"{sha8}{ext}"
    target = images_dir / local_name
    if not target.exists():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                target.write_bytes(r.read())
        except Exception as e:
            sys.stderr.write(f"download fail {url}: {e}\n")
            return None
    return f"/images/intake/{local_name}"


# ─────────────────────────────────────────────────────────────────────────────
# Pass 1: rewrite remote image URLs to local
# ─────────────────────────────────────────────────────────────────────────────
REMOTE_IMG_RE = re.compile(
    r'src="(https?://[^"]+\.(?:jpg|jpeg|png|webp|gif|svg)(?:\?[^"]*)?)"',
    re.IGNORECASE,
)

def rewrite_remote_images(text: str, project: Path) -> tuple[str, int, int]:
    """Replace every remote img URL with a downloaded local path. Returns
    (new_text, downloaded, fail)."""
    seen: dict[str, str] = {}
    fails = 0
    def sub(m: re.Match) -> str:
        nonlocal fails
        url = m.group(1)
        if url in seen:
            local = seen[url]
        else:
            local = download_to_intake(url, project)
            if local is None:
                fails += 1
                seen[url] = url  # leave as-is
                return m.group(0)
            seen[url] = local
        return f'src="{local}"'
    new_text = REMOTE_IMG_RE.sub(sub, text)
    downloaded = sum(1 for v in seen.values() if v.startswith("/images/"))
    return new_text, downloaded, fails


# ─────────────────────────────────────────────────────────────────────────────
# Pass 2: replace Stitch wordmark with <img> logo
# ─────────────────────────────────────────────────────────────────────────────
# Stitch wordmarks look like:
#   <span className="text-slate-900 font-extrabold text-xl ...tracking-tight">
#     Seattle Decking <span className="text-primary">Co.</span>
#   </span>
# A nested <span>...</span> means we can't use a non-greedy regex (matches the
# inner closing tag). Solution: find the OPENING <span ...> by signature, then
# walk forward counting <span> opens vs closes until balance hits zero.

WORDMARK_OPEN_RE = re.compile(
    r'<span\s+className="[^"]*\b(?:font-extrabold|font-bold|font-black)\b[^"]*\btracking-tight\b[^"]*"[^>]*>',
)

def find_balanced_span(text: str, open_match: re.Match) -> tuple[int, int] | None:
    """Given an opening <span> match, return (start, end_after_closing) of the full
    balanced element, or None if not balanced."""
    start = open_match.start()
    depth = 1
    pos = open_match.end()
    n = len(text)
    while pos < n and depth > 0:
        next_open = text.find("<span", pos)
        next_close = text.find("</span>", pos)
        if next_close == -1:
            return None
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + len("<span")
        else:
            depth -= 1
            pos = next_close + len("</span>")
    if depth == 0:
        return start, pos
    return None


def inject_logo(text: str, logo_path: str, business_name: str) -> tuple[str, int]:
    """Replace the first wordmark <span>...</span> (with balanced nesting) with an
    <img> logo wrapped in a link to /. Returns (new_text, count)."""
    if not logo_path:
        return text, 0
    m = WORDMARK_OPEN_RE.search(text)
    if not m:
        return text, 0
    span = find_balanced_span(text, m)
    if not span:
        return text, 0
    start, end = span
    replacement = (
        f'<a href="/" className="flex items-center">'
        f'<img src="{logo_path}" alt="{business_name}" '
        f'className="h-10 w-auto object-contain" />'
        f'</a>'
    )
    return text[:start] + replacement + text[end:], 1


# ─────────────────────────────────────────────────────────────────────────────
# Pass 3: build a Services dropdown in the navbar
# ─────────────────────────────────────────────────────────────────────────────
NAVBAR_SERVICES_LINK_RE = re.compile(
    r'(<a\s+className="[^"]*"\s+href="/services">Services</a>)',
)

# Anchors used to inject Locations dropdown + Blog link AFTER existing nav items.
# Locations dropdown goes after Gallery. Blog link goes after Contact (if present)
# OR after FAQ (older Stitch templates). The first matching anchor wins.
NAVBAR_GALLERY_LINK_RE = re.compile(
    r'(<a\s+className="[^"]*"\s+href="/gallery">Gallery</a>)',
)
NAVBAR_CONTACT_LINK_RE = re.compile(
    r'(<a\s+className="[^"]*"\s+href="/contact">Contact</a>)',
)
NAVBAR_FAQ_LINK_RE = re.compile(
    r'(<a\s+className="[^"]*"\s+href="/faq">FAQ</a>)',
)
# Footer Privacy/Terms placeholder links: stitch templates leave these as href="#".
FOOTER_PRIVACY_RE = re.compile(
    r'<a\s+className="([^"]*)"\s+href="#">\s*Privacy Policy\s*</a>',
)
FOOTER_TERMS_RE = re.compile(
    r'<a\s+className="([^"]*)"\s+href="#">\s*Terms of Service\s*</a>',
)

def _dropdown_jsx(label: str, root_href: str, items: list[tuple[str, str]]) -> str:
    """Generic hover-dropdown JSX. items = [(slug, label), ...]."""
    items_jsx = "\n".join(
        f'              <a href="/{slug}" className="block px-4 py-2 text-sm text-slate-700 hover:bg-primary/10 hover:text-primary transition-colors">{lbl}</a>'
        for slug, lbl in items
    )
    return f'''<div className="relative group">
            <a href="{root_href}" className="text-slate-600 hover:text-primary font-bold text-sm uppercase tracking-wider transition-colors flex items-center gap-1">{label}<svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/></svg></a>
            <div className="absolute left-0 top-full pt-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
              <div className="bg-white rounded-xl shadow-2xl border border-slate-200 py-2 w-64">
{items_jsx}
              </div>
            </div>
          </div>'''


def build_services_dropdown(service_pages: list[tuple[str, str]]) -> str:
    """Return JSX for a hover-dropdown nav item showing all service pages."""
    if not service_pages:
        return ""
    return _dropdown_jsx("Services", "/services", service_pages)


def build_locations_dropdown(location_pages: list[tuple[str, str]]) -> str:
    """Return JSX for a hover-dropdown listing all location pages. Returned JSX
    is meant to be APPENDED after the Gallery link (additive, not destructive)."""
    if not location_pages:
        return ""
    # No /locations index page in the current pipeline; root link points to home
    # so the user always has something live behind the dropdown anchor.
    return _dropdown_jsx("Locations", "/", location_pages)


def build_blog_link() -> str:
    """A simple Blog top-level nav link, intended to be APPENDED after FAQ."""
    return ('<a className="text-slate-600 hover:text-primary font-bold text-sm '
            'uppercase tracking-wider transition-colors" href="/blog">Blog</a>')


def slug_to_label(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("-", " ").split())


def discover_service_pages(project: Path) -> list[tuple[str, str]]:
    """Return [(slug, label)] for every service-looking page under src/app/."""
    out = []
    app_dir = project / "src" / "app"
    if not app_dir.exists():
        return out
    for page in app_dir.iterdir():
        if not page.is_dir():
            continue
        if not (page / "page.tsx").exists():
            continue
        slug = page.name
        if SERVICE_HINT_PAT.match(slug):
            out.append((slug, slug_to_label(slug)))
    out.sort()
    return out


def discover_location_pages(project: Path, intake: dict) -> list[tuple[str, str]]:
    """Return [(slug, label)] for every location page under src/app/.
    A location is any top-level slug that:
      - has page.tsx
      - is NOT a service (per SERVICE_HINT_PAT)
      - is NOT in RESERVED_SLUGS
      - MATCHES a target market — either equals it OR contains it as a token
        (handles slugs like 'deck-builder-bellevue').
    The label is the matched city name only ('Bellevue'), not the full slug."""
    target_markets = [
        m.strip().lower().replace(" ", "-")
        for m in (intake.get("targetMarkets") or [])
        if isinstance(m, str) and m.strip()
    ]

    candidates: list[tuple[str, str]] = []
    app_dir = project / "src" / "app"
    if not app_dir.exists():
        return []
    for page in app_dir.iterdir():
        if not page.is_dir():
            continue
        if not (page / "page.tsx").exists():
            continue
        slug = page.name
        slow = slug.lower()
        if slow in RESERVED_SLUGS:
            continue
        if SERVICE_HINT_PAT.match(slow):
            continue

        if target_markets:
            # Find which market this slug references. Prefer longest market name
            # match so 'mercer-island' wins over 'mercer' if both were markets.
            matched_city = None
            for city in sorted(target_markets, key=len, reverse=True):
                if slow == city or f"-{city}" in f"-{slow}-" or f"-{city}-" in f"-{slow}-":
                    matched_city = city
                    break
            if not matched_city:
                continue
            label = slug_to_label(matched_city)
        else:
            label = slug_to_label(slug)
        candidates.append((slug, label))

    candidates.sort()
    return candidates


def has_blog(project: Path) -> bool:
    """True iff src/app/blog/page.tsx exists."""
    return (project / "src" / "app" / "blog" / "page.tsx").exists()


# ─────────────────────────────────────────────────────────────────────────────
# Driver
# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intake", required=True)
    ap.add_argument("--project", required=True)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    intake = json.loads(Path(args.intake).read_text())

    business_name = intake.get("businessName", "").strip()
    raw_logo = (intake.get("logo") or "").strip()
    logo_path = download_to_intake(raw_logo, project) if raw_logo else ""

    service_pages = discover_service_pages(project)
    location_pages = discover_location_pages(project, intake)
    blog_present = has_blog(project)

    services_dropdown = build_services_dropdown(service_pages) if service_pages else ""
    locations_dropdown = build_locations_dropdown(location_pages) if location_pages else ""
    blog_link = build_blog_link() if blog_present else ""

    pages = sorted((project / "src" / "app").rglob("page.tsx"))
    report = {
        "logo_local_path": logo_path,
        "service_pages_discovered": [slug for slug, _ in service_pages],
        "location_pages_discovered": [slug for slug, _ in location_pages],
        "blog_present": blog_present,
        "pages": [],
    }
    for page in pages:
        text = page.read_text()
        original = text

        text, dl_count, dl_fails = rewrite_remote_images(text, project)
        text, logo_n = inject_logo(text, logo_path, business_name) if logo_path else (text, 0)

        # Replace Services link with dropdown — idempotent (skip if already a
        # dropdown, detected by the dropdown's caret SVG signature).
        services_dropdown_n = 0
        if services_dropdown and ">Services<svg " not in text:
            text, services_dropdown_n = NAVBAR_SERVICES_LINK_RE.subn(services_dropdown, text, count=1)

        # Append Locations dropdown after Gallery link — idempotent on the page
        # (skip if a Locations dropdown is already present anywhere in this file).
        locations_dropdown_n = 0
        if locations_dropdown and ">Locations<svg " not in text:
            text, locations_dropdown_n = NAVBAR_GALLERY_LINK_RE.subn(
                lambda m: m.group(1) + locations_dropdown, text, count=1
            )

        # Append Blog link after Contact (preferred) or FAQ (fallback) — additive.
        # Idempotent: skip if a /blog link already exists in this file.
        blog_link_n = 0
        if blog_link and 'href="/blog"' not in text:
            new_text, n = NAVBAR_CONTACT_LINK_RE.subn(
                lambda m: m.group(1) + blog_link, text, count=1
            )
            if n == 0:
                new_text, n = NAVBAR_FAQ_LINK_RE.subn(
                    lambda m: m.group(1) + blog_link, text, count=1
                )
            text = new_text
            blog_link_n = n

        # Footer: rewrite Privacy/Terms href="#" → /privacy and /terms when those
        # pages exist. Idempotent — leaves the link as-is when target missing.
        privacy_rewrites = 0
        terms_rewrites = 0
        if (project / "src" / "app" / "privacy" / "page.tsx").exists():
            text, privacy_rewrites = FOOTER_PRIVACY_RE.subn(
                r'<a className="\1" href="/privacy">Privacy Policy</a>', text
            )
        if (project / "src" / "app" / "terms" / "page.tsx").exists():
            text, terms_rewrites = FOOTER_TERMS_RE.subn(
                r'<a className="\1" href="/terms">Terms of Service</a>', text
            )

        if text != original:
            page.write_text(text)
        report["pages"].append({
            "path": str(page.relative_to(project)),
            "remote_images_localized": dl_count,
            "image_download_fails": dl_fails,
            "logo_injected": logo_n,
            "services_dropdown_injected": services_dropdown_n,
            "locations_dropdown_injected": locations_dropdown_n,
            "blog_link_injected": blog_link_n,
            "footer_privacy_rewrites": privacy_rewrites,
            "footer_terms_rewrites": terms_rewrites,
        })

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
