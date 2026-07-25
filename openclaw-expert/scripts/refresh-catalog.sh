#!/bin/bash
# Re-fetch upstream llms.txt, diff against current catalog.json, regenerate catalog.
# Run nightly via cron OR manually after an OpenClaw release.
#
# Exit codes:
#   0 = no change (catalog regenerated, identical page set)
#   1 = fetch failed
#   2 = diff produced changes (catalog regenerated; review the diff, add annotations)
#   3 = REFUSED — diff claims >20% of pages removed; treat as a parser break, not
#       an upstream deletion. Catalog left untouched. See the guard below.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLMS_TMP="/tmp/openclaw-llms-$$.txt"
DIFF_OUT="/tmp/openclaw-catalog-diff-$$.json"
trap 'rm -f "$LLMS_TMP" "$DIFF_OUT"' EXIT

echo "==> Fetching $SKILL_DIR/catalog.json upstream"
if ! curl -fsSL --max-time 30 -o "$LLMS_TMP" https://docs.openclaw.ai/llms.txt; then
    echo "ERROR: fetch failed" >&2
    exit 1
fi

echo "==> Diffing against current catalog"
python3 "$SKILL_DIR/scripts/build-catalog.py" --input "$LLMS_TMP" --diff > "$DIFF_OUT"

ADDED=$(python3 -c "import json; d=json.load(open('$DIFF_OUT')); print(len(d['added']))")
REMOVED=$(python3 -c "import json; d=json.load(open('$DIFF_OUT')); print(len(d['removed']))")
RENAMED=$(python3 -c "import json; d=json.load(open('$DIFF_OUT')); print(len(d['title_changed']))")

echo "    added=$ADDED removed=$REMOVED renamed=$RENAMED"

# GUARD (added 2026-07-25): upstream changed the llms.txt link format in ~2026-06
# (appended ": description" to every line). The old parser matched 2 of 765 links,
# so an unguarded regen would have replaced a 464-page catalog with a 2-page stub
# and orphaned every annotation + anchor link. Never overwrite on a mass "removal".
OLD_COUNT=$(python3 -c "import json; print(len(json.load(open('$SKILL_DIR/catalog.json'))['pages']))" 2>/dev/null || echo 0)
if [[ "$OLD_COUNT" -gt 0 && "$REMOVED" -gt $((OLD_COUNT / 5)) ]]; then
    echo "ERROR: diff claims $REMOVED of $OLD_COUNT pages removed (>20%)." >&2
    echo "       That is almost always a PARSER break, not an upstream deletion." >&2
    echo "       Inspect the fetched llms.txt link format before regenerating:" >&2
    echo "         head -20 $LLMS_TMP   # (copy it out — this temp file is deleted on exit)" >&2
    echo "       Catalog left UNCHANGED. Fix scripts/build-catalog.py LINK_RE, then re-run." >&2
    exit 3
fi

echo "==> Backing up catalog.json"
cp -a "$SKILL_DIR/catalog.json" "$SKILL_DIR/catalog.json.bak" 2>/dev/null || true

echo "==> Regenerating catalog.json"
python3 "$SKILL_DIR/scripts/build-catalog.py" --input "$LLMS_TMP"

# Post-regen sanity: annotations must survive the merge.
ANN_LINKED=$(python3 -c "import json; print(sum(1 for p in json.load(open('$SKILL_DIR/catalog.json'))['pages'] if p.get('annotation')))")
ANN_FILES=$(find "$SKILL_DIR/annotations" -name '*.md' | wc -l)
echo "    annotations linked=$ANN_LINKED on-disk=$ANN_FILES"
if [[ "$ANN_LINKED" -lt "$ANN_FILES" ]]; then
    echo "    WARN: $((ANN_FILES - ANN_LINKED)) annotation file(s) not linked — run scripts/sync-annotations.py" >&2
fi

if [[ "$ADDED" -gt 0 || "$REMOVED" -gt 0 || "$RENAMED" -gt 0 ]]; then
    echo
    echo "==> Catalog changes detected:"
    cat "$DIFF_OUT"
    exit 2
fi

exit 0
