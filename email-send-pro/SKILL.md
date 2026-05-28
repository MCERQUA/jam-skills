---
name: email-send-pro
description: Canonical send wrapper for JamBot outbound email. Provider-agnostic (AgentMail + InkBox) — renders structured JSON into branded responsive HTML and ships via the tenant's configured provider. Use for EVERY outbound email so format stays consistent — no raw markdown, no plain-text walls, always tenant-branded. Triggers on send/email/draft/reply outbound asks once host has authorization to send.
---

# email-send-pro

The single send path for outbound JamBot email. Agents pass STRUCTURED JSON describing intent (intro, sections, optional CTA, optional canvas links). The wrapper validates, renders branded responsive HTML with a Jinja2 template, and ships via the tenant's configured provider — AgentMail (default) or InkBox (paid identities).

**You do NOT write HTML. You write the payload.** Branding, layout, header, footer, signature, CTA styling — all handled by the template.

## When to use

- Any outbound email going through `jam-bot@agentmail.to` (or a tenant inbox)
- Any outbound email going through a paid InkBox identity (`<handle>@inkboxmail.com`)
- Research debriefs, client status updates, internal team briefs, follow-ups, intro emails
- ANYWHERE you'd previously have hand-written an `html=...` body to AgentMail

## When NOT to use

- Inbound reply drafts inside AgentMail UI (different rendering path)
- Voice / SMS / mesh — wrong channel
- Existing legacy send sites already in production — leave them alone until host@mesh migrates them. If you see plain-text output where you expected this format, flag to host@mesh with the sending script's path.

## NEVER use Gmail tools. AgentMail + InkBox only.

## The wrapper

`/usr/local/bin/email-send-pro` — Python, takes JSON via stdin or `--input <file>`.

```
email-send-pro --preview < payload.json    # render only, print preview path
email-send-pro --send    < payload.json    # actually send via tenant's provider
email-send-pro --send --from-inbox jam-bot@agentmail.to --input payload.json
email-send-pro --preview --preview-out /tmp/my-preview.html --input payload.json
email-send-pro --send --reply-to-message-id <id> --input payload.json   # on-thread reply
```

`--send` is REQUIRED for sends. Never sends by default.

**Canonical source (version-controlled):** `/home/mike/MIKE-AI/scripts/email-send-pro/email-send-pro`. Edit there, then reinstall via `sudo bash /home/mike/MIKE-AI/scripts/install-email-send-pro-2026-05-27.sh`. Never edit `/usr/local/bin/email-send-pro` in place.

The legacy AgentMail-only wrapper at `/usr/local/bin/agentmail-send-pro` is preserved for fallback during migration. New callers should use `email-send-pro`.

## Provider routing

Each tenant's `branding.json` declares which provider sends its mail:

```json
{
  "email_provider": "agentmail"   // default — uses jam-bot@agentmail.to + per-inbox keys
}
```

```json
{
  "email_provider": "inkbox",
  "inkbox_inbox": "seattleroofing@inkboxmail.com",
  "inkbox_phone": "+15092861499",
  "inkbox_phone_id": "73a4c863-b3be-4ebd-b2e0-3d47c3b0ba4b",
  "inkbox_api_key_env_var": "INKBOX_API_KEY_SEATTLEROOFING"
}
```

| Provider | API | Auth | Endpoint |
|---|---|---|---|
| `agentmail` (default) | AgentMail v0 | `Authorization: Bearer <key>` | `POST https://api.agentmail.to/v0/inboxes/<from_inbox>/messages/send` |
| `inkbox` | InkBox v1 | `X-API-Key: <key>` | `POST https://inkbox.ai/api/v1/mail/mailboxes/<inkbox_inbox>/messages` |

### AgentMail key lookup (in order)

1. Env var `AGENTMAIL_API_KEY_<LABEL>` where `<LABEL>` = inbox local-part uppercased (e.g. `joshai@agentmail.to` → `AGENTMAIL_API_KEY_JOSHAI`)
2. Env var `AGENTMAIL_API_KEY`
3. Same names looked up in `/mnt/system/base/.platform-keys.env`

### InkBox key lookup (in order)

1. Env var named by `branding.inkbox_api_key_env_var` (default `INKBOX_API_KEY`)
2. `SETUP_INKBOX_API_KEY` (setup-host fallback)
3. Plain `INKBOX_API_KEY`
4. Each name looked up in: os.environ → `/mnt/clients/<tenant>/openclaw/workspace/.env` → `/mnt/system/setup-host/.env` → `/mnt/system/base/.platform-keys.env`

If no key resolves, the wrapper refuses with a clear error naming the env vars it tried.

### InkBox failure modes (handled in wrapper)

