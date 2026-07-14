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
Your container already mounts the full mesh, so `mesh-send` reaches it directly. Body goes on **stdin** (not a flag):
```bash
printf '%s\n' "Please generate an image: <clear prompt + any style/character notes>. Deliver it to the shared drop and reply here when done." \
  | mesh-send --to mac-claude@mesh --kind task --subject "<short what-you-need>"
```
- `--kind task` for work you want done; `--kind message` for a question/chat.
- Be specific: for images, give the full prompt + character/style guidance + where to deliver.
- `mesh-send` is on your PATH (same place as your other mesh tools).

## How results come back
1. **Text / links / status** → the Mac replies with a mesh message straight to **your inbox** — read it with your normal `mesh-recv` / inbox check.
2. **Files (images, etc.)** → the Mac drops them into a shared mesh drop it and you both can see:
   `/mnt/agent-mesh/mesh/EVENTS/<topic>/` (e.g. `.../kyle-images/`). You mount the mesh, so you can **read those files directly**. It will tell you the exact path/filenames in its reply.
   - If you need the file inside your own workspace/uploads (e.g. to post or serve it), copy it from the shared drop into your uploads. (For some tenants a host relay does this automatically — e.g. Kyle's `kyle-image-relay.sh` lands mac images in bhb's uploads; if you don't have one, just `cp` from the shared drop.)

## Worked example (image generation)
```bash
printf '%s\n' \
  "Generate a cartoon image of <subject>, <style>, <any character sheet notes>." \
  "Save it to the shared kyle-images drop and reply with the filename." \
  | mesh-send --to mac-claude@mesh --kind task --subject "image: <subject>"
# → the Mac generates via ChatGPT, drops the PNG to /mnt/agent-mesh/mesh/EVENTS/kyle-images/,
#   and replies to your inbox with the filename. Read the file from that path.
```

## Notes / gotchas
- The Mac is a **shared** resource — one at a time is polite; it may take a minute.
- It can only write the **shared mesh** (`/mnt/agent-mesh/...`), not your `/mnt/clients` volume — that's why files land in the shared drop and (optionally) get relayed into your uploads.
- Reply-round-trips work because your container mounts the full mesh and the Mac syncs it. If `mesh-send` ever says "recipient inbox not found" for `mac-claude`, it's an address typo — the mount is there.
- This is for OWNER/agent tasks. Don't expose it as a customer-facing capability.
