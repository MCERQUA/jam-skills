---
name: canvas-pages
description: How to create, open, verify, and manage canvas pages in OpenVoiceUI. Covers the complete workflow — write HTML, open with [CANVAS:], verify, set privacy, assign category, manage uploads.
---

# Canvas Pages — Complete Workflow

Read this skill before creating ANY canvas page.

## Step 0: Check the User's Chosen Style (ALWAYS FIRST)

```bash
cat /app/runtime/canvas-pages/canvas-styles/ACTIVE-STYLE.md
```

- **If this file exists**, the user has chosen a design system for THEIR pages.
  It is LAW for every page you build: follow its design rules, and start every
  new page by copying `/app/runtime/canvas-pages/canvas-styles/active-template.html`
  (keep its full `<style>` foundation, replace the demo content). The color/theme
  rules further down in this skill are OVERRIDDEN by the active style.
- **If the file does not exist**, use the classic default system below
  (dark theme + `canvas-web-design` skill).
- The user changes styles on the "Canvas Styles" page (`canvas-styles.html`).
  If they ask to change how their pages look, point them there — or call the
  style API yourself: `curl -s http://openvoiceui:5001/api/canvas/styles` to list,
  `curl -s -X POST http://openvoiceui:5001/api/canvas/styles/<id>/activate` to switch.

## Step 1: Write the File

```
write({
  path: "/app/runtime/canvas-pages/my-page.html",
  content: "<!DOCTYPE html>...complete HTML..."
})
```

Write path is ALWAYS: `/app/runtime/canvas-pages/<page-name>.html`

## Step 2: Open It

Embed `[CANVAS:my-page]` in your spoken response:

```
"Here's the plan I built for you. [CANVAS:my-page] It covers..."
```

Repeating `[CANVAS:same-page]` on an already-open page forces a refresh — use this after updating an existing page.

**CRITICAL:** NEVER use the openclaw `canvas` tool with `action: "present"`. It WILL fail with "node required". ALWAYS use the `[CANVAS:page-id]` tag in your response text.

**CRITICAL:** When asked to CREATE something, you MUST use the write tool FIRST. `[CANVAS:name]` alone opens an EXISTING page — it does NOT create anything.

## Step 3: Verify It Opened

Run this AFTER the [CANVAS:] tag fires:

```bash
curl -s http://openvoiceui:5001/api/canvas/context
```

Returns: `{"current_page": "my-page.html", "current_title": "...", "updated_at": "..."}`

- If `current_page` matches → confirm to user
- If still on old page → say so and send `[CANVAS:my-page]` again
- If null/empty → canvas panel may be closed, send the tag again

## Step 3.5: Lint It (REQUIRED)

After writing or updating a page, run the deterministic QA check and fix EVERY issue:

```bash
curl -s http://openvoiceui:5001/api/canvas/lint/my-page
```

Returns `{"ok": true|false, "issues": [...]}` — flags emoji-as-icons, banned purple/pink,
CDN frameworks, missing viewport/page-icon meta, and active-style mismatches.
(If the endpoint 404s, this server predates the style system — skip.)

## Step 3.6: Mobile Viewport Pass (MANDATORY — before QA submission)

A page that clears CRITICAL bugs but skips the viewport pass ships as `0 CRIT / N HIGH`
and the build agent believes it is almost done — it is not. Responsive breakage is HIGH,
not cosmetic. **Check all three viewports and fix every layout break BEFORE submitting to
QA — this is required, not a bonus step** (QA finding 2026-07-12):

1. **Desktop** — ~1280px wide: intended layout, nothing clipped.
2. **Tablet** — ~768px: grids reflow, no horizontal scroll, tap targets ≥44px.
3. **Mobile** — ~375px: single-column where needed, no text/element overflow, no
   horizontal page scroll (wide tables/diagrams/code scroll INSIDE their own
   `overflow-x:auto` container — the page body must never scroll sideways).

Verify by resizing the browser (or DevTools device toolbar) at each width. Any element
that overflows, clips, or forces body-level horizontal scroll is a blocking fix, not a
QA note. Only submit once all three pass.

## Canvas Page HTML Rules

- **Desktop icon (REQUIRED):** Add `<meta name="page-icon" content="ICON_TYPE">` in the `<head>`. This sets the desktop icon. Available types: `dashboard`, `game`, `music`, `tools`, `book`, `upload`, `image-creator`, `file-explorer`, `interactive-map`, `style-guide`, `crm`, `voice-studio`, `ai-app-library`, `website`, `internet`, `settings`, `document`. Pick the closest match.
- **NO external CDN scripts** — Tailwind CDN, Bootstrap CDN are BANNED (break in sandboxed iframes)
  - **Exception:** `cdn.jsdelivr.net` is whitelisted for Three.js and similar libraries
- **All CSS and JS must be inline** — `<style>` and `<script>` tags only
- **Google Fonts `@import` in `<style>` is OK** — graceful fallback to sans-serif
- **Theme:** follow the ACTIVE STYLE (Step 0) if one is set. Only when no active
  style exists: dark theme, background `#0d1117` or `#13141a`, text `#e2e8f0`,
  accents blue `#3b82f6`, cyan `#06b6d4`, amber `#f59e0b`, emerald `#10b981`