- `403` — recipient not opted in or compliance block. Permanent fail, no retry.
- `409` — region not whitelisted (e.g. CA destinations from a US-only number). Permanent fail.
- `429` / `5xx` / `0` (URLError) — transient, exponential backoff (2s, 4s, 8s, max 3 retries).
- Other 4xx — permanent fail, surfaced to caller.

## Payload schema

```json
{
  "tenant": "josh",
  "to": "josh@contractorschoiceagency.com",
  "cc": ["mike@example.com"],
  "bcc": [],
  "from_inbox": "jam-bot@agentmail.to",
  "subject": "BTIS Research Debrief — what we found + next options",
  "intro": "Quick update on the BTIS research we ran this afternoon.",
  "sections": [
    {
      "heading": "What we found",
      "body": "Three concrete things stood out in their pricing model...",
      "bullets": [
        "Their pay-per-claim tier undercuts our flat by 12%",
        "Their bind-to-quote ratio is reported as 0.34"
      ],
      "canvas_links": ["https://josh.jam-bot.com/canvas-pages/btis-debrief.html"]
    },
    {
      "heading": "Options for next move",
      "body": "We could go three directions from here...",
      "bullets": ["Stand pat on existing book", "Match their pay-per-claim", "Reposition on service depth"]
    }
  ],
  "cta_label": "View full research",
  "cta_url": "https://josh.jam-bot.com/canvas-pages/btis-research.html",
  "signature_style": "warm",
  "labels": ["btis", "research"],
  "in_reply_to": "<message-id>",
  "attachments": [
    {"filename": "btis-debrief.pdf", "mime_type": "application/pdf", "content_base64": "<base64>"}
  ],
  "review_mode": false
}
```

| Field | Required | Notes |
|---|---|---|
| `tenant` | recommended | Loads `/mnt/clients/<tenant>/openclaw/workspace/branding.json`; falls back to default brand. Drives provider routing. |
| `to` | yes | String or list of strings |
| `cc`, `bcc` | no | Lists of strings; pass-through to provider |
| `from_inbox` | no | AgentMail only. Defaults to `jam-bot@agentmail.to`. **Ignored for InkBox tenants** — they always send from `branding.inkbox_inbox`. |
| `subject` | yes | ≥ 8 chars |
| `intro` | yes | First paragraph above sections |
| `sections` | yes | ≥ 1 section; each needs `heading` + `body` |
| `sections[].bullets` | no | Strings only; DON'T prefix with `-` or `*` |
| `sections[].canvas_links` | no | Must match `https://<sub>.jam-bot.com/canvas-pages/*.html` |
| `cta_label` + `cta_url` | no | Both or neither |
| `signature_style` | no | `warm` (default: "Thanks,") / `formal` ("Best regards,") / `brief` ("—,") |
| `labels` | no | AgentMail only (InkBox API does not accept labels — silently ignored with a WARN). |
| `in_reply_to` | no | Message id to reply to ON-THREAD. See "Reply threading" below. Also settable via `--reply-to-message-id` (CLI overrides payload). |
| `attachments` | no | `[{filename, mime_type, content_base64}]`. Both providers support it. |
| `review_mode` | no | Boolean. When true, forces preview behavior + injects a yellow banner. Equivalent to env `EMAIL_REVIEW_MODE=true`. |

## Validation rules — wrapper REFUSES if violated

- `subject` shorter than 8 chars
- Zero sections, or a section missing `heading` / `body`
- `body` starts with `#` (raw markdown heading leak)
- `body` contains `**` or `__` (raw markdown bold leak)
- `bullets[]` entry starts with `-` or `*` (already a list — strip the marker)
- `canvas_links[]` doesn't match the `*.jam-bot.com/canvas-pages/*.html` pattern
- `cta_label` without `cta_url` or vice versa
- `attachments[].content_base64` not valid base64
- `email_provider == "inkbox"` but `inkbox_inbox` empty in branding

## Migration aid: legacy markdown body

If a caller passes a legacy `body` string with markdown (instead of `intro` + `sections`), the wrapper auto-renders it to HTML using the canonical `markdown_to_html` helper from `/home/mike/MIKE-AI/scripts/email-processor/joshai-helpers.py`. This stops the plain-text-leak bug today without forcing every caller to migrate atomically.

**The wrapper emits a WARN line:** `LEGACY PAYLOAD: 'body' received without 'sections'. Auto-rendering markdown→HTML. Please migrate to structured 'sections:' format.`

Callers should switch to structured `sections:` format to get full branding + canvas-link cards + CTA support + no-false-promises checks.

## REVIEW_MODE

Two ways to activate:
1. Env var `EMAIL_REVIEW_MODE=true` (process-wide gate, useful in cron)
2. Payload field `"review_mode": true` (per-send gate)

