#!/bin/bash
# sms-send.sh — agent-side SMS sender. Wraps POST <host>:6450/send.
#
# Usage: bash sms-send.sh <tenant> <to-phone-E164> "<body>"
#
# The router prepends "[<tenant>] " to the body so the operator knows which agent texted.
# Returns the Twilio SID on success.
#
# Host IP is auto-detected from the container's default route (different per tenant bridge).
# Override with SMS_ROUTER_URL env var if needed.

set -euo pipefail

TENANT="${1:?tenant required (nick / danielle / test-dev / mike)}"
TO="${2:?to phone E.164 required (+1XXXXXXXXXX)}"
BODY="${3:?body required}"

# ── CROSS-TENANT RECIPIENT GUARD (2026-09-07) ───────────────────────────────────────
# This script took <tenant> and <to> as independent arguments and never checked that the
# destination belonged to the tenant. Measured 2026-09-07 23:07:08Z: danielle's "Daily
# Money Brief from Danielle" was DELIVERED (HTTP 201, not blocked) to +19132063301 —
# phatty's owner. danielle's own USER.md documents her number as +12894048807, on the very
# line that shows how to call this script. One wrong argument put one client's business
# content on another client's phone, and nothing in the path could see it.
#
# The check is deliberately NARROW, because a tenant legitimately texts numbers we have
# never seen (leads, customers, suppliers):
#   · destination NOT in the registry        -> ALLOW  (unknown != wrong; do not break outreach)
#   · destination registered to THIS tenant  -> ALLOW
#   · destination registered to ANOTHER one  -> REFUSE (this is the only unambiguous case)
# So it blocks exactly tonight's failure and nothing else. Override for a deliberate
# cross-tenant send (a human relaying, an operator test) with SMS_ALLOW_CROSS_TENANT=1,
# which is logged by the router either way.
REG520="${REG520_FILE:-/mnt/system/setup-host/config/registered-520.json}"
if [ "${SMS_ALLOW_CROSS_TENANT:-0}" != "1" ] && [ -r "$REG520" ]; then
  OWNER=$(TO="$TO" REG="$REG520" python3 -c "
import json, os, sys
try:
    d = json.load(open(os.environ['REG']))
except Exception:
    sys.exit(0)                      # registry unreadable -> do not block a real send
e = d.get(os.environ['TO'])
if isinstance(e, dict) and e.get('tenant'):
    print(e['tenant'])
" 2>/dev/null || true)
  if [ -n "$OWNER" ] && [ "$OWNER" != "$TENANT" ]; then
    echo "REFUSED: $TO is registered to tenant '$OWNER', not '$TENANT'." >&2
    echo "  Sending '$TENANT' content to another tenant's owner is a cross-tenant leak." >&2
    echo "  If this is deliberate, re-run with SMS_ALLOW_CROSS_TENANT=1." >&2
    exit 3
  fi
fi

# Auto-detect host IP from container's default route.
# /proc/net/route format: column 2 = destination (00000000 = default), column 3 = gateway in hex little-endian.
detect_host_ip() {
  awk '$2 == "00000000" { print $3 }' /proc/net/route | head -1 \
    | python3 -c 'import sys; h=sys.stdin.read().strip(); print(".".join(str(int(h[i:i+2],16)) for i in range(6,-1,-2)))' 2>/dev/null \
    || echo "172.17.0.1"
}

ROUTER="${SMS_ROUTER_URL:-http://$(detect_host_ip):6450}"

# Try a DIRECT POST first (works when run on the host, or if the router is bridge-reachable).
RESPONSE=$(curl -s --max-time 6 -X POST "$ROUTER/send" \
  -H 'Content-Type: application/json' \
  -d "$(TENANT="$TENANT" TO="$TO" BODY="$BODY" python3 -c "
import json, os
print(json.dumps({'tenant': os.environ['TENANT'], 'to': os.environ['TO'], 'body': os.environ['BODY']}))
")" 2>/dev/null || true)

SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok',False))" 2>/dev/null || echo "false")
SID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('twilio_sid') or '')" 2>/dev/null || echo "")

if [ "$SUCCESS" = "True" ]; then
  echo "SMS sent OK. Twilio SID: $SID"
  echo "  Router: $ROUTER"; echo "  To: $TO"; echo "  From-tenant: $TENANT"
  exit 0
fi

# Direct send failed — expected from inside a tenant container, since the router is bound to
# 127.0.0.1 (security hardening) and unreachable on the bridge. Fall back to the OUTBOUND QUEUE:
# write a request to the mesh-mounted queue; the host-side jambot-sms-outbound-drain.py (cron */1)
# picks it up and POSTs it to the loopback router. /mnt/agent-mesh is mounted in every tenant
# container, so this works platform-wide. (Added 2026-06-22 — the loopback bind broke the direct path.)
QDIR=/mnt/agent-mesh/mesh/sms-outbound-queue
if mkdir -p "$QDIR" 2>/dev/null; then
  QF="$QDIR/$(date -u +%Y%m%dT%H%M%S)-${TENANT}-$$.json"
  if TENANT="$TENANT" TO="$TO" BODY="$BODY" python3 -c "
import json, os
open(os.environ.get('QF','$QF'),'w').write(json.dumps({'tenant':os.environ['TENANT'],'to':os.environ['TO'],'body':os.environ['BODY']}))
" QF="$QF" 2>/dev/null; then
    echo "SMS QUEUED (router not directly reachable — host drain will send within ~1 min)."
    echo "  Queue: $QF"; echo "  To: $TO"; echo "  From-tenant: $TENANT"
    exit 0
  fi
fi

echo "ERROR: SMS send failed (direct POST refused AND queue write failed)" >&2
echo "  Router: $ROUTER" >&2
echo "$RESPONSE" >&2
exit 1
