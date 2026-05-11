#!/usr/bin/env bash
# headshot-finder.sh — orchestrator. Tries Hunter (linkedin URL only) +
# DataForSEO Google Images + company team page in order, downloads the best
# candidate, validates content type. NEVER touches Facebook.
#
# Usage:
#   headshot-finder.sh <first> <last> <company> [--domain X.com] [--out path]
#
# Output: JSON {saved_to, source, confidence, image_url, linkedin_url, notes}.
# Exit 0 = image saved, 1 = no photo found, 2 = bad args / missing env.

set -uo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: headshot-finder.sh <first> <last> <company> [--domain X.com] [--out path]" >&2
    exit 2
fi

FIRST="$1"; LAST="$2"; COMPANY="$3"; shift 3
DOMAIN=""
OUT=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --domain) DOMAIN="$2"; shift 2 ;;
        --out)    OUT="$2"; shift 2 ;;
        *) echo "headshot-finder.sh: unknown arg: $1" >&2; exit 2 ;;
    esac
done

[[ -z "$OUT" ]] && OUT="/tmp/headshot-${FIRST}-${LAST}.jpg"
HERE="$(cd "$(dirname "$0")" && pwd)"

LINKEDIN_URL=""
SAVED=""
SOURCE=""
CONF=0
IMG_URL=""
NOTES=""

# --- Step 1: Hunter (cheap, gives us linkedin_url for record) -------------
if [[ -n "$DOMAIN" && -n "${HUNTER_API_KEY:-}" ]]; then
    h=$("$HERE/from-hunter.sh" "$FIRST" "$LAST" "$DOMAIN" 2>/dev/null) || h=""
    if [[ -n "$h" ]]; then
        LINKEDIN_URL=$(echo "$h" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("linkedin_url") or "")' 2>/dev/null)
    fi
fi

# --- Step 2: DataForSEO Google Images -------------------------------------
if [[ -n "${DATAFORSEO_LOGIN:-}" && -n "${DATAFORSEO_PASSWORD:-}" ]]; then
    domain_arg=()
    [[ -n "$DOMAIN" ]] && domain_arg=(--domain "$DOMAIN")
    g=$("$HERE/from-google-image.sh" "$FIRST" "$LAST" "$COMPANY" --limit 10 "${domain_arg[@]}" 2>/dev/null) || g="[]"
    # Try top candidates in order until one downloads as a real image
    while IFS= read -r entry; do
        [[ -z "$entry" || "$entry" == "null" ]] && continue
        url=$(echo "$entry" | python3 -c 'import json,sys;print(json.load(sys.stdin)["url"])' 2>/dev/null)
        conf=$(echo "$entry" | python3 -c 'import json,sys;print(json.load(sys.stdin)["confidence_hint"])' 2>/dev/null)
        page=$(echo "$entry" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("source_url",""))' 2>/dev/null)
        [[ -z "$url" ]] && continue
        if "$HERE/download-image.sh" "$url" "$OUT" --referer "$page" >/dev/null 2>&1; then
            SAVED="$OUT"; SOURCE="google-images"; CONF="$conf"; IMG_URL="$url"
            NOTES="DataForSEO SERP rank-best, host=$(echo "$entry" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("source_domain",""))' 2>/dev/null)"
            break
        fi
    done < <(echo "$g" | python3 -c 'import json,sys
try: arr = json.load(sys.stdin)
except Exception: arr = []
for e in arr: print(json.dumps(e))')
fi

# --- Step 3: Company team page (last resort, requires --domain) -----------
if [[ -z "$SAVED" && -n "$DOMAIN" ]]; then
    c=$("$HERE/from-company-site.sh" "$FIRST" "$LAST" "$DOMAIN" 2>/dev/null) || c=""
    if [[ -n "$c" ]]; then
        url=$(echo "$c" | python3 -c 'import json,sys;print(json.load(sys.stdin)["url"])' 2>/dev/null)
        page=$(echo "$c" | python3 -c 'import json,sys;print(json.load(sys.stdin)["page_url"])' 2>/dev/null)
        if "$HERE/download-image.sh" "$url" "$OUT" --referer "$page" >/dev/null 2>&1; then
            SAVED="$OUT"; SOURCE="company-site"; CONF=70; IMG_URL="$url"
            NOTES="extracted from $page"
        fi
    fi
fi

# --- Emit result ----------------------------------------------------------
python3 - <<PY
import json
print(json.dumps({
    "saved_to":     "$SAVED" or None,
    "source":       "$SOURCE" or None,
    "confidence":   int("$CONF") if "$CONF" else 0,
    "image_url":    "$IMG_URL" or None,
    "linkedin_url": "$LINKEDIN_URL" or None,
    "notes":        "$NOTES" or None,
    "person":       "${FIRST} ${LAST}",
    "company":      "${COMPANY}",
}))
PY

[[ -n "$SAVED" ]] && exit 0 || exit 1
