#!/bin/bash
# Re-fetch upstream llms.txt, diff against current catalog.json, regenerate catalog.
# Run nightly via cron OR manually after an OpenClaw release.
#
# Exit codes:
#   0 = no change OR added/removed/renamed pages (catalog regenerated)
#   1 = fetch failed
#   2 = diff produced changes (catalog regenerated; mesh-post optional)
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

echo "==> Regenerating catalog.json"
python3 "$SKILL_DIR/scripts/build-catalog.py" --input "$LLMS_TMP"

if [[ "$ADDED" -gt 0 || "$REMOVED" -gt 0 || "$RENAMED" -gt 0 ]]; then
    echo
    echo "==> Catalog changes detected:"
    cat "$DIFF_OUT"
    exit 2
fi

exit 0
