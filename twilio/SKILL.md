---
name: twilio
description: Make outbound phone calls with a natural agent voice (Orpheus via Groq) or send SMS. Default to Orpheus for calls — it sounds natural. Only use the Polly script if explicitly asked.
---

# Twilio — Voice Calls & SMS

Make outbound phone calls and send SMS messages via Twilio.

## Environment Variables (already injected into the container)

- `TWILIO_ACCOUNT_SID` — Account SID
- `TWILIO_AUTH_TOKEN` — Auth token
- `TWILIO_FROM_NUMBER` — FROM phone number (`+16029327909`)
- `GROQ_API_KEY` — used for Orpheus TTS rendering

## Outbound Call — Orpheus agent voice (DEFAULT)

**Use this for every call unless the user specifically asks for Polly.**

```bash
bash /mnt/shared-skills/twilio/twilio-call-orpheus.sh "+1XXXXXXXXXX" "Your message here"
```

With a specific voice:

```bash
bash /mnt/shared-skills/twilio/twilio-call-orpheus.sh "+1XXXXXXXXXX" "Hey, quick update…" daniel
```

### What happens

1. Renders the message to a natural-sounding WAV via **Groq Orpheus** (`canopylabs/orpheus-v1-english`)
2. Transcodes to MP3 (22.05 kHz mono, ~80KB per 10s of speech)
3. Writes it to `/app/runtime/uploads/tts-<ts>-<pid>.mp3` — publicly fetchable at `https://<tenant>.jam-bot.com/uploads/<file>.mp3`
4. Places a Twilio call using `<Response><Play>URL</Play></Response>` TwiML
5. If Orpheus fails, auto-falls-back to Polly `<Say>` so the call still goes through

### Orpheus Voices

| Voice | Feel |
|-------|------|
| `daniel` | Male, neutral US (default) |
| `troy` | Male, warm/deep |
| `austin` | Male, casual |
| `autumn` | Female, warm |
| `diana` | Female, professional |
| `hannah` | Female, younger/friendly |

Pass voice as the third argument, or set `TWILIO_VOICE` env var.

## Outbound Call — Polly fallback only

Only use this if explicitly asked for Amazon Polly (robotic voice). Default to the Orpheus script above.

```bash
bash /mnt/shared-skills/twilio/twilio-call.sh "+1XXXXXXXXXX" "Your message here"
```

## Sending an SMS

```bash
bash /mnt/shared-skills/twilio/twilio-sms.sh "+1XXXXXXXXXX" "Your website is live! Check it out at https://example.com"
```

### SMS Rules

- Max 1600 characters per message (Twilio auto-segments)
- Include opt-out language for marketing: "Reply STOP to unsubscribe"
- Never send SMS without user consent

## Manual curl (only if scripts are unavailable)

```bash
curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Calls.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
  -d "To=+1XXXXXXXXXX" \
  -d "From=${TWILIO_FROM_NUMBER}" \
  --data-urlencode "Twiml=<Response><Say voice=\"Polly.Matthew\">Your message here.</Say></Response>"
```

## Rules

- NEVER call or text without the user explicitly asking
- ALWAYS confirm the phone number before dialing
- Keep call messages under 30 seconds of speech (~75 words) — longer = slower Twilio fetch
- For urgent notifications only — don't spam calls
- Default to Orpheus. Only use Polly if the user asks for "the robot voice" or Orpheus is down
- Log every call/SMS attempt in conversation so there's an audit trail
