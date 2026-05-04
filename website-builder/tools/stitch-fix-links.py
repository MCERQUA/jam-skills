#!/usr/bin/env python3
"""
stitch-fix-links.py — Replace dead `href="#"` placeholders + bare CTA <button>s with
real navigation, based on the link text and the project's actual route inventory.

Stitch HTML mockups always use href="#" and unwrapped <button> for CTAs. This tool:
  1. Discovers actual routes by scanning src/app/<slug>/page.tsx
  2. Maps link text (and CTA button text) → routes via a generic ruleset
  3. Rewrites the JSX in every page.tsx
  4. Wraps "CTA-shaped" <button>s in <a href> so they navigate

Generic. No client/project-specific text. Routes are discovered, not hardcoded.

Usage:
  stitch-fix-links.py --project <next-project-root> [--intake <intake.json>]
"""
import argparse
import json
import re
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Link-text → route slug rules (generic — match any decking/roofing/etc business)
# Order matters: more specific phrases first.
# ─────────────────────────────────────────────────────────────────────────────
TEXT_TO_SLUG = [
    # Contact-flavored CTAs
    (r"\b(get|request|claim)\s+(a|my|your)?\s*(free\s+)?(personalized\s+)?(estimate|quote)\b", "contact"),
    (r"\b(schedule|book)\s+(my|your|a)?\s*(free\s+)?(quote|consultation|estimate|appointment)\b", "contact"),
    (r"\b(contact|reach|talk to)\s+(us|me)\b", "contact"),
    (r"\bcontact\s*us\s*now\b", "contact"),
    (r"\bget\s*in\s*touch\b", "contact"),
    (r"\bget\s+started\b", "contact"),
    (r"^contact$", "contact"),
    (r"^request\s+free\s+quote$", "contact"),
    (r"^request\s+quote$", "contact"),
    (r"^get\s+a?\s*quote$", "contact"),
    # Gallery/portfolio
    (r"\b(view|see|browse)\s+(our)?\s*(custom\s+|project\s+|full\s+)?(gallery|portfolio|projects|work)\b", "gallery"),
    (r"^gallery$", "gallery"),
    (r"^portfolio$", "gallery"),
    (r"^project\s+portfolio$", "gallery"),
    # Services
    (r"\b(explore|view|see|browse)\s+(our|all)?\s*(services|options)\b", "services"),
    (r"\bview\s+services\b", "services"),
    (r"^services$", "services"),
    (r"^our\s+services$", "services"),
    (r"^materials\s+guide$", "services"),
    # About
    (r"\b(our|the)\s+story\b", "about"),
    (r"\babout\s+(us|me)\b", "about"),
    (r"^about$", "about"),
    (r"^our\s+process$", "about"),
    (r"^the\s+design\s+process$", "about"),
    # FAQ
    (r"^faq$", "faq"),
    (r"^faqs$", "faq"),
    (r"^frequently\s+asked\s+questions$", "faq"),
    (r"^help$", "faq"),
    (r"^help\s+center$", "faq"),
    # Reviews — fall back to about (since reviews live on home/about typically)
    (r"\bread\s+more\s+reviews\b", "about"),
    (r"^reviews$", "about"),
    # Home
    (r"^home$", "home"),
    # Privacy / Terms / Legal
    (r"^privacy(\s+policy)?$", "privacy"),
    (r"^terms(\s+of\s+service)?$", "terms"),
    (r"^cookie(\s+policy)?$", "privacy"),
    # Catchall: arrow-only "Learn More" / "Read More" / "Explore" near a service
    # — these will be handled by service-context detection below.
]

# Service-specific phrases — when found near a service card, link to /services#<slug>.
SERVICE_PHRASE_RE = re.compile(
    r"\b(explore|view|learn|read|see)\s+(more|all)?\s*"
    r"(pvc|composite|cedar|membrane|custom\s+curved|railing|vinyl|wood|hardwood|softwood|"
    r"\s+(decking|roofing|siding|fencing|flooring|paving|landscaping))?\b",
    re.IGNORECASE,
)
TRADITIONAL_WOOD_RE = re.compile(r"\btraditional\s+wood\b", re.IGNORECASE)


def slug_to_path(slug: str) -> str:
    return "/" if slug == "home" else f"/{slug}"


def discover_routes(project: Path) -> set[str]:
    """Scan src/app/**/page.tsx and return the set of available slugs."""
    out = {"home"}  # src/app/page.tsx = home
    app_dir = project / "src" / "app"
    if not app_dir.exists():
        return out
    for page in app_dir.rglob("page.tsx"):
        rel = page.relative_to(app_dir).parent
        if str(rel) == ".":
            continue
        out.add(str(rel))
    return out


def resolve_link_text(text: str, available: set[str]) -> str | None:
    """Return the slug a link should point to, or None if no rule matched."""
    t = text.strip().lower()
    if not t:
        return None
    if SERVICE_PHRASE_RE.search(t) or TRADITIONAL_WOOD_RE.search(t):
        return "services" if "services" in available else None
    for pat, slug in TEXT_TO_SLUG:
        if re.search(pat, t):
            if slug in available:
                return slug
            # Fallback: contact links accepted even if /contact missing — use anchor on home
            if slug == "contact":
                return None
    return None


