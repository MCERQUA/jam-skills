---
name: mac-tool
description: The Mac (mac-claude@mesh) is a shared TOOL any agent can use for things the VPS can't do — real ChatGPT/browser image generation, browsing sites that block the datacenter IP, and other residential-IP / real-desktop tasks. TRIGGER when you need an on-model image generated via ChatGPT, need a real browser on a residential IP, or want to hand a browser/desktop task to "the Mac". Send a request over the mesh and the Mac does it and replies.
metadata: {"openclaw": {"emoji": "🖥️"}}
---

# The Mac — a shared tool you call over the mesh (`mac-claude@mesh`)

**What it is:** `mac-claude@mesh` is a real Mac (macdaddy) running Claude with a real browser and a **residential IP**. It can do things the VPS agents cannot:
- Generate images through a **real ChatGPT / DALL·E browser session** (on-model, high quality — e.g. the BHB/Kyle character images).
- **Browse sites that block datacenter IPs** (the VPS is a datacenter IP; the Mac is residential, so it isn't blocked).
- Any real-desktop / real-browser task you'd otherwise be unable to do from a container.

Think of it as a colleague at a real computer you can hand a task to. You don't run it — you **ask it over the mesh** and it replies.

## The ONE correct address
Always `mac-claude@mesh`. **Not** `mac`, `macdaddy`, `chatgpt-mac`, or anything else — a wrong address makes `mesh-send` fail with "recipient not found". (That mistake is exactly why earlier attempts "couldn't find the Mac".)

## How to send it a task

### Image generation (DALL-E via ChatGPT) — USE THIS FORMAT
The Mac's `mac-claude-listener` auto-dispatches subjects containing **`image-gen`**:
```bash
printf '%s\n' '{"prompt":"A professional spray foam insulation team on a job site, cinematic lighting","tenant":"danielle"}' \
  | mesh-send --to mac-claude@mesh --kind task --subject "image-gen: danielle spray-foam-team"
# → Mac generates via ChatGPT DALL-E (~60-90s), drops PNG to EVENTS/danielle-images/,
#   replies to YOUR inbox with the VPS path. Relay copies to your uploads/ in ~2min.
```
**Critical**: subject MUST contain `image-gen` or `chatgpt-image` for auto-dispatch.
Without that keyword, the listener acks silently and nothing runs.

JSON body fields: `prompt` (required), `tenant` (your tenant name), `drop_dir` (defaults to `{tenant}-images`).

For full detail: read the `mac-image-gen` skill.

### Generic Claude task
```bash
printf '%s\n' '{"task":"<your task>","model":"claude-sonnet-4-6"}' \
  | mesh-send --to mac-claude@mesh --kind task --subject "claude-task: <short description>"
```

### Body goes on **stdin** (not a flag). `mesh-send` is on your PATH.

## How results come back
1. **Text / links / status** → the Mac replies with a mesh message straight to **your inbox** — read it with your normal `mesh-recv` / inbox check.
2. **Files (images, etc.)** → the Mac drops them to the VPS EVENTS drop:
   `/mnt/agent-mesh/mesh/EVENTS/{tenant}-images/` — you can read these directly.
   The VPS relay (`danielle-image-relay.sh`, `kyle-image-relay.sh`) then copies to
   your `uploads/` and notifies you (runs every 2 minutes).

## Worked example (image generation)
```bash
# Danielle's voice agent requests an image:
printf '%s\n' '{"prompt":"Modern luxury home, architectural photography, blue sky","tenant":"danielle"}' \
  | mesh-send --to mac-claude@mesh --kind task --subject "image-gen: danielle luxury home"

# Mac generates (~60-90s), drops gen-<ts>.png to EVENTS/danielle-images/
# Relay copies to /mnt/clients/danielle/openvoiceui/uploads/ in ~2 min
# Relay notifies danielle-voice@mesh: "Images ready in uploads..."
# Serve at: https://danielle.jam-bot.com/uploads/gen-<ts>.png
```

## Notes / gotchas
- The Mac is a **shared** resource — one at a time is polite; it may take a minute.
- It can only write the **shared mesh** (`/mnt/agent-mesh/...`), not your `/mnt/clients` volume — that's why files land in the shared drop and (optionally) get relayed into your uploads.
- Reply-round-trips work because your container mounts the full mesh and the Mac syncs it. If `mesh-send` ever says "recipient inbox not found" for `mac-claude`, it's an address typo — the mount is there.
- This is for OWNER/agent tasks. Don't expose it as a customer-facing capability.
