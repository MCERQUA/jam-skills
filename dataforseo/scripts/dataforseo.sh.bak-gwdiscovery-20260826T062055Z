#!/bin/bash
# DataForSEO API helper — called from OpenClaw agents
# Routes ALL calls through the social dashboard proxy for cost tracking.
# Usage: bash dataforseo.sh <endpoint> '<json_body>'
# Example: bash dataforseo.sh "keywords_data/google_ads/search_volume/live" '[{"keywords":["roof repair"],"location_name":"United States","language_name":"English"}]'
#
# Optional: set CLIENT_TAG to attribute a call to a specific client/site when
# one tenant serves multiple businesses (e.g. src-desktop's PAA pulls across
# queen-anne-roofing vs ballard-roofing share the same tenant hostname).
#   CLIENT_TAG=queen-anne-roofing bash dataforseo.sh "serp/google/organic/live/advanced" '[...]'

set -euo pipefail

ENDPOINT="${1:?Usage: dataforseo.sh <endpoint> '<json_body>'}"
BODY="${2:?Usage: dataforseo.sh <endpoint> '<json_body>'}"

# Resolve tenant from container hostname (openclaw-<username> → <username>)
TENANT="${HOSTNAME#openclaw-}"
if [ -z "$TENANT" ] || [ "$TENANT" = "$HOSTNAME" ]; then
  TENANT="${USER:-unknown}"
fi

# Proxy URL — social dashboard on the host, reachable via Docker gateway
PROXY_URL="${DATAFORSEO_PROXY_URL:-http://172.25.0.1:6350}"

# Sanitize to a plain slug so it can't break out of the JSON body
CLIENT_TAG_CLEAN=$(printf '%s' "${CLIENT_TAG:-}" | tr -c 'A-Za-z0-9_-' '_')
CLIENT_TAG_FIELD=""
if [ -n "$CLIENT_TAG_CLEAN" ]; then
  CLIENT_TAG_FIELD=", \"client_tag\": \"$CLIENT_TAG_CLEAN\""
fi

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$PROXY_URL/api/seo/proxy?tenant=$TENANT" \
  -H "Content-Type: application/json" \
  -d "{\"endpoint\": \"$ENDPOINT\", \"data\": $BODY, \"source\": \"agent\"$CLIENT_TAG_FIELD}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY_RESP=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ge 400 ]; then
  echo "ERROR: HTTP $HTTP_CODE from proxy" >&2
  echo "$BODY_RESP" >&2
  exit 1
fi

echo "$BODY_RESP"
