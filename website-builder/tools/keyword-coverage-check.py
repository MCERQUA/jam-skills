#!/usr/bin/env python3
"""
keyword-coverage-check.py — Verify every page recommended by research exists AND
contains its target keywords. Fails build (exit 1) if anything is missing.

Reads page-recommendations.md table rows. For each row:
  1. Confirm the route exists at src/app/<slug>/page.tsx
  2. Confirm each Primary Keyword from the row appears (case-insensitive) in:
     - the H1 OR the H2s
     - somewhere in the page body

Usage:
  keyword-coverage-check.py --project <next-project-root> [--recommendations <path>]
"""
import argparse
import json
import re
import sys
from pathlib import Path


# Match table rows of the form:
#   | <num> | <Page name> | <url> | <kw1, kw2, ...> | <vol> | <reason> |
# Or the simpler intake-pages form:
#   | <num> | <Page name> | <url> | REQUIRED |
ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|"           # number
    r"\s*([^|]+)\s*\|"            # page name
    r"\s*([^|]+)\s*\|"            # url
    r"\s*([^|]+)\s*\|"            # keywords or "REQUIRED"
    r"(.*)$",                     # rest (volume/reason for service rows)
    re.MULTILINE,
)

NOT_RECOMMENDED_HEADER_RE = re.compile(r"###\s+Not Recommended", re.IGNORECASE)


def url_to_slug(url: str) -> str:
    u = url.strip().strip("/")
    if u in ("", "."):
        return "home"
    # First path segment (so /deck-cost-seattle/ → deck-cost-seattle)
    return u.split("/")[0].split("?")[0].split("#")[0]


def parse_recommendations(path: Path) -> list[dict]:
    """Return list of {slug, name, keywords[]} for every row that should be built."""
    if not path.exists():
        return []
    text = path.read_text()

    # Cut off everything after "### Not Recommended" header
    cut = NOT_RECOMMENDED_HEADER_RE.search(text)
    if cut:
        text = text[:cut.start()]

    rows = []
    for m in ROW_RE.finditer(text):
        num, name, url, kw_or_required, rest = m.groups()
        name = name.strip()
        url = url.strip()
        kw_field = kw_or_required.strip()

        # Skip header separator rows
        if set(name) <= set("- :|"):
            continue
        if name.lower() in ("page", "name"):
            continue

        slug = url_to_slug(url)
        if slug in ("privacy", "terms"):
            # Legal pages have no keyword targeting
            keywords = []
        elif kw_field.upper() == "REQUIRED":
            keywords = []  # intake page — no keyword requirement here
        else:
            keywords = [k.strip() for k in kw_field.split(",") if k.strip()]
        rows.append({"num": int(num), "slug": slug, "name": name, "url": url, "keywords": keywords})
    return rows


def find_page(project: Path, slug: str) -> Path | None:
    if slug == "home":
        p = project / "src" / "app" / "page.tsx"
    else:
        p = project / "src" / "app" / slug / "page.tsx"
    return p if p.exists() else None


def headings_text(jsx: str) -> tuple[str, list[str], list[str]]:
    """Extract H1 text, H2 texts, body text (no tags) from a page.tsx."""
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", jsx, re.DOTALL | re.IGNORECASE)
    h1 = re.sub(r"<[^>]+>", " ", h1_match.group(1)) if h1_match else ""
    h1 = re.sub(r"\s+", " ", h1).strip()

    h2s = []
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", jsx, re.DOTALL | re.IGNORECASE):
        h = re.sub(r"<[^>]+>", " ", m.group(1))
        h = re.sub(r"\s+", " ", h).strip()
        h2s.append(h)

    body = re.sub(r"<[^>]+>", " ", jsx)
    body = re.sub(r"\s+", " ", body).lower()
    return h1.lower(), [h.lower() for h in h2s], body


def check_page(page_path: Path, keywords: list[str]) -> dict:
    if not keywords:
        return {"ok": True, "found_in_body": [], "missing_in_body": [], "in_h1_or_h2": []}

    jsx = page_path.read_text()
    h1, h2s, body = headings_text(jsx)
    headings_blob = (h1 + " " + " ".join(h2s)).lower()

    missing_in_body = []
    found_in_body = []
    in_h1_or_h2 = []
    for kw in keywords:
        kl = kw.lower()
        if kl in body:
            found_in_body.append(kw)
        else:
            missing_in_body.append(kw)
        if kl in headings_blob:
            in_h1_or_h2.append(kw)

    return {
        "ok": len(missing_in_body) == 0 and len(in_h1_or_h2) > 0,
        "found_in_body": found_in_body,
        "missing_in_body": missing_in_body,
        "in_h1_or_h2": in_h1_or_h2,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--recommendations", default=None)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    rec_path = Path(args.recommendations) if args.recommendations \
        else project / "ai" / "research" / "page-recommendations.md"

    rows = parse_recommendations(rec_path)
    if not rows:
        print(json.dumps({"ok": False, "error": f"no recommendations found at {rec_path}"}))
        sys.exit(1)

    results = []
    missing_pages = []
    keyword_failures = []

    for row in rows:
        page = find_page(project, row["slug"])
        if page is None:
            missing_pages.append(row)
            results.append({**row, "status": "MISSING_PAGE", "page_path": None})
            continue
        chk = check_page(page, row["keywords"])
        if not chk["ok"] and row["keywords"]:
            keyword_failures.append({**row, "check": chk})
        results.append({**row, "status": "OK" if chk["ok"] else "WEAK_KEYWORDS",
                        "page_path": str(page.relative_to(project)),
                        "check": chk})

    summary = {
        "ok": len(missing_pages) == 0 and len(keyword_failures) == 0,
        "total_required": len(rows),
        "missing_pages": [{"slug": r["slug"], "name": r["name"], "url": r["url"]} for r in missing_pages],
        "keyword_failures": [
            {"slug": kf["slug"], "missing": kf["check"]["missing_in_body"], "in_h1_or_h2": kf["check"]["in_h1_or_h2"]}
            for kf in keyword_failures
        ],
        "results": results,
    }
    print(json.dumps(summary, indent=2))
    sys.exit(0 if summary["ok"] else 1)


if __name__ == "__main__":
    main()
