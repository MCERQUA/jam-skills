#!/usr/bin/env bash
# =============================================================================
# webdev-preview.sh — wake THIS tenant's live-preview container, from inside the
# tenant's own agent container. For the voice-app live-edit flow ONLY.
#
#   webdev-preview.sh wake          # start it, return immediately (non-blocking)
#   webdev-preview.sh wait [secs]   # block until it actually serves (default 45)
#   webdev-preview.sh status        # JSON: is it up / starting / ready
#
# WHY THIS EXISTS
# The webdev container is the client's live preview — the thing they watch
# hot-reload while you edit their site. It is NOT a steady-state service: real
# live-edit sessions are occasional, so the container is STOPPED by default and
# woken on demand. Keeping 14 of them idle cost ~4 GiB of RAM permanently.
#
# THE ONE RULE THAT MATTERS: call `wake` the MOMENT the user asks to see their
# site — BEFORE you start editing. A Next.js dev server takes ~17s to cold-boot
# and serve its first request. If you wake it first and then edit, those 17s
# happen while you are already working and the client never waits. If you edit
# first and wake after, the client stares at a loading page.
#
# Reaches the host wakeup service over the jambot-shared bridge gateway
# (172.19.0.1:5199) — internal to the container network, never public.
# =============================================================================
set -uo pipefail

HOST="${WAKEUP_HOST:-172.19.0.1}"
PORT="${WAKEUP_PORT:-5199}"
BASE="http://${HOST}:${PORT}"

# Tenant identity. NOTE (verified 2026-07-24 across the fleet): openclaw
# containers do NOT set JAMBOT_TENANT — it is empty everywhere. The real,
# consistently-present identity is AGENT_URI = "<tenant>-voice@mesh", so that
# is what actually resolves here. JAMBOT_TENANT is honoured first only as an
# override for host-side testing.
TENANT="${JAMBOT_TENANT:-${AGENT_URI%%@*}}"
TENANT="${TENANT%%-voice}"; TENANT="${TENANT%%-host}"; TENANT="${TENANT%%-sms}"
if [ -z "$TENANT" ]; then
    echo "webdev-preview: cannot determine tenant (set JAMBOT_TENANT)" >&2
    exit 2
fi

CMD="${1:-wake}"

_get() {  # _get <path>  → body on stdout, curl-less fallback via python3
    if command -v curl >/dev/null 2>&1; then
        curl -s --max-time 15 "${BASE}$1"
    else
        # openclaw containers ship without curl — urllib is always present.
        python3 -c "
import sys,urllib.request
try:
    print(urllib.request.urlopen('${BASE}$1', timeout=15).read().decode())
except Exception as e:
    # an HTTP 202 is success for /webdev; urllib raises only on >=400
    import urllib.error
    if isinstance(e, urllib.error.HTTPError) and e.code < 400:
        print(e.read().decode())
    else:
        print('{\"ok\":false,\"error\":\"%s\"}' % e)
"
    fi
}

_ready() { _get "/webdev-status/${TENANT}" | grep -q '"ready": *true'; }

case "$CMD" in
    wake)
        _get "/webdev/${TENANT}"
        echo
        ;;
    status)
        _get "/webdev-status/${TENANT}"
        echo
        ;;
    wait)
        deadline=$(( $(date +%s) + ${2:-45} ))
        _get "/webdev/${TENANT}" >/dev/null   # ensure it is starting
        while [ "$(date +%s)" -lt "$deadline" ]; do
            if _ready; then echo "ready"; exit 0; fi
            sleep 2
        done
        echo "not-ready-within-timeout" >&2
        exit 1
        ;;
    *)
        echo "usage: webdev-preview.sh {wake|wait [secs]|status}" >&2
        exit 2
        ;;
esac
