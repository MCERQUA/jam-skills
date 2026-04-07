#!/bin/bash
# Slack voice reply sender — generates Groq Orpheus TTS audio and sends to Slack
# Usage: bash slack-voice-send.sh "message text" [channel_id] [voice] [direction]
#
# Requires: GROQ_API_KEY, SLACK_BOT_TOKEN env vars
# Defaults: channel=SLACK_CHANNEL_COMPANY, voice=troy, no direction tag
#
# Voices: troy, austin, daniel (male) | autumn, diana, hannah (female)
# Directions: professionally, friendly, cheerful, confidently, warm, excited

set -euo pipefail

MESSAGE="${1:?Usage: slack-voice-send.sh \"message\" [channel_id] [voice] [direction]}"
CHANNEL="${2:-${SLACK_CHANNEL_COMPANY:-${SLACK_CHANNEL_AI_UPDATES:-}}}"
VOICE="${3:-troy}"
DIRECTION="${4:-}"

if [ -z "${GROQ_API_KEY:-}" ]; then
  echo '{"ok":false,"error":"GROQ_API_KEY not set"}'
  exit 1
fi

if [ -z "${SLACK_BOT_TOKEN:-}" ]; then
  echo '{"ok":false,"error":"SLACK_BOT_TOKEN not set"}'
  exit 1
fi

if [ -z "${CHANNEL:-}" ]; then
  echo '{"ok":false,"error":"No channel specified and no default channel env var set"}'
  exit 1
fi

# Add vocal direction tag if provided
TTS_INPUT="$MESSAGE"
if [ -n "$DIRECTION" ]; then
  TTS_INPUT="[$DIRECTION] $MESSAGE"
fi

# Generate unique temp filenames
TMPID="voice-reply-$$-$(date +%s)"
WAV_FILE="/tmp/${TMPID}.wav"
MP3_FILE="/tmp/${TMPID}.mp3"

echo "Generating TTS audio with Groq Orpheus (voice: $VOICE)..."

# Step 1: Generate WAV with Groq Orpheus
HTTP_CODE=$(curl -s -w "%{http_code}" https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json,sys; print(json.dumps({'model':'canopylabs/orpheus-v1-english','voice':'${VOICE}','input':sys.argv[1],'response_format':'wav'}))" "$TTS_INPUT")" \
  -o "$WAV_FILE")

if [ "$HTTP_CODE" != "200" ]; then
  echo "Groq TTS API returned HTTP $HTTP_CODE"
  cat "$WAV_FILE" 2>/dev/null
  rm -f "$WAV_FILE"
  exit 1
fi

WAV_SIZE=$(stat -c%s "$WAV_FILE" 2>/dev/null || stat -f%z "$WAV_FILE" 2>/dev/null || echo "0")
if [ "$WAV_SIZE" -lt 1000 ]; then
  echo "WAV file too small ($WAV_SIZE bytes) — TTS likely failed"
  rm -f "$WAV_FILE"
  exit 1
fi

echo "WAV generated (${WAV_SIZE} bytes). Converting to MP3..."

# Step 2: Convert WAV to MP3
ffmpeg -y -i "$WAV_FILE" -codec:a libmp3lame -q:a 2 "$MP3_FILE" 2>/dev/null

MP3_SIZE=$(stat -c%s "$MP3_FILE" 2>/dev/null || stat -f%z "$MP3_FILE" 2>/dev/null || echo "0")
echo "MP3 ready (${MP3_SIZE} bytes). Uploading to Slack..."

# Step 3a: Get presigned upload URL from Slack
UPLOAD_RESP=$(curl -s -X POST https://slack.com/api/files.getUploadURLExternal \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "filename=voice-reply.mp3&length=${MP3_SIZE}")

UPLOAD_URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('upload_url',''))")
FILE_ID=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d.get('file_id',''))")

if [ -z "$UPLOAD_URL" ]; then
  echo "Failed to get Slack upload URL"
  echo "$UPLOAD_RESP"
  rm -f "$WAV_FILE" "$MP3_FILE"
  exit 1
fi

# Step 3b: Upload file to presigned URL
curl -s -X POST "$UPLOAD_URL" -F "file=@$MP3_FILE" > /dev/null

# Step 3c: Complete upload and share to channel
COMPLETE_RESP=$(curl -s -X POST https://slack.com/api/files.completeUploadExternal \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"files\":[{\"id\":\"$FILE_ID\",\"title\":\"Voice Reply\"}],\"channel_id\":\"$CHANNEL\"}")

echo "$COMPLETE_RESP"

# Cleanup
rm -f "$WAV_FILE" "$MP3_FILE"

# Check result
OK=$(echo "$COMPLETE_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read()).get('ok', False))" 2>/dev/null || echo "false")
if [ "$OK" = "True" ] || [ "$OK" = "true" ]; then
  echo "Voice reply sent successfully to channel $CHANNEL"
else
  echo "Upload may have failed — check response above"
fi
