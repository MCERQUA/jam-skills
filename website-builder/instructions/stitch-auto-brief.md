# Stitch Auto-Generate Design Brief — CANONICAL (route 1.B/1.C)

This composes the prompt sent to Stitch for AUTO-generated designs. Stitch only produces
distinctive work if prompted like a senior art director who also understands SEO and has a
real per-page plan. A generic "modern + animated" prompt yields generic, samey output — the
exact failure Mike flagged 2026-06-01 ("they all look the same and are quite boring").

**MANDATORY: route 1.B/1.C MUST call Stitch (stitch-mcp.sh / Stitch MCP) to GENERATE screens.
The section-library boilerplate (`sections-fallback-1c/`) is a LAST-RESORT only if Stitch
genuinely fails after retries — NEVER a substitute for generating. Do not skip Stitch.**

## How to compose the Stitch prompt (per page, via generate_screen_from_text)

Build each page's prompt from these layers. Fill the bracketed parts from the RESEARCH
(`ai/research/*.md`: keywords, page-recommendations, competitors, design-notes) + intake.

### 1. Persona + standard (every prompt opens with this)
> You are a world-class art director and conversion-focused web designer with deep SEO and
> [INDUSTRY] expertise. Design a PREMIUM, distinctive, agency-grade [PAGE TYPE] — not a
> template. Think editorial layout, confident oversized typography, intentional whitespace,
> layered depth, and real cinematic photography. Avoid generic SaaS-card grids and stock
> hero-over-three-columns clichés.

**Anchor the vibe with a reference (vibe > specs — /stitch skill).** Stitch responds far better
to a named design vibe than to raw RGB triples. Open with ONE concrete reference anchor true to
the brand, e.g. *"the editorial confidence of Stripe, the cinematic product photography of Apple,
the trade-authority of a premium contractor brand."* Pick references that fit THIS industry — not
generic tech — then let sections 2–5 make it specific.

### 2. Brand art-direction (consistent across pages — the "design system")
Establish ONE design system FIRST and reuse it for every page — without it, N pages = N button
styles; with it they look like one designer made them (/stitch skill). Two ways to seed it:
- **Route 1.B (template base):** pass the template's DESIGN.md and instruct *"expand on this base
  style and elevate it"* — don't restart from scratch, build ON the supplied system.
- **Route 1.C (generate):** generate the HOME page first, grab its auto-derived design-system asset
  id (`list_design_systems`), and attach that same id to every subsequent page generate.

Derive ONE distinctive aesthetic from the research/brand and state it concretely:
- **Palette:** [primary/accent/neutrals from .brand/colors.json] — name the mood (e.g. "deep
  navy authority + steel-blue accent + warm off-white"). NEVER purple/indigo unless brand-true.
- **Typography:** a pairing with personality (display + grotesque/serif body) + a type-scale.
- **Visual motif/concept:** ONE ownable idea for THIS brand (e.g. for security trades:
  "protection & precision — strong geometric framing, subtle shield/grid motifs, sharp edges,
  authoritative imagery of real work"). Not literal cliché (no CCTV-camera-watching-you).
- **Motion language:** scroll-reveal, parallax depth, micro-interactions, animated stats.
- **Imagery direction:** cinematic, real-context photography of the actual trade/work.

### 3. ANTI-SAMENESS — vary layout per page (critical)
Pages must feel like a designed *system*, not clones. Assign each page a DISTINCT layout
archetype so no two are identical. Rotate among, e.g.:
- full-bleed cinematic hero · split asymmetric hero · editorial left-rail · centered statement
- alternating zig-zag feature rows · bento grid · stat band · comparison table · timeline/steps
- testimonial spotlight · FAQ accordion · pricing/coverage matrix · big-CTA closer
Each page: a different hero treatment + a different section rhythm. State the archetype in the prompt.

### 4. SEO + conversion plan (per page — bake intent into the design)
For each page state: the **target keyword + search intent** (from keywords.md), what the page
must **convey** to rank + earn trust, and the **conversion path** (every page leads + ends with
"Get a Quote" + click-to-call [PHONE]). Tell Stitch the page's job, not just its looks.

### 5. Per-page composition — NUMBERED SECTION LIST (REQUIRED for full pages)
From `page-recommendations.md`: the exact sections this page needs, in order, each with a
1-line design intent. **The numbered list is not optional** — without it Stitch truncates to
3-4 sections even with the Pro model. Enumerate every section explicitly:

> Generate ALL [N] sections in one scrollable page:
> 1. HERO: [headline] [subhead] [CTA] [trust indicators]
> 2. [SECTION NAME]: [content description]
> 3. [SECTION NAME]: [content description]
> ... through [N]

Typical full homepage has 8-10 sections: Hero, Services/Features, Comparison or Stats,
Proof/Gallery, How It Works, Testimonials, FAQ, CTA close, Footer.

## Hard requirements (every screen)

**MODEL — HARD RULE (verified 2026-06-04):**
- **ALWAYS use `modelId: "GEMINI_3_PRO"`** — this is not optional
- `GEMINI_3_1_PRO` silently falls back to Flash and produces 3-section truncated output
- `GEMINI_3_FLASH` or omitting modelId = 3-4 sections (~6,000px). GEMINI_3_PRO = 9 sections (~14,000px)
- Do NOT attach a `designSystem` when maximizing content depth — it reduces output by ~25%.
  Describe colors/fonts in the prompt instead. Use design system only for multi-page consistency.

**CONTENT:**
- Premium/distinctive, NOT template-y. Real cinematic imagery, confident type, depth, craft.
- Per-page layout variety (no two pages the same skeleton).
- "Get a Quote" CTA + click-to-call [PHONE] in header (sticky) + page top + page bottom.
- **Generate DESKTOP only. Do NOT ask Stitch for "mobile" or "responsive" variants** — its
  responsive output is broken (HARD GUARD, /stitch skill). Responsive is added in the CODE stage
  (Tailwind breakpoints); accessibility/contrast is fixed in the post-gen WCAG QA pass. Don't rely
  on Stitch for either, and don't waste a generate on a "make it mobile" reprompt.
- Brand palette exact; no purple/indigo unless brand-true.
- Industry-appropriate register (avoid wrong-niche imagery, e.g. no claim-surveillance/spying for security-trade insurance).

Downstream (handled by the build, not by the Stitch prompt — /stitch skill):
- Every generated `<img>` is downloaded to `public/images/` and referenced locally (Phase 6). Grep
  each image's `data-alt` (Stitch's baked image-gen prompt) before sourcing a replacement; AIDA
  URLs are downscaled — append `=w1600` for full resolution.
- build-pages translates the Stitch HTML faithfully (Stitch is the design source of truth; do not
  flatten it back into generic sections), then adds Tailwind responsive breakpoints.
- A WCAG/contrast QA pass runs post-build (Stitch drifts on contrast + touch targets).
- Stitch can't do landscape/kiosk/in-car layouts — never route those to it.
