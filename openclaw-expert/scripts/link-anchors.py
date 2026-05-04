#!/usr/bin/env python3
"""
Read audit-anchors/anchor-NN-*.md frontmatter, link each anchor to the
upstream page IDs it affects in catalog.json. Idempotent.

Usage: python3 link-anchors.py
"""
import json
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ANCHORS_DIR = SKILL_DIR / "audit-anchors"
CATALOG_PATH = SKILL_DIR / "catalog.json"

FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
ANCHOR_FILE_RE = re.compile(r"anchor-(\d+)-")


def parse_frontmatter(text: str) -> dict:
    """Tiny YAML subset — we control the file format."""
    m = FM_RE.match(text)
    if not m:
        return {}
    body = m.group(1)
    out = {}
    current_list_key = None
    for line in body.splitlines():
        if not line.strip():
            current_list_key = None
            continue
        if line.startswith("  - "):
            if current_list_key:
                out.setdefault(current_list_key, []).append(line[4:].strip().strip('"'))
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if val == "":
                current_list_key = key
                out[key] = []
            else:
                out[key] = val
                current_list_key = None
    return out


def url_to_page_id(url: str) -> str:
    path = url.replace("https://docs.openclaw.ai/", "").replace(".md", "")
    return path.replace("/", "__")


def main():
    catalog = json.loads(CATALOG_PATH.read_text())
    pages_by_id = {p["id"]: p for p in catalog["pages"]}

    # Reset audit_anchors on all pages (idempotent rebuild)
    for p in catalog["pages"]:
        p["audit_anchors"] = []

    linked_count = 0
    for anchor_file in sorted(ANCHORS_DIR.glob("anchor-*.md")):
        m = ANCHOR_FILE_RE.match(anchor_file.name)
        if not m:
            continue
        anchor_num = int(m.group(1))
        fm = parse_frontmatter(anchor_file.read_text())
        urls = fm.get("upstream_pages", [])
        if isinstance(urls, str):
            urls = [urls]
        for url in urls:
            pid = url_to_page_id(url)
            page = pages_by_id.get(pid)
            if page is None:
                print(f"  WARN: anchor {anchor_num} references unknown page id '{pid}' (url: {url})")
                continue
            if anchor_num not in page["audit_anchors"]:
                page["audit_anchors"].append(anchor_num)
                linked_count += 1

    # Sort audit_anchors per page for stability
    for p in catalog["pages"]:
        p["audit_anchors"].sort()

    CATALOG_PATH.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"Linked {linked_count} anchor↔page edges across "
          f"{sum(1 for p in catalog['pages'] if p['audit_anchors'])} pages")


if __name__ == "__main__":
    main()
