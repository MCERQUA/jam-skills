---
name: stitch
description: "Google Stitch AI-powered UI design generation. Use when the user mentions stitch, UI design generation, design-to-code, screen generation, or wants to create/edit UI mockups programmatically."
metadata:
  version: 2.0.0
---

# Google Stitch — AI UI Design Generation

Generate production-ready UI designs (HTML + Tailwind) from text prompts, OR fetch designs a
human built in the Stitch web UI. v2.0.0 rewrite (2026-06-01) — corrects three errors that
silently broke every automated build for months. Read the #1 rule.

## ⚠️ THE #1 RULE — `generate` RETURNS the screen; DO NOT verify via `list_screens`

**`generate_screen_from_text` returns the generated screen — with its `htmlCode.downloadUrl`
— INSIDE ITS OWN RESPONSE. Capture the design FROM THAT RESPONSE. `list_screens` returns
`{}` (empty) for API-generated screens and always has — DO NOT use it to "verify" generation.**

The old skill said "generate, then poll `list_screens` to confirm success." `list_screens`
stays empty for API-gen screens → every build concluded "Stitch failed" → silently fell back
to the section-library templates — even though generate had **succeeded** and the real design
HTML was in the response. Verified 2026-06-01: one `generate_screen_from_text` returned a full
navy "Surveillance Insurance — Landing" design (HTML downloads fine, correct fonts/colors)
while `list_screens` returned `{}`. **The response IS the result. Parse it, download the HTML.**

`list_screens` / `get_screen` DO work — but only for screens a human created in the **web UI**
(persisted, listable). API-generated screens are returned inline, not reliably listed.
So: **generate → read the response. supply → list/get.**

## Call it via `stitch-mcp.sh` (raw HTTP) — NOT the claude.ai MCP, NOT a sub-agent

```bash
exec("bash /mnt/shared-skills/stitch/stitch-mcp.sh <tool> '<json>'")
#   (also at /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh)
```
- `stitch-mcp.sh` = raw JSON-RPC over HTTP; it returns the FULL response (screen + htmlCode).
  This is the path that works. Verified.
- Do NOT use the claude.ai MCP `mcp__stitch__generate_screen_from_text` — that wrapper TIMES
  OUT and returns nothing usable. (Its read tools are fine; its generate is not.)
- Never spawn a z-code sub-agent to drive Stitch.

## Models
- **`GEMINI_3_1_PRO`** (best) or `GEMINI_3_FLASH` (faster). **`GEMINI_3_PRO` is DEPRECATED** —
  do NOT use it (the old skill defaulted to it).

## DESKTOP vs MOBILE
- Request `"deviceType": "DESKTOP"` for websites (MOBILE for app mockups). Note: a DESKTOP
  request may still return a 780px screen labeled "Mobile" — the HTML is responsive Tailwind,
  so it renders fine; the device hint guides composition only.

---

## PATH A — AUTO-GENERATE (routes 1.B template+expand / 1.C generate): the working flow

