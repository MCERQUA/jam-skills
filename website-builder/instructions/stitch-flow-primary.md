# PRIMARY BUILD FLOW — Plan → Review → Generate → Review → Serve-whole (proven 2026-06-01)

This is the DEFAULT website-build flow. It replaces the old "scaffold + embed Stitch HTML into
Next via StitchPage" approach, which is now a FALLBACK only (see end). Origin: a full night of
debugging surveillanceinsurance — the scaffold approach kept collapsing pages back to a generic
look, and even faithful Stitch output was generic *until* every page got a complete, reviewed
content+SEO+component brief. Mike: "we cant have homepages with 2 things on it we need FULL high
performing seo strong websites… the only way is proper planning and research of ALL aspects before
we formulate the prompt to send to stich for each page… then someone needs to REVIEW IT and make
sure it has all the stuff, if not give the page back… in a loop until it has everything."

## Why the old approach failed (do not repeat)
- The scaffold wrapped every Stitch page in a generic default `<Navbar>/<Footer>` and StitchPage
  STRIPPED Stitch's own nav/footer + head → looked like the default template.
- StitchPage embedded Stitch HTML via `dangerouslySetInnerHTML`, then relied on the project's
  Tailwind to compile Stitch's custom classes (it didn't) → unstyled; and the Tailwind Play CDN
  `<script>` can't execute inside dangerouslySetInnerHTML → unstyled + Material-Symbols icons
  rendered as raw text.
- Thin prompts (art-direction only, or "SERVICE_LOCAL safe/light template") → Stitch invented
  sparse, generic pages.

## The flow (per site)

1. **RESEARCH** (existing Phase 1) — keywords, competitors, content-strategy, topical-map,
   page-recommendations, faq-research. Real DataForSEO data. This is the source of truth.

2. **SITE PLAN** — the page set + each page's target keyword/intent + the internal-link map.

3. **PER-PAGE PLAN → REVIEW LOOP** (the missing layer that makes pages full). For EACH page:
   - **Planner** (sub-agent): read ALL research, write a COMPLETE brief to
     `ai/page-briefs/<name>.md` containing, all with REAL specific content (no lorem / no
     fabricated stats/prices/testimonials): meta title (≤60) + description (≤155); one kw-rich H1
     + value prop; primary kw + intent + 3+ secondary kws; the FULL ORDERED section inventory the
     page type needs, each with its ACTUAL copy (hero → trust → core value sections specific to
     the page's topic & exposures → who-needs-it → real claims scenarios → cost guidance →
     related/cross-sell coverages → FAQ 6+ real Q&As → final CTA → footer w/ agency attribution);
     4+ internal links w/ anchor text; schema types; CTA placement.
   - **Reviewer** (sub-agent): score the brief against the rubric (see `brief-review-rubric`
     below). Output `{pass, missing[], score}`. **If not pass, send the `missing[]` back to the
     planner to revise; loop until pass.** (In practice a strong planner passes first try; the
     loop is the safety net.)

4. **GENERATE FROM THE BRIEF** — Stitch prompt = `[art direction + design system + brand/contrast
   rules]` + the FULL approved brief. Use `stitch-mcp.sh generate_screen_from_text` (DESKTOP,
   GEMINI_3_1_PRO), one shared `designSystem` asset across all pages for consistency. Capture
   `htmlCode.downloadUrl` FROM the response (search `outputComponents[]` for the `design` member —
   see `stitch-capture` note; never hardcode `[0]`). Pass the args via a FILE
   (`cat args.json | …` or `"$(cat …)"`) — inline shell quoting breaks on apostrophes/`$`.

5. **OUTPUT REVIEW LOOP** (Mike's "review the OUTPUT too"). After generation, verify the rendered
   HTML contains EVERY section the brief planned (programmatic section presence + screenshot
   review for contrast/light-on-light/dark-on-dark/unstyled-CTA). **If a section is missing, loop
   back** — re-prompt emphasizing the missing section (or use `edit_screens` for a surgical add).
   NOTE the Stitch "content budget" seesaw: forcing one section back can compress another, so
   check ALL sections each pass; converges in 2–3 iterations. Prefer `edit_screens` over full
   regen to avoid the seesaw.

6. **SERVE WHOLE** — output each page as its COMPLETE Stitch HTML (its own nav + fonts + sections
   + footer), assembled into a static site (`home→index.html`, `coverages/x→coverages/x/index.html`).
   Deploy that static site (Netlify or webdev). Do NOT chop it into the Next scaffold. The Stitch
   HTML is self-contained (Tailwind Play CDN + Google Fonts inline) and renders whole.

## Brand rule (lead-gen sites)
Display the SITE name in words (e.g. `surveillanceinsurance.com` → "Surveillance Insurance")
everywhere a company name appears. The underlying agency (e.g. "Contractor's Choice Agency")
appears ONLY as a small footer attribution (and on the About page body, as the operator).

## Art-direction rule (kills the generic look)
Feed Stitch a real art-directed brief, NOT "SERVICE_LOCAL safe/light template." Bold, cinematic,
distinctive, on-brand; oversized display type; real cinematic photography; ONE sharp accent;
intentional layout variety per page. The same Stitch tool produces generic OR stunning output
purely on prompt quality.

## Contrast / component rules (bake into every prompt — Mike's QC point)
On dark bg use light text; on light surface use dark text; NEVER light-on-light or dark-on-dark.
EVERY CTA is a FILLED accent button with dark text — never plain text. WCAG AA legible.

## brief-review-rubric (the reviewer's gate)
Pass ONLY if all present + substantive: meta title ≤60 kw-led · meta desc ≤155 kw+CTA · one
kw-rich H1 + value prop · primary kw + intent + 3+ secondary · hero(headline/subhead/CTA) ·
trust · core value sections SPECIFIC to the page (real exposures/coverages, not generic) ·
who-needs-it (named) · 3+ real claims scenarios (where relevant) · cost guidance (honest
ranges, no invented prices) · related/cross-sell · FAQ 6+ real Q&As · 4+ internal links w/
anchors · schema (Service/FAQPage/BreadcrumbList as fitting) · CTA at header+hero+mid+footer ·
ALL content real (no lorem/fabrication).

## FALLBACK (only when Stitch genuinely fails after retries)
The Next scaffold + section-library approach (templates/sections-fallback-1c). Use ONLY if Stitch
is unavailable/erroring for a page after retries. It is NOT the default and NOT a shortcut.
