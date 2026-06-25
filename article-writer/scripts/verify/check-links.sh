#!/usr/bin/env bash
# check-links.sh — DETERMINISTIC broken-link scan (no LLM).
#
# Scans EVERY link in the staged article body (internal + outbound) and confirms
# each resolves to a live HTTP 200/2xx/3xx. ZERO broken links allowed to publish.
#
#   - Outbound (http/https): HEAD then GET fallback; must be < 400.
#   - Internal (/path):       resolved against meta.site_url; must be < 400 IF the
#                             site is live. Brand-new internal links to a money page
#                             that already exists are validated against the live site.
#                             (A link to THIS not-yet-published post is skipped.)
#
# Usage:  check-links.sh <work_dir>
# Exit:   0 = PASS (all links live), 1 = FAIL (>=1 broken)
set -uo pipefail
WORK_DIR="${1:?usage: check-links.sh <work_dir>}"
LIB="$(cd "$(dirname "$0")/../lib" && pwd)"
ART="$WORK_DIR/article.mdx"; [ -f "$ART" ] || ART="$WORK_DIR/article.md"
META="$WORK_DIR/meta.json"

site_url=""
this_slug=""
if [ -f "$META" ]; then
  site_url=$(jq -r '.site_url // ""' "$META" 2>/dev/null)
fi
# this post's own slug (so we don't fail on a self-link to the unpublished page)
this_slug=$(awk '/^slug:/{gsub(/slug:|"|'"'"'| /,""); print; exit}' "$ART" 2>/dev/null)

# Extract URLs via the shared python extractor (markdown + html links)
mapfile -t URLS < <(python3 - "$WORK_DIR" "$LIB" <<'PY'
import sys, os
work_dir, lib = sys.argv[1], sys.argv[2]
sys.path.insert(0, lib)
from article_io import load_article, extract_links
art = load_article(work_dir)
seen=set()
for l in extract_links(art["body"]):
    u=l["url"]
    if u and u not in seen:
        seen.add(u); print(u)
PY
)

echo "=== GATE: broken-link-scan ==="
echo "  site_url=$site_url  this_slug=$this_slug  links_found=${#URLS[@]}"

fail=0
checked=0
UA="Mozilla/5.0 (compatible; JamBot-BlogFactory-LinkCheck/1.0)"

check_url () {
  local url="$1"
  # HEAD first
  local code
  code=$(curl -s -o /dev/null -L --max-time 20 -A "$UA" -w "%{http_code}" -I "$url" 2>/dev/null)
  if [ "$code" = "000" ] || [ "${code:0:1}" = "4" ] || [ "${code:0:1}" = "5" ]; then
    # some servers reject HEAD — retry GET
    code=$(curl -s -o /dev/null -L --max-time 25 -A "$UA" -w "%{http_code}" "$url" 2>/dev/null)
  fi
  echo "$code"
}

for u in "${URLS[@]}"; do
  target="$u"
  # internal link → resolve against site_url
  if [[ "$u" == /* ]]; then
    if [ -z "$site_url" ]; then
      echo "  [SKIP] internal link (no site_url to resolve): $u"
      continue
    fi
    # self-link to the not-yet-published post → skip
    if [ -n "$this_slug" ] && [[ "$u" == *"/blog/$this_slug"* ]]; then
      echo "  [SKIP] self-link to unpublished post: $u"
      continue
    fi
    target="${site_url%/}$u"
  fi
  code=$(check_url "$target")
  checked=$((checked+1))
  if [ "$code" = "000" ] || [ "${code:0:1}" = "4" ] || [ "${code:0:1}" = "5" ]; then
    echo "  [FAIL] $code  $target"
    fail=$((fail+1))
  else
    echo "  [PASS] $code  $target"
  fi
done

if [ "$fail" -gt 0 ]; then
  echo "  >>> broken-link-scan: FAIL ($fail broken of $checked checked)"
  exit 1
fi
echo "  >>> broken-link-scan: PASS ($checked links live)"
exit 0
