#!/usr/bin/env bash
# from-hunter.sh — Hunter.io email-finder lookup for the LinkedIn URL +
# position. NO image fetch (Hunter doesn't return one). Cheap source of
# linkedin_url for record-keeping.
#
# Usage:
#   from-hunter.sh "<First>" "<Last>" "<domain>"
#
# Output: JSON {linkedin_url, twitter, position, email, score} to stdout.
# Exit 0 on found, 1 on not found, 2 on bad args / missing env.

set -uo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: from-hunter.sh <first> <last> <domain>" >&2
    exit 2
fi

FIRST="$1"; LAST="$2"; DOMAIN="$3"

if [[ -z "${HUNTER_API_KEY:-}" ]]; then
    echo "from-hunter.sh: HUNTER_API_KEY not set" >&2
    exit 2
fi

resp=$(curl -sS --max-time 15 \
    "https://api.hunter.io/v2/email-finder?domain=${DOMAIN}&first_name=${FIRST}&last_name=${LAST}&api_key=${HUNTER_API_KEY}")

RESP="$resp" python3 - <<'PY'
import json, os, sys
try:
    d = json.loads(os.environ["RESP"]).get("data") or {}
except Exception as e:
    print(f"from-hunter.sh: parse error: {e}", file=sys.stderr); sys.exit(1)
out = {
    "linkedin_url": d.get("linkedin_url"),
    "twitter":      d.get("twitter"),
    "position":     d.get("position"),
    "email":        d.get("email"),
    "score":        d.get("score", 0),
}
if not (out["linkedin_url"] or out["email"]):
    sys.exit(1)
print(json.dumps(out))
PY
