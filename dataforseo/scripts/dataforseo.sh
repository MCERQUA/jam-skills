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
    [ -n "${DATAFORSEO_PROXY_URL:-}" ] && { printf '%s' "$DATAFORSEO_PROXY_URL"; return 0; }
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
    # LOUD, NOT SILENT. The fallback path still returns correct DATA — the caller can and
    # should proceed — but the COST TRACKING is gone, and that is invisible by nature:
    # nothing errors, no output is missing, and the dashboard simply shows less spend than
    # actually occurred. A tracker that under-reports without complaining is worse than one
    # that is visibly down. So we say it out loud, every call, and leave a machine-readable
    # marker a reconciler can find later.
    PROXY_URL=""
    echo "WARNING: dataforseo cost-tracking proxy is UNREACHABLE from this container." >&2
    echo "         Tried: \$DATAFORSEO_PROXY_URL, container default gateway, 172.18.0.1," >&2
    echo "         172.17.0.1, host.docker.internal, 172.25.0.1 — all refused connection." >&2
    echo "         Calls will still work via direct API auth, but SPEND WILL NOT BE RECORDED" >&2
    echo "         in the social-dashboard SEO history. Report this to host@mesh." >&2
    _marker="${TMPDIR:-/tmp}/.dataforseo-untracked-spend.log"
    printf '%s tenant=%s endpoint=%s proxy=UNREACHABLE\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${TENANT:-unknown}" "${ENDPOINT:-?}" >> "$_marker" 2>/dev/null
fi

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