```bash
# 1. Create project
stitch-mcp.sh create_project '{"title":"<Brand> — <project>"}'      # → result.name = projects/<PID>

# 2. Create/attach a DESIGN SYSTEM first (consistency; informs every screen).
#    ⚠️ USE `create_design_system` (full theme object incl. designMd field) — NOT
#    `create_design_system_from_design_md`, which requires a `selectedScreenInstance`
#    (an already-uploaded screen) and FAILS on fresh projects. This trap cost test-dev
#    a full debugging round on 2026-06-07.
stitch-mcp.sh create_design_system '{
  "projectId":"<PID>",
  "designSystem":{"displayName":"<name>","theme":{
    "colorMode":"DARK|LIGHT","headlineFont":"SPACE_GROTESK","bodyFont":"WORK_SANS",
    "roundness":"ROUND_TWELVE","customColor":"#hex",
    "designMd":"<your DESIGN.md / style brief goes HERE as a theme field>"}}
}'   # → result.name = assets/<DSID> (returned directly — no list call needed)
#    (If you skip step 2, the first generate auto-derives a design system — grab its asset id
#     from list_design_systems and pass it to all subsequent generates for consistency.)

# 3. Generate EACH page — pass designSystem + model. THE RESPONSE CONTAINS THE SCREEN.
stitch-mcp.sh generate_screen_from_text '{
  "projectId":"<PID>", "designSystem":"assets/<DSID>",
  "deviceType":"DESKTOP", "modelId":"GEMINI_3_1_PRO",
  "prompt":"<design-director prompt for THIS page — see instructions/stitch-auto-brief.md>"
}'
#   Parse the response: result.content[0].text (JSON) → outputComponents[] →
#   ⚠️ outputComponents is a MIXED list in ANY order: {designSystem}, {design}, {text},
#      {suggestion}×N. SEARCH for the member with `design.screens[]` — do NOT hardcode [0]
#      (when a design system is returned, [0]=designSystem and [1]=design). Verified 2026-06-01.
#        design.screens[0].htmlCode.downloadUrl   ← download THIS = the page HTML
#        design.screens[0].screenshot.downloadUrl ← preview PNG
#        design.screens[0].id/.title/.prompt
#      The {designSystem} member carries {name} — reuse it as designSystem on later pages
#      (no separate list_design_systems call needed after the home generate).
#   Capture htmlCode.downloadUrl FROM THIS RESPONSE immediately. Do NOT call list_screens.

# 4. Download each screen's HTML:
curl -sL "<htmlCode.downloadUrl>" -o .stitch-pages/<slug>.html
```

- **15 pages = 15 generate calls** (loop the page list). A single API prompt returns ONE
  screen — the "one prompt → 15 pages" behavior is the WEB UI only.
- Each generate takes ~1–3 min; `stitch-mcp.sh` blocks until the response returns the screen.
  If a single call truly errors (not just slow), retry that one page once.

### ⚠️ HARD GOTCHAS (every one of these wedged an agent on 2026-06-07)
1. **projectId is BARE NUMERIC** (`15150567938732718645`) in EVERY tool param named
   `projectId` — passing `projects/<id>` returns "entity not found" with zero hint why.
   The `projects/` prefix belongs ONLY in `name`-format params (`get_project`, `get_screen`).
2. **TIMEOUTS ARE NORMAL, NEVER RETRY A GENERATE.** Via MCP-server transport the call times
   out at ~60s while generation keeps running server-side for 1–3 min. On timeout: do NOT
   re-fire — poll `list_screens` every 30–90s until the screen appears. Re-firing duplicates
   work, burns quota, and triggers transient 401 "auth errors" (rate limiting) that look like
   credential failure but aren't. If you see a 401 mid-batch: WAIT 60s, poll — don't re-auth,
   don't re-fire.
3. **Model: `GEMINI_3_1_PRO`.** `GEMINI_3_PRO` is hard-deprecated in the API enum now.
4. **Multi-variant runs**: ONE project + ONE design system + N generate calls, each prompt
   carrying a DISTINCT layout archetype label (V1 minimal-cards / V2 HUD-gauges / V3
   timeline-board / V4 map-first / V5 bento-stats…). Fire, then poll `list_screens` once for
   all of them — don't poll per-screen.

## 🤐 COMMS CONTRACT — how to talk to the user during ANY Stitch build (Mike, 2026-06-07)

