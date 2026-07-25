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

# Annotation filename -> current catalog page id, for upstream pages that were
# renamed or retired out from under an annotation we still want to keep.
# Verified against the 2026-07-25 catalog rebuild (761 pages).
RENAMED_PAGES = {
    "security__anti-loop": "tools__loop-detection",
    "security__prompt-injection": "security__THREAT-MODEL-ATLAS",
    "skills__skill-vetter": "clawhub__security-audits",
    "providers__glm": "providers__zai",
    "channels__bluebubbles": "channels__imessage-from-bluebubbles",
    "plugins__skill-workshop": "tools__skill-workshop",
}


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
        # Upstream collapsed section landing pages (`automation/index.md` ->
        # `automation`) in ~2026-06. Annotation filenames keep the legacy `__index`
        # spelling; alias both directions rather than renaming client-visible files.
        page = (
            by_id.get(page_id)
            or by_id.get(page_id.removesuffix("__index"))
            or by_id.get(f"{page_id}__index")
            or by_id.get(RENAMED_PAGES.get(page_id, ""))
        )
        if not page:
            print(f"  WARN: annotation '{ann_file.name}' has no matching catalog page id")
            continue

        fm = parse_fm(ann_file.read_text())
        rel_path = f"annotations/{ann_file.name}"

        # A single annotation file can be pointed at by more than one page — e.g. a
        # renamed upstream page keeps the old link while the remap adds the new one.
        # Stamp lastVerified on EVERY page pointing at this file, or a page keeps
        # reporting stale after the annotation was re-verified.
        targets = [page] + [
            p for p in catalog["pages"]
            if p is not page and p.get("annotation") == rel_path
        ]
        for target in targets:
            target["annotation"] = rel_path
            if fm.get("last-verified"):
                target["lastVerified"] = f"{fm['last-verified']}T00:00:00+00:00"
            if fm.get("relevance") == "jambot-critical":
                target["relevance"] = "high"
                tags = target.get("tags") or []
                if "jambot-critical" not in tags:
                    tags.append("jambot-critical")
                target["tags"] = tags
        updated += 1

    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n")
    print(f"Synced {updated} annotation→catalog entries")


if __name__ == "__main__":
    main()
