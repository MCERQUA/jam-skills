#!/bin/bash
# Fetch a single OpenClaw doc page, cache locally for 24h.
#
# Usage:
#   fetch-page.sh <url-or-page-id>           # fetches + caches + prints
#   fetch-page.sh --no-cache <url-or-id>     # bypass cache, force refetch
#   fetch-page.sh --path-only <url-or-id>    # print cache file path only
#
# Cache lives in cache/<page-id>.md; metadata in cache/<page-id>.meta.json
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CATALOG="$SKILL_DIR/catalog.json"
CACHE_DIR="$SKILL_DIR/cache"
TTL_HOURS=24

NO_CACHE=0
PATH_ONLY=0
while [[ $# -gt 0 && "$1" == --* ]]; do
    case "$1" in
        --no-cache) NO_CACHE=1; shift ;;
        --path-only) PATH_ONLY=1; shift ;;
        *) echo "unknown flag: $1" >&2; exit 2 ;;
    esac
done

if [[ $# -eq 0 ]]; then
    echo "Usage: fetch-page.sh [--no-cache|--path-only] <url-or-page-id>" >&2
    exit 2
fi

INPUT="$1"

# Resolve to URL via catalog if input is a page id
if [[ "$INPUT" == https://* ]]; then
    URL="$INPUT"
    PAGE_ID="$(python3 -c "
import sys
url = sys.argv[1]
path = url.replace('https://docs.openclaw.ai/', '').replace('.md','')
print(path.replace('/', '__'))
" "$URL")"
else
    URL="$(python3 -c "
import json, sys
cat = json.load(open(sys.argv[1]))
pid = sys.argv[2]
for p in cat['pages']:
    if p['id'] == pid:
        print(p['url']); sys.exit(0)
sys.exit(1)
" "$CATALOG" "$INPUT")" || { echo "page id not in catalog: $INPUT" >&2; exit 1; }
    PAGE_ID="$INPUT"
fi

CACHE_FILE="$CACHE_DIR/$PAGE_ID.md"
META_FILE="$CACHE_DIR/$PAGE_ID.meta.json"

mkdir -p "$CACHE_DIR"

CACHE_FRESH=0
if [[ "$NO_CACHE" -eq 0 && -f "$CACHE_FILE" ]]; then
    AGE_SEC=$(( $(date +%s) - $(stat -c %Y "$CACHE_FILE") ))
    if [[ "$AGE_SEC" -lt $((TTL_HOURS*3600)) ]]; then
        CACHE_FRESH=1
    fi
fi

if [[ "$CACHE_FRESH" -eq 0 ]]; then
    if ! curl -fsSL --max-time 30 -o "$CACHE_FILE.tmp" "$URL"; then
        echo "ERROR: fetch failed for $URL" >&2
        rm -f "$CACHE_FILE.tmp"
        exit 1
    fi
    mv "$CACHE_FILE.tmp" "$CACHE_FILE"
    SHA=$(sha256sum "$CACHE_FILE" | cut -d' ' -f1)
    cat > "$META_FILE" <<META
{
  "page_id": "$PAGE_ID",
  "url": "$URL",
  "fetchedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "sha256": "$SHA",
  "bytes": $(stat -c %s "$CACHE_FILE")
}
META
fi

if [[ "$PATH_ONLY" -eq 1 ]]; then
    echo "$CACHE_FILE"
else
    cat "$CACHE_FILE"
fi
