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


# Upstream page ids that moved out from under an existing anchor's frontmatter.
# Keep the anchor files historically accurate; remap here instead of rewriting them.
RENAMED_PAGES = {
    "providers__glm": "providers__zai",          # GLM docs consolidated under Z.AI in 5.22
    "channels__bluebubbles": "channels__imessage-from-bluebubbles",
    "skills__skill-vetter": "clawhub__security-audits",
    "security__anti-loop": "tools__loop-detection",
    "security__prompt-injection": "security__THREAT-MODEL-ATLAS",
    "plugins__skill-workshop": "tools__skill-workshop",
}


def url_to_page_id(url: str) -> str:
    path = url.replace("https://docs.openclaw.ai/", "")
    if path.endswith(".md"):
        path = path[:-3]
    return path.replace("/", "__")


def resolve_page(pid: str, pages_by_id: dict):
    """Resolve an anchor's page id against the current catalog.

    Handles two upstream shifts: section landing pages collapsed
    (`tools/index.md` -> `tools`), and pages renamed or merged outright.
    """
    for candidate in (
        pid,
        pid.removesuffix("__index"),
        f"{pid}__index",
        RENAMED_PAGES.get(pid, ""),
    ):
        if candidate and candidate in pages_by_id:
            return pages_by_id[candidate]
    return None


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
            page = resolve_page(pid, pages_by_id)
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