- **BANNED:** purple (#764ba2, #667eea), pink, magenta — NEVER use these
- **BANNED:** emoji as UI icons — copy professional inline SVG icons from
  `/app/runtime/canvas-pages/canvas-styles/icons.html` (27 stroke icons, currentColor —
  they inherit any style). If that file doesn't exist, use plain Unicode symbols or
  hand-inline SVG. Emoji ONLY when the user explicitly asks for emoji content.
- **Make it visual** — cards, grids, tables, real data. No blank pages.
- **Mobile width (hard rule):** the host injects a 25px safe-area padding — that is
  the ONLY horizontal inset. On phones (≤640px) wrappers/sections get ZERO side
  padding; cards keep only their internal 16-20px. Never stack padded containers —
  text should span the full width inside the safe area. Backgrounds may bleed wider.
- For premium design patterns, read the `canvas-web-design` skill

## Interactive Buttons (postMessage)

```html
<button onclick="window.parent.postMessage({type:'canvas-action', action:'speak', text:'message'}, '*')">Ask AI</button>
<button onclick="window.parent.postMessage({type:'canvas-action', action:'navigate', page:'page-id'}, '*')">Go to Page</button>
<button onclick="window.parent.postMessage({type:'canvas-action', action:'menu'}, '*')">Page Menu</button>
```

Other actions: `open-url` (with `url` field), `close`.
External links: `<a href="..." target="_blank">`.
Display external site in canvas: `[CANVAS_URL:https://example.com]` tag in response text.

NEVER use `href="#"` — it does nothing in the iframe.

## Page Privacy

All canvas pages are **PRIVATE by default**. NEVER set a page to public when creating it.

ONLY make a page public if the user EXPLICITLY asks (separate request from creation):
```bash
curl -s -X PATCH http://openvoiceui:5001/api/canvas/manifest/page/PAGE_ID \
  -H "Content-Type: application/json" -d '{"is_public": true}'
```

When making public, warn: "This will make the page viewable by anyone with the link."
Public URL: `https://DOMAIN/pages/pagename.html`

**Locked pages:** Admin can lock pages (🔐). You CANNOT change visibility on locked pages (API returns 403). You CAN still edit the content.

## Desktop Category Assignment

After creating a page, assign it to a category:
```bash
curl -s -X PATCH http://openvoiceui:5001/api/canvas/manifest/page/PAGE_ID \
  -H "Content-Type: application/json" -d '{"category":"CATEGORY_ID"}'
```

Always tell the user where the page is going on their desktop.

## Uploads

**Storage:** `/app/runtime/uploads/` (container) → `/uploads/<filename>` (browser URL)

```bash
# List uploads
curl -s http://openvoiceui:5001/api/workspace/browse?path=Uploads

# Upload a file
curl -s -X POST http://openvoiceui:5001/api/upload -F "file=@/path/to/file.png"
```

Returns: `{"url": "/uploads/<uuid>.png", "original_name": "file.png"}`

- Max upload: 100 MB
- Uploads are PERMANENT — UI actions never delete server files
- Use `/uploads/<filename>` in `<img>` tags, CSS backgrounds, etc.

### Public-URL delivery fallback — hand the OWNER one file without making a page public

Measured 2026-09-08 (hrsf, `CANVAS_REQUIRE_AUTH=true`): `GET /uploads/<file>` → **HTTP 200 with no
login**; `GET /pages/<page>.html` on a private page → **401**. So any file you drop in
`/app/runtime/uploads/` is a no-auth download URL at `https://<tenant>.jam-bot.com/uploads/<file>`
— the right way to text or email the owner a zip, an MP3, a rendered video or a PDF when the canvas
page that holds it stays private. (Pattern from hrsf-voice 2026-09-05, five-song zip; bhb-voice
2026-09-05, pirate animation.) This is OUR system, so it satisfies the no-Claude-artifacts rule —
an artifact link never goes to a client; an `/uploads/` link may.

Four rules, all load-bearing:
1. **The URL is public to anyone who has it.** Never a quote, an estimate, a price sheet, a
   customer list, a lead, or anything with a person's name/phone/email in it. Those stay behind
   the Clerk gate on a canvas page.
2. **Only for a file the owner asked to receive.** It is not a way around page visibility: a page
   the owner has not asked to make public stays private (canvas-page-visibility skill HARD RULE),
   and you do not export a private page's contents into `/uploads/` to dodge that.
3. **Queue-ack is not delivery.** An SMS/email API's 200 means queued. Report "sent" only with the
   carrier/inbox receipt; until then the status is "queued, not yet confirmed" (bhb 2026-09-05 sat
   in exactly that state for a day).
4. **Name it so the owner can find it again.** `/uploads/<uuid>.png` is what `/api/upload` returns;
   for a deliverable, copy it to a readable name (`memaws-first-drop-songs.zip`) before you send the link.

## Path Mapping (CRITICAL)

| Container Path | Browser URL |
|----------------|-------------|
| `/app/runtime/canvas-pages/foo.html` | `/pages/foo.html` |
| `/app/runtime/canvas-pages/foo.png` | `/pages/foo.png` |
| `/app/runtime/uploads/bar.jpg` | `/uploads/bar.jpg` |

NEVER use `/app/runtime/` or `/canvas-pages/` in HTML `src` attributes. Always use the browser URL paths.

## Text Measurement with Pretext

For advanced text layout — virtualized lists, chat bubbles, auto-sizing containers, canvas text rendering — use `@chenglou/pretext`. It measures text height/width ~500x faster than DOM reads, with zero layout reflow. Load via jsdelivr (whitelisted):

```html
<script type="module">
import { prepare, layout, prepareWithSegments, walkLineRanges }
  from 'https://cdn.jsdelivr.net/npm/@chenglou/pretext/+esm';

const prepared = prepare('Your text here', '16px Inter');
const { height, lineCount } = layout(prepared, containerWidth, 22);
</script>
```

Read `/mnt/shared-skills/pretext/SKILL.md` for the full API, patterns (shrink-to-fit bubbles, masonry, variable-width columns), and canvas rendering examples.

## Delegate Heavy Pages

For polished user-facing pages (500+ lines), delegate to a sub-agent or use maxcode/z-code. Read the `coding-delegation` skill for patterns.

Quick internal pages you can write inline.
