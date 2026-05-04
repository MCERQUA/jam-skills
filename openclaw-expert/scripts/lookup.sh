#!/bin/bash
# Look up OpenClaw doc pages by keyword, tag, anchor ID, or section.
#
# Usage:
#   lookup.sh <query>                 # keyword search across title/url/section/tags
#   lookup.sh tag:<name>              # by tag (e.g. tag:jambot-critical)
#   lookup.sh section:<name>          # by section (e.g. section:Plugins)
#   lookup.sh anchor:<N>              # by audit-anchor number (1-15)
#   lookup.sh relevance:high          # by jambot relevance
#   lookup.sh annotated               # only pages we've annotated
#   lookup.sh stale [DAYS]            # annotations not verified in N days (default 60)
#
# Output: tab-separated id | title | url | annotation | anchors
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="$SKILL_DIR/catalog.json"

if [[ ! -f "$CATALOG" ]]; then
    echo "ERROR: $CATALOG not found. Run scripts/build-catalog.py first." >&2
    exit 1
fi

if [[ $# -eq 0 ]]; then
    echo "Usage: lookup.sh <query|tag:NAME|section:NAME|anchor:N|relevance:high|annotated|stale [DAYS]>" >&2
    exit 2
fi

QUERY="$1"
SHIFT_ARG="${2:-}"

python3 - "$CATALOG" "$QUERY" "$SHIFT_ARG" <<'PYEOF'
import json
import re
import sys
from datetime import datetime, timezone, timedelta

catalog_path, query, shift_arg = sys.argv[1], sys.argv[2], sys.argv[3]
catalog = json.load(open(catalog_path))
pages = catalog["pages"]

def matches(p, kind, value):
    if kind == "tag":
        return value in (p.get("tags") or [])
    if kind == "section":
        return p["section"].lower() == value.lower() or value.lower() in p["section"].lower()
    if kind == "anchor":
        return value in [str(a) for a in (p.get("audit_anchors") or [])]
    if kind == "relevance":
        return p.get("relevance") == value
    if kind == "annotated":
        return bool(p.get("annotation"))
    if kind == "stale":
        days = int(value or "60")
        if not p.get("annotation"):
            return False
        lv = p.get("lastVerified")
        if not lv:
            return True
        dt = datetime.fromisoformat(lv.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt) > timedelta(days=days)
    # Fallback: keyword search
    blob = " ".join([
        p["id"], p["title"], p["url"], p["section"],
        " ".join(p.get("tags") or []),
    ]).lower()
    return value.lower() in blob

if ":" in query and not query.startswith("http"):
    kind, _, value = query.partition(":")
    results = [p for p in pages if matches(p, kind, value)]
elif query in ("annotated",):
    results = [p for p in pages if matches(p, query, "")]
elif query == "stale":
    results = [p for p in pages if matches(p, "stale", shift_arg)]
else:
    results = [p for p in pages if matches(p, "_kw", query)]

results.sort(key=lambda p: (p["section"], p["id"]))

if not results:
    print("(no matches)", file=sys.stderr)
    sys.exit(0)

print(f"# {len(results)} match(es) for '{query}'")
for p in results:
    ann = p.get("annotation") or "-"
    anchors = ",".join(str(a) for a in (p.get("audit_anchors") or [])) or "-"
    rel = p.get("relevance", "?")
    print(f"{p['id']}\t[{rel}]\t{p['title']}\t{p['url']}\tann={ann}\tanchors={anchors}")
PYEOF
