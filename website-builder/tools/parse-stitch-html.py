#!/usr/bin/env python3
"""parse-stitch-html.py

Parse the Stitch-generated HTML mockups in `<project>/.stitch-pages/*.html` and
emit a machine-readable structure file at `<project>/.stitch-pages/structure.json`.

This is the source-of-truth contract that Phase 4 (BUILD-PAGES) consumes when
generating per-page TodoWrite lists and per-page React components.

Usage:
    parse-stitch-html.py <stitch-pages-dir>
    parse-stitch-html.py /mnt/clients/src/openclaw/workspace/Websites/.../.stitch-pages

Output:
    <stitch-pages-dir>/structure.json

Exit codes:
    0 success (structure.json written, at least one page parsed)
    1 directory not found / no html files
    2 parse failure on every page
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: BeautifulSoup4 required (pip install beautifulsoup4)", file=sys.stderr)
    sys.exit(1)


HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
TAILWIND_COLOR_CLASS_RE = re.compile(
    r"\b(bg|text|border|from|to|via|ring|shadow)-([a-z]+)-(\d{2,3})\b"
)


# ---------- section classification heuristics ---------------------------------

def classify_section(idx: int, sec, page_name: str) -> str:
    """Return a short semantic type for the section.

    Heuristics, in priority order. Each section is classified ONCE; the first
    matching rule wins. Order matters: most-specific rules first.
    """
    text = sec.get_text(" ", strip=True).lower()
    classes = " ".join(sec.get("class", []) or [])
    has_form = bool(sec.find("form"))
    has_h1 = bool(sec.find("h1"))
    grid_cards = len(sec.select("[class*='grid'] > *")) if sec.select("[class*='grid']") else 0
    img_count = len(sec.find_all("img"))

    # Hero wins if it's section 0 AND has h1 — even if there's an embedded
    # quote/estimate form widget (very common pattern in Stitch hero sections).
    if idx == 0 and has_h1:
        return "hero"

    if has_form:
        if "contact" in text or "quote" in text or "estimate" in text:
            return "contact-form"
        return "form-section"

    if idx == 0 and "min-h" in classes:
        return "hero"

    # Trust bar / logos: short height, multiple small images or company names
    if (
        ("trusted by" in text or "as seen on" in text or "featured" in text)
        and img_count >= 3
    ):
        return "trust-bar"

    if (
        "testimonial" in text
        or sec.find(class_=re.compile(r"\btestimonial", re.I))
        or any(
            k in text for k in (
                "happy homeowner", "happy customer", "what our clients",
                "hear from our", "from our customers", "reviews from",
            )
        )
    ):
        return "testimonials"

    if "faq" in text or sec.find(class_=re.compile(r"\bfaq", re.I)):
        return "faq"

    if "process" in text or "how it works" in text or "step" in text:
        return "process"

    if any(k in text for k in ("guarantee", "warranty", "promise")):
        return "guarantee"

    if grid_cards in (3, 4, 5, 6) and any(
        k in text for k in (
            "service", "what we do", "offering", "solution", "decking", "siding",
            "roofing", "pvc", "composite", "cedar",
        )
    ):
        return "services-grid"

    if grid_cards >= 3 and any(k in text for k in ("benefit", "why choose", "feature")):
        return "benefits-grid"

    if "before" in text and "after" in text:
        return "before-after"

    if "gallery" in text or img_count >= 6:
        return "gallery"

    if "cta" in classes.lower() or (idx > 0 and "ready" in text and sec.find("a")):
        return "cta-band"

    if grid_cards >= 2:
        return "feature-grid"

    return f"section-{idx}"


# ---------- per-section content extraction ------------------------------------

def extract_section(idx: int, sec, page_name: str) -> dict:
    sec_type = classify_section(idx, sec, page_name)

    h1 = sec.find("h1")
    h2 = sec.find("h2")
    eyebrow = None
    eyebrow_el = sec.find(class_=re.compile(r"eyebrow|kicker|overline", re.I))
    if eyebrow_el:
        eyebrow = eyebrow_el.get_text(" ", strip=True)

    cta_text = None
    cta_el = sec.find("a", class_=re.compile(r"button|btn|cta", re.I))
    if cta_el is None:
        cta_el = sec.find("button")
    if cta_el:
        cta_text = cta_el.get_text(" ", strip=True)

    grid_items = sec.select("[class*='grid'] > *")
    card_count = len(grid_items) if grid_items else 0

    img_count = len(sec.find_all("img"))

    sub_headings = [h.get_text(" ", strip=True) for h in sec.find_all(["h2", "h3", "h4"])][:8]

    out = {
        "type": sec_type,
        "h1": h1.get_text(" ", strip=True) if h1 else None,
        "h2": h2.get_text(" ", strip=True) if h2 else None,
        "eyebrow": eyebrow,
        "ctaText": cta_text,
        "cardCount": card_count,
        "imgCount": img_count,
        "subHeadings": sub_headings,
    }
    return {k: v for k, v in out.items() if v not in (None, [], 0)}


# ---------- page-level extraction --------------------------------------------

def extract_palette(html: str) -> list[str]:
    """Return de-duplicated hex colors mentioned anywhere in the page."""
    seen = []
    for m in HEX_RE.finditer(html):
        h = m.group(0).upper()
        if h not in seen:
            seen.append(h)
        if len(seen) >= 12:
            break
    return seen


def extract_button_styles(soup) -> dict:
    """Pick a representative primary and secondary button class string."""
    out = {}
    primary_btn = soup.find(["a", "button"], class_=re.compile(r"\b(bg-primary|btn-primary|cta-primary)\b"))
    if primary_btn is not None:
        out["primary"] = " ".join(primary_btn.get("class", []) or [])
    secondary_btn = soup.find(["a", "button"], class_=re.compile(r"\b(btn-secondary|cta-secondary|outline)\b"))
    if secondary_btn is not None:
        out["secondary"] = " ".join(secondary_btn.get("class", []) or [])
    return out


def parse_page(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    sections = soup.find_all("section")
    section_data = [extract_section(i, sec, path.stem) for i, sec in enumerate(sections)]

    return {
        "sectionCount": len(sections),
        "sections": section_data,
        "colorsUsed": extract_palette(html),
        "buttonStyles": extract_button_styles(soup),
        "hasHeader": bool(soup.find("header")),
        "hasFooter": bool(soup.find("footer")),
    }


# ---------- main --------------------------------------------------------------

def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1

    target = Path(argv[1])
    if not target.exists():
        print(f"ERROR: directory not found: {target}", file=sys.stderr)
        return 1

    if target.is_file() and target.suffix == ".html":
        # Single-file mode (handy for debugging).
        result = {target.stem: parse_page(target)}
        print(json.dumps(result, indent=2))
        return 0

    html_files = sorted(target.glob("*.html"))
    if not html_files:
        print(f"ERROR: no .html files in {target}", file=sys.stderr)
        return 1

    result: dict = {}
    failures = []
    for f in html_files:
        try:
            result[f.stem] = parse_page(f)
        except Exception as e:  # noqa: BLE001
            failures.append((f.name, str(e)))

    if not result:
        print(f"ERROR: failed to parse any page; failures={failures}", file=sys.stderr)
        return 2

    out_path = target / "structure.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    summary_types = Counter()
    for page in result.values():
        for sec in page.get("sections", []):
            summary_types[sec.get("type", "?")] += 1

    print(f"OK: wrote {out_path}")
    print(f"  pages parsed: {len(result)} ({', '.join(sorted(result.keys()))})")
    print(f"  total sections: {sum(p['sectionCount'] for p in result.values())}")
    print(f"  section types: {dict(summary_types.most_common(8))}")
    if failures:
        print(f"  warnings: {len(failures)} page(s) failed: {failures}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
