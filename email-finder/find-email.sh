#!/usr/bin/env bash
# find-email.sh — find a business email for <first> <last> at <domain>.
#
# Tries providers in order: Hunter (primary) → Snov (fallback) → Apollo
# (company enrichment only). Prints the highest-confidence hit as JSON to
# stdout. Exits 0 if any provider returned an email, 1 otherwise.
#
# Usage:
#   find-email.sh <first> <last> <domain> [--provider hunter|snov|apollo|all]
#   find-email.sh "Joel" "Pressley" "insulate48.com"
#   find-email.sh "Joel" "Pressley" "insulate48.com" --provider snov
#
# Required env (read from /mnt/system/base/.platform-keys.env or container env):
#   HUNTER_API_KEY, SNOV_USER_ID, SNOV_SECRET, APOLLO_API_KEY

set -uo pipefail

if [[ $# -lt 3 ]]; then
    cat >&2 <<EOF
usage: find-email.sh <first> <last> <domain> [--provider hunter|snov|apollo|all]
EOF
    exit 2
fi

FIRST="$1"; LAST="$2"; DOMAIN="$3"
PROVIDER="all"
if [[ "${4:-}" == "--provider" && -n "${5:-}" ]]; then
    PROVIDER="$5"
fi

require_env() {
    local var="$1"
    if [[ -z "${!var:-}" ]]; then
        echo "find-email.sh: $var not set" >&2
        return 1
    fi
}

try_hunter() {
    require_env HUNTER_API_KEY || return 1
    local resp
    resp=$(curl -sS --max-time 15 \
        "https://api.hunter.io/v2/email-finder?domain=${DOMAIN}&first_name=${FIRST}&last_name=${LAST}&api_key=${HUNTER_API_KEY}") || return 1
    python3 - <<PY
import json, sys
try:
    d = json.loads('''$resp''')
except Exception:
    sys.exit(1)
data = d.get("data") or {}
email = data.get("email")
if not email:
    sys.exit(1)
out = {
    "email": email,
    "confidence": data.get("score", 0),
    "source": "hunter",
    "name": (data.get("first_name","") + " " + data.get("last_name","")).strip() or "${FIRST} ${LAST}",
    "title": data.get("position") or "",
    "linkedin": data.get("linkedin_url") or "",
}
print(json.dumps(out))
PY
}

try_snov() {
    require_env SNOV_USER_ID || return 1
    require_env SNOV_SECRET || return 1
    local token
    token=$(curl -sS --max-time 15 -X POST "https://api.snov.io/v1/oauth/access_token" \
        -d "grant_type=client_credentials&client_id=${SNOV_USER_ID}&client_secret=${SNOV_SECRET}" \
        | python3 -c 'import sys,json
try:
  d=json.load(sys.stdin)
  print(d.get("access_token",""))
except Exception:
  pass') || return 1
    [[ -z "$token" ]] && return 1
    local resp
    resp=$(curl -sS --max-time 15 -X POST "https://api.snov.io/v1/get-emails-from-names" \
        -d "access_token=${token}&firstName=${FIRST}&lastName=${LAST}&domain=${DOMAIN}") || return 1
    python3 - <<PY
import json, sys
try:
    d = json.loads('''$resp''')
except Exception:
    sys.exit(1)
data = d.get("data") or {}
emails = data.get("emails") or []
if not emails:
    sys.exit(1)
top = emails[0]
out = {
    "email": top.get("email"),
    "confidence": top.get("emailStatus") == "valid" and 90 or 60,
    "source": "snov",
    "name": data.get("name") or "${FIRST} ${LAST}",
    "title": top.get("position") or "",
    "linkedin": top.get("sourcePage") or "",
}
print(json.dumps(out))
PY
}

try_apollo() {
    # Apollo's free plan blocks people/match — only org enrichment works.
    # We surface the org info so the caller can fall back to LinkedIn manually.
    require_env APOLLO_API_KEY || return 1
    local resp
    resp=$(curl -sS --max-time 15 -X POST "https://api.apollo.io/v1/organizations/search" \
        -H "X-Api-Key: ${APOLLO_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"q_organization_domains\":\"${DOMAIN}\"}") || return 1
    python3 - <<PY
import json, sys
try:
    d = json.loads('''$resp''')
except Exception:
    sys.exit(1)
orgs = d.get("organizations") or []
if not orgs:
    sys.exit(1)
o = orgs[0]
out = {
    "email": None,  # free plan can't return people emails
    "confidence": 0,
    "source": "apollo-org-only",
    "name": o.get("name"),
    "title": "",
    "linkedin": o.get("linkedin_url") or "",
    "phone": o.get("phone") or "",
    "_note": "Apollo free plan returns company data only; use LinkedIn to find people manually.",
}
print(json.dumps(out))
PY
}

best=""; best_conf=-1
for p in hunter snov apollo; do
    if [[ "$PROVIDER" != "all" && "$PROVIDER" != "$p" ]]; then continue; fi
    out=$("try_$p" 2>/dev/null) || continue
    [[ -z "$out" ]] && continue
    conf=$(python3 -c "import json,sys; print(json.loads('$out').get('confidence',0))" 2>/dev/null || echo 0)
    if (( conf > best_conf )); then
        best="$out"; best_conf="$conf"
    fi
    # short-circuit on a strong hunter hit
    if [[ "$p" == "hunter" && "$conf" -ge 80 ]]; then break; fi
done

if [[ -n "$best" ]]; then
    echo "$best"
    exit 0
fi

echo '{"email":null,"confidence":0,"source":"none","note":"no provider returned an email"}'
exit 1