The user asked for an app, not a build log. **Exactly TWO user-facing messages for a normal build:**
1. **Ack** (one line): "I'll design and build that — give me a few minutes."
2. **Done** (one line): "Done — <name> is open in your canvas." (+ open it: write the canvas
   page and emit the canvas-open tag so it's already on screen when they read the message.)

**NEVER narrate:** "looking at the Stitch skill", "creating a project", "setting up a design
system", "generation takes 1-3 minutes", "polling", "got an entity-not-found, retrying",
sub-agent spin-ups, API errors you recovered from. ALL of that is silent internal work.
- Errors you can recover from (timeouts, rate limits, one bad variant): recover silently.
- Only surface a problem if you need a DECISION from the user — one concise question, no
  tool-level detail ("Want it dark or light?" not "the design-system API returned 401").
- Progress pings only if the build exceeds ~10 min: one line, no internals ("Still building —
  a couple more minutes.").

## END-TO-END "make a webapp for this" recipe (the whole flow, silent)
1. One-line ack (per contract above).
2. Stitch: create project → create_design_system (style fitting the subject) →
   generate (deviceType MOBILE unless told otherwise, GEMINI_3_1_PRO) → download HTML.
3. Adapt the HTML into a canvas page: single file, fix asset/CDN links, any persistence goes
   to server APIs (NEVER localStorage), save to canvas-pages + register in the manifest.
4. Open it in the canvas (canvas-open tag) — THEN send the done message.
5. Keep the Stitch project URL in your notes; offer it only if the user asks for variants.

## MOBILE APP CONCEPTS recipe (webapp/app-style asks — NOT a separate skill)
"Design a mobile app / webapp" asks use the exact same flow as websites with 3 changes:
- `deviceType":"MOBILE"` (or `TABLET`) on every generate.
- Prompts describe APP chrome, not page sections: bottom nav (5 items max), floating action
  buttons, bottom sheets, gauges/cards — enumerate sections in order like website prompts.
- Concept exploration = the multi-variant pattern above (gotcha 4): one shared design system,
  one generate per style variant. Deliverable to the user = the project URL:
  `https://stitch.withgoogle.com/projects/<PID>` (all variants browsable there).
Reference run: project 15150567938732718645 (2026-06-07, 5 sprayfoam-ops layouts, zero retries).
- Prompt quality is the whole game — use `instructions/stitch-auto-brief.md` (design-director
  persona + art direction + SEO plan + per-page layout variety). Generic prompts → samey output.

## PATH B — SUPPLY (route 1.A): human designs in web UI, you fetch (rock-solid)

Human builds pages at **stitch.withgoogle.com**, supplies the project ID (one prompt there can
yield all 15 pages). Then:
```bash
stitch-mcp.sh list_screens '{"projectId":"<PID>"}'     # WORKS for web-UI screens — lists all
stitch-mcp.sh get_screen '{"name":"projects/<PID>/screens/<SID>","projectId":"<PID>","screenId":"<SID>"}'
curl -sL "<htmlCode.downloadUrl>" -o .stitch-pages/<slug>.html
```
Verified: pulled 27 real web-UI screens this way. Use when a human wants design control, or as
the design path when auto-generate isn't wanted.

---

## IMAGES (keep — still accurate + valuable)
1. **Every `<img>` has `data-alt`** = the full image-gen prompt Stitch baked in (style, subject,
   lighting, setting). Use it to regenerate (HF z-image-turbo / working image gen) or source a
   matching real photo. Always grep `data-alt` before guessing what an image should be.
2. **AIDA URL sizing:** bare `lh3.googleusercontent.com/aida/...` is downscaled; append `=w1600`
   / `=w2048` for native res (mobile cap 780, desktop 2560).
3. **Supplied logo/client images — two paths:**
   - **API generate (`stitch-mcp.sh`) is TEXT-only** — it does not ingest an uploaded file. So
     for the automated path, supplied assets are wired in at BUILD time (website-builder Phase 6,
     RULE 6 "supplied media wins"): Stitch lays out the image SLOTS, the build fills them with the
     real files. Reference the brand in the prompt.
   - **Web UI Experimental Mode DOES accept image references** (Gemini Pro/3 path) — so for
     route 1.A (manual), you can upload the logo/competitor screenshots and use an image-anchored
     prompt: *"Redesign this; keep the layout structure but use my brand colors [hex list] and
     this logo."* That's the way to get supplied assets baked directly into Stitch output.

## Writing effective prompts
Structure (in order): purpose → core components → layout → style/theme → data/content → branding.
- GOOD: "Dashboard, left sidebar nav, 4 KPI cards top, line chart below, recent-activity table.
  Dark theme, Inter, rounded-8." · BAD: "Create a dashboard / make it better."
- Seed design tokens: "8-pt grid, radius 12, Inter, primary #3b82f6, surface #1e1e2e."
- Keep prompts < ~5000 chars (longer drops components).

## Iterating: `edit_screens` + `generate_variants`
```bash
stitch-mcp.sh edit_screens '{"projectId":"P","selectedScreenIds":["S"],"prompt":"Change hero bg to navy gradient"}'
stitch-mcp.sh generate_variants '{"projectId":"P","selectedScreenIds":["S"],"prompt":"Explore layouts","variantOptions":{"variantCount":3,"creativeRange":"EXPLORE"}}'
```
- One change at a time, surgical, directional ("left/right/above"), reference precisely.
- creativeRange: REFINE (subtle) · EXPLORE (balanced) · REIMAGINE (radical).
- variant aspects: LAYOUT, COLOR_SCHEME, IMAGES, TEXT_FONT, TEXT_CONTENT.

## Research synthesis — quality, modes, failure modes (web-UI + general)
Merged from a 2026-06-01 web/reddit research pass (residential-laptop@mesh; sources at bottom).
Applies mostly to the **web UI** (route 1.A) + prompt quality generally.

**Two levers that actually move quality:**
1. **DESIGN.md / design system FIRST** — without it, 10 pages = 10 button styles; with it they
   look like one designer made them. You can **EXTRACT a DESIGN.md from any reference URL** whose
   aesthetic the client admires (web UI) — huge lift, and it's the natural source for route 1.B
   ("base this on [reference], then expand/elevate"). For the API path, this = `create_design_system` (designMd goes in theme.designMd) then attach to every generate.
2. **One change per prompt; EDIT-first** — Stitch's own guide: combining layout + component
   changes makes it recreate the whole layout. For edits, use `edit_screens` (API) / click the
   design's Edit button first (web UI) — otherwise it regenerates instead of editing. Prompts
   >5000 chars silently drop components. Split internally: layout → colors → type → polish.

**Modes (web UI):** Standard (Gemini Flash, ~350 gen/mo, Figma export, NO image upload) for
ideation; **Experimental (Gemini Pro/3, ~50-200/mo, accepts IMAGE references, NO Figma)** for
"redesign this screenshot in our style" + final polish. Manual canvas nudges don't burn gens —
only AI prompts do.

**Prompt patterns:** vibe > specs ("premium & minimalist, like Stripe" beats RGB triples);
image-anchored ("keep layout, use my colors [hex]"); "Map the user flow for X, then design all
pages" forces flow-thinking; clicking an interactive element auto-generates the next screen in
the same style (free design-system propagation).

**Known failure modes (build pipeline passes to compensate):** output is often **fixed-width /
non-responsive** → responsive pass needed; **a11y/contrast/touch-targets fail WCAG** → a11y audit
pass; **vague prompts → generic Material-3 look** → always specify tone keywords + reference;
**mobile vs web don't share context** → separate threads, shared DESIGN.md; **"Stitch
unavailable"** → region/eligibility gate, clear stitch.withgoogle.com cookies; code export is
**structural scaffold, not production** → needs token mapping (a `stitch-to-react` community
skill exists as a converter reference).

**Where Stitch fits:** it's the **art-director stage** — design exploration + Figma/code export.
Responsive, a11y, code-quality, backend, deploy all belong DOWNSTREAM (the website-builder
pipeline). Don't try to make Stitch do a full-stack tool's job.

## Addendum — reddit deep-dive findings (residential-laptop, 2nd pass; high-signal)
- **Stitch PM (rustin0303) confirms:** consistency/design-system support is weak and is a Q1
  focus. Annotations on a screen preserve the IMAGE context but NOT your written reasoning —
  **put the "why" in CHAT, not in annotations.** Chat edits keep full context.
- **Chat-driven, NOT one-shot:** iterate via Stitch's chat/edit mode; re-prompting from scratch
  loses context and regresses. Treat Stitch as a conversation, not a render endpoint.
- **NO responsive iteration inside Stitch (HARD GUARD):** generating mobile/responsive variants
  mid-flow WIPES the desktop version and reverts to 1998-table grids. **Generate DESKTOP-only in
  Stitch; do responsive in the code stage** (Tailwind responsive utils). Refuse "make it mobile"
  prompts mid-flow.
- **Mode budget split (free tier):** the Redesign/Pro model caps ~4-5 screens/day; Flash
  continues 15+ at "still really good" quality. **Spend Pro gens on the hero/style-setter
  screen(s), then propagate via Flash** — the design system carries the Pro quality forward.
- **Seed-page consistency trick (when no design system):** build the first page polished, then
  "build [other page] using the SAME base layout, components, and style as [first page]." Cheaper
  than a design-system round-trip for short flows.
- **Auto-suggest chaining:** Stitch ends each generation with next-step suggestions; accepting
  them yields cohesive multi-screen flows "for free" (one user got 20 coherent screens this way).
- **Post-gen QA is mandatory:** art directors confirm colors/styles drift + WCAG/contrast/
  touch-targets routinely fail. Run an a11y/contrast audit (axe-core / pa11y) before "done."
- **Landscape is broken** — Stitch can't do landscape layouts (kiosk/TV/in-car). Route away.
- **Downstream Stitch→code applicator (waxman555's 4-prompt sequence — use in the build):**
  1. *Extract:* "Read the Stitch DESIGN.md and extract a production design system → design-tokens.md
     (tokens, typography, spacing, cards, buttons, sections). Don't touch business logic."
  2. *Primitives:* "Using design-tokens.md, build/improve reusable primitives (buttons, cards,
     badges, section containers, headings, form fields). Minimal, aligned to project structure."
  3. *Pilot one page:* "Apply the design to [one page] only — preserve data bindings, auth, APIs."
  4. *Rollout:* compare the piloted page vs others, fan out shared patterns.
  Decouples token-extract → primitives → single-page pilot → fan-out (safe vs "redo whole app").
- **Bulletproof fallback to MCP:** if the MCP path misbehaves, export the Stitch .zip and drop it
  in the project. (MCP capture-from-response is preferred; this corroborates skill v2's #1 rule.)

## Tool reference (verified live 2026-06-01)
| Tool | Notes |
|---|---|
| `create_project` | `{"title":"..."}` → result.name=projects/{id} |
| `list_projects` / `get_project` | `{"filter":"view=owned"}` ; `{"name":"projects/{id}"}` |
| `create_design_system_from_design_md` | `REQUIRES selectedScreenInstance (an uploaded screen) — FAILS on fresh projects; use `create_design_system` instead |
| `list_design_systems` | `{"projectId"}` → designSystems[].name=assets/{id} — EXISTS |
| `apply_design_system` / `update_design_system` | exist; verify per use |
| `generate_screen_from_text` | `{projectId, designSystem, deviceType, modelId:GEMINI_3_1_PRO, prompt}` — **screen returned IN the response** |
| `list_screens` / `get_screen` | web-UI screens only; NOT for API-gen |
| `edit_screens` / `generate_variants` | iterate on existing screens |

## TROUBLESHOOTING
- "list_screens empty after generate" → NOT a failure. The screen is in the generate RESPONSE
  (`result.content[0].text → outputComponents[].design.screens[].htmlCode.downloadUrl`).
- claude.ai MCP generate times out → use `stitch-mcp.sh` instead.
- `GEMINI_3_PRO` error → deprecated; use `GEMINI_3_1_PRO`.

## Canvas-page integration
Download `htmlCode.downloadUrl` → strip `<script src="cdn.tailwindcss.com">` → inline CSS →
add postMessage bridge → save as canvas page.
