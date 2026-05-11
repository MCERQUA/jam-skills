#!/usr/bin/env bash
# quota.sh — show remaining Hunter + Snov quota for the month.
# Apollo isn't shown (org search is unlimited on free plan; people endpoints
# are gated by plan tier, not credits).
#
# Usage:
#   quota.sh                # both providers, human-readable
#   quota.sh --raw          # both providers, raw JSON
#   quota.sh --hunter       # Hunter only
#   quota.sh --snov         # Snov only

set -uo pipefail

MODE="all"
RAW=0
for arg in "$@"; do
    case "$arg" in
        --hunter) MODE="hunter" ;;
        --snov)   MODE="snov" ;;
        --raw)    RAW=1 ;;
        *) echo "usage: quota.sh [--hunter|--snov] [--raw]" >&2; exit 2 ;;
    esac
done

show_hunter() {
    [[ -z "${HUNTER_API_KEY:-}" ]] && { echo "Hunter: HUNTER_API_KEY not set" >&2; return 1; }
    local resp
    resp=$(curl -sS --max-time 15 "https://api.hunter.io/v2/account?api_key=${HUNTER_API_KEY}")
    if (( RAW )); then echo "$resp"; return 0; fi
    python3 - <<PY
import json,sys
try:
    d = json.loads('''$resp''').get("data", {})
except Exception:
    print("Hunter: parse error")
    sys.exit(1)
plan = d.get("plan_name","?")
reset = d.get("reset_date","?")
req = d.get("requests", {})
sa, su = req.get("searches", {}).get("available","?"), req.get("searches", {}).get("used","?")
va, vu = req.get("verifications", {}).get("available","?"), req.get("verifications", {}).get("used","?")
print(f"Hunter ({plan}, resets {reset}):")
print(f"  searches:      {su}/{sa} used")
print(f"  verifications: {vu}/{va} used")
PY
}

show_snov() {
    [[ -z "${SNOV_USER_ID:-}" || -z "${SNOV_SECRET:-}" ]] && { echo "Snov: keys not set" >&2; return 1; }
    local token
    token=$(curl -sS --max-time 15 -X POST "https://api.snov.io/v1/oauth/access_token" \
        -d "grant_type=client_credentials&client_id=${SNOV_USER_ID}&client_secret=${SNOV_SECRET}" \
        | python3 -c 'import sys,json
try:
  d=json.load(sys.stdin); print(d.get("access_token",""))
except Exception: pass')
    [[ -z "$token" ]] && { echo "Snov: OAuth failed" >&2; return 1; }
    local resp
    resp=$(curl -sS --max-time 15 "https://api.snov.io/v1/get-balance" -H "Authorization: Bearer $token")
    if (( RAW )); then echo "$resp"; return 0; fi
    python3 - <<PY
import json,sys
try:
    d = json.loads('''$resp''')
    bal = d.get("data", {})
except Exception:
    print("Snov: parse error"); sys.exit(1)
print(f"Snov:")
print(f"  balance:      {bal.get('balance','?')} credits")
print(f"  resets in:    {bal.get('limit_resets_in','?')} days")
PY
}

[[ "$MODE" == "all" || "$MODE" == "hunter" ]] && show_hunter
[[ "$MODE" == "all" || "$MODE" == "snov" ]] && show_snov
