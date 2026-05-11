#!/usr/bin/env bash
# from-google-image.sh — Google Images SERP via DataForSEO. Returns ranked
# image URLs for "<First> <Last> <Company>" filtered for headshot likelihood
# (LinkedIn-hosted > company-domain > everything else).
#
# Usage:
#   from-google-image.sh "<First>" "<Last>" "<Company>" [--limit N] [--domain X.com]
#
# Output: JSON array of {rank, url, source_domain, source_url, confidence_hint}
# to stdout. Exit 0 on results, 1 on no results, 2 on bad args.
#
# Cost: ~$0.0006 per call. Uses paid DataForSEO API.

set -uo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: from-google-image.sh <first> <last> <company> [--limit N] [--domain X.com]" >&2
    exit 2
fi

FIRST="$1"; LAST="$2"; COMPANY="$3"; shift 3
LIMIT=10
DOMAIN=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)  LIMIT="$2"; shift 2 ;;
        --domain) DOMAIN="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ -z "${DATAFORSEO_LOGIN:-}" || -z "${DATAFORSEO_PASSWORD:-}" ]]; then
    echo "from-google-image.sh: DATAFORSEO_LOGIN/PASSWORD not set" >&2
    exit 2
fi

QUERY="\"${FIRST} ${LAST}\" ${COMPANY} headshot OR portrait OR linkedin"

payload=$(QUERY="$QUERY" LIMIT="$LIMIT" python3 -c '
import json, os
print(json.dumps([{
  "keyword": os.environ["QUERY"],
  "location_code": 2840,
  "language_code": "en",
  "depth": int(os.environ["LIMIT"]),
}]))')

resp=$(curl -sS --max-time 60 \
    -u "${DATAFORSEO_LOGIN}:${DATAFORSEO_PASSWORD}" \
    -H "Content-Type: application/json" \
    -X POST \
    -d "$payload" \
    "https://api.dataforseo.com/v3/serp/google/images/live/advanced")

DOMAIN_FILTER="$DOMAIN" RESP="$resp" python3 - <<'PY'
import json, os, sys, urllib.parse
try:
    d = json.loads(os.environ["RESP"])
except Exception as e:
    print(f"from-google-image.sh: parse error: {e}", file=sys.stderr); sys.exit(1)

tasks = d.get("tasks", [])
if not tasks or tasks[0].get("status_code") != 20000:
    msg = (tasks[0].get("status_message") if tasks else "no tasks") if tasks else "no tasks"
    print(f"from-google-image.sh: dataforseo error: {msg}", file=sys.stderr); sys.exit(1)

result = (tasks[0].get("result") or [{}])[0]
items = (result.get("items") or [])
if not items:
    print("[]"); sys.exit(1)

domain = os.environ.get("DOMAIN_FILTER","").lower().strip()
out = []
for i, it in enumerate(items, 1):
    img_url = it.get("source_url") or it.get("url")  # source_url = direct image URL
    src_url = it.get("url") or ""                      # url = page hosting the image
    if not img_url:
        continue
    try:
        host = urllib.parse.urlparse(src_url).netloc.lower()
    except Exception:
        host = ""
    # Confidence hint: company-domain hand-curated photos beat LinkedIn directory
    # results (which can match the wrong person of the same name)
    if domain and domain in host:
        conf = 95
        hint = "company-domain"
    elif "licdn.com" in (img_url or "") or "linkedin.com" in host:
        conf = 85
        hint = "linkedin-hosted"
    elif any(s in host for s in ("facebook.com","fbcdn.net","m.facebook.com")):
        # Skip — no FB by policy
        continue
    elif any(s in host for s in ("crunchbase.com","bloomberg.com","forbes.com","spfa.org","sprayfoam.com","sprayfoammagazine.com")):
        conf = 65
        hint = "industry-source"
    else:
        conf = 40
        hint = "unranked"
    out.append({
        "rank": i,
        "url": img_url,
        "source_domain": host,
        "source_url": src_url,
        "confidence_hint": conf,
        "hint_reason": hint,
    })

# Sort: highest confidence first, then by original SERP rank
out.sort(key=lambda x: (-x["confidence_hint"], x["rank"]))
print(json.dumps(out, indent=2))
PY
