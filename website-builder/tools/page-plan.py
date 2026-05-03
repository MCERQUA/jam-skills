#!/usr/bin/env python3
"""page-plan.py

Phase 3.5 of the website-build pipeline. Deterministic page plan generator.

For every page in `intake.pages`, assign:
  - the Stitch source HTML it should be built from (literal if supplied, cloned
    from a sibling if not, or HALT if neither)
  - the primary + secondary keywords (from DataForSEO research)
  - the page role (literal | cloned-from | needs-decision)

The output is `ai/page-map.json`. Phase 5 BUILD-PAGES is locked to it — it may
NOT build a page that isn't in this map and may NOT skip one that is.

Usage:
    page-plan.py <project-path>

Exit codes:
    0 — page-map.json written, no halt-warnings
    1 — page-map.json written WITH halt-warnings (Phase 5 must not run; surface
        for review)
    2 — invalid project layout (missing intake.json, missing structure.json, etc.)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# Slug normalization for matching Stitch screen names to intake page slugs.
# "Modern Artisan Homepage" → "home"
# "Modern Artisan About Us" → "about"
NAME_TO_SLUG_PATTERNS = [
    (re.compile(r"\bhome(\s*page)?\b", re.I), "home"),
    (re.compile(r"\babout(\s*us)?\b", re.I), "about"),
    (re.compile(r"\bservices?\b", re.I), "services"),
    (re.compile(r"\bcontact(\s*us)?\b", re.I), "contact"),
    (re.compile(r"\bfaq\b", re.I), "faq"),
    (re.compile(r"\bgallery\b", re.I), "gallery"),
    (re.compile(r"\bportfolio\b", re.I), "gallery"),
    (re.compile(r"\bblog\b", re.I), "blog"),
    (re.compile(r"\breviews?\b", re.I), "reviews"),
    (re.compile(r"\btestimonials?\b", re.I), "reviews"),
    (re.compile(r"\bpricing\b", re.I), "pricing"),
    (re.compile(r"\bteam\b", re.I), "team"),
]

# Sensible clone fallbacks: if intake.pages lists `contact` but no `contact`
# Stitch screen, clone the closest stylistic sibling so the new page carries
# the same look. NEVER fall back to a generic SERVICE_LOCAL boilerplate template.
CLONE_FALLBACKS = {
    "contact": ["home", "about"],       # contact pages usually mirror home's hero+CTA pattern
    "gallery": ["services", "home"],    # gallery pages mirror services' grid layout
    "blog": ["services", "home"],
    "reviews": ["about", "home"],
    "team": ["about"],
    "pricing": ["services"],
    # any new service-detail slug (e.g. /pvc-decking) clones services
}


def name_to_slug(name: str) -> str | None:
    for pat, slug in NAME_TO_SLUG_PATTERNS:
        if pat.search(name):
            return slug
    return None


def derive_keywords(slug: str, keywords_md_text: str, primary_keywords_intake: list[str]) -> tuple[str, list[str]]:
    """Return (primary_keyword, secondary_keywords[]) for a page.

    Heuristic — match keyword strings to slug. Prefer keywords from keywords.md
    that contain the slug or a known synonym for it.
    """
    synonyms = {
        "home": ["deck builder", "deck construction", "deck company"],
        "about": ["about", "our team", "company"],
        "services": ["services", "decking services", "outdoor"],
        "contact": ["contact", "quote", "estimate", "consultation"],
        "faq": ["faq", "frequently asked", "questions"],
        "gallery": ["gallery", "portfolio", "projects"],
        "pvc-decking": ["pvc decking", "pvc deck"],
        "composite-decking": ["composite decking", "composite deck"],
        "cedar-decking": ["cedar decking", "cedar deck"],
    }
    needles = synonyms.get(slug, [slug.replace("-", " ")])

    matches: list[str] = []
    for line in keywords_md_text.lower().splitlines():
        for n in needles:
            if n in line:
                # Pull the keyword from the first column-ish chunk
                m = re.search(r"\|\s*\d+\s*\|\s*([^|]+?)\s*\|", line)
                if m:
                    kw = m.group(1).strip()
                    if kw and kw not in matches:
                        matches.append(kw)
                    break
    primary = matches[0] if matches else (primary_keywords_intake[0] if primary_keywords_intake else slug.replace("-", " "))
    secondary = matches[1:5]
    return primary, secondary


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2

    project = Path(argv[1]).resolve()
    intake_path = project / ".intake.json"
    structure_path = project / ".stitch-pages" / "structure.json"
    keywords_md = project / "ai" / "research" / "keywords.md"

    if not intake_path.exists():
        print(f"ERROR: intake.json not found at {intake_path}", file=sys.stderr)
        return 2
    if not structure_path.exists():
        print(f"ERROR: .stitch-pages/structure.json not found — Phase 3 incomplete", file=sys.stderr)
        return 2

    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    keywords_text = keywords_md.read_text(encoding="utf-8") if keywords_md.exists() else ""

    pages_requested: list[str] = list(intake.get("pages") or [])
    stitch_screens: list[dict] = list(intake.get("stitchScreens") or [])
    primary_keywords_intake: list[str] = list(intake.get("primaryKeywords") or [])

    # Build name→slug→screenId map from intake.stitchScreens
    name_to_screen = {}
    for s in stitch_screens:
        slug = name_to_slug(s.get("name", ""))
        if slug:
            name_to_screen[slug] = s

    # Also build slug→html_path map from what was actually fetched into .stitch-pages/
    fetched_slugs = set(structure.keys())

    pages_out: list[dict] = []
    warnings: list[str] = []
    halt_warnings: list[str] = []

    # Service-detail pages: any page in intake.services whose slug isn't in
    # intake.pages explicitly, but the user may want as a sub-page. Skip for v2.

    for slug in pages_requested:
        route = "/" if slug == "home" else f"/{slug}"

        if slug in fetched_slugs:
            # Literal Stitch supplied + fetched
            screen = name_to_screen.get(slug)
            screen_id = screen.get("id") if screen else None
            primary_kw, secondary_kw = derive_keywords(slug, keywords_text, primary_keywords_intake)
            pages_out.append({
                "slug": slug,
                "route": route,
                "stitch_source_screen_id": screen_id,
                "stitch_html": f".stitch-pages/{slug}.html",
                "role": "literal",
                "expected_section_count": structure[slug].get("sectionCount"),
                "primary_keyword": primary_kw,
                "secondary_keywords": secondary_kw,
            })
        else:
            # No literal Stitch — try clone fallback
            clone_options = CLONE_FALLBACKS.get(slug, ["home"])
            clone_from = next((s for s in clone_options if s in fetched_slugs), None)
            primary_kw, secondary_kw = derive_keywords(slug, keywords_text, primary_keywords_intake)

            if clone_from:
                pages_out.append({
                    "slug": slug,
                    "route": route,
                    "stitch_source_screen_id": None,
                    "stitch_html": f".stitch-pages/{clone_from}.html",
                    "role": "cloned-from",
                    "cloned_from": clone_from,
                    "expected_section_count": structure[clone_from].get("sectionCount"),
                    "primary_keyword": primary_kw,
                    "secondary_keywords": secondary_kw,
                    "_note": f"No Stitch screen supplied for '{slug}'. Cloning structure from '{clone_from}.html' to preserve style continuity. Copy will be adapted from research + intake.",
                })
                warnings.append(f"Page '{slug}' cloned from '{clone_from}' (no exact Stitch supplied)")
            else:
                pages_out.append({
                    "slug": slug,
                    "route": route,
                    "stitch_source_screen_id": None,
                    "stitch_html": None,
                    "role": "needs-decision",
                    "primary_keyword": primary_kw,
                    "secondary_keywords": secondary_kw,
                    "_warning": f"No Stitch screen supplied for '{slug}' and no acceptable sibling to clone from. Pipeline cannot proceed without Mike picking a Stitch source — HALT.",
                })
                halt_warnings.append(f"Page '{slug}' has no Stitch source and no clone fallback")

    # Always-required infra pages — these are NOT in page-map.json's main pages[]
    # because they aren't Stitch-driven, but Phase 5 still creates them.
    infra_pages = ["privacy", "terms"]

    page_map = {
        "projectName": intake.get("projectName"),
        "businessName": intake.get("businessName"),
        "domain": intake.get("domain"),
        "tier1": "stitch" if stitch_screens else ("template" if intake.get("designTemplate") else "generate"),
        "pages": pages_out,
        "infraPages": infra_pages,
        "warnings": warnings,
        "haltWarnings": halt_warnings,
    }

    out_path = project / "ai" / "page-map.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(page_map, indent=2) + "\n", encoding="utf-8")

    print(f"OK: wrote {out_path}")
    print(f"  tier1: {page_map['tier1']}")
    print(f"  pages: {len(pages_out)}")
    print(f"    literal:        {sum(1 for p in pages_out if p['role']=='literal')}")
    print(f"    cloned-from:    {sum(1 for p in pages_out if p['role']=='cloned-from')}")
    print(f"    needs-decision: {sum(1 for p in pages_out if p['role']=='needs-decision')}")
    if warnings:
        print("  warnings:")
        for w in warnings:
            print(f"    - {w}")
    if halt_warnings:
        print("  HALT WARNINGS (Phase 5 cannot run):")
        for w in halt_warnings:
            print(f"    - {w}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
