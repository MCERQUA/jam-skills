#!/usr/bin/env python3
"""
make_schema.py — build JSON-LD (BlogPosting + BreadcrumbList + FAQPage) from a staged
article, DETERMINISTICALLY (no LLM). Writes <work_dir>/schema.json.

FAQ extraction: finds the "## Frequently Asked Questions" (or "## FAQ") section, then
each "### <question>" sub-heading + the paragraph(s) that follow become a Q/A.

Usage: make_schema.py <config.json> <work_dir>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from article_io import load_article  # noqa: E402


def extract_faq(body):
    # locate FAQ section
    m = re.search(r"^##\s+(?:frequently asked questions|faq)\b.*$", body,
                  re.IGNORECASE | re.MULTILINE)
    if not m:
        return []
    section = body[m.end():]
    # stop at next ## (new top section)
    nxt = re.search(r"^##\s+", section, re.MULTILINE)
    if nxt:
        section = section[:nxt.start()]
    qas = []
    parts = re.split(r"^###\s+", section, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.strip().split("\n", 1)
        q = lines[0].strip()
        a = (lines[1].strip() if len(lines) > 1 else "")
        # answer = first non-empty paragraph
        a = re.split(r"\n\s*\n", a)[0].strip() if a else ""
        # strip markdown links → text
        a = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", a)
        a = re.sub(r"[*_`#>-]", "", a).strip()
        if q and a:
            qas.append((q, a))
    return qas


def main():
    cfg = json.load(open(sys.argv[1]))
    work = sys.argv[2]
    art = load_article(work)
    fm = art["frontmatter"]
    body = art["body"]

    site = cfg["site_url"].rstrip("/")
    prefix = cfg.get("blog_path_prefix", "/blog/")
    slug = fm.get("slug", "")
    url = f"{site}{prefix}{slug}"
    date = fm.get("date", "")

    graph = [
        {
            "@type": "BlogPosting",
            "headline": fm.get("title", ""),
            "description": fm.get("description", "") or fm.get("excerpt", ""),
            "datePublished": date,
            "dateModified": date,
            "author": {"@type": "Organization", "name": cfg.get("site_author", cfg["brand"])},
            "publisher": {"@type": "Organization", "name": cfg["brand"],
                          "url": site},
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "url": url,
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": site + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog",
                 "item": f"{site}{prefix.rstrip('/')}"},
                {"@type": "ListItem", "position": 3, "name": fm.get("title", ""),
                 "item": url},
            ],
        },
    ]

    qas = extract_faq(body)
    if qas:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in qas
            ],
        })

    schema = {"@context": "https://schema.org", "@graph": graph}
    out = os.path.join(work, "schema.json")
    json.dump(schema, open(out, "w"), indent=2)
    print(f"make_schema: wrote {out} ({len(graph)} nodes, {len(qas)} FAQ)")


if __name__ == "__main__":
    main()
