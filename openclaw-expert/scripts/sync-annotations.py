#!/usr/bin/env python3
"""
Scan annotations/*.md, update catalog.json:
  - annotation: relative path to the .md file
  - lastVerified: read from frontmatter
  - relevance: bumped to 'high' if frontmatter says jambot-critical
Idempotent.
"""
import json
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ANN_DIR = SKILL_DIR / "annotations"
CATALOG = SKILL_DIR / "catalog.json"

FM_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


def parse_fm(text):
    m = FM_RE.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith("  - "):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"')
    return out


def main():
    catalog = json.loads(CATALOG.read_text())
    by_id = {p["id"]: p for p in catalog["pages"]}

    updated = 0
    for ann_file in sorted(ANN_DIR.glob("*.md")):
        page_id = ann_file.stem  # filename without .md
        page = by_id.get(page_id)
        if not page:
            print(f"  WARN: annotation '{ann_file.name}' has no matching catalog page id")
            continue

        fm = parse_fm(ann_file.read_text())
        rel_path = f"annotations/{ann_file.name}"

        page["annotation"] = rel_path
        if fm.get("last-verified"):
            page["lastVerified"] = f"{fm['last-verified']}T00:00:00+00:00"
        if fm.get("relevance") == "jambot-critical":
            page["relevance"] = "high"
            tags = page.get("tags") or []
            if "jambot-critical" not in tags:
                tags.append("jambot-critical")
            page["tags"] = tags
        updated += 1

    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"Synced {updated} annotation→catalog entries")


if __name__ == "__main__":
    main()
