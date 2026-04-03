#!/bin/bash
# DataForSEO API helper — called from OpenClaw agents
# Usage: bash dataforseo.sh <endpoint> '<json_body>'
# Example: bash dataforseo.sh "keywords_data/google_ads/search_volume/live" '[{"keywords":["roof repair"],"location_name":"United States","language_name":"English"}]'

set -euo pipefail

ENDPOINT="${1:?Usage: dataforseo.sh <endpoint> '<json_body>'}"
BODY="${2:?Usage: dataforseo.sh <endpoint> '<json_body>'}"

if [ -z "$DATAFORSEO_LOGIN" ] || [ -z "$DATAFORSEO_PASSWORD" ]; then
  echo "ERROR: DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD must be set" >&2
  exit 1
fi

AUTH=$(echo -n "$DATAFORSEO_LOGIN:$DATAFORSEO_PASSWORD" | base64)
URL="https://api.dataforseo.com/v3/$ENDPOINT"

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$URL" \
  -H "Authorization: Basic $AUTH" \
  -H "Content-Type: application/json" \
  -d "$BODY")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY_RESP=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ge 400 ]; then
  echo "ERROR: HTTP $HTTP_CODE" >&2
  echo "$BODY_RESP" >&2
  exit 1
fi

echo "$BODY_RESP"
