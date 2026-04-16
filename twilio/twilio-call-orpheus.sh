#!/bin/bash
# Twilio Outbound Call with Orpheus agent voice
# Renders TTS via Groq Orpheus, writes to uploads dir, fires Twilio <Play> call.
# Usage: bash twilio-call-orpheus.sh "+1XXXXXXXXXX" "Your message here" [voice]
# Env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, GROQ_API_KEY
# Optional env: TWILIO_TENANT (default: foamology), TWILIO_VOICE (default: daniel)
# Voices: troy, austin, daniel, autumn, diana, hannah
# Fallback: if Orpheus render fails, falls back to Polly <Say>.

set -euo pipefail

TO="${1:?Usage: twilio-call-orpheus.sh <to-number> <message> [voice]}"
MESSAGE="${2:?Usage: twilio-call-orpheus.sh <to-number> <message> [voice]}"
VOICE="${3:-${TWILIO_VOICE:-daniel}}"
TENANT="${TWILIO_TENANT:-foamology}"
PUBLIC_HOST="${TENANT}.jam-bot.com"
UPLOADS_DIR="/app/runtime/uploads"

if [ -z "${TWILIO_ACCOUNT_SID:-}" ] || [ -z "${TWILIO_AUTH_TOKEN:-}" ] || [ -z "${TWILIO_FROM_NUMBER:-}" ]; then
  echo "ERROR: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER must be set" >&2
  exit 1
fi

TS=$(date +%s)
BASENAME="tts-${TS}-$$"
WAV="/tmp/${BASENAME}.wav"
MP3_LOCAL="${UPLOADS_DIR}/${BASENAME}.mp3"
PUBLIC_URL="https://${PUBLIC_HOST}/uploads/${BASENAME}.mp3"

render_orpheus() {
  local payload
  payload=$(jq -cn \
    --arg model "canopylabs/orpheus-v1-english" \
    --arg input "$MESSAGE" \
    --arg voice "$VOICE" \
    --arg fmt "wav" \
    '{model:$model, input:$input, voice:$voice, response_format:$fmt}')

  local http
  http=$(curl -sS -w '%{http_code}' \
    https://api.groq.com/openai/v1/audio/speech \
    -H "Authorization: Bearer ${GROQ_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    -o "$WAV")

  if [ "$http" != "200" ]; then
    echo "Orpheus render failed (HTTP $http)" >&2
    return 1
  fi

  if [ ! -s "$WAV" ]; then
    echo "Orpheus returned empty WAV" >&2
    return 1
  fi

  if ! ffmpeg -y -loglevel error -i "$WAV" -codec:a libmp3lame -q:a 4 -ar 22050 -ac 1 "$MP3_LOCAL"; then
    echo "ffmpeg transcode failed" >&2
    return 1
  fi

  rm -f "$WAV"
  return 0
}

fire_call() {
  local twiml="$1"
  curl -sS -X POST \
    "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Calls.json" \
    -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
    -d "To=${TO}" \
    -d "From=${TWILIO_FROM_NUMBER}" \
    --data-urlencode "Twiml=${twiml}"
}

if render_orpheus; then
  echo "Orpheus rendered: ${MP3_LOCAL} ($(stat -c%s "$MP3_LOCAL") bytes)"
  TWIML="<Response><Play>${PUBLIC_URL}</Play></Response>"
  MODE="orpheus"
else
  echo "WARN: falling back to Polly" >&2
  ESC=$(echo "$MESSAGE" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g; s/"/\&quot;/g; s/'"'"'/\&apos;/g')
  TWIML="<Response><Say voice=\"Polly.Matthew\">${ESC}</Say></Response>"
  MODE="polly-fallback"
fi

RESPONSE=$(fire_call "$TWIML")
SID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sid',''))" 2>/dev/null || echo "")
STATUS=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")

if [ -n "$SID" ]; then
  echo "Call initiated"
  echo "  SID:    $SID"
  echo "  Status: $STATUS"
  echo "  Mode:   $MODE"
  echo "  To:     $TO"
  echo "  From:   $TWILIO_FROM_NUMBER"
  echo "  Voice:  $VOICE"
  echo "  URL:    $PUBLIC_URL"
else
  echo "ERROR: Twilio call failed" >&2
  echo "$RESPONSE" >&2
  exit 1
fi
