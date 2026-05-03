#!/usr/bin/env python3
"""stitch-fidelity-check.py

Compare a built Next.js site against its Stitch source-of-truth structure file
and emit a fidelity score. Used as a gate at the end of Phase 4 (BUILD-PAGES).

Inputs:
    <project-path>      — root of the Next.js project (contains src/, .stitch-pages/)
    --threshold <0..1>  — minimum acceptable score (default 0.85)
    --strict            — require ALL pages to pass; default = average passes
    --report <path>     — write JSON report (default: <project>/.quality-gate/stitch-fidelity.json)

Logic:
    For each page in .stitch-pages/structure.json:
      1. Find the matching app route file:
            home  -> src/app/page.tsx
            <pg>  -> src/app/<pg>/page.tsx  (or src/app/<pg>.tsx)
      2. Count rendered <Section* />, <Hero*/>, generic <section>, and named-imported
         section components in the page module + any directly-imported sub-modules.
      3. Score = matched_sections / stitch_section_count.
         A "match" is per-index: positions 0..N-1 each compared as type-OK or any-section-OK.

Exit codes:
    0   passed (score >= threshold)
    1   fidelity below threshold OR report shows missing pages
    2   structure.json not found / project layout invalid
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# Section component import detection.
# Phase 4 conventions:
#   - Page imports <Section> components from src/components/sections/*.
#   - <Hero* />, <Services* />, <FAQ* />, <Testimonials* />, etc. are all "sections".
SECTION_TAG_RE = re.compile(r"<([A-Z][A-Za-z0-9]+)(?:\s+[^>]*)?\s*/?>")
NEXT_DYNAMIC_IMPORT_RE = re.compile(r"dynamic\(\s*\(?\s*\)?\s*=>\s*import\(['\"]([^'\"]+)['\"]\)")
STATIC_IMPORT_FROM_RE = re.compile(
    r"^\s*import\s+\{?\s*([A-Za-z0-9_,\s]+)\}?\s+from\s+['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)


# ---------- helpers -----------------------------------------------------------

def find_page_file(project: Path, page_name: str) -> Path | None:
    """Return the page.tsx file backing the given Stitch page name."""
    app = project / "src" / "app"
    if page_name == "home":
        candidates = [app / "page.tsx", app / "page.jsx"]
    else:
        candidates = [
            app / page_name / "page.tsx",
            app / page_name / "page.jsx",
            app / f"{page_name}.tsx",
            app / f"{page_name}.jsx",
        ]
    for c in candidates:
        if c.exists():
            return c
    return None


def all_jsx_components_used(file_path: Path, project: Path, depth: int = 0) -> list[str]:
    """Walk the page file plus any imported relative components and collect
    capitalized component tag names used in JSX. Limited recursion to avoid
    blow-up on framework imports."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    # Strip JS/TS comments to avoid false positives on tag names in comments.
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)

    components_here = SECTION_TAG_RE.findall(text)

    if depth >= 2:
        return components_here

    # Recurse into local relative imports only — not into node_modules paths.
    imported_files: list[Path] = []
    for m in STATIC_IMPORT_FROM_RE.finditer(text):
        spec = m.group(2)
        if not (spec.startswith(".") or spec.startswith("@/")):
            continue
        if spec.startswith("@/"):
            resolved = project / "src" / spec[2:]
        else:
            resolved = (file_path.parent / spec).resolve()
        for ext in (".tsx", ".jsx", ".ts", ".js", "/index.tsx", "/index.jsx"):
            cand = Path(str(resolved) + ext)
            if cand.exists():
                imported_files.append(cand)
                break
    for m in NEXT_DYNAMIC_IMPORT_RE.finditer(text):
        spec = m.group(1)
        if spec.startswith("@/"):
            resolved = project / "src" / spec[2:]
        else:
            resolved = (file_path.parent / spec).resolve()
        for ext in (".tsx", ".jsx", ".ts", ".js"):
            cand = Path(str(resolved) + ext)
            if cand.exists():
                imported_files.append(cand)
                break

    aggregated = list(components_here)
    for sub in imported_files[:30]:  # cap to avoid runaway recursion
        aggregated.extend(all_jsx_components_used(sub, project, depth + 1))
    return aggregated


