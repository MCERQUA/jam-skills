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

# Auto-detect host IP from container's default route.
# /proc/net/route format: column 2 = destination (00000000 = default), column 3 = gateway in hex little-endian.
detect_host_ip() {
  awk '$2 == "00000000" { print $3 }' /proc/net/route | head -1 \
    | python3 -c 'import sys; h=sys.stdin.read().strip(); print(".".join(str(int(h[i:i+2],16)) for i in range(6,-1,-2)))' 2>/dev/null \
    || echo "172.17.0.1"
}

ROUTER="${SMS_ROUTER_URL:-http://$(detect_host_ip):6450}"

RESPONSE=$(curl -s -X POST "$ROUTER/send" \
  -H 'Content-Type: application/json' \
  -d "$(TENANT="$TENANT" TO="$TO" BODY="$BODY" python3 -c "
import json, os
print(json.dumps({'tenant': os.environ['TENANT'], 'to': os.environ['TO'], 'body': os.environ['BODY']}))
")")

SUCCESS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok',False))" 2>/dev/null || echo "false")
SID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('twilio_sid') or '')" 2>/dev/null || echo "")

if [ "$SUCCESS" = "True" ]; then
  echo "SMS sent OK. Twilio SID: $SID"
  echo "  Router: $ROUTER"
  echo "  To: $TO"
  echo "  From-tenant: $TENANT"
else
  echo "ERROR: SMS send failed" >&2
  echo "  Router: $ROUTER" >&2
  echo "$RESPONSE" >&2
  exit 1
fi
