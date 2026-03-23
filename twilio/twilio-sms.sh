#!/bin/bash
# Twilio SMS — send a text message
# Usage: bash twilio-sms.sh "+1XXXXXXXXXX" "Your message here"
# Env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

set -euo pipefail

TO="${1:?Usage: twilio-sms.sh <to-number> <message>}"
MESSAGE="${2:?Usage: twilio-sms.sh <to-number> <message>}"

if [ -z "${TWILIO_ACCOUNT_SID:-}" ] || [ -z "${TWILIO_AUTH_TOKEN:-}" ] || [ -z "${TWILIO_FROM_NUMBER:-}" ]; then
  echo "ERROR: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER must be set" >&2
  exit 1
fi

RESPONSE=$(curl -s -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
  -d "To=${TO}" \
  -d "From=${TWILIO_FROM_NUMBER}" \
  --data-urlencode "Body=${MESSAGE}")

# Extract key fields
SID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sid',''))" 2>/dev/null || echo "")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")

if [ -n "$SID" ] && [ "$SID" != "null" ]; then
  echo "SMS sent successfully"
  echo "  Message SID: $SID"
  echo "  Status: $STATUS"
  echo "  To: $TO"
  echo "  From: $TWILIO_FROM_NUMBER"
else
  echo "ERROR: SMS failed" >&2
  echo "$RESPONSE" >&2
  exit 1
fi
