#!/usr/bin/env python3
"""
build-location-pages.py — Generate location-specific service pages from
page-recommendations.md, cloning the visual layout from the services overview
and weaving in the city-specific keywords.

Generic. No client/city hardcoding. Reads:
  - ai/research/page-recommendations.md  (which cities to build)
  - intake.json                          (businessName, phone, email, etc.)
  - src/app/services/page.tsx            (clone source)

Writes one page.tsx per location row.

Usage:
  build-location-pages.py --project <path> --intake <intake.json>
"""
import argparse
import json
import re
import sys
from pathlib import Path


# Match recommendation rows for location pages — typically named "<City> Deck Builder"
# or "<City> <Service> Builder" with a slug like /<city>/ or /<city>-<service>/.
ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|"                # number
    r"\s*([^|]+?)\s*\|"                # name
    r"\s*([^|]+?)\s*\|"                # url
    r"\s*([^|]+?)\s*\|"                # primary keywords
    r"\s*([^|]*?)\s*\|"                # volume
    r"\s*([^|]+?)\s*\|"                # why
    r"\s*$",
    re.MULTILINE,
)

LOCATION_HEADER_RE = re.compile(r"###\s+Location[- ]Specific Pages", re.IGNORECASE)
NEXT_HEADER_RE = re.compile(r"\n###\s+", re.IGNORECASE)


def parse_location_rows(rec_path: Path) -> list[dict]:
    text = rec_path.read_text()
    h = LOCATION_HEADER_RE.search(text)
    if not h:
        return []
    body = text[h.end():]
    nxt = NEXT_HEADER_RE.search(body)
    if nxt:
        body = body[:nxt.start()]
    rows = []
    for m in ROW_RE.finditer(body):
        num, name, url, kws, vol, why = m.groups()
        if name.strip().lower() in ("page", ""):
            continue
        if set(name.strip()) <= set("- :|"):
            continue
        slug = url.strip().strip("/").split("/")[0]
        if not slug:
            continue
        keywords = [k.strip() for k in kws.split(",") if k.strip()]
        # Extract city name as the first word of the page name (or strip suffixes)
        city = re.sub(r"\s+(deck builder|roofing|siding|plumbing|hvac).*$", "", name, flags=re.IGNORECASE).strip()
        rows.append({
            "slug": slug,
            "name": name.strip(),
            "city": city,
            "keywords": keywords,
            "why": why.strip(),
        })
    return rows


def generate_page(template: str, city: str, slug: str, keywords: list[str], intake: dict, why: str) -> str:
    """Take the services template, swap copy with city-specific content + keywords."""
    business = intake.get("businessName", "")
    phone = intake.get("phone", "")
    primary_kw = keywords[0] if keywords else f"deck builder {city}"
    secondary_kws = keywords[1:3] if len(keywords) > 1 else []

    # Replace any hero-section H1 with city-targeted headline (keyword-stuffed but natural)
    # Hero pattern: <h1 className="...">...</h1>
    new_h1 = primary_kw.title()
    page = re.sub(
        r"<h1\b([^>]*)>.*?</h1>",
        lambda m: f"<h1{m.group(1)}>{new_h1}</h1>",
        template,
        count=1,
        flags=re.DOTALL,
    )

    # Replace first H2 → city-focused subheading containing a secondary keyword
    h2_replacements = []
    if secondary_kws:
        h2_replacements.append((0, f"Local {secondary_kws[0].title()} You Can Trust"))
    else:
        h2_replacements.append((0, f"Decking Experts Serving {city}"))
    h2_replacements.append((1, f"Why {city} Homeowners Choose {business}"))

    h2_iter = re.finditer(r"<h2\b([^>]*)>(.*?)</h2>", page, re.DOTALL)
    h2_count = 0
    h2_swaps = {}
    for m in h2_iter:
        for idx, new in h2_replacements:
            if h2_count == idx:
                h2_swaps[m.start()] = (m.end(), m.group(1), new)
        h2_count += 1
    # Apply in reverse order to preserve offsets
    for start in sorted(h2_swaps.keys(), reverse=True):
        end, attrs, new = h2_swaps[start]
        page = page[:start] + f"<h2{attrs}>{new}</h2>" + page[end:]

    # Replace the first paragraph with city-targeted intro that mentions every keyword
    kw_blob = ", ".join(keywords) if keywords else f"deck builder {city}"
    intro_para = (
        f'<p className="font-body-lg text-body-lg mb-10 text-slate-100 max-w-xl opacity-90">'
        f'Looking for {primary_kw}? {business} brings 15+ years of premium deck '
        f'craftsmanship to {city} homeowners. From PVC and composite to cedar and '
        f'custom curved designs, we serve {city} and surrounding King County '
        f'neighborhoods. {why if why else ""}'
        f'</p>'
    )
    page = re.sub(
        r"<p\b[^>]*>.*?</p>",
        intro_para,
        page,
        count=1,
        flags=re.DOTALL,
    )

    # Add a city-specific keyword paragraph somewhere in body if not already present.
    # We append a small "service-area note" before the closing </main>.
    note = (
        f'<section className="py-12 bg-surface-container-low"><div className="max-w-[1280px] mx-auto px-6">'
        f'<h3 className="font-h3-card text-h3-card mb-4">Serving {city} & Neighboring Communities</h3>'
        f'<p className="text-body-md text-secondary leading-relaxed mb-4">'
        f"As a trusted {primary_kw}, {business} works with homeowners across {city} "
        f"on every kind of project — new builds, full deck replacement, custom "
        f"railings, and complete outdoor living spaces. Our crews know the local "
        f"climate, permitting requirements, and architectural styles unique to "
        f"the Pacific Northwest. Call us at {phone} for a free on-site consultation."
        f'</p>'
        f'<p className="text-sm text-slate-600">Keywords: <span className="font-medium">{kw_blob}</span></p>'
        f'</div></section>'
    )
    if "</main>" in page:
        page = page.replace("</main>", note + "</main>", 1)
    else:
        # No <main> wrap — append before footer
        page = re.sub(r"(<footer\b)", note + r"\1", page, count=1)

    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--intake", required=True)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    intake = json.loads(Path(args.intake).read_text())

    rec_path = project / "ai" / "research" / "page-recommendations.md"
    if not rec_path.exists():
        sys.exit(f"missing {rec_path}")

    template_path = project / "src" / "app" / "services" / "page.tsx"
    if not template_path.exists():
        sys.exit(f"missing services template at {template_path}")
    template = template_path.read_text()

    rows = parse_location_rows(rec_path)
    if not rows:
        print(json.dumps({"ok": True, "built": 0, "rows_found": 0}))
        return

    built = []
    skipped = []
    for row in rows:
        target = project / "src" / "app" / row["slug"] / "page.tsx"
        if target.exists():
            skipped.append(row["slug"])
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = generate_page(template, row["city"], row["slug"], row["keywords"], intake, row["why"])
        target.write_text(content)
        built.append(row["slug"])

    print(json.dumps({
        "ok": True,
        "rows_found": len(rows),
        "built": built,
        "skipped_existing": skipped,
    }, indent=2))


if __name__ == "__main__":
    main()