SECTION_COMPONENT_HINTS = {
    "hero": re.compile(r"^Hero", re.I),
    "trust-bar": re.compile(r"(TrustBar|LogoStrip|AsSeenOn)", re.I),
    "services-grid": re.compile(r"(Services|Offerings|WhatWeDo|ServiceList|ServicesGrid)", re.I),
    "benefits-grid": re.compile(r"(Benefits|WhyChooseUs|Features|FeatureGrid)", re.I),
    "process": re.compile(r"(Process|HowItWorks|Steps)", re.I),
    "testimonials": re.compile(r"(Testimonials|Reviews|HappyClients|HappyHomeowners)", re.I),
    "faq": re.compile(r"^FAQ", re.I),
    "guarantee": re.compile(r"(Guarantee|Warranty|Promise)", re.I),
    "before-after": re.compile(r"(BeforeAfter|Compare)", re.I),
    "gallery": re.compile(r"(Gallery|Portfolio)", re.I),
    "contact-form": re.compile(r"(Contact|Quote|Estimate|RequestQuote)", re.I),
    "form-section": re.compile(r"(Form|Lead)", re.I),
    "cta-band": re.compile(r"(CTA|CTABand|CallToAction)", re.I),
    "feature-grid": re.compile(r"(Feature|Card)", re.I),
}

GENERIC_SECTION_NAMES = {"Section", "section", "Container", "Wrapper"}


def matches_type(component_name: str, expected_type: str) -> bool:
    pat = SECTION_COMPONENT_HINTS.get(expected_type)
    if pat is None:
        return False
    return bool(pat.search(component_name))


def is_any_section(component_name: str) -> bool:
    if component_name in GENERIC_SECTION_NAMES:
        return True
    for pat in SECTION_COMPONENT_HINTS.values():
        if pat.search(component_name):
            return True
    return False


# ---------- main scoring loop -------------------------------------------------

def score_page(project: Path, page_name: str, expected: dict) -> dict:
    page_file = find_page_file(project, page_name)
    if page_file is None:
        return {
            "page": page_name,
            "found": False,
            "expectedSections": expected["sectionCount"],
            "renderedComponents": [],
            "matched": 0,
            "score": 0.0,
            "reason": "page file not found in src/app",
        }

    components = all_jsx_components_used(page_file, project)
    expected_sections = expected.get("sections", [])
    expected_count = expected["sectionCount"]

    matched_strict = 0
    matched_any = 0
    notes: list[str] = []

    available = list(components)

    for sec in expected_sections:
        sec_type = sec.get("type", "")
        # Strict match: a component name patterns the section type.
        idx_strict = next(
            (i for i, c in enumerate(available) if matches_type(c, sec_type)), None
        )
        if idx_strict is not None:
            matched_strict += 1
            matched_any += 1
            available.pop(idx_strict)
            continue
        # Loose match: any "section-shaped" component.
        idx_any = next(
            (i for i, c in enumerate(available) if is_any_section(c)), None
        )
        if idx_any is not None:
            matched_any += 1
            notes.append(f"loose match for type={sec_type}: used <{available[idx_any]}/>")
            available.pop(idx_any)
        else:
            notes.append(f"NO match for type={sec_type}")

    # Score weights strict matches more heavily; a loose match is half-credit.
    raw = (matched_strict + 0.5 * (matched_any - matched_strict)) / max(expected_count, 1)
    score = max(0.0, min(1.0, raw))

    return {
        "page": page_name,
        "found": True,
        "pageFile": str(page_file.relative_to(project)),
        "expectedSections": expected_count,
        "renderedComponents": components,
        "matchedStrict": matched_strict,
        "matchedAny": matched_any,
        "score": round(score, 3),
        "notes": notes,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--threshold", type=float, default=0.85)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv[1:])

    project: Path = args.project.resolve()
    structure_path = project / ".stitch-pages" / "structure.json"
    if not structure_path.exists():
        print(f"ERROR: {structure_path} not found — run parse-stitch-html.py first", file=sys.stderr)
        return 2

    structure = json.loads(structure_path.read_text(encoding="utf-8"))
    if not isinstance(structure, dict) or not structure:
        print(f"ERROR: structure.json is empty or malformed", file=sys.stderr)
        return 2

    pages = []
    for name, expected in structure.items():
        pages.append(score_page(project, name, expected))

    avg = sum(p["score"] for p in pages) / max(len(pages), 1)
    all_found = all(p["found"] for p in pages)
    all_pass = all(p["score"] >= args.threshold for p in pages)

    report = {
        "threshold": args.threshold,
        "strict": args.strict,
        "averageScore": round(avg, 3),
        "allFound": all_found,
        "allPagesPass": all_pass,
        "pages": pages,
    }

    out_path = args.report or (project / ".quality-gate" / "stitch-fidelity.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"=== Stitch fidelity report ===")
    print(f"  pages: {len(pages)}  threshold: {args.threshold}  strict: {args.strict}")
    for p in pages:
        flag = "OK " if p["score"] >= args.threshold else "FAIL"
        if not p["found"]:
            flag = "MISS"
        print(f"  [{flag}] {p['page']}  score={p['score']:.2f}  expected={p['expectedSections']}  matched={p.get('matchedStrict','-')} strict / {p.get('matchedAny','-')} any")
    print(f"  averageScore: {avg:.3f}")
    print(f"  report: {out_path}")

    if args.strict:
        return 0 if (all_found and all_pass) else 1
    return 0 if (all_found and avg >= args.threshold) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
