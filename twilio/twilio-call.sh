#!/bin/bash
# Twilio Outbound Call — plays a TTS message when recipient picks up
# Usage: bash twilio-call.sh "+1XXXXXXXXXX" "Your message here"
# Env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
# Optional: TWILIO_VOICE (default: Polly.Matthew)

set -euo pipefail

TO="${1:?Usage: twilio-call.sh <to-number> <message>}"
MESSAGE="${2:?Usage: twilio-call.sh <to-number> <message>}"
VOICE="${TWILIO_VOICE:-Polly.Matthew}"

if [ -z "${TWILIO_ACCOUNT_SID:-}" ] || [ -z "${TWILIO_AUTH_TOKEN:-}" ] || [ -z "${TWILIO_FROM_NUMBER:-}" ]; then
  echo "ERROR: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER must be set" >&2
  exit 1
fi

# Escape XML special characters in the message
MESSAGE_ESCAPED=$(echo "$MESSAGE" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&apos;/g')

TWIML="<Response><Say voice=\"${VOICE}\">${MESSAGE_ESCAPED}</Say></Response>"

RESPONSE=$(curl -s -X POST \
  "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Calls.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
  -d "To=${TO}" \
  -d "From=${TWILIO_FROM_NUMBER}" \
  --data-urlencode "Twiml=${TWIML}")

# Extract key fields
SID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('sid',''))" 2>/dev/null || echo "")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")

if [ -n "$SID" ] && [ "$SID" != "null" ]; then
  echo "Call initiated successfully"
  echo "  Call SID: $SID"
  echo "  Status: $STATUS"
  echo "  To: $TO"
  echo "  From: $TWILIO_FROM_NUMBER"
  echo "  Voice: $VOICE"
else
  echo "ERROR: Call failed" >&2
  echo "$RESPONSE" >&2
  exit 1
fi
