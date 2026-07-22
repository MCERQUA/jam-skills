---
name: mac-image-gen
description: "Request a ChatGPT/DALL-E image from the Mac (mac-claude@mesh). The Mac generates it via the real ChatGPT browser, SCPs the PNG to the VPS EVENTS drop, the VPS relay copies it to your uploads/, and the relay notifies you. Use for high-quality AI images — no API key needed, uses the real ChatGPT DALL-E interface."
metadata: {"openclaw": {"emoji": "🎨"}}
---

# Mac Image Generation — DALL-E via mac-claude@mesh

The Mac (macdaddy) runs a persistent listener (`com.jambot.mac-claude-listener`) that watches
`mac-claude@mesh` inbox every 4 seconds. When an `image-gen` task arrives, it:

1. Drives ChatGPT in Chrome via Peekaboo automation
2. Generates the image with DALL-E
3. Downloads the PNG
4. SCPs it to `/mnt/agent-mesh/mesh/EVENTS/{tenant}-images/` on the VPS
5. Replies to YOUR inbox with `{"success": true, "result": "/mnt/agent-mesh/mesh/EVENTS/..."}`
6. The VPS relay (`danielle-image-relay.sh`, `kyle-image-relay.sh`, etc.) copies it to your
   `uploads/` within 2 minutes and sends you a second notification.

## How to request an image

Subject MUST contain `image-gen` for the listener to auto-dispatch:

```bash
# Simple text prompt (body is treated as {"prompt": <body>})
printf '%s\n' "Generate an image of a professional spray foam insulation team on a job site, cinematic lighting, photorealistic" \
  | mesh-send --to mac-claude@mesh --kind task --subject "image-gen: spray-foam-team"

# Structured JSON (recommended — lets you specify tenant + delivery dir)
printf '%s\n' '{"prompt":"A modern luxury home exterior with spray foam insulation visible, architectural photo","tenant":"danielle","drop_dir":"danielle-images"}' \
  | mesh-send --to mac-claude@mesh --kind task --subject "image-gen: danielle luxury home"
```

## Message body fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `prompt` | string | **required** | Full DALL-E prompt — be specific |
| `tenant` | string | inferred from sender | Your tenant name (e.g. `danielle`) |
| `drop_dir` | string | `{tenant}-images` | EVENTS drop subdirectory name |

## Reply format

The Mac replies to your inbox with a `task-result` message:
```json
{"success": true, "result": "/mnt/agent-mesh/mesh/EVENTS/danielle-images/gen-1234567890.png"}
```

## Relay → uploads (automatic, ~2 min)

The VPS cron relay runs every 2 minutes per tenant:
- `danielle-image-relay.sh` → `/mnt/clients/danielle/openvoiceui/uploads/`
- `kyle-image-relay.sh` → `/mnt/clients/bhb/openvoiceui/uploads/`

After relay, images are at: `https://{tenant}.jam-bot.com/uploads/{filename}`

The relay also sends you a mesh notification listing the new files.

## Adding relay for a new tenant

On the VPS host:
```bash
# Copy the relay script
cp /home/mike/MIKE-AI/scripts/danielle-image-relay.sh \
   /home/mike/MIKE-AI/scripts/{tenant}-image-relay.sh
# Edit: change DEST path + mesh-send --to {tenant}-voice@mesh
# Add cron:  */2 * * * *  bash /home/mike/MIKE-AI/scripts/{tenant}-image-relay.sh >> /home/mike/MIKE-AI/logs/{tenant}-image-relay.log 2>&1
# Create drop dir: mkdir -p /mnt/agent-mesh/mesh/EVENTS/{tenant}-images
```

## Usage examples

```bash
# Quick image request (voice agent skill pattern):
REQUEST_IMAGE() {
  local PROMPT="$1"
  local TENANT="${2:-danielle}"
  printf '%s\n' "{\"prompt\":\"$PROMPT\",\"tenant\":\"$TENANT\"}" \
    | mesh-send --to mac-claude@mesh --kind task \
        --subject "image-gen: $TENANT $(date +%s)"
  echo "Image requested — check uploads in ~3 min or watch inbox for task-result"
}

# Then poll your inbox for the reply:
# mesh-recv   (or let the openclaw session pick it up)
```

## Notes

- Generation takes ~60-90 seconds on the Mac (DALL-E via ChatGPT UI)
- DALL-E quality (gpt-image-1 / DALL-E 3 via ChatGPT Plus) — photorealistic, high-res
- The Mac is a **shared** resource — one request at a time is polite
- If ChatGPT session is logged out, the request fails — host will see the error in Mac logs
- For fast/cheap image gen (lower quality), use the `gemini-image` skill instead
