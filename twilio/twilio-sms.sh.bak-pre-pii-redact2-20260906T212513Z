#!/bin/bash
# Twilio SMS — send a text message
# Usage: bash twilio-sms.sh "+1XXXXXXXXXX" "Your message here"
#
# Env:
#   TWILIO_ACCOUNT_SID   (required)
#   TWILIO_AUTH_TOKEN    (required)
#   TWILIO_SMS_FROM      (preferred — Canadian +16476991930 JamBot SMS number)
#   TWILIO_FROM_NUMBER   (fallback — Arizona +16029327909, used for VOICE; only SMS-fallback if SMS_FROM unset)
#
# IMPORTANT: All JamBot agent-to-operator SMS MUST send from +16476991930 (Canadian/JamBot).
# The Arizona +16029327909 is reserved for US-client voice (Seattle Roofing etc.) and is OFF-LIMITS
# as an SMS sender for the agent mesh.

set -euo pipefail

TO="${1:?Usage: twilio-sms.sh <to-number> <message>}"
MESSAGE="${2:?Usage: twilio-sms.sh <to-number> <message>}"

# Prefer the Canadian SMS number; fall back to TWILIO_FROM_NUMBER only if SMS_FROM not set
FROM="${TWILIO_SMS_FROM:-${TWILIO_FROM_NUMBER:-}}"

if [ -z "${TWILIO_ACCOUNT_SID:-}" ] || [ -z "${TWILIO_AUTH_TOKEN:-}" ] || [ -z "$FROM" ]; then
  echo "ERROR: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_SMS_FROM (or TWILIO_FROM_NUMBER) must be set" >&2
  exit 1
fi

# Hard-block the Arizona number as an SMS sender — it's reserved for US-client voice only
if [ "$FROM" = "+16029327909" ]; then
  echo "ERROR: SMS from +16029327909 (Arizona) is BLOCKED. That number is reserved for US-client voice." >&2
  echo "       Set TWILIO_SMS_FROM=+16476991930 in env (it's in /mnt/system/base/.openclaw-keys.env)." >&2
  echo "       If the container has stale env, restart it: docker compose -f /mnt/clients/<u>/compose/docker-compose.yml restart openclaw" >&2
  exit 2
fi

RESPONSE=$(curl -s -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
  -d "To=${TO}" \
  -d "From=${FROM}" \
  --data-urlencode "Body=${MESSAGE}")

# Extract key fields
SID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sid',''))" 2>/dev/null || echo "")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")

if [ -n "$SID" ] && [ "$SID" != "null" ]; then
  echo "SMS sent successfully"
  echo "  Message SID: $SID"
  echo "  Status: $STATUS"
  echo "  To: $TO"
  echo "  From: $FROM"
else
  echo "ERROR: SMS failed" >&2
  echo "$RESPONSE" >&2
  exit 1
fi