# ─────────────────────────────────────────────────────────────────────────────
# JSX rewriting
# ─────────────────────────────────────────────────────────────────────────────

# <a ... href="#">TEXT</a>  — plain link
A_HREF_HASH_RE = re.compile(
    r'(<a\b[^>]*?\bhref=)"#"((?:[^>]*?>))(.*?)(</a>)',
    re.DOTALL,
)

# <button ...>TEXT</button>  — bare button (no onClick, no wrapping <a>)
BUTTON_RE = re.compile(
    r'(<button\b)([^>]*?)(>)(.*?)(</button>)',
    re.DOTALL,
)


def extract_visible_text(jsx_inner: str) -> str:
    """Strip JSX tags and entities to get the human-visible text of an element body."""
    # Remove tags
    txt = re.sub(r"<[^>]+>", " ", jsx_inner)
    # JSX entities
    txt = txt.replace("&amp;", "&").replace("&nbsp;", " ").replace("&#123;", "{").replace("&#125;", "}")
    return re.sub(r"\s+", " ", txt).strip()


def is_cta_button(attrs: str, text: str) -> bool:
    """Heuristic: CTA buttons usually have a non-trivial visible label and look like
    a primary/accent button (filled bg, padding, non-icon-only)."""
    if not text or len(text) < 3:
        return False
    # Skip icon-only buttons (those with only material-symbols span content)
    if re.search(r"material-symbols-(outlined|rounded|sharp)", text, re.I):
        return False
    # Skip "submit" form buttons — they need a real form handler, not a link
    if re.search(r'\btype="submit"', attrs):
        return False
    return True


def rewrite_links(jsx: str, available: set[str]) -> tuple[str, dict]:
    """Rewrite href='#' anchors and CTA buttons. Returns new JSX + counts."""
    counts = {"a_resolved": 0, "a_unresolved": 0, "button_wrapped": 0, "button_skipped": 0}

    def fix_a(m: re.Match) -> str:
        prefix, mid, body, close = m.group(1), m.group(2), m.group(3), m.group(4)
        text = extract_visible_text(body)
        slug = resolve_link_text(text, available)
        if slug is None:
            counts["a_unresolved"] += 1
            return m.group(0)
        path = slug_to_path(slug)
        counts["a_resolved"] += 1
        return f'{prefix}"{path}"{mid}{body}{close}'

    jsx = A_HREF_HASH_RE.sub(fix_a, jsx)

    # Track positions of already-open <a> so we can skip buttons that are already wrapped.
    # Simple linear scan: for each button match, check if the most recent unclosed <a>
    # opens BEFORE the button starts.
    def is_already_wrapped(start: int) -> bool:
        """Return True if `start` is inside an open <a> ... </a>."""
        # Walk anchors before `start` and count depth
        depth = 0
        for am in re.finditer(r'<a\b[^>]*>|</a>', jsx[:start]):
            if am.group().startswith("</"):
                depth -= 1
            else:
                depth += 1
        return depth > 0

    def fix_button(m: re.Match) -> str:
        if is_already_wrapped(m.start()):
            counts["button_skipped"] += 1
            return m.group(0)
        open_tag, attrs, gt, body, close = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        text = extract_visible_text(body)
        if not is_cta_button(attrs, text):
            counts["button_skipped"] += 1
            return m.group(0)
        slug = resolve_link_text(text, available)
        if slug is None:
            counts["button_skipped"] += 1
            return m.group(0)
        path = slug_to_path(slug)
        counts["button_wrapped"] += 1
        # Wrap the entire <button> in <a href="...">. The button keeps its visual styling.
        return f'<a href="{path}">{open_tag}{attrs}{gt}{body}{close}</a>'

    jsx = BUTTON_RE.sub(fix_button, jsx)

    # Idempotency cleanup: collapse any double-wrapped <a><a>...</a></a> patterns
    # left over from prior runs of this tool.
    jsx = re.sub(
        r'<a\s+href="([^"]+)"[^>]*>\s*<a\s+href="\1"[^>]*>',
        r'<a href="\1">',
        jsx,
    )
    jsx = re.sub(
        r'</a>\s*</a>',
        r'</a>',
        jsx,
    )

    return jsx, counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--intake", help="optional intake.json — used for page list discovery fallback")
    args = ap.parse_args()

    project = Path(args.project).resolve()
    available = discover_routes(project)
    if args.intake:
        try:
            intake = json.loads(Path(args.intake).read_text())
            for p in (intake.get("pages") or []):
                available.add(p)
        except Exception:
            pass

    pages = sorted((project / "src" / "app").rglob("page.tsx"))
    report = {"available_routes": sorted(available), "pages": []}
    for page in pages:
        text = page.read_text()
        new_text, counts = rewrite_links(text, available)
        if new_text != text:
            page.write_text(new_text)
        report["pages"].append({
            "path": str(page.relative_to(project)),
            **counts,
        })

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
