# Twilio — Voice Calls & SMS

Make outbound phone calls and send SMS messages via Twilio.

## Environment Variables (available in container)
- `TWILIO_ACCOUNT_SID` — Account SID
- `TWILIO_AUTH_TOKEN` — Auth token
- `TWILIO_FROM_NUMBER` — Your Twilio phone number (+16029327909)

## Making an Outbound Call

Use the helper script at `/mnt/shared-skills/twilio/twilio-call.sh`:

```bash
# Call with a spoken message
bash /mnt/shared-skills/twilio/twilio-call.sh "+1XXXXXXXXXX" "Hey, this is your AI assistant. Just wanted to let you know your website build is complete."

# Call with a custom voice (default: Polly.Matthew)
TWILIO_VOICE="Polly.Joanna" bash /mnt/shared-skills/twilio/twilio-call.sh "+1XXXXXXXXXX" "Hello from JamBot!"
```

### Available Voices
- `Polly.Matthew` — Male, US English (default)
- `Polly.Joanna` — Female, US English
- `Polly.Amy` — Female, British English
- `Polly.Brian` — Male, British English
- `Polly.Joey` — Male, US English (casual)

### What Happens
1. Twilio calls the number
2. When they pick up, the message is read aloud via TTS
3. The call ends after the message plays
4. Script returns the Call SID and status

## Sending an SMS

Use the helper script at `/mnt/shared-skills/twilio/twilio-sms.sh`:

```bash
# Send a text message
bash /mnt/shared-skills/twilio/twilio-sms.sh "+1XXXXXXXXXX" "Your website is live! Check it out at https://example.com"
```

### SMS Rules
- Max 1600 characters per message (Twilio auto-segments)
- Include opt-out language for marketing: "Reply STOP to unsubscribe"
- Never send SMS without user consent

## Manual curl (if scripts unavailable)

### Call
```bash
curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Calls.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
  -d "To=+1XXXXXXXXXX" \
  -d "From=${TWILIO_FROM_NUMBER}" \
  --data-urlencode "Twiml=<Response><Say voice=\"Polly.Matthew\">Your message here.</Say></Response>"
```

### SMS
```bash
curl -s -X POST "https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json" \
  -u "${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}" \
  -d "To=+1XXXXXXXXXX" \
  -d "From=${TWILIO_FROM_NUMBER}" \
  --data-urlencode "Body=Your message here."
```

## Rules
- NEVER call or text without the user explicitly asking
- ALWAYS confirm the phone number before calling/texting
- Keep call messages under 30 seconds of speech (~75 words)
- For urgent notifications only — don't spam calls
- Log every call/SMS attempt to memory for audit trail