When active:
- A yellow warning banner is injected at the top of the rendered HTML.
- `--send` is downgraded to preview behavior — the email is rendered to disk but NOT sent.
- Caller still receives the preview path on stdout.

Use this to gate a final visual review before allowing actual send.

## Reply threading (in_reply_to)

To reply ON the existing email thread instead of starting a new message, set
`in_reply_to` (payload) or pass `--reply-to-message-id <id>` (CLI overrides the
payload). The SAME branded HTML+text is rendered — only the transport endpoint
changes:

| Provider | Without `in_reply_to` | With `in_reply_to` |
|---|---|---|
| `agentmail` | `POST .../inboxes/<from_inbox>/messages/send` (new message) | `POST .../inboxes/<from_inbox>/messages/<message_id>/reply` (on-thread; recipients + subject inferred from the original thread, so `to`/`cc`/`subject` in the payload are not resent) |
| `inkbox` | normal messages endpoint | same messages endpoint + `in_reply_to_message_id` added to the POST body |

All validation, branding, no-false-promises checks, and REVIEW_MODE behavior are
identical to a normal send. In `--preview`, the stderr shows an
`ON-THREAD REPLY → would hit <endpoint>` line plus `in_reply_to=<id>`. An empty
or non-string `in_reply_to` is rejected.

```bash
# On-thread reply, structured payload
email-send-pro --send --input - <<'EOF'
{
  "tenant": "josh",
  "to": "josh@contractorschoiceagency.com",
  "subject": "Re: your BTIS question",
  "intro": "Following up on your thread.",
  "sections": [{"heading": "Quick answer", "body": "Yes — no rate change needed."}],
  "in_reply_to": "msg_abc123thread"
}
EOF
```

`joshai-helpers.py` `send_reply()` routes entirely through this path (passing
`in_reply_to`) — it no longer forks off to call AgentMail's `/reply` endpoint
directly (closed 2026-05-28).

## No-false-promises rule (warning, not refusal)

The wrapper scans for promise phrasing and prints a warning. **Rewrite before sending.**

| Don't write | Do write |
|---|---|
| "We will have this ready by Tuesday" | "We could potentially have this ready by mid-week" |
| "Guaranteed bind by Friday" | "Targeting a bind around Friday" |
| "Done by 2026-05-30" | "Targeting around the end of next week" |
| "We will fix this tomorrow" | "We could have a fix in tomorrow" |

Trigger phrases: `we will`, `guaranteed`, `by <weekday>`, `by tomorrow`, `by next week`, ISO date `YYYY-MM-DD`.

## Canvas-link inclusion rule

If there is a canvas page that backs what a section discusses, **include it in that section's `canvas_links`**. Multiple canvas pages per section is fine. The reader expects to be able to click through to the live artifact — never describe a canvas page without linking it.

## Branding

Per-tenant branding file: `/mnt/clients/<tenant>/openclaw/workspace/branding.json`.
Schema: `/mnt/system/base/skills/email-send-pro/branding.schema.json`.
Default fallback: `/mnt/system/base/skills/email-send-pro/branding.default.json`.

To onboard a new tenant's brand, drop a JSON file at the tenant path with any subset of fields. Missing fields fall back to default.

## Four worked examples

### 1. Research debrief (the BTIS example — AgentMail default tenant)

```bash
email-send-pro --send --input - <<'EOF'
{
  "tenant": "josh",
  "to": "josh@contractorschoiceagency.com",
  "subject": "BTIS Research Debrief — what we found + next options",
  "intro": "Quick update on the BTIS research we ran this afternoon. Three things stood out and we want your call on next move.",
  "sections": [
    {"heading": "What we found",
     "body": "BTIS pricing undercuts our flat-rate tier by roughly 12% on the pay-per-claim option, but their bind-to-quote ratio is reported in the 0.34 range — meaning a lot of quoting effort that doesn't convert.",
     "bullets": ["Pay-per-claim tier undercuts ours by ~12%", "Bind-to-quote ratio ~0.34 (industry avg ~0.45)", "No service-tier differentiation in their public materials"],
     "canvas_links": ["https://josh.jam-bot.com/canvas-pages/btis-debrief.html"]},
    {"heading": "Options",
     "body": "We see three reasonable next moves.",
     "bullets": ["Stand pat — bank the service-depth story", "Match their pay-per-claim and absorb margin hit", "Reposition explicitly against their conversion gap"]}
  ],
  "cta_label": "View full research",
  "cta_url": "https://josh.jam-bot.com/canvas-pages/btis-research.html",
  "signature_style": "warm"
}
EOF
```

### 2. Client status update (AgentMail, src tenant)

