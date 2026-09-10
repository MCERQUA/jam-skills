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

### Image generation — send ONE `KIND: task`; the runner claims it (2026-09-10)
The old `mac-claude-listener` (subject-keyword auto-dispatch, ChatGPT/DALL-E, 300 s cap) is
RETIRED — it failed three real jobs in one evening. Today `task-runner` on the Mac claims every
`KIND: task` addressed to it, renders with the real browser rigs (~13 min), writes the PNG straight
into `/mnt/clients/<tenant>/openvoiceui/uploads/` and replies `task-result` with the path. No
subject keyword is required, no per-tenant relay script exists, and a 5-minute silence is normal.
Full request shape, the brand gates the Mac applies, and the identity-platform rule (naming
"Facebook post" is fine; only ACTIONS on an account are held): read the `mac-image-gen` skill.

### The guard, and the one thing you must never do about it (2026-09-10)
The Mac holds tasks that ACT on a client's identity platforms (post, publish, log in, claim, edit a
listing, credentials) — recall over precision, by design. Two kinds are exempt from holding on a
platform's NAME alone: content generation (image-gen, social-media-designer, copy, caption, video)
and read-only research (`KIND: read-only-research`, or subject prefix `scrape:` / `research:` /
`lookup:` — public pages only; write actions and credential words still hold). **Declare the KIND in
the header; the guard reads the filename and KIND/SUBJECT, never body prose.**
**If a task is held: keep the real words.** Fix the KIND, drop the action you did not mean, or ask
host@mesh. Never paraphrase a blocklisted term ("the photo-sharing app whose address is…",
"authenticate" for "login") — a disguised request is unreadable to every later reader and is itself
held as spelled-around. A hold is not a verdict on you; a paraphrase is.

### Generic Claude task
```bash
printf '%s\n' '{"task":"<your task>","model":"claude-sonnet-4-6"}' \
  | mesh-send --to mac-claude@mesh --kind task --subject "claude-task: <short description>"
```

### Body goes on **stdin** (not a flag). `mesh-send` is on your PATH.

## How results come back
1. **Text / links / status** → the Mac replies with a mesh message straight to **your inbox** — read it with your normal `mesh-recv` / inbox check.
2. **Files (images, etc.)** → land in your own `/mnt/clients/<tenant>/openvoiceui/uploads/`
   (a fleet relay copies the Mac's EVENTS drop; there is no per-tenant relay script or cron).
   The `task-result` reply names the file and its `/uploads/<file>` URL.

## Worked example (image generation)
```bash
# A tenant's voice agent requests an image:
printf '%s\n' '{"prompt":"Modern luxury home, architectural photography, blue sky","tenant":"<tenant>"}' \
  | mesh-send --to mac-claude@mesh --kind task --subject "image-gen: <tenant> luxury home"

# Mac generates (~60-90s), drops gen-<ts>.png to EVENTS/<tenant>-images/
# Relay copies to /mnt/clients/<tenant>/openvoiceui/uploads/ in ~2 min
# Relay notifies <tenant>-voice@mesh: "Images ready in uploads..."
# Serve at: https://<tenant>.jam-bot.com/uploads/gen-<ts>.png
```

## Notes / gotchas
- The Mac is a **shared** resource — one at a time is polite; it may take a minute.
- It can only write the **shared mesh** (`/mnt/agent-mesh/...`), not your `/mnt/clients` volume — that's why files land in the shared drop and (optionally) get relayed into your uploads.
- Reply-round-trips work because your container mounts the full mesh and the Mac syncs it. If `mesh-send` ever says "recipient inbox not found" for `mac-claude`, it's an address typo — the mount is there.
- This is for OWNER/agent tasks. Don't expose it as a customer-facing capability.
