---
name: mac-image-gen
description: "Request a generated image from the Mac lane (mac-claude@mesh). The Mac's task-runner claims your KIND: task, renders it with the real browser rigs (Grok/CDP with type + logo layers) in ~13 minutes, delivers the PNG into your tenant's uploads/ and replies with the paths. TRIGGER: post image, ad graphic, comparison card, product still. NOT for video (that is the studio single-shot lane) and NOT for posting anywhere."
---

# mac-image-gen — how a tenant agent gets an image made on the Mac

**Mechanism (2026-09-10, measured):** you send one mesh **task**; `task-runner` on macdaddy
**claims** it (one consumer, one claim — the old `mac-claude-listener` that polled the inbox every
4 s with a 300-second cap is RETIRED; it failed three real jobs in one evening and is not coming
back). The runner drives the on-screen Grok composer over CDP, applies the tenant's type and logo
layers from the brand kit, and writes the finished PNG to
`/mnt/clients/<tenant>/openvoiceui/uploads/` (a fleet relay copies the EVENTS drop — there is no
per-tenant relay script or cron to add). A real job takes **~13 minutes median**; do not re-send
because nothing arrived in 5. You get a `task-result` reply with the file path and the public
`/uploads/<file>` URL; a refusal is a `task-result` with `success:false` and the reason.

## How to request an image

```bash
mesh-send --to mac-claude@mesh --kind task \
  --subject "image-gen: <what it is, 6 words>" \
  --end-of-turn "mac-claude@mesh — render and reply with the uploads path" <<'BODY'
TENANT: <your tenant>
PURPOSE: <where it will be used — e.g. Facebook post, GBP photo, quote card, ad>
SUBJECT: <one plain-English paragraph of what the image shows>
STYLE: <mood, composition, aspect (1:1 · 4:5 · 16:9), text overlay wording if any>
BRAND: use the tenant brand kit (colors/type/logo are on the Mac already; name a hex only to override)
DELIVER: /mnt/clients/<tenant>/openvoiceui/uploads/
BODY
```

Naming a platform in PURPOSE ("Facebook post", "Google Business photo") is fine and expected —
generating content for a platform is the product. The identity-platform guard holds only
**actions** on a client's account (post, publish, log in, claim, update a listing, credentials);
never a platform's name in a content request (Mike, 2026-09-10; `jamfact identity platform`).

## Gates the Mac applies to every image (write to them; each one otherwise rewrites your task)
- **No generated before/after photos** for any client (fleet rule 2026-07-28). Ask for a comparison
  of TYPES or a single "after" state instead.
- **Climate leads from the brand kit**: a hot-humid market (e.g. Central Texas, zone 2A) leads with
  heat/cool-house/lower-bills; cold, icicles, "meat locker", "ready for winter" may only support.
- **Brand palette/type come from the kit**, reconciled with the tenant's canvas style; do not paste
  a palette unless you are overriding on purpose.
- **Text in the image** is rendered as a real type layer, so give the exact wording; keep it short.

## Reply format (task-result)
`success: true` · `file: /mnt/clients/<tenant>/openvoiceui/uploads/<name>.png` · `url: /uploads/<name>.png`
· `poster`/variants if produced · `notes` naming any gate substitution. `success: false` carries `reason`.

## Notes
- One task = one image. A batch of six is six tasks; the runner serialises them on one browser.
- Do not run image generation on the VPS (Mike 2026-09-04: heavy jobs go to the Mac lane).
- Video (image-to-video, clips) is NOT this skill: it is the studio single-shot lane
  (`wan-video-queue/` → studio-queue on the Mac) — see `video-to-mac/SKILL.md`.
- Previous listener-model text of this skill is archived outside the shared mount (graveyard
  `skills-degeneric-backups-20260910/mac-image-gen/`); nothing in it should be followed.
