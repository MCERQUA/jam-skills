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
# ── RESOLVE THE HOST PROXY, DO NOT HARDCODE A BRIDGE IP (host@mesh 2026-08-26) ──
# This was hardcoded to http://172.25.0.1:6350. That address is not assigned on this
# host at all, so every call from a submesh worker failed and fell through to a direct
# API call. MEASURED: 28 site-build research files carry a worker's note that the proxy
# was unreachable, the oldest from 2026-07-28. The workers behaved correctly every time —
# they documented the fallback and flagged that spend was untracked. Nobody read the notes.
#
# WHY NO SINGLE IP IS CORRECT: containers here are multi-homed (a per-tenant bridge plus
# jambot-shared), and Docker reassigns bridge subnets when a network is recreated. Measured
# from openclaw-josh: default gateway 10.40.176.1, but the dashboard answers on 172.18.0.1.
# A literal address is a guess with an expiry date.
#
# WHY 400 COUNTS AS REACHABLE: a 400 is the APPLICATION answering — the TCP connect and the
# HTTP exchange both succeeded. Only 000 means no route. Treating a 4xx as "down" would
# reject the working address.
_resolve_proxy_base() {
    [ -n "${JINA_PROXY_URL:-}" ] && { printf '%s' "$JINA_PROXY_URL"; return 0; }
    [ -n "${JAMBOT_PROXY_URL:-}" ]     && { printf '%s' "$JAMBOT_PROXY_URL"; return 0; }

    _cache="${TMPDIR:-/tmp}/.jambot-proxy-base"
    if [ -r "$_cache" ]; then
        _cached=$(cat "$_cache" 2>/dev/null)
        if [ -n "$_cached" ] && [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "$_cached/api/leads" 2>/dev/null)" != "000" ]; then
            printf '%s' "$_cached"; return 0
        fi
    fi

    # Candidates: the container's real default gateway first (from /proc/net/route, which
    # exists in every Linux container — `ip` does NOT; it is absent in these images and an
    # `ip route` parse silently yielded an empty gateway here).
    _cands=""
    if [ -r /proc/net/route ]; then
        _hex=$(awk '$2=="00000000" && $1!="Iface" {print $3; exit}' /proc/net/route 2>/dev/null)
        if [ -n "$_hex" ] && [ "$_hex" != "00000000" ]; then
            _cands="$(printf '%d.%d.%d.%d' \
                0x${_hex#??????} 0x$(echo "$_hex" | cut -c5-6) \
                0x$(echo "$_hex" | cut -c3-4) 0x$(echo "$_hex" | cut -c1-2) 2>/dev/null)"
        fi
    fi
    _cands="$_cands 172.18.0.1 172.17.0.1 host.docker.internal 172.25.0.1"

    for _c in $_cands; do
        [ -z "$_c" ] && continue
        if [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://$_c:6350/api/leads" 2>/dev/null)" != "000" ]; then
            printf 'http://%s:6350' "$_c" > "$_cache" 2>/dev/null
            printf 'http://%s:6350' "$_c"; return 0
        fi
    done
    return 1
}

if PROXY_URL=$(_resolve_proxy_base); then
    :
else
    PROXY_URL=""
    echo "WARNING: jina proxy UNREACHABLE from this container — calls may still work via" >&2
    echo "         direct auth, but usage will NOT be recorded. Report to host@mesh." >&2
fi

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
