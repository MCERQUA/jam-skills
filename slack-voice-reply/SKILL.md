# Slack Voice Reply Skill

Generate voice audio replies using Groq Orpheus TTS and send them to Slack channels. Use this when you want to reply with a voice message instead of (or in addition to) text.

## When to Use

- User asks you to send a voice reply to Slack
- You're in a Slack channel and want to reply with audio
- User says "voice reply", "audio reply", "send a voice message"
- Any time a spoken/audio response would be more engaging than text

## Environment Variables (Pre-configured)

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Groq API key for Orpheus TTS |
| `SLACK_BOT_TOKEN` | Bot auth token (xoxb-...) |
| `SLACK_CHANNEL_AI_UPDATES` | Default channel for AI updates |
| `SLACK_CHANNEL_LEADS` | Channel for lead notifications |
| `SLACK_CHANNEL_COMPANY` | Main company channel |

## Available Voices

| Voice | Gender | Best For |
|-------|--------|----------|
| `troy` | Male | Professional, authoritative |
| `austin` | Male | Casual, friendly |
| `daniel` | Male | Warm, conversational |
| `autumn` | Female | Default, natural |
| `diana` | Female | Professional, clear |
| `hannah` | Female | Friendly, approachable |

## Vocal Direction Tags (Optional)

Add these at the start of the input text for expression control:
- `[professionally]` — business tone
- `[friendly]` — warm and approachable
- `[cheerful]` — upbeat energy
- `[confidently]` — assertive delivery
- `[warm]` — caring tone
- `[excited]` — high energy

Example: `"[professionally] Welcome to Seattle Roofing Company. How can we help you today?"`

## Step-by-Step: Generate and Send Voice Reply

### Step 1: Generate WAV audio with Groq Orpheus

```bash
curl -s https://api.groq.com/openai/v1/audio/speech \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "canopylabs/orpheus-v1-english",
    "voice": "troy",
    "input": "[professionally] Your message text here",
    "response_format": "wav"
  }' \
  -o /tmp/voice-reply.wav
```

### Step 2: Convert WAV to MP3

```bash
ffmpeg -y -i /tmp/voice-reply.wav -codec:a libmp3lame -q:a 2 /tmp/voice-reply.mp3
```

### Step 3: Upload MP3 to Slack (3-step upload flow)

Slack requires a 3-step upload process:

```bash
# 3a: Get presigned upload URL
MP3_SIZE=$(stat -c%s /tmp/voice-reply.mp3)
UPLOAD_RESP=$(curl -s -X POST https://slack.com/api/files.getUploadURLExternal \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "filename=voice-reply.mp3&length=${MP3_SIZE}")

# Extract URL and file ID (use python3 or jq)
UPLOAD_URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['upload_url'])")
FILE_ID=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['file_id'])")

# 3b: Upload file to presigned URL
curl -s -X POST "$UPLOAD_URL" -F "file=@/tmp/voice-reply.mp3"

# 3c: Complete upload and share to channel
curl -s -X POST https://slack.com/api/files.completeUploadExternal \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"files\":[{\"id\":\"$FILE_ID\",\"title\":\"Voice Reply\"}],\"channel_id\":\"$SLACK_CHANNEL_COMPANY\",\"initial_comment\":\"Here's my voice response:\"}"
```

**To reply in a thread**, add `"thread_ts":"THREAD_TIMESTAMP"` to the completeUploadExternal JSON body.

### Step 4: Clean up temp files

```bash
rm -f /tmp/voice-reply.wav /tmp/voice-reply.mp3
```

## Helper Script

Use the helper script for quick voice replies:

```bash
bash /mnt/shared-skills/slack-voice-reply/slack-voice-send.sh "Your message text" [channel_id] [voice] [direction]
```

Examples:
```bash
# Default voice (troy) to company channel
bash /mnt/shared-skills/slack-voice-reply/slack-voice-send.sh "Hey team, the roof inspection is scheduled for Thursday"

# Specific voice and channel
bash /mnt/shared-skills/slack-voice-reply/slack-voice-send.sh "New lead from the website" "$SLACK_CHANNEL_LEADS" "diana" "cheerful"

# With vocal direction
bash /mnt/shared-skills/slack-voice-reply/slack-voice-send.sh "[excited] Great news, we closed the deal!" "$SLACK_CHANNEL_AI_UPDATES"
```

## Both Text + Voice Reply

For the best experience, send BOTH a text message and the voice audio. Use the helper script for the voice part:

```bash
# 1. Send text first
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"channel\": \"$SLACK_CHANNEL_COMPANY\", \"text\": \"Your text message here\"}"

# 2. Send voice version
bash /mnt/shared-skills/slack-voice-reply/slack-voice-send.sh "Your text message here" "$SLACK_CHANNEL_COMPANY" "troy" "professionally"
```

## Limits

- **Max input:** 5,000 characters per TTS call
- **For longer text:** Split into multiple audio files and send sequentially
- **Audio format:** WAV from Groq (24kHz) → convert to MP3 with ffmpeg
- **Cost:** ~$0.05 per 1K characters (very cheap)

## Channel Routing

| Content | Channel Variable |
|---------|-----------------|
| General team updates, voice replies | `$SLACK_CHANNEL_COMPANY` |
| AI status, task completions | `$SLACK_CHANNEL_AI_UPDATES` |
| Lead notifications | `$SLACK_CHANNEL_LEADS` |
| Specific channel by ID | Use the channel ID directly (e.g., `C0XXXXXXXX`) |
