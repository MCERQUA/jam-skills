---
name: canvas-page-visibility
description: How any tenant agent makes its own canvas pages PUBLIC (reachable without login) or PRIVATE again — a one-line call to the OpenVoiceUI canvas API using the AGENT_API_KEY every container already has. No session cookie, no admin, no asking the host. TRIGGER when you need to make a canvas page public/shareable (e.g. to link it from a tweet or send it to a client), make a page private again, or someone asks "make this page public / shareable."
---

# Making a canvas page public (or private) — self-service

## HARD RULE — no auto-public, ever

**NEVER set `is_public: true` automatically, as part of creating a page, or from a playbook.**
A page may only go public when a human user (admin or client) explicitly requests it in a
separate message AFTER the page already exists. Before doing it, warn: "This makes the page
viewable by anyone with the link — no login required." If a human did not ask in this
conversation, do not do it.

You do NOT need a Clerk session cookie, admin rights, or the host for this. Every openclaw
container already has `AGENT_API_KEY`, and the OpenVoiceUI canvas API accepts it as an
`X-Agent-Key` header for page-visibility changes.

## Make a page PUBLIC (viewable without login — only on explicit human request)
```bash
curl -s -X PATCH "http://openvoiceui:5001/api/canvas/manifest/page/<PAGE_ID>" \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"is_public": true}'
```
Replace `<PAGE_ID>` with the page's id (the filename without `.html`, e.g. `bigheads-and-robbers`).
Success = HTTP 200 with `"is_public":true` in the returned JSON.

## Make a page PRIVATE again
```bash
curl -s -X PATCH "http://openvoiceui:5001/api/canvas/manifest/page/<PAGE_ID>" \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"is_public": false}'
```

## The public URL
Once public, the page is reachable at `https://<your-tenant>.jam-bot.com/pages/<PAGE_ID>` with
no login. That's the link to put in a tweet / send to a client.

## Notes
- Pages are **private (Clerk-gated) by default** — this call is how you opt a specific one public.
- If the call returns **403 "locked"**, an admin has `is_locked` set on that page — you can't change
  its visibility; ask the host to unlock it.
- The host `openvoiceui:5001` resolves on your tenant's internal network (also `openvoiceui-<tenant>:5001`).
- This is READ-nothing/WRITE-visibility-only; it does not expose secrets. Only YOUR tenant's pages.

## Need to hand the owner ONE FILE, not a page?

You do not have to make the page public. Files in `/app/runtime/uploads/` are served at
`/uploads/<file>` **without login** (measured 2026-09-08). See canvas-pages skill → Uploads →
"Public-URL delivery fallback" for the four rules (no PII ever · only what the owner asked for ·
queue-ack is not delivery · readable filename). The page itself stays private under the HARD RULE above.