```bash
email-send-pro --send --input - <<'EOF'
{
  "tenant": "src",
  "to": "stephen@example.com",
  "subject": "Queen Anne lander — copy in place, awaiting your review",
  "intro": "The Queen Anne neighborhood lander has the copy and FAQ blocks in place. Putting it in front of you for review before we point DNS.",
  "sections": [
    {"heading": "What we got done", "body": "Copy + 25-question FAQ block + Netlify form wired. Page passes mobile Lighthouse at 96.",
     "bullets": ["Hero + service grid (commit a8f31c2)", "25-Q FAQ block (commit d4e7991)", "Netlify form + spam guard"],
     "canvas_links": ["https://src.jam-bot.com/canvas-pages/queen-anne-preview.html"]},
    {"heading": "What we need from you", "body": "Two pieces — final NAP confirmation for the Queen Anne footer, and a thumbs-up on the hero photo we picked."}
  ],
  "signature_style": "warm"
}
EOF
```

### 3. Internal team brief (AgentMail, host tenant)

```bash
email-send-pro --send --input - <<'EOF'
{
  "tenant": "host",
  "to": "mike@jam-bot.com",
  "subject": "Nightly synthesis — host summary for 2026-05-27",
  "intro": "Short readout of what shipped, what's blocked, and what host wants Mike to weigh in on.",
  "sections": [
    {"heading": "Shipped",
     "body": "Three things landed since the morning brief.",
     "bullets": ["email-send-pro wrapper staged + skill doc written", "BTIS research canvas page published on josh tenant", "Foambot voice greeting fix verified against Z.AI B"]},
    {"heading": "Blocked / decision needed",
     "body": "One item needs Mike's call before agents can proceed.",
     "bullets": ["Queen Anne lander still missing NAP — we cannot fabricate per memory rule"]}
  ],
  "signature_style": "brief"
}
EOF
```

### 4. Paid InkBox tenant — Seattle Roofing client update

This tenant has `email_provider: "inkbox"` in branding.json, so the wrapper routes through `seattleroofing@inkboxmail.com` automatically. No `from_inbox` needed (and any override is ignored).

```bash
email-send-pro --send --input - <<'EOF'
{
  "tenant": "src",
  "to": "homeowner@example.com",
  "cc": ["dispatch@seattleroofing.example"],
  "subject": "Roof inspection scheduled — Tuesday between 9 and 11",
  "intro": "Confirming the roof inspection on your home next Tuesday. Here's what to expect and how to prep.",
  "sections": [
    {"heading": "What we'll do on site",
     "body": "Full visual inspection of the roof surface, flashing, valleys, and attic ventilation. Photo report sent same day.",
     "bullets": ["Walk the roof and document conditions", "Check flashing and valley seams", "Inspect attic for moisture or daylight"]},
    {"heading": "What we need from you",
     "body": "Two quick items so we can get in and out fast.",
     "bullets": ["Clear access to the attic hatch", "A phone you can pick up around 8:45am for the on-the-way text"]}
  ],
  "cta_label": "View your job page",
  "cta_url": "https://src.jam-bot.com/canvas-pages/job-seattle-roofing-2026.html",
  "signature_style": "warm"
}
EOF
```

## Migration note

Existing AgentMail send sites continue to operate. If you see a plain-text outbound email going out from a tenant where you'd expect this format, flag the originating script's path to `host@mesh`. We're migrating callers one at a time; no big-bang cutover.

## Files

| Path | What |
|---|---|
| `/home/mike/MIKE-AI/scripts/email-send-pro/email-send-pro` | **Canonical version-controlled source.** Edit here, then reinstall. |
| `/home/mike/MIKE-AI/scripts/install-email-send-pro-2026-05-27.sh` | Installer (copies canonical source → `/usr/local/bin`, snapshots prior) |
| `/usr/local/bin/email-send-pro` | The installed wrapper (Python, --preview / --send, AgentMail + InkBox). Do NOT edit in place. |
| `/usr/local/bin/agentmail-send-pro` | Legacy AgentMail-only wrapper (kept for fallback during migration) |
| `/mnt/system/base/skills/email-send-pro/template.html` | Jinja2 HTML template |
| `/mnt/system/base/skills/email-send-pro/branding.schema.json` | Branding JSONSchema |
| `/mnt/system/base/skills/email-send-pro/branding.default.json` | Fallback default brand |
| `/mnt/clients/<tenant>/openclaw/workspace/branding.json` | Per-tenant override |
| `/mnt/system/base/.platform-keys.env` | Where `AGENTMAIL_API_KEY` + per-label keys live |
| `/mnt/system/setup-host/.env` | Where `SETUP_INKBOX_API_KEY` lives |
| `/mnt/clients/<tenant>/openclaw/workspace/.env` | Where per-tenant `INKBOX_API_KEY*` lives |
| `/tmp/inkbox-openapi.json` | Cached InkBox OpenAPI spec (refresh on schema changes) |
