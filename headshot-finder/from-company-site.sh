#!/usr/bin/env bash
# from-company-site.sh — Best-effort headshot extraction from a company's
# team / about / leadership page. Tries common URL paths, parses HTML for
# <img> tags near the person's name. Heuristic-first; for tricky sites a
# sub-agent fallback can do better but is out of scope for this script.
#
# Usage:
#   from-company-site.sh "<First>" "<Last>" "<domain>"
#
# Output: JSON {url, page_url, source} to stdout if found.
# Exit 0 on found, 1 on not found, 2 on bad args.

set -uo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: from-company-site.sh <first> <last> <domain>" >&2
    exit 2
fi

FIRST="$1"; LAST="$2"; DOMAIN="$3"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

DOMAIN=$(echo "$DOMAIN" | sed -E 's|^https?://||; s|^www\.||; s|/.*$||')

PATHS=(
    "/team"  "/about/team"  "/our-team"  "/leadership"
    "/our-people" "/people" "/about" "/about-us"
    "/staff" "/management" "/who-we-are" "/meet-the-team"
)

extract_image() {
    local url="$1"
    local html
    html=$(curl -sS --max-time 12 -L -A "$UA" "$url" 2>/dev/null) || return 1
    [[ -z "$html" || ${#html} -lt 500 ]] && return 1
    PERSON="${FIRST} ${LAST}" PAGE_URL="$url" HTML="$html" python3 <<'PY'
import os, re, sys, urllib.parse
text = os.environ["HTML"]
person = os.environ["PERSON"].strip()
page_url = os.environ["PAGE_URL"]
img_re = re.compile(r'<img[^>]+>', re.IGNORECASE)
src_re = re.compile(r'\bsrc=["\']([^"\']+)["\']', re.IGNORECASE)
alt_re = re.compile(r'\balt=["\']([^"\']+)["\']', re.IGNORECASE)
matches = []
for m in img_re.finditer(text):
    img_tag = m.group(0)
    src_m = src_re.search(img_tag)
    if not src_m:
        continue
    src = src_m.group(1)
    alt_m = alt_re.search(img_tag)
    alt = alt_m.group(1) if alt_m else ""
    sl = src.lower()
    if any(s in sl for s in ("logo", "icon", "favicon", "spacer", "background", "data:image")):
        continue
    score = 0
    if person.lower() in alt.lower():
        score = 100
    else:
        ctx_start = max(0, m.start() - 600)
        ctx_end = min(len(text), m.end() + 600)
        if person.lower() in text[ctx_start:ctx_end].lower():
            score = 70
    if score > 0:
        full = urllib.parse.urljoin(page_url, src)
        matches.append((score, full))
matches.sort(reverse=True)
if matches:
    import json
    print(json.dumps({"url": matches[0][1], "page_url": page_url, "source": "company-site"}))
PY
}

for base in "https://${DOMAIN}" "https://www.${DOMAIN}"; do
    for path in "${PATHS[@]}"; do
        result=$(extract_image "${base}${path}")
        if [[ -n "$result" ]]; then
            echo "$result"
            exit 0
        fi
    done
done

exit 1
