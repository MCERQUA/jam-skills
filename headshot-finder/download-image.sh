#!/usr/bin/env bash
# download-image.sh — Generic image downloader with realistic UA, content-type
# validation, max-size cap, and basic anti-bot-page protection. Returns 0 on a
# real image saved, non-zero on any failure.
#
# Usage:
#   download-image.sh <url> <output-path> [--referer <url>]

set -uo pipefail

if [[ $# -lt 2 ]]; then
    echo "usage: download-image.sh <url> <output-path> [--referer <url>]" >&2
    exit 2
fi

URL="$1"; OUT="$2"; shift 2
REFERER=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --referer) REFERER="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
MAX_BYTES=5242880  # 5MB

mkdir -p "$(dirname "$OUT")"

headers=()
[[ -n "$REFERER" ]] && headers+=(-H "Referer: $REFERER")

# Fetch into a tmp file, then validate before promoting
TMP=$(mktemp --suffix=.imgtmp)
trap 'rm -f "$TMP"' EXIT

http_status=$(curl -sS --max-time 30 -L \
    -A "$UA" \
    "${headers[@]}" \
    --max-filesize "$MAX_BYTES" \
    -o "$TMP" \
    -w "%{http_code}" \
    "$URL")

if [[ "$http_status" != "200" ]]; then
    echo "download-image.sh: HTTP $http_status for $URL" >&2
    exit 3
fi

# Validate content
size=$(stat -c %s "$TMP" 2>/dev/null || stat -f %z "$TMP" 2>/dev/null || echo 0)
if [[ "$size" -lt 1024 ]]; then
    echo "download-image.sh: file too small ($size bytes) — likely error page" >&2
    exit 4
fi

# Magic bytes check — JPEG (FF D8), PNG (89 50 4E 47), WEBP (RIFF...WEBP), GIF
magic=$(head -c 12 "$TMP" | od -An -tx1 | tr -d ' \n' | head -c 24)
case "$magic" in
    ffd8ff*) ;;                                 # JPEG
    89504e47*) ;;                               # PNG
    52494646????????57454250*) ;;               # WEBP (RIFF then WEBP at offset 8)
    47494638*) ;;                               # GIF
    *)
        echo "download-image.sh: file is not a recognized image (magic=${magic})" >&2
        exit 5 ;;
esac

mv "$TMP" "$OUT"
trap - EXIT
echo "$OUT"
