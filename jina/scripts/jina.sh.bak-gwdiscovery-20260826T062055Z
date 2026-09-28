#!/bin/bash
# Jina AI helper — called from OpenClaw agents. MIRRORS dataforseo.sh.
# Routes ALL calls through the social-dashboard proxy on :6350 for cost tracking.
# The proxy holds JINA_API_KEY — agents NEVER hold the key.
#
# Usage:  bash jina.sh <product> '<json_body>'
#   product ∈ reader | search | embeddings | rerank | segment | grounding
#
# Examples:
#   bash jina.sh reader     '{"url":"https://competitor.com/services"}'
#   bash jina.sh search     '{"q":"best spray foam contractor phoenix"}'
#   bash jina.sh embeddings '{"input":["chunk a","chunk b"],"model":"jina-embeddings-v3","dimensions":1024}'
#   bash jina.sh rerank     '{"query":"R-value","documents":["...","..."],"top_n":5}'
#   bash jina.sh segment    '{"content":"<long text>","return_chunks":true}'   # FREE
#   bash jina.sh grounding  '{"statement":"Closed-cell foam is ~R-6.5/inch."}'  # heavy/gated
#
# Optional: CLIENT_TAG=<slug> attributes spend when one tenant serves multiple sites.
#
# ⚠️ STATUS: the /api/jina/* proxy is PLAN-ONLY (docs/jambot/jina-integration-plan.md).
#    This helper is shovel-ready — it works the moment the backend route ships.

set -euo pipefail

PRODUCT="${1:?Usage: jina.sh <product> '<json_body>'}"
BODY="${2:?Usage: jina.sh <product> '<json_body>'}"

case "$PRODUCT" in
  reader|search|embeddings|rerank|segment|grounding) : ;;
  *) echo "ERROR: unknown product '$PRODUCT' (reader|search|embeddings|rerank|segment|grounding)" >&2; exit 2 ;;
esac

# Resolve tenant from container hostname (openclaw-<username> → <username>)
TENANT="${HOSTNAME#openclaw-}"
if [ -z "$TENANT" ] || [ "$TENANT" = "$HOSTNAME" ]; then
  TENANT="${USER:-unknown}"
fi

# Proxy URL — social dashboard on the host, reachable via Docker gateway
PROXY_URL="${JINA_PROXY_URL:-http://172.25.0.1:6350}"

# Sanitize CLIENT_TAG to a plain slug so it can't break out of the JSON body
CLIENT_TAG_CLEAN=$(printf '%s' "${CLIENT_TAG:-}" | tr -c 'A-Za-z0-9_-' '_')
CLIENT_TAG_FIELD=""
if [ -n "$CLIENT_TAG_CLEAN" ]; then
  CLIENT_TAG_FIELD=", \"client_tag\": \"$CLIENT_TAG_CLEAN\""
fi

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$PROXY_URL/api/jina/$PRODUCT?tenant=$TENANT" \
  -H "Content-Type: application/json" \
  -d "{\"body\": $BODY, \"source\": \"agent\"$CLIENT_TAG_FIELD}")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY_RESP=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -ge 400 ]; then
  echo "ERROR: HTTP $HTTP_CODE from Jina proxy (product=$PRODUCT)" >&2
  echo "$BODY_RESP" >&2
  exit 1
fi

echo "$BODY_RESP"
