# WEBSITE-BUILD.md — Automated Website Build Workflow

## NON-NEGOTIABLE RULES (Read Before Any Phase)

You are building a client-deliverable website. Violating any one of these rules
fails the entire build. There is no "build with warnings". A phase passes its
gate or the build fails.

**RULE 0 — Determine the design source FIRST.** Read `intake.stitchScreens` and `intake.designTemplate` BEFORE any other phase decision. The result picks one of three paths:

| TIER 1 winner | Trigger | What it means |
|---|---|---|
| **1.A — Stitch supplied** | `intake.stitchScreens` non-empty | The user gave you existing Stitch screens by ID. FETCH them via `get_screen` and use them as the LITERAL blueprint. DO NOT call `create_project` or `generate_screen_from_text`. DO NOT add pages that aren't in the supplied screens. DO NOT mix in any "PAGE COMPOSITION BY BUSINESS TYPE" boilerplate from this doc. |
| **1.B — Design Template** | `intake.designTemplate` non-empty AND `stitchScreens` empty | The user picked a built-in template. Use its `designMd` tokens as the design source for Phase 3 generation. |
| **1.C — Generate from brand controls** | both empty | Phase 3 **MUST call Stitch** (`generate_screen_from_text` per page, with a shared design system — see Phase 3 Steps 3b–5) to generate every screen, using the design-director prompt in `instructions/stitch-auto-brief.md`. Building pages from the `sections-fallback-1c/` section library INSTEAD of generating with Stitch is **FORBIDDEN** unless Stitch genuinely fails — that flat output is exactly what we avoid. The "PAGE COMPOSITION BY BUSINESS TYPE" boilerplate is a STRUCTURAL REFERENCE for which sections a page needs — NOT a substitute for generating the design. Section library = LAST-RESORT fallback ONLY when Stitch errors (e.g. STITCH_API_KEY unavailable / create_project fails after retry); if you skip Stitch without a documented failure, the build is INVALID. |

Every phase below branches on this winner. Mix-and-match is forbidden — never use 1.A's Stitch HTMLs alongside 1.C's boilerplate templates.

**RULE 1 — Palette source is CONDITIONAL on TIER 1.**
- If 1.A wins → palette comes from the **fetched Stitch HTMLs themselves** (parse `colorsUsed` in `structure.json`). Logo / theme / manual color pickers are reference only — they do NOT override Stitch's palette.
- If 1.B wins → palette comes from the template's `designMd` tokens.
- If 1.C wins → cascade: Logo sampled (`extract-logo-colors.sh`) > Theme preset (`intake.theme`) > Manual pickers (`intake.colors.*`) > defaults.

Phase 1.5 BRAND-EXTRACT may still write `.brand/colors.json` for reference + favicon background, but Phase 4 (DESIGN SYSTEM) consults the TIER-1-appropriate palette source — NOT always `.brand/colors.json`.

**RULE 2 — Color tweaks come AFTER first deploy.** Do not adjust the supplied design's palette during the build. If the user wants to refine colors, that's a follow-up via `/build-rebuild --from design-system`.

**RULE 3 — DataForSEO is mandatory for Phase 1.** Read `/mnt/shared-skills/dataforseo/SKILL.md` and call the API for keyword volumes, CPCs, and SERP data. Web-search results, "industry estimates", and your own guesses are unacceptable. If DataForSEO is unavailable, the build halts. Every row in `keywords.md` MUST cite an integer search_volume and decimal CPC from `.dfs/volumes.json` — string ranges like "Low (50-100)" are unacceptable.

**RULE 4 — No purple, no indigo, no violet, no fuchsia.** Hue range 240-290 is forbidden. Phase 7 enforces with `tools/color-allowlist-check.py`. Tailwind classes `bg-purple-*`, `bg-indigo-*`, `bg-violet-*`, `bg-fuchsia-*` (and the same for `text/border/from/to/via`) are banned. Default `#4F46E5` indigo MUST NEVER appear.

**RULE 5 — Logo must be visible in every page render.** Phase 6 copies the logo to `public/logo.png`, generates favicons, wires the `<Logo />` component into Navbar. Build is incomplete if the deployed header shows a wordmark fallback when a logo file exists.

**RULE 6 — Supplied media wins over generated.** Phase 6 ASSETS uses `intake.heroImage`, `intake.teamImage`, `intake.gallery[]` for slots that match. Only generate AI images for slots Stitch left empty AND no user media exists for. Never replace a user-supplied image with an AI-generated one.

**RULE 7 — Quality gate is functional, not static.** Phase 7 runs `pnpm build` (prod, in webdev container), curls every URL in `sitemap.xml`, runs color allowlist + Stitch fidelity check, AND the host-side **visual gate** (`quality-review/visual-check.py` via the build-watchdog: WCAG contrast, mobile overflow, broken images, clipped/empty sections — the Quality Officer's eyes). `tsc --noEmit` alone is theater. A build is NOT done until the visual gate returns `pass` — see Phase 7 A6.

**RULE 8 — Deploy reconciles the webdev container's environment.** Phase 8 calls `tools/webdev-deploy.sh <client> <project>` which inspects `WEBDEV_PROJECT_NAME`, rewrites compose if mismatched, ensures `.env.local` exists, recreates the service, HTTP 200-checks. The site MUST serve at the client's webdev URL after Phase 8 completes — verified by curl, not by trust.

**RULE 9 — Snapshot the intake into the project repo.** Phase 8 copies `~/Websites/<project>/.intake.json` to `~/Websites/<project>/docs/website-intake-snapshot.json` and commits it. Future Mike + future agents need to know what was originally requested.

**RULE 10 — Push to GitHub.** Phase 9 (VERIFICATION) creates the GitHub repo if it doesn't exist (using `intake.projectName` as the repo name under the configured org/user) and pushes the working branch. Build is not complete until the code is on GitHub.

**RULE 11 — Failure stops the pipeline.** "Marked complete with warnings" is forbidden. If a phase gate fails, set `status: failed` with the failing gate name and HALT.

**RULE 12 — Conversion rules are MANDATORY.** Every client is a home-service business, and a beautiful site that doesn't make the phone ring is a failed build. **Read `CONVERSION-RULES.md` (this skill dir) and apply all 8 rules on every build** — above-the-fold trust-stack + `tel:` phone (sticky, no modal), ≤4 form fields, mobile PageSpeed >70 / <2s, reviews at every scroll depth, real photos (never stock), financing on service pages, sticky CTAs. The Phase 7 visual gate (RULE 7) MUST also verify: a clickable `tel:` link above the fold, form ≤4 fields, no auto-play hero video, no first-visit popup, hero image <500KB. A build that violates a conversion rule fails the gate.

---

## ⚠️ CONTAINER RULE — NON-NEGOTIABLE

**You are running inside an openclaw container (2GB RAM). The webdev container (3GB) is what compiles and serves the website.**

**NEVER run `pnpm build` inside this container. It will OOM-kill the process and fail the build.**

| Command | Where it runs | OK in openclaw? |
|---------|--------------|-----------------|
| `pnpm install` | openclaw workspace | ✅ Yes — just downloads packages |
| `pnpm add`, `pnpm dlx` | openclaw workspace | ✅ Yes — package management only |
| `pnpm tsc --noEmit` | openclaw workspace | ✅ Yes — type-check only, lightweight |
| `pnpm build` | **webdev container** | ❌ NEVER in openclaw — it OOMs |
| `pnpm dev` | **webdev container** | ❌ Never in openclaw |

The webdev container handles compilation automatically when the active project is switched in Phase 6.

---

## ⚠️ STOP — READ THIS FIRST

**You do not use this file directly. Ever.**

This file describes the automated build pipeline that runs ONLY when the canvas page triggers it after the user clicks "Start Research". The pipeline is executed by the canvas system, not by you responding to a user request.

**If a user asks you to make, build, or create a website:**
→ Open `[CANVAS:website-setup]` and use the secretary form-fill mode (see TOOLS.md)
→ Do NOT create directories, write intake.json, or touch any of this build workflow

**If you receive `/website-build <project-name>`:**
→ This is the canvas pipeline calling you — ONLY then read and follow this file

**Never** initiate a website build on your own. The user clicks "Start Research". The canvas sends the command. You execute the phases. That is the only sequence.

---

## Trigger

You receive a message from the automated build pipeline asking you to execute the 9-phase website build.

**Triggered by:** A message containing `Read WEBSITE-BUILD.md and execute the full automated build for project: <project-name>`

The intake data is at: `~/Websites/<project-name>/.intake.json`
The status file is at: `~/Websites/<project-name>/.build-status.json`

### Phase Map (canonical order — DO NOT REORDER)

| # | Phase | Type | Output | Gate |
|---|-------|------|--------|------|
| 1 | RESEARCH | sub-agent | `ai/research/keywords.md` + `.dfs/*.json` | `.dfs/volumes.json` exists + non-empty |
| 1.5 | BRAND-EXTRACT | inline | `.brand/colors.json` (+ `.brand/logo.png`) | primary not in hue 240-290 |
| 2 | SCAFFOLD | exec | Next.js project + deps | `pnpm install` exits 0 |
| 3 | STITCH PAGES | inline | `.stitch-pages/*.html` + `structure.json` | every page in intake has a Stitch HTML |
| 4 | DESIGN SYSTEM | inline | `globals.css`, `tailwind.config.ts`, `fonts.ts` | uses `.brand/colors.json` + Stitch palette |
| 5 | BUILD PAGES | sub-agent | `src/app/**/page.tsx`, `src/components/sections/*.tsx` | `stitch-fidelity-check.py` ≥ 0.85 |
| 6 | ASSETS | inline | `public/logo.png`, favicons, hero/og images | `<Logo />` referenced from Navbar |
| 7 | QUALITY GATE | inline | `.quality-gate/*.json` reports | prod build OK + every URL 200 + 0 violations |
| 8 | DEPLOY | exec | webdev-deploy.sh runs | webdev container healthy + serves new project |
| 9 | VERIFICATION | inline | final checklist report | all 6 verification curls pass |

## Before You Start

1. Read the intake file: `~/Websites/<project-name>/.intake.json`
2. Read the status file to check for already-completed phases
3. **Resume logic:** If a phase already has `"status": "complete"` in the status file, SKIP it entirely — do not re-run it. Start from the first phase that is NOT complete.
4. **Classify the business type** (see section below) — do this BEFORE any build work
5. Tell the user which business type was detected and which phase you're starting from.

## Resuming From a Failed/Interrupted Build

Check each phase in order. Skip any with `"status": "complete"`. Start from the first non-complete phase.

Example: if `research` and `scaffold` are complete but `design-system` is `in_progress` or `failed` → start at Phase 3.

**Before each phase, re-read the status file** to confirm the previous phases are complete.

---

## BUSINESS TYPE CLASSIFICATION — DO THIS FIRST

**Before writing a single file, read the intake and classify the business.** Every design decision flows from this classification.

### How to classify

Read `~/Websites/<project-name>/.intake.json`. Look at `industry`, `businessDescription`, `services`, and any other available fields.

### BUSINESS_TYPE classes

| Class | Examples |
|-------|----------|
| `SERVICE_LOCAL` | Contractors, HVAC, plumbing, electrical, roofing, landscaping, cleaning, pest control, insurance agents, security, auto repair, medical/dental practice, real estate agent — any local service sold in-person |
| `SAAS_PRODUCT` | Software product, app, platform, API, developer tool, SaaS subscription |
| `PROFESSIONAL_SERVICES` | Law firm, accounting firm, consulting agency, marketing agency, design studio — expertise sold as advisory/retainer |
| `ECOMMERCE` | Physical or digital products with a shopping cart |
| `RESTAURANT_FOOD` | Restaurant, café, catering, food truck, bakery |

**When in doubt between SERVICE_LOCAL and PROFESSIONAL_SERVICES:** If they have a physical service area, come to the customer's location, or do hands-on work → SERVICE_LOCAL. If they do pure advisory/strategy work remotely → PROFESSIONAL_SERVICES.

**Record the classification immediately:**
Write the detected `BUSINESS_TYPE` into `.claude/CLAUDE.md` (created in Phase 2 Scaffold). Every subsequent phase must reference this classification.

---

## DESIGN RULES BY BUSINESS TYPE — APPLIES ONLY WHEN TIER 1 = 1.C (generate-from-controls)

**HARD GATE — read RULE 0 in NON-NEGOTIABLE RULES at top of file FIRST.** This entire section applies ONLY when both `intake.stitchScreens` AND `intake.designTemplate` are empty. When EITHER is set:
- Stitch / Template is the design source of truth
- Section count, section types, layout decisions come from Stitch / Template
- DO NOT inject TrustBar / HowItWorks / Stats / Features sections that aren't in the supplied design
- DO NOT enforce "minimum 8 sections" or any section-count rule from this section
- The CSS palette comes from `parse-stitch-html.py` colorsUsed (1.A) or `designTemplate.designMd` (1.B), NOT from the CSS-variable defaults below

**If you skip this gate and apply the rules below to a 1.A or 1.B build, the build fails the Stitch fidelity gate (Phase 7) AND the visual outcome will not match the supplied design — see SRC build 2026-05-02 incident where TrustBar + Features were injected into a Stitch-supplied home that called for 5 sections.**

These fallback rules exist for 1.C builds because a dark SaaS aesthetic on a local plumber's website destroys trust and drives customers away. The aesthetic MUST match customer expectations for the industry — but ONLY when there is no supplied design to defer to.

---

### SERVICE_LOCAL design rules

**Background:** WHITE (`#ffffff`) or very light gray (`#f9fafb`). **NEVER dark.** Do not use dark backgrounds, dark cards, or dark hero sections for service businesses. Customers expect professional and trustworthy, not "startup cool."

**Section alternation:** Alternate `bg-white` → `bg-gray-50` → `bg-white` → `bg-gray-50` (or equivalent via CSS vars). Never stack two dark sections.

**Phone number placement — REQUIRED in ALL of these locations:**
- Navbar (desktop header — before the CTA button)
- Hero section (large, prominent, with Phone icon)
- CTA section (the "call to action" section near bottom of page)
- Footer

**Hero layout preference:** `split-right` (text on left, image/photo on right) OR `centered` with a real photo background. **NOT** a centered text-only dark section. SERVICE_LOCAL businesses sell trust and local presence — a photo of real work or real team builds confidence.

**Trust signals — REQUIRED above the fold (in Hero or TrustBar immediately below):**
Include at least 3 of these from the intake/research data:
- Years in business ("25+ Years of Experience")
- Number of jobs/clients ("2,000+ Projects Completed")
- Certifications and licenses (list the real ones from intake)
- Review rating ("4.9★ on Google — 200+ Reviews")
- Licensed/Bonded/Insured badge

**Animations:** Subtle fade-in on scroll only. **NO** looping background animations. **NO** floating orbs. **NO** gradient blobs. **NO** particles. These scream "tech startup" to a customer looking for a plumber.

**Typography:** Clean, readable sans-serif (Inter, Geist, Nunito). NOT heavy display weights for body text. Headings can be bold but must remain legible.

**Home page minimum:** 8 sections (see Page Composition below). SERVICE_LOCAL sites need depth to build trust with customers and rank for local SEO.

**Every service needs its own dedicated page** (e.g., `/spray-foam-insulation`, `/general-liability-insurance`). Generic `/services` landing page is not enough.

**CTAs prioritize phone calls and form submissions** — NOT "Learn More" or "Discover". Customers want to hire, not browse.

**CSS variables for SERVICE_LOCAL (apply in Phase 3):**
```css
:root {
  --background: 0 0% 100%;        /* pure white */
  --card: 210 20% 98%;            /* near-white */
  --foreground: 222 47% 11%;      /* near-black text */
  --muted: 210 20% 96%;           /* light gray sections */
  --muted-foreground: 215 16% 47%;
}
/* Do NOT add a .dark class override for SERVICE_LOCAL — there is no dark mode */
```

---

### SAAS_PRODUCT design rules

**Background:** Dark or light — match the product's personality. Dark backgrounds are fine here. Floating orbs and gradient backgrounds are acceptable aesthetic choices for software products.

**Hero:** Centered text-only OR split layout — both work. Animated backgrounds OK.

**Section count:** 5-6 sections on home page is appropriate. Clarity over depth.

**Animations:** Creative animations allowed — particles, orbs, gradients, parallax. Keep them tasteful.

**CTAs:** "Get Started Free", "Try It Now", "Sign Up", "Start Building" — action-oriented and product-focused.

**Trust signals:** GitHub stars, active users, uptime stats, featured-in badges (only if real from intake/research).

**Pricing page:** Required if product has tiers. See Pricing rules below.

---

### PROFESSIONAL_SERVICES design rules

**Background:** Light backgrounds strongly preferred. Law firms and accountants must communicate authority and trustworthiness — not tech-startup energy.

**Typography:** Serif headings acceptable (Playfair Display, Lora) for law/accounting. Clean sans-serif for agencies.

**Social proof:** Case studies or results sections preferred over generic testimonials. Specific outcomes ("Recovered $2.4M in a wrongful termination case") outperform vague praise.

**Phone in header:** Required (same as SERVICE_LOCAL).

**Section count:** 6-7 sections per home page.

**Animations:** Subtle. No floating orbs. Tasteful fade-in animations only.

**CTAs:** "Schedule a Consultation", "Request a Proposal", "Book a Discovery Call" — not "Get Started Free."

---

### ECOMMERCE

Standard product-grid layout. Not covered in detail in this document. Ensure product cards, cart functionality, and checkout flow are priority over editorial content.

---

### RESTAURANT_FOOD

Menu-first layout. Hero with food photography. Online ordering/reservation CTA above the fold. Not covered in detail here.

---

## Build Quality Standards (Read Before Every Build)

These are non-negotiable. A site that violates these will fail the quality gate.

### NEVER do these:
- **No fake testimonials.** Do not generate placeholder people ("Alex Chen, Software Developer, San Francisco"). Developers and business owners will immediately spot fabricated reviews and lose trust. See Testimonials section below for what to do instead.
- **No placeholder stats.** Do not put "500+ Clients Served" or "25 Years Experience" unless the intake or research explicitly confirms it. Made-up stats are worse than no stats — they set wrong expectations and damage credibility.
- **No broken external links.** All GitHub, social, and external URLs must come from the intake's `socials` field. If a URL isn't in intake, use `#` or omit the link entirely. Never guess a URL.
- **No unimplemented paid tiers.** If Pro/Enterprise pricing is listed but intake has no payment system, mark those tiers "Coming Soon" — do NOT add CTAs that link to nowhere.
- **No contact forms without a backend.** The contact form must either (a) POST to a working `/api/contact` route, or (b) use a mailto fallback. A broken form is worse than no form.
- **No pages that 404 from footer links.** Every link in the footer must point to a real page. /privacy, /terms, /blog — if you link to them, they must exist.
- **No wrong-industry aesthetics.** A dark floating-orb hero on an insurance agency website will cause the business owner to reject the entire build on sight. Match the aesthetic to the BUSINESS_TYPE before writing a single component.

### ALWAYS do these:
- **Classify the business type first.** Let it drive every decision.
- **Use intake data for all URLs and contact info.** GitHub URL from `socials.github`. Email from `email`. Phone from `phone`. Domain from `domain`.
- **Every page must have its own metadata export** with a unique title and description. Not just layout.tsx.
- **Set metadataBase to the intake domain**, not a hardcoded URL.
- **Feature descriptions must include a concrete example.** "Extensible skill system" is not a feature description. "Add skills like 'research competitors', 'schedule appointments', or 'send invoices' — without touching core code" is.

---

## Status File Protocol

The canvas page polls `.build-status.json` every 5 seconds to show progress. You MUST update it at every phase transition.

```json
{
  "projectName": "<name>",
  "status": "building",
  "startedAt": "<iso>",
  "updatedAt": "<iso>",
  "completedAt": null,
  "error": null,
  "currentPhase": "<phase-name>",
  "phases": {
    "research":      { "status": "not_started", "message": null },
    "scaffold":      { "status": "not_started", "message": null },
    "design-system": { "status": "not_started", "message": null },
    "stitch-pages":  { "status": "not_started", "message": null },
    "build-pages":   { "status": "not_started", "message": null },
    "assets":        { "status": "not_started", "message": null },
    "quality-gate":  { "status": "not_started", "message": null },
    "deploy":        { "status": "not_started", "message": null },
    "verification":  { "status": "not_started", "message": null }
  },
  "devUrl": "https://dev-test-dev.jam-bot.com"
}
```

**Phase status values:** `not_started` | `in_progress` | `complete` | `failed`
**Top-level status:** `queued` | `building` | `complete` | `failed`

To update, read the current file, modify the relevant fields, write it back. Always update `updatedAt`.

---

## Phase 1: RESEARCH (sub-agent, ~3-5 minutes)

**Update status:** `currentPhase: "research"`, `phases.research.status: "in_progress"`, `phases.research.message: "Starting market research..."`

### Step 0 — CONSUME the Brand Report's plan if present (skip re-research)

The Online Brand Report is the single SEO research engine (see `instructions/` + the system map). If its `seo-plan.json` was produced for this domain, **consume it instead of re-querying DataForSEO** — same data, one pass, and it carries the money-page matrix + interlink silo the live research doesn't.

```bash
# The brand report writes seo-plan.json next to its HTML. The build trigger drops it at
# ~/Websites/<project>/ai/seo-plan.json (copy it there if you have it from the report run).
if [ -f ~/Websites/<project>/ai/seo-plan.json ]; then
  python3 /mnt/shared-skills/website-builder/tools/seo-plan-to-research.py ~/Websites/<project>
fi
```

- If it **succeeds (exit 0)**, the research files (`keywords.md`, `topical-map.md`, `faq-research.md`, `page-recommendations.md`, `competitors.md`, `content-strategy.md`, `.dfs/volumes.json`) are written, `ai/build-plan.json` (money pages + interlink map + supporting content) is written, and `intake.pages` is seeded with the supporting pages **+ the service×area money pages**. **Skip the DataForSEO sub-agent below — go straight to the Phase 1 GATE.** Set `phases.research.message: "Consumed Brand Report seo-plan.json (money-page matrix + coverage + silo)"`.
- If there's **no `seo-plan.json`** (exit 1, greenfield with no prior report), run the full DataForSEO research sub-agent below as normal.

**Create research directory:**
```
~/Websites/<project>/ai/research/
~/Websites/<project>/ai/research/.dfs/
```

**Before spawning, copy intake for sub-agent access:**
```bash
cp ~/Websites/<project>/.intake.json ~/Websites/<project>/ai/.intake-copy.json
```

**Spawn a sub-agent:**
```
sessions_spawn({
  task: "You are a market researcher. Read the business intake at ~/Websites/<PROJECT>/ai/.intake-copy.json.

Your job: Research this business's market and competitors using REAL DATA from DataForSEO. Write findings to ~/Websites/<PROJECT>/ai/research/.

MANDATORY FIRST STEP: Read /mnt/shared-skills/dataforseo/SKILL.md to understand the API and the JSONL output format. This phase REQUIRES DataForSEO data — web search results for keyword volumes are unacceptable.

TASKS (do all in this order):

1. DATAFORSEO PULL (mandatory — every keyword/CPC/SERP datum below MUST come from these calls):
   a. dataforseo.sh keywords_for_site for top 3 competitors (from intake) → ai/research/.dfs/competitor-keywords.json
   b. Compose a candidate term list (40-60 terms): intake's services × locations × intent variants. Write to ai/research/.dfs/candidates.txt
   c. dataforseo.sh search_volume_live for the candidate list → ai/research/.dfs/volumes.json
   d. dataforseo.sh google_organic_serp_live for top 5 head terms → ai/research/.dfs/serps.json
   e. dataforseo.sh backlinks_summary_live for top 3 competitor domains → ai/research/.dfs/backlinks.json

2. COMPETITOR ANALYSIS — for each of the top 5-10 competitors (from .dfs/competitor-keywords.json + intake): name, URL, strengths, weaknesses, total backlinks (from .dfs/backlinks.json), top organic keywords. Save to: ai/research/competitors.md

3. KEYWORD STRATEGY — read .dfs/volumes.json. Group keywords by intent (informational, commercial, transactional, navigational). Each entry must list: keyword, MONTHLY VOLUME AS AN INTEGER from DFS (no "Low/Medium/High" qualifiers), CPC AS A DECIMAL from DFS, competition_index from DFS, assigned target page. Save as a Markdown table to: ai/research/keywords.md
   At the top of keywords.md, write: 'Tools Used: DataForSEO (live pull, $X.XX cost — sum of API responses)'.
   FORBIDDEN in keywords.md: any string ranges like "Low (50-100)", "Medium (200-500)", "~250/mo", "estimated", or empty volume cells. Every row MUST have an integer volume traceable to .dfs/volumes.json. Phase 5 will read this file and put these keywords in page titles + H1s — fake numbers means fake SEO.

4. TOPICAL MAP — read .dfs/volumes.json + .dfs/serps.json. Cluster keywords into 4-8 topical clusters (e.g. "decking materials", "deck installation cost", "deck permits + regulations", "outdoor living design"). For each cluster: list pillar keyword (highest volume in cluster), 5-12 supporting keywords, 2-4 intent gaps competitors aren't covering, recommended hub-or-spoke page. Save to: ai/research/topical-map.md

5. FAQ RESEARCH — extract People-Also-Ask questions and "what/how/why" intent keywords from .dfs/serps.json + .dfs/volumes.json. Produce 20-40 Q&A pairs grouped by intent cluster. Each Q has: the question (verbatim from SERP), 2-3 sentence answer drafted from intake + competitor research, target page assignment. Save to: ai/research/faq-research.md

6. PAGE RECOMMENDATIONS — based on topical-map.md + intake.pages + intake.services + intake.targetMarkets, recommend the FULL site page set for SEO strength. List: every page in intake.pages (must keep), recommended additions (e.g. service-detail pages per intake.services entry, location pages per intake.targetMarkets if local SEO opportunity warrants). Each recommendation includes WHY (which keywords it captures + their volume). Save to: ai/research/page-recommendations.md
   Note: Phase 3.5 PAGE PLAN uses intake.pages as authoritative for what gets BUILT — recommendations here are for Mike to review and add to intake.pages on next run. DO NOT silently expand intake.pages.

7. MARKET ANALYSIS — Summarize the local market using DFS-backed numbers: total monthly search volume in the niche, average CPC, competitive density. Identify gaps where competitors have low backlink counts on high-CPC terms. Save to: ai/research/market-analysis.md

8. COMPETITOR ANALYSIS — for each of the top 5-10 competitors (from .dfs/competitor-keywords.json + intake): name, URL, strengths, weaknesses, total backlinks (from .dfs/backlinks.json), top organic keywords. Save to: ai/research/competitors.md

9. CONTENT STRATEGY — One paragraph per page in intake.pages: what this page should achieve, primary keyword (from keywords.md), secondary keywords, conversion CTA. Save to: ai/research/content-strategy.md

10. DESIGN NOTES — Based on competitor websites: what visual patterns work in this industry, what's overused, what would differentiate this business. Note BUSINESS_TYPE and whether competitor sites use light or dark backgrounds. Save to: ai/research/design-notes.md

GATE: When done, verify ALL of these files exist AND non-empty:
  ai/research/.dfs/volumes.json (≥30 keyword rows)
  ai/research/keywords.md (≥30 rows, every row has integer volume + decimal CPC, no string ranges)
  ai/research/topical-map.md (≥4 clusters)
  ai/research/faq-research.md (≥20 Q&A pairs)
  ai/research/page-recommendations.md
  ai/research/competitors.md
  ai/research/content-strategy.md
If any are missing/empty/violating, set phases.research.status='failed' with message describing what's missing — do NOT mark complete.

IMPORTANT: After completing ALL tasks (and only if the gate passes), update ~/Websites/<PROJECT>/.build-status.json:
- Set phases.research.status to 'complete'
- Set phases.research.message to 'Research complete — N competitors, M keywords (DFS), $X.XX spend'
- Set updatedAt to current time

End with: OUTPUT_SAVED: ai/research/  (and a one-line summary of DFS keyword count + cost)",
  label: "website-research-<project>"
})
```

**After sub-agent returns, host-side gate (you, not the sub-agent):**
```bash
PROJECT_DIR=~/Websites/<project>
test -s "$PROJECT_DIR/ai/research/.dfs/volumes.json" || { echo "GATE FAIL: .dfs/volumes.json missing/empty"; exit 1; }
KW_COUNT=$(python3 -c "import json; d=json.load(open('$PROJECT_DIR/ai/research/.dfs/volumes.json')); print(sum(len(t.get('result',[])) for t in d.get('tasks',[])))")
[ "${KW_COUNT:-0}" -ge 30 ] || { echo "GATE FAIL: only $KW_COUNT keywords from DFS, need ≥30"; exit 1; }
```

If the gate fails, set `phases.research.status: "failed"` with the failing condition in `message`, set top-level `status: "failed"`, and HALT. Do NOT proceed to Phase 1.5.

**After sub-agent completes:** Read `ai/research/competitors.md` and `ai/research/keywords.md` to verify they exist and that keywords.md has DFS-backed numbers (no `~` or "estimated" qualifiers in the volume column).

---

## Phase 1.5: BRAND-EXTRACT (inline, ~30 seconds)

**Purpose:** Sample real pixel colors from the client's logo file. The intake's `brandColors` field is a hint only — the LOGO is the source of truth. Without this phase, builds fall back to whatever the intake has, which has historically been Tailwind defaults (indigo `#4F46E5`) producing purple websites that violate the no-purple rule.

**Update status:** `currentPhase: "brand-extract"`, `phases.brand-extract.status: "in_progress"`, `phases.brand-extract.message: "Sampling logo colors..."`

**Step 1 — locate the logo:**
```bash
PROJECT_DIR=~/Websites/<project>
mkdir -p "$PROJECT_DIR/.brand"

# Logo source priority:
# 1. .intake.json → brandAssets.logo (server URL or local path)
# 2. .intake.json → logo (legacy field)
# 3. ~/openvoiceui/uploads/<project>-logo*.{png,svg,jpg}  (manual upload)
LOGO_REF="$(python3 -c "
import json
d=json.load(open('$PROJECT_DIR/.intake.json'))
print(d.get('brandAssets',{}).get('logo') or d.get('logo') or '')
" 2>/dev/null)"

if [ -z "$LOGO_REF" ]; then
    # Fallback search
    LOGO_REF="$(ls ~/openvoiceui/uploads/${PROJECT}-logo*.png ~/openvoiceui/uploads/${PROJECT}-logo*.svg 2>/dev/null | head -1)"
fi

if [ -z "$LOGO_REF" ]; then
    echo "GATE FAIL: no logo found in intake.brandAssets.logo, intake.logo, or uploads/${PROJECT}-logo.*"
    # Mark phase failed and HALT
    exit 1
fi
```

**Step 2 — extract colors:**
```bash
bash /mnt/shared-skills/website-builder/tools/extract-logo-colors.sh \
    --logo "$LOGO_REF" \
    --output "$PROJECT_DIR/.brand/colors.json"
```

The script writes:
- `.brand/colors.json` with `{primary, primaryHsl, accent, accentHsl, neutral, dominantHues, isMonochrome, warnings}`
- Hue range 240-290 (purple/indigo) is auto-rejected at the script level — primary will NEVER be purple even if the logo has purple accents

**Step 3 — copy logo asset for Phase 6:**
```bash
# Determine extension and copy as canonical .brand/logo.<ext>
case "$LOGO_REF" in
    *.svg|*.SVG) cp "$LOGO_REF" "$PROJECT_DIR/.brand/logo.svg" ;;
    http*://*) curl -fsSL "$LOGO_REF" -o "$PROJECT_DIR/.brand/logo.png" ;;
    *) cp "$LOGO_REF" "$PROJECT_DIR/.brand/logo.png" ;;
esac
```

**Step 4 — handle monochrome / palette warnings:**

Read `.brand/colors.json`. If `isMonochrome: true` OR `warnings` mentions "primary and accent are within 20deg":
- Phase 4 (DESIGN SYSTEM) will compute a complementary accent from the primary (rotate hue +180°). No action needed here, but log a note in `phases.brand-extract.message`.

**Step 5 — gate:**
```bash
PRIMARY_HUE=$(python3 -c "
import json
d=json.load(open('$PROJECT_DIR/.brand/colors.json'))
h=d.get('primaryHsl','0 0% 0%').split()[0]
print(h)
")
# Sanity: primary must NOT be purple/indigo
python3 -c "
h=float('$PRIMARY_HUE')
import sys
sys.exit(1 if 240 <= h <= 290 else 0)
" || { echo "GATE FAIL: extracted primary is in forbidden hue range $PRIMARY_HUE"; exit 1; }
```

**Step 6 — mark complete:**
Update `phases.brand-extract.status: "complete"`, message: `"Logo colors extracted: primary=<hex>, accent=<hex>"`.

---

## Phase 2: SCAFFOLD (exec, ~1-2 minutes)

**Update status:** `currentPhase: "scaffold"`, `phases.scaffold.status: "in_progress"`, `phases.scaffold.message: "Copying templates and installing dependencies..."`

The project directory already exists (canvas created it). Do these steps:

0. **Normalize the intake — BLOG IS MANDATORY (the one sanctioned expansion of `intake.pages`):**
Every JamBot site ships with a blog. This is the ONLY place the pipeline is allowed to add to `intake.pages` (Phase 3.5 still treats the result as authoritative; the no-silent-expansion rule in Phase 1 is about *research recommendations*, not this fixed policy). Ensure `"blog"` is present, then write `.blog-seed.json` so Phase 5.5 knows which intro post to write:
```bash
python3 <<'PY'
import json, os, glob, re
proj = os.path.expanduser('~/Websites/<project>')
intake = json.load(open(f"{proj}/.intake.json"))
pages = intake.get('pages') or []
if 'blog' not in [p.lower() for p in pages]:
    pages.append('blog')
    intake['pages'] = pages
    json.dump(intake, open(f"{proj}/.intake.json",'w'), indent=2)
    print("intake.pages: appended 'blog'")
else:
    print("intake.pages: blog already present")
# Pick the intro-post topic from research (topical map → first foundational topic),
# falling back to a sensible industry-intro title. Phase 5.5 writes the actual post.
topic = None
tm = sorted(glob.glob(f"{proj}/ai/research/topical-map.md"))
if tm:
    txt = open(tm[0]).read()
    m = re.search(r'^\s*[-*\d.]+\s+(.{8,80})$', txt, re.M)
    if m: topic = m.group(1).strip().rstrip('.')
biz = intake.get('businessName') or intake.get('industry') or 'our company'
if not topic:
    topic = f"What to Know About {intake.get('industry','Our Services').title()}"
slug = re.sub(r'[^a-z0-9]+','-', topic.lower()).strip('-')[:60]
json.dump({"slug": slug, "title": topic, "business": biz}, open(f"{proj}/.blog-seed.json",'w'), indent=2)
print(f"blog-seed: /{('blog/'+slug)} — \"{topic}\"")
PY
```

1. **Copy project template files:**
```bash
# IMPORTANT: use trailing /. NOT /* — bash * glob silently skips dotfiles
# like .gitignore. Worker-a's cheer-insurance scaffold (2026-05-23) committed
# node_modules wholesale because of this. /. copies hidden files correctly.
cp -r /mnt/shared-skills/website-builder/templates/project/. ~/Websites/<project>/
```

2. **Copy animation wrappers:**
```bash
mkdir -p ~/Websites/<project>/src/components/animations
cp /mnt/shared-skills/website-builder/templates/animations/*.tsx ~/Websites/<project>/src/components/animations/
```

3. **Copy section templates:**
```bash
mkdir -p ~/Websites/<project>/src/components/sections
cp /mnt/shared-skills/website-builder/templates/sections/*.tsx ~/Websites/<project>/src/components/sections/
```

4. **Create public directory structure:**
```bash
mkdir -p ~/Websites/<project>/public/og
```

5. **Update package.json name:**
```bash
cd ~/Websites/<project> && sed -i 's/"project-name"/"<project>"/' package.json
```

6. **Write .claude/CLAUDE.md** from intake data + research findings:
Read the intake JSON and research files. Fill in the CLAUDE.md template with:
- Business name, industry, domain
- **BUSINESS_TYPE classification** (one of: SERVICE_LOCAL, SAAS_PRODUCT, PROFESSIONAL_SERVICES, ECOMMERCE, RESTAURANT_FOOD)
- **Design approach summary** — e.g. "SERVICE_LOCAL: white backgrounds, phone in header, 8+ sections, no dark theme, no orbs"
- Brand colors (primary, secondary, accent)
- Tone, fonts
- Target customer
- Pages list (for SERVICE_LOCAL: include individual service pages)
- Primary CTA (for SERVICE_LOCAL: phone call or "Get a Free Quote")
- Key findings from research (top competitors, target keywords)
- Contact info: phone, email, address, hours
- Social/GitHub URLs from intake `socials` field
- Whether this is an open-source project (affects social proof strategy)
- Trust signals available from intake (years in business, certifications, review count/rating, job count)

7. **Install dependencies:**
```bash
cd ~/Websites/<project> && pnpm install --no-frozen-lockfile
```

8. **Initialize shadcn/ui:**
```bash
cd ~/Websites/<project> && pnpm dlx shadcn@latest init -y
cd ~/Websites/<project> && pnpm dlx shadcn@latest add button card badge separator input textarea label -y
```

9. **Install animation deps:**
```bash
cd ~/Websites/<project> && pnpm add motion lenis
```

10. **Initialize git:**
```bash
cd ~/Websites/<project> && git init && git add -A && git commit -m "feat: scaffold <project> from website-builder templates"
cd ~/Websites/<project> && git checkout -b web-dev
```

**Update status:** `phases.scaffold.status: "complete"`, `phases.scaffold.message: "Project scaffolded with real templates"`

---

## Phase 3: STITCH PAGES (inline, ~2-4 minutes per page) — MANDATORY

> **⚠️ PRIMARY FLOW (default since 2026-06-01): `instructions/stitch-flow-primary.md`.**
> Per-page **plan → brief-review loop → generate-from-brief → output-review loop → serve the WHOLE
> Stitch HTML as a static site** (do NOT chop it into the Next scaffold). Briefs live in
> `ai/page-briefs/<name>.md`; one shared design system across all pages; bold art direction +
> strict contrast/brand rules baked into every prompt. The Next-scaffold/StitchPage embedding +
> section-library is now a FALLBACK only (Stitch unavailable after retries). Read
> `instructions/stitch-flow-primary.md` BEFORE executing this phase — it has the why, the rubric,
> and the gotchas (capture-from-response index, file-based args, FAQ/cost seesaw, font links).

**Why this runs BEFORE Design System:** Stitch is the design source of truth. Phase 4 (DESIGN SYSTEM) reads palette + typography from the fetched Stitch HTMLs. Building tokens first and asking Stitch later produces visual conflicts.

### Step 0 — Detect TIER 1 (design source) and BRANCH

```bash
PROJECT_DIR=~/Websites/<project>
TIER1=$(python3 -c "
import json
d=json.load(open('$PROJECT_DIR/.intake.json'))
ss=d.get('stitchScreens') or []
dt=d.get('designTemplate') or None
print('stitch' if ss else ('template' if dt else 'generate'))
")
echo "TIER1=$TIER1"
```

**Update status:** `currentPhase: "stitch-pages"`, `phases.stitch-pages.status: "in_progress"`, `phases.stitch-pages.message: "TIER1=<TIER1>: <fetching|generating> page layouts..."`

---

### TIER 1.A — FETCH SUPPLIED STITCH SCREENS (when `intake.stitchScreens` non-empty)

**This is the most common path and the one Mike uses for production builds.** The user has already designed the site in Stitch and supplied the project ID + screen IDs. Your job is to FETCH them and save the HTMLs verbatim. DO NOT call `create_project`. DO NOT call `generate_screen_from_text`. DO NOT add screens for pages the user didn't supply (Phase 3.5 PAGE PLAN handles unsupplied pages by cloning a sibling).

**Step 1 — Parse projectId from intake:**

```bash
PROJECT_DIR=~/Websites/<project>
mkdir -p "$PROJECT_DIR/.stitch-pages"

# The form's onStitchInput() parses the pasted markdown into stitchScreens[]
# but the project ID itself is in the stitchInstructions free text. Regex it.
STITCH_PROJECT_ID=$(python3 -c "
import json, re
d=json.load(open('$PROJECT_DIR/.intake.json'))
text = d.get('stitchInstructions') or ''
m = re.search(r'\bID:\s*(\d{10,})', text)
print(m.group(1) if m else '')
")
[ -z "$STITCH_PROJECT_ID" ] && { echo "GATE FAIL: could not parse Stitch project ID from intake.stitchInstructions"; exit 1; }
echo "Stitch project ID: $STITCH_PROJECT_ID"
```

**Step 2 — For each supplied screen, fetch its HTML:**

For EACH `intake.stitchScreens[i]`:

1. Map the screen `name` to a page slug using these patterns (FIRST match wins):
   - `/Home(page)?/i` → `home`
   - `/About(\s*Us)?/i` → `about`
   - `/Services?/i` → `services`
   - `/Contact(\s*Us)?/i` → `contact`
   - `/FAQ/i` → `faq`
   - `/Gallery|Portfolio/i` → `gallery`
   - `/Reviews|Testimonials/i` → `reviews`
   - `/Pricing/i` → `pricing`
   - `/Team/i` → `team`
   - If no match, slugify the name (lowercase, hyphens, alphanum only) and use that.

2. Call the Stitch skill's `get_screen` for each `screenId` against `STITCH_PROJECT_ID`:
   ```bash
   exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh get_screen '{\"name\": \"projects/$STITCH_PROJECT_ID/screens/$SCREEN_ID\", \"projectId\": \"$STITCH_PROJECT_ID\", \"screenId\": \"$SCREEN_ID\"}'")
   ```

3. The response contains `htmlCode.downloadUrl`. Download:
   ```bash
   curl -L -s -o "$PROJECT_DIR/.stitch-pages/<slug>.html" "<htmlCode.downloadUrl>"
   ```
   (Mike's `intake.stitchInstructions` even says "Use a utility like `curl -L`".)

4. If a `screenshot.downloadUrl` exists, download that too as `.stitch-pages/<slug>.png` for debugging.

**Step 3 — Run the structure parser:**
```bash
python3 /mnt/shared-skills/website-builder/tools/parse-stitch-html.py "$PROJECT_DIR/.stitch-pages"
```
This writes `.stitch-pages/structure.json`. Phase 5 consumes it.

**Step 4 — GATE (host-side, mandatory):**
```bash
# Every supplied screen must have produced a non-empty HTML.
N_SUPPLIED=$(python3 -c "import json;print(len(json.load(open('$PROJECT_DIR/.intake.json'))['stitchScreens']))")
N_FETCHED=$(ls "$PROJECT_DIR/.stitch-pages/"*.html 2>/dev/null | wc -l)
[ "$N_FETCHED" -lt "$N_SUPPLIED" ] && { echo "GATE FAIL: fetched $N_FETCHED of $N_SUPPLIED supplied screens"; exit 1; }
echo "Fetched $N_FETCHED Stitch screens (all supplied)."
```

**If any single supplied screen failed to fetch, set `phases.stitch-pages.status: "failed"` and HALT.** Pages the user supplied are non-negotiable.

**Step 5 — Write manifest:**
```bash
python3 -c "
import json, os
d = json.load(open('$PROJECT_DIR/.intake.json'))
manifest = {
  'projectId': '$STITCH_PROJECT_ID',
  'tier1': 'stitch',
  'pages': []
}
# (mapping from name→slug applied above; record what's on disk)
import glob
for html in sorted(glob.glob('$PROJECT_DIR/.stitch-pages/*.html')):
    slug = os.path.basename(html)[:-5]
    manifest['pages'].append({'slug': slug, 'htmlPath': '.stitch-pages/' + slug + '.html', 'status': 'complete'})
open('$PROJECT_DIR/.stitch-pages/manifest.json', 'w').write(json.dumps(manifest, indent=2))
"
```

**Mark complete:** `phases.stitch-pages.status: "complete"`, `message: "<N> supplied Stitch screens fetched; structure.json written"`. Continue to Phase 3.5 PAGE PLAN.

---

### TIER 1.B / 1.C — GENERATE STITCH SCREENS (only when no `intake.stitchScreens` supplied)

This path runs ONLY when 1.A doesn't fire. The historical generate-from-prompt logic remains below for these paths. If `intake.designTemplate` is set, embed its `compactDesignMd` in the prompts; otherwise, generate from brand controls.

(The legacy generation steps below execute ONLY in TIER 1.B / 1.C.)

### Step 1 — Check for a selected design template

Read `~/Websites/<project>/.intake.json` and look at `intake.designTemplate`. Two cases:

**Case A — `designTemplate` is null or missing:**
The user did not pick a template from the Design Template Gallery. You will still run Stitch, but use only the brand colors/fonts/style from the intake (no DESIGN.md to embed).

**Case B — `designTemplate.designMd` is a non-empty string:**
The user picked a template. You will compact the DESIGN.md into a ~600-character token block and embed it in every page prompt.

### Step 2 — Compact the DESIGN.md (only in Case B)

Stitch prompts must stay under ~3500 characters or components get dropped. The DESIGN.md is too long to embed verbatim (often 4000-8000 chars). You must extract the key tokens:

Read `intake.designTemplate.designMd` and produce a `compactDesignMd` string of this exact shape:

```
DESIGN: {creative-north-star or first ## heading}
COLORS: primary {hex}, surface {hex}, accent {hex}, text {hex}
TYPOGRAPHY: headlines {font-name}, body {font-name}, scale {if mentioned}
SHAPE: {roundness rule}
KEY RULES:
- {rule 1 — most distinctive 'do' or 'don't'}
- {rule 2}
- {rule 3}
SIGNATURE: {one-line description of the signature element if present}
```

Aim for under 700 characters. Keep only what would change a layout decision.

### Step 3 — Create the Stitch project (once)

```bash
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh create_project '{\"title\": \"<businessName> — <project>\"}'")
```

Save the returned project ID into a variable. You'll use it for every page generation.

If `create_project` returns an error, mark `phases.stitch-pages.status: "failed"` with the error message and HALT the build (top-level `status: "failed"`). Per the NON-NEGOTIABLE RULES, Stitch is the design source of truth — Phase 5 (BUILD PAGES) refuses to run without `.stitch-pages/structure.json`. Do NOT continue.

### Step 3b — Establish ONE shared design system (the consistency anchor)

All pages MUST share a single design system or they come out as N different styles. Get a
design-system asset id ONCE, then attach it to EVERY page generate (Step 4). Two ways:

**Path 1 — explicit (Case B template, or compose one from brand/research):**
```bash
exec("bash .../stitch-mcp.sh create_design_system_from_design_md '{\"projectId\":\"<PID>\",\"designMd\":\"<compactDesignMd or a designMd composed from brand colors/fonts + the stitch-auto-brief art direction>\"}'")
exec("bash .../stitch-mcp.sh list_design_systems '{\"projectId\":\"<PID>\"}'")   # → designSystems[0].name = assets/<DSID>
```

**Path 2 — derive from the home page (Mike's autonomous recipe):** generate the HOME page first
(Step 4, with a rich `stitch-auto-brief` art-direction prompt). Stitch auto-creates a design
system from it. Then `list_design_systems` → grab `assets/<DSID>`. Use that DSID for ALL
remaining pages. This makes each site's style distinctive (driven by the home prompt) yet
internally consistent.

Save `<DSID>`. If neither path yields a design-system asset id, you may proceed passing brand
colors in each prompt, but consistency will be weaker — prefer getting a DSID.

### Step 4 — Generate one screen per page

Read `intake.pages` (a string array like `["home","about","services","contact","faq"]`).

For EACH page name, build a prompt with this structure (keep under 3500 chars total):

```
{Page} page for {businessName}, a {industry} business {city/region from address}.

What the business does: {description}
Target audience: {idealCustomer}, geographic scope: {geographicScope}
Services: {first 5 services from intake.services, comma separated}
Primary SEO keywords: {first 3 from intake.primaryKeywords}
Brand tone: {tone}
Brand colors: primary {colors.primary}, secondary {colors.secondary}, accent {colors.accent}, background {colors.background}

Required sections for this {page} page:
{infer sections from page name — see SECTION INFERENCE below}

{compactDesignMd if Case B, otherwise omit this block}

Mobile-first, production-ready, accessible. No placeholder copy — write real headlines using the SEO keywords above.
```

**SECTION INFERENCE — required sections by page name:**

| Page name | Required sections |
|-----------|-------------------|
| `home` | hero with H1 + CTA, trust strip, services preview (4 cards), why-choose-us (3 cols), recent work / gallery, testimonials, service area or map, FAQ teaser, footer CTA |
| `about` | hero, story / origin, team grid, values (3 cols), credentials/licenses, CTA |
| `services` | hero, full services grid (one card per service from intake.services), process (3-5 steps), pricing or quote CTA, FAQ |
| `service` (singular) | hero, what it includes, process, pricing tiers or quote, gallery, FAQ, related services |
| `contact` | hero, contact form, contact info block (phone/email/address/hours), service area map placeholder, FAQ |
| `faq` | hero, accordion of 8-12 questions targeting SEO keywords, contact CTA |
| `gallery` / `projects` | hero, filterable grid, individual project preview, CTA |
| `blog` | hero, featured post, recent posts grid, categories sidebar, newsletter CTA |
| `pricing` | hero, comparison table, FAQ, contact CTA |
| `testimonials` / `reviews` | hero, reviews grid, rating summary, CTA to leave a review |

For any page name not in the table, infer required sections from the page name and the site type (`intake.siteType`).

**Run the generation** — use `GEMINI_3_PRO` (NOT 3_1_PRO — see note), DESKTOP only, and TEE the response to a per-page file so Step 5 can capture the screen from it:

```bash
mkdir -p ~/Websites/<project>/.stitch-pages
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh generate_screen_from_text '{\"projectId\": \"<PID>\", \"deviceType\": \"DESKTOP\", \"modelId\": \"GEMINI_3_PRO\", \"prompt\": \"<escaped-prompt>\"}' > ~/Websites/<project>/.stitch-pages/<page>.resp.json 2>&1")
```

**⚠️ MODEL RULE (verified 2026-06-04 — this was wrong before):**
- Use `"GEMINI_3_PRO"` — produces full 9-section pages (~14,000px, ~36KB HTML)
- `"GEMINI_3_1_PRO"` silently falls back to Flash and produces TRUNCATED 3-section pages (~6,000px). The previous instruction saying it was the correct model was WRONG.
- `GEMINI_3_FLASH` or omitting modelId = same truncated output. Always specify `GEMINI_3_PRO`.

**⚠️ DESIGN SYSTEM RULE (verified 2026-06-04):**
- Do NOT attach `designSystem` when generating content-rich pages — it reduces output height by ~25%.
- Describe colors, fonts, and style in the prompt itself instead.
- Only use a design system if you need strict visual consistency across 10+ pages in a batch AND are willing to accept shorter per-page content.

**⚠️ SECTION ENUMERATION RULE (verified 2026-06-04):**
- The prompt MUST contain a numbered list of every section: "Generate ALL N sections: 1. HERO: ... 2. SERVICES: ... 3. ..."
- Without this explicit list, even GEMINI_3_PRO truncates to 3-4 sections.
- Typical full page: 8-10 sections. Name them all.

Critical JSON-escape rules: replace `"` with `\"` and newlines with `\\n` inside the prompt before embedding.
Build the prompt from `instructions/stitch-auto-brief.md` (design-director persona + per-page layout variety + mandatory numbered section list) so pages are distinctive and full-length, not generic stubs.
NOTE: each `generate_screen_from_text` returns the finished screen in its response (~1-3 min) —
do NOT poll list_screens; Step 5 reads `<page>.resp.json`.

### Step 5 — CAPTURE THE SCREEN FROM THE GENERATE RESPONSE (do NOT poll list_screens)

**⚠️ The `generate_screen_from_text` RESPONSE already contains the finished screen + its HTML
download URL. Capture it from the response. DO NOT call `list_screens` — it returns `{}` (empty)
for API-generated screens and ALWAYS HAS. The old "wait 60s, poll list_screens, retry 3×" flow
is what made every build falsely conclude Stitch failed and fall back to the section library.
Verified 2026-06-01.** (See stitch skill v2.0.0 rule #1.)

In Step 4 you teed the generate response to `~/Websites/<project>/.stitch-pages/<page>.resp.json`.
Parse it for the screen + HTML URL and download immediately:

```bash
mkdir -p ~/Websites/<project>/.stitch-pages
URL=$(python3 - ~/Websites/<project>/.stitch-pages/<page>.resp.json <<'PY'
import json,sys,re
raw=open(sys.argv[1]).read()
try:
    o=json.loads(raw); inner=json.loads(o["result"]["content"][0]["text"])
    # CRITICAL: outputComponents is a MIXED list — it can contain {designSystem}, {design},
    # {text}, and {suggestion} members in ANY order. The design is NOT always index [0]
    # (when a design system is returned it is usually [0] and the design is [1]). SEARCH for
    # the member that has a design.screens[].htmlCode — never hardcode [0]. (Verified against a
    # real surveillanceinsurance home response 2026-06-01: [0]=designSystem, [1]=design.)
    # ALSO: design.screens[] can hold MULTIPLE screens where only ONE (often the LAST) carries
    # htmlCode — the others are screenshot-only. SEARCH screens for the one with htmlCode;
    # do NOT assume screens[0]. (Verified 2026-06-01: a brief-driven generate returned 4 screens,
    # only screens[3] had htmlCode.downloadUrl.)
    url=""
    for comp in inner.get("outputComponents", []):
        d=comp.get("design")
        if not (d and d.get("screens")): continue
        for scr in d["screens"]:
            hc=(scr.get("htmlCode") or {})
            if hc.get("downloadUrl"): url=hc["downloadUrl"]; break
        if url: break
    print(url)
except Exception:
    m=re.search(r'https://contribution\.usercontent\.google\.com/download\?[^"\\ ]+', raw)
    print(m.group(0) if m else "")
PY
)
[ -n "$URL" ] && curl -L -s -o ~/Websites/<project>/.stitch-pages/<page>.html "$URL"
```

**Bonus — the HOME response carries the design system for free.** The same `outputComponents`
list includes a `{designSystem: {name, designSystem, version}}` member. Grab its `name` here and
reuse it as the `designSystem` arg on every subsequent page generate — you do NOT need a separate
`list_design_systems` call after the home page:
```bash
DSID=$(python3 -c "import json,sys;o=json.load(open(sys.argv[1]));inner=json.loads(o['result']['content'][0]['text']);print(next((c['designSystem'].get('name','') for c in inner.get('outputComponents',[]) if c.get('designSystem')),''))" ~/Websites/<project>/.stitch-pages/home.resp.json 2>/dev/null)
```

Also grab the screenshot for the manifest/debug (same response → search the `design` member's `screens[0].screenshot.downloadUrl`).
Record the screen `id` from the response for the manifest. A page is DONE when its
`.stitch-pages/<page>.html` exists and is non-empty — verify that, NOT list_screens.

DESKTOP-ONLY: generate every page with `deviceType: DESKTOP`. Never iterate responsive/mobile
inside Stitch (it wipes the desktop version) — responsive is handled in the build/code stage.

### Step 6 — Failure handling per page (HALT-ON-FAIL)

If a page fails after 3 retries OR `generate_screen_from_text` returns an error:
- Mark `phases.stitch-pages.status: "failed"` with `message="page <name> failed: <details>"`
- Set top-level `status: "failed"`
- HALT the build — do NOT proceed to other pages, do NOT proceed to Phase 4

There is no "partial success" mode for Stitch. Every page in the intake's pages list MUST have a corresponding `.stitch-pages/<page>.html`. Phase 5 (BUILD PAGES) refuses to run with missing pages.

### Step 7 — Mark phase complete

After ALL pages have been generated (no partials allowed):

- `phases.stitch-pages.status: "complete"`
- `phases.stitch-pages.message: "<N> page layouts generated, all pages present"`
- Write a manifest at `~/Websites/<project>/.stitch-pages/manifest.json`:
  ```json
  {
    "projectId": "<stitch-project-id>",
    "generatedAt": "<iso>",
    "compactDesignMd": "<the compacted block, or empty>",
    "pages": [
      {"name": "home", "screenId": "<SID>", "htmlPath": ".stitch-pages/home.html", "status": "complete"},
      {"name": "about", "screenId": "<SID>", "htmlPath": ".stitch-pages/about.html", "status": "complete"}
    ],
    "failed": []
  }
  ```

If the WHOLE phase failed (e.g. create_project failed, OR any single page in the intake's pages list could not be generated after retries), mark `phases.stitch-pages.status: "failed"`, set top-level `status: "failed"`, and HALT the build. Phase 5 (BUILD PAGES) WILL NOT run without Stitch HTMLs — see Rule 3 in NON-NEGOTIABLE RULES at the top.

After all Stitch HTMLs are downloaded, run the structure parser:
```bash
python3 /mnt/shared-skills/website-builder/tools/parse-stitch-html.py \
    ~/Websites/<project>/.stitch-pages
```
This writes `.stitch-pages/structure.json` — the machine-readable contract Phase 5 consumes for fidelity checking. If parse fails, mark phase failed and HALT.

---

## Phase 3.5: PAGE PLAN (inline, ~10 seconds) — NEW

**Purpose:** Before any pages are built, decide which Stitch HTML each page in `intake.pages` will be built from. Two outcomes per page:
- `literal` — Mike supplied a Stitch screen for this page; build that page from the supplied HTML 1:1
- `cloned-from` — Mike did NOT supply Stitch for this page; clone structure from a stylistic sibling supplied screen (preserves visual consistency)
- `needs-decision` — neither possible; HALT for Mike to provide more Stitch screens or remove the page

This phase is DETERMINISTIC. No sub-agent. Run the script.

```bash
python3 /mnt/shared-skills/website-builder/tools/page-plan.py ~/Websites/<project>
```

**Outputs:** `~/Websites/<project>/ai/page-map.json` — Phase 5's locked input.

**Exit codes:**
- `0` — page-map.json written, no halt-warnings → continue to Phase 4
- `1` — page-map.json written WITH halt-warnings (one or more pages have no Stitch source AND no acceptable clone fallback) → set `phases.page-plan.status: "failed"`, surface haltWarnings to canvas console, HALT
- `2` — invalid project layout → set failed, HALT

When 0: `phases.page-plan.status: "complete"`, `message: "<N> pages mapped: <X> literal + <Y> cloned-from"`.

---

## Phase 4: DESIGN SYSTEM (inline, ~1 minute) — was Phase 3

**Why this runs AFTER Stitch:** Stitch has already chosen a palette and button rhythm. We extract those choices into CSS tokens so every page Phase 5 builds renders consistently with the Stitch mockups.

**Update status:** `currentPhase: "design-system"`, `phases.design-system.status: "in_progress"`, `phases.design-system.message: "Configuring brand colors and typography from logo + Stitch..."`

**Read these files in order:**
1. `~/Websites/<project>/.brand/colors.json` (from Phase 1.5) — primary, accent, neutral are LOCKED.
2. `~/Websites/<project>/.stitch-pages/structure.json` (from Phase 3) — `colorsUsed` array per page, `buttonStyles`.
3. `/mnt/shared-skills/website-builder/instructions/design-system.md` — the existing template doc.
4. `.claude/CLAUDE.md` for BUSINESS_TYPE.

**Source-of-truth precedence (NEVER deviate):**

| Token | Source | Notes |
|-------|--------|-------|
| `--primary` | `.brand/colors.json → primaryHsl` | NEVER from intake.colorPrimary |
| `--accent` | `.brand/colors.json → accentHsl` | If `warnings` mentions "within 20deg", compute complementary: `(primaryHue + 180) % 360 91% 60%` |
| `--neutral` / muted / border | `.brand/colors.json → neutralHsl` | Lighten for muted, darken for border |
| `--background`, `--foreground` | BUSINESS_TYPE rules below | Light theme for SERVICE_LOCAL |
| Heading + body fonts | intake `fonts` field, falls back to BUSINESS_TYPE defaults | Stitch's chosen font is a hint not a mandate (Stitch may pick fonts not on Google Fonts) |
| Button style | Stitch `structure.json → buttonStyles.primary` if present | Otherwise default rounded-lg primary |

### Step 1: Set CSS variables in `src/app/globals.css`

Use `.brand/colors.json` HSL values. Do NOT use intake `colorPrimary` etc.

**For SERVICE_LOCAL — apply these overrides non-negotiably:**
```css
:root {
  --background: 0 0% 100%;           /* pure white — do NOT change for SERVICE_LOCAL */
  --foreground: 222 47% 11%;         /* near-black */
  --card: 210 20% 98%;               /* near-white card bg */
  --card-foreground: 222 47% 11%;
  --muted: 210 20% 96%;              /* light gray — used for alternating sections */
  --muted-foreground: 215 16% 47%;
  --border: 214 32% 91%;

  /* THESE MUST come from .brand/colors.json — NEVER hardcoded indigo defaults */
  --primary: <primaryHsl from .brand/colors.json>;
  --primary-foreground: 0 0% 100%;
  --accent: <accentHsl from .brand/colors.json — or computed complementary>;
  --accent-foreground: 0 0% 100%;
}
/* Do NOT add a .dark { } block for SERVICE_LOCAL — no dark mode */
```

**For SAAS_PRODUCT or PROFESSIONAL_SERVICES:** Set background, surface, border, text, muted colors appropriate to their theme. Dark is acceptable for SAAS_PRODUCT only. `--primary` and `--accent` STILL come from `.brand/colors.json`, never from intake.

**Forbidden:** any `:root` value that lands in HSL hue 240-290. Phase 7 will fail the build if found. The default `#4F46E5` (indigo-600 HSL `243 75% 59%`) MUST NEVER appear.

### Step 2: Configure tailwind.config.ts
- Set `colors.primary`, `colors.accent` from `.brand/colors.json`
- Set `fontFamily.heading` and `fontFamily.body` from intake fonts (or BUSINESS_TYPE defaults)

### Step 3: Set up fonts in `src/lib/fonts.ts`
- Import the heading and body fonts from Google Fonts
- Match the tone from intake:
  - SERVICE_LOCAL + PROFESSIONAL_SERVICES → clean sans-serif (Inter, Nunito, Geist)
  - PROFESSIONAL_SERVICES → serif headings acceptable (Playfair Display, Lora)
  - SAAS_PRODUCT → modern sans-serif (Geist, Inter, DM Sans)

### Step 4: Write design approach to `.claude/CLAUDE.md`
Add a section confirming:
- BUSINESS_TYPE
- Background approach (light/dark)
- Whether phone prop is used (SERVICE_LOCAL and PROFESSIONAL_SERVICES → yes)
- Hero layout to use (SERVICE_LOCAL → `split-right` preferred, SAAS → `centered` ok)
- Animation style (SERVICE_LOCAL → fade-in only, SAAS → full creative allowed)
- The exact `--primary` and `--accent` HSL values that came from `.brand/colors.json`

### Step 5: Git commit
```bash
cd ~/Websites/<project> && git add -A && git commit -m "style: apply brand design system from logo + Stitch"
```

**Gate:** Run `grep -E "indigo|purple|violet|fuchsia|#4F46E5|243 7" ~/Websites/<project>/src/app/globals.css ~/Websites/<project>/tailwind.config.ts` — if ANY hits, fail this phase with the offending file:line.

**Update status:** `phases.design-system.status: "complete"`, `phases.design-system.message: "Design system configured (primary=<hex>, accent=<hex>)"`

---

## Phase 5: BUILD PAGES (sub-agent, ~5-10 minutes) — was Phase 4

**Update status:** `currentPhase: "build-pages"`, `phases.build-pages.status: "in_progress"`, `phases.build-pages.message: "Translating Stitch HTMLs to Next.js pages..."`

**Pre-conditions (verify BEFORE spawning the sub-agent — fail Phase 5 if missing):**
1. `~/Websites/<PROJECT>/.stitch-pages/structure.json` exists and lists every page in `intake.pages` AND `intake.stitchScreens[].name`-mapped slug. If a page is missing, fail with `"Phase 3 incomplete: page <name> has no Stitch HTML"`. Do NOT spawn the sub-agent.
2. `~/Websites/<PROJECT>/ai/page-map.json` exists (Phase 1.6 PAGE PLAN output) — assigns each page to a Stitch source screen + role + keywords.
3. `~/Websites/<PROJECT>/.brand/colors.json` exists.

**Spawn ONE sub-agent with this exact prompt (do not embellish, do not add boilerplate, do not include any "build a great website" guidance — every word below is load-bearing):**

```
sessions_spawn({
  task: "You translate Stitch HTML mockups into Next.js page.tsx files. You DO NOT design. You DO NOT add sections. You DO NOT remove sections. You preserve structure verbatim and only substitute copy.

INPUT (locked):
  ~/Websites/<PROJECT>/.stitch-pages/structure.json   — machine-parsed Stitch structure per page
  ~/Websites/<PROJECT>/.stitch-pages/<page>.html       — raw Stitch HTML per page (your blueprint)
  ~/Websites/<PROJECT>/ai/page-map.json                — page → stitch-source mapping + per-page keywords
  ~/Websites/<PROJECT>/ai/research/keywords.md         — DFS-backed keyword data
  ~/Websites/<PROJECT>/ai/research/faq-research.md     — researched FAQ Q&A
  ~/Websites/<PROJECT>/.brand/colors.json              — locked palette
  ~/Websites/<PROJECT>/.intake.json                    — business info, contact, socials, services, address

OUTPUT (locked):
  ~/Websites/<PROJECT>/src/app/<route>/page.tsx        — one file per page in page-map.json
  ~/Websites/<PROJECT>/src/components/sections/<...>.tsx — only if a Stitch section needs a new template; copy from /mnt/shared-skills/website-builder/templates/sections/ as the base

HARD RULES:
1. For each page in page-map.json, read its assigned <stitch_source>.html and structure.json[page] FIRST.
2. Build the page.tsx with EXACTLY the section count + section order from structure.json. No additions. No removals.
3. Hero H1 = the H1 from structure.json (you may insert the page's primary keyword if it fits naturally; otherwise verbatim).
4. Page <title> in metadata = '<H1> | <businessName>' — primary keyword MUST appear in title.
5. Section copy: replace Stitch's placeholder text with real copy derived from intake + keywords.md + faq-research.md. Section structure (headings, card count, layout) is FROZEN.
6. Forbidden imports/colors: no Tailwind palette classes from purple/indigo/violet/fuchsia families. No hex literals outside .brand/colors.json.
7. Logo + Navbar API: <Navbar businessName='...' logoSrc='/logo.png' phone='...' navItems={...} cta={...} /> — there is no 'logo' prop.
8. Image slots in Stitch: the corresponding <img> URL is captured in structure.json[page].images[]. Reference those by their public path that Phase 6 will populate (/images/<slot>.<ext>). DO NOT invent new image slots Stitch didn't have. DO NOT remove image slots Stitch did have.
9. Pages NOT in page-map.json may NOT be built. If intake.pages references a page that page-map.json doesn't, that's a Phase 1.6 bug — set phases.build-pages.status='failed' and HALT.
10. **SECTION COMPONENT ALLOWLIST**: `src/components/sections/` IS the allowlist. You may ONLY import section components that already exist in that directory. Run `ls src/components/sections/` FIRST. If a Stitch section type needs a component that doesn't exist (e.g. Stitch has a 'before-after' section but no BeforeAfter.tsx in sections/), COPY a similar canonical template from `/mnt/shared-skills/website-builder/templates/sections/<name>.tsx` to your project's `src/components/sections/<name>.tsx` AS THE BASE, then customize.
11. **FORBIDDEN imports for 1.A and 1.B builds**: TrustBar, Features, FeaturesBento, HowItWorks, Stats, Pricing, BlogList, ErrorPage, NotFound, ThemeToggle. These live in `/mnt/shared-skills/website-builder/templates/sections-fallback-1c/` and are ONLY for 1.C generate-from-controls builds. If you import any of these in a 1.A/1.B build, the build fails. Stitch did not call for them — do not invent them.
12. **No section additions, no section removals.** Per the structure.json sectionCount target. If Stitch has 5 sections, build 5. If 7, build 7. The number is fixed by the supplied design.
13. **INTERNAL-LINK SILO (if `ai/build-plan.json` exists — from the consumed Brand Report plan).** Read `ai/build-plan.json` → `interlink_map`. For every entry whose `from` matches the page you're building, add an internal `<Link href="/<to>">` using the entry's `anchor` text. Concentrate these in a **"Related Services & Areas"** section near the page bottom (one block, not stuffed inline): money pages link to the same service in nearby cities + other services in the same city + up to their pillar; supporting blog posts link up to their money page. This is the ranking lever — money pages must accumulate these inbound internal links. Every `href` must resolve to a real page in page-map.json (skip any that don't). This adds links, not new sections — it lives inside the page's existing footer/related area.

STANDARD INFRASTRUCTURE (build these once, NOT in any per-page section):
- src/app/layout.tsx: metadataBase=new URL('https://<intake.domain>'), JSON-LD per BUSINESS_TYPE (LocalBusiness for service-local; include address, telephone, openingHours, areaServed from intake), openGraph.images=[{url:'/og/default.png',width:1200,height:630}], icons={icon:'/favicon.ico',apple:'/apple-touch-icon.png'}
- src/app/sitemap.ts: emit one entry per page in page-map.json
- public/robots.txt: User-agent: * / Allow: / / Sitemap: https://<intake.domain>/sitemap.xml
- /privacy and /terms: minimal pages (not in page-map but must exist for legal/footer compliance)
- src/app/api/contact/route.ts: basic POST handler that accepts the contact form payload — must exist so the form does not 404. If intake.email is set, send via mailto fallback or log.

VERIFICATION (run before marking complete):
- pnpm tsc --noEmit  (must exit 0)
- python3 /mnt/shared-skills/website-builder/tools/stitch-fidelity-check.py ~/Websites/<PROJECT> --threshold 0.85 --strict
- python3 /mnt/shared-skills/website-builder/tools/color-allowlist-check.py ~/Websites/<PROJECT>

If any of those exit non-zero, set phases.build-pages.status='failed' with the failing report path in message. DO NOT mark complete.

When complete: phases.build-pages.status='complete', message='<N> pages translated from Stitch, fidelity ≥ 0.85'. Then end with: OUTPUT_SAVED: src/app/page.tsx",
  label: "website-pages-<project>"
})
```

**After sub-agent returns, host-side post-checks:**
```bash
PROJ=~/Websites/<project>
test -f "$PROJ/src/app/layout.tsx" || { echo "GATE FAIL: no layout.tsx"; exit 1; }
test -f "$PROJ/src/app/sitemap.ts" || { echo "GATE FAIL: no sitemap.ts"; exit 1; }
test -f "$PROJ/src/app/api/contact/route.ts" || { echo "GATE FAIL: no contact route"; exit 1; }
# every page in page-map.json must have a page.tsx
python3 -c "
import json,os,sys
m=json.load(open('$PROJ/ai/page-map.json'))
missing=[p for p in m['pages'] if not os.path.exists(f\"$PROJ/src/app/{('' if p['route']=='/' else p['route'].lstrip('/'))}/page.tsx\".replace('//','/'))]
if missing:
    print('GATE FAIL: missing page.tsx for:', [p['route'] for p in missing]); sys.exit(1)
print('OK: all', len(m['pages']), 'pages built')
"
```

---

## Phase 5.5: WRITE INTRO BLOG POST (sub-agent, ~2-3 minutes)

**Purpose:** Every JamBot site ships with a blog and at least ONE real intro post (policy from Phase 2 step 0). The `/blog` index was already designed by Stitch + built by Phase 5; this phase writes the actual first post and wires it in. A blog with zero posts is a 404 trap and dead SEO weight — never ship one.

**Update status:** `currentPhase: "blog-post"`, `phases.blog-post.status: "in_progress"`.

**Prereqs:** `~/Websites/<project>/.blog-seed.json` exists (Phase 2 wrote it) and `src/app/blog/page.tsx` exists (Phase 5 built the index). If `.blog-seed.json` is missing, regenerate it inline from research, do not skip.

Spawn a sub-agent:
```
task: "You are an SEO content writer. Project: ~/Websites/<PROJECT>.
1. Read .blog-seed.json (slug, title, business) and ai/research/{keywords,content-strategy,topical-map}.md.
2. Write ONE genuine intro blog post at src/app/blog/<slug>/page.tsx (a real Next.js App-Router route — NO MDX dependency):
   - export const metadata = { title, description } — title ≤ 60 chars incl. brand, description ≤ 155 chars, both keyword-rich from keywords.md.
   - 700–1000 words of REAL, specific, non-fluff copy about the topic, grounded in the research (use actual services, target markets, and 2–4 target keywords naturally — no keyword stuffing, no lorem, no fabricated stats/quotes).
   - Structure: H1 = post title, a 2–3 sentence intro, 3–5 H2 sections, a short closing. Use the SAME design-system components/classes the other built pages use (import the site's Section/Container/Button components; match the Stitch palette + type — do NOT introduce a new style).
   - Add JSON-LD (BlogPosting schema) via a <script type='application/ld+json'> with headline, datePublished (use the build date string passed in BUILD_DATE), author = business name, publisher = business name.
   - End with the standard conversion CTA (link to /contact + click-to-call the intake phone).
   - 2–3 internal links into the body pointing to real built routes (/services, a service page, /about).
3. Update the /blog index (src/app/blog/page.tsx): if it has Stitch placeholder post cards, make the FIRST card a real link to /blog/<slug> with the post title + a 1-line excerpt; remove/comment any other placeholder cards that link nowhere (no card may link to a 404).
4. Add the post route to src/app/sitemap.ts (one new entry: /blog/<slug>).
5. Do NOT run pnpm build (Phase 7 does the functional gate). End with: OUTPUT_SAVED: src/app/blog/<slug>/page.tsx",
  label: "blog-post-<project>"
```
Pass `BUILD_DATE` = today's UTC date (`date -u +%Y-%m-%d`) into the sub-agent prompt so the schema date is not fabricated.

**Host-side post-check:**
```bash
PROJ=~/Websites/<project>
SLUG=$(python3 -c "import json;print(json.load(open('$PROJ/.blog-seed.json'))['slug'])")
test -f "$PROJ/src/app/blog/$SLUG/page.tsx" || { echo "GATE FAIL: intro blog post not written"; exit 1; }
grep -q "blog/$SLUG" "$PROJ/src/app/blog/page.tsx" || echo "WARN: /blog index does not link the new post — sub-agent must fix before Phase 7"
grep -q "blog/$SLUG" "$PROJ/src/app/sitemap.ts" || echo "WARN: post route missing from sitemap.ts"
echo "OK: intro blog post at /blog/$SLUG"
```

**Mark complete:** `phases.blog-post.status: "complete"`, `message: "Intro post /blog/<slug> written + linked from index + sitemap"`.

---

## Phase 6: ASSETS (inline, ~3-4 minutes) — was Phase 5

**Update status:** `currentPhase: "assets"`, `phases.assets.status: "in_progress"`, `phases.assets.message: "Copying logo, generating favicons, generating brand images..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/images.md`

This phase ships the visual assets the site needs: (1) the actual logo file copied into `public/`, (2) favicons, (3) page imagery. Every asset is saved to disk — nothing is held in memory.

### IMAGE SOURCE PRIORITY (2026-06-01 — read first)
Fill each image slot from the FIRST available source, in this order:
1. **Supplied media (RULE 6)** — `intake.heroImage/teamImage/gallery[]` / logo. Always wins.
2. **Stitch's OWN images (primary for the Stitch design path).** Every `<img>` in the Stitch
   HTML is a public AIDA URL Stitch generated — **download it (keyless), appending `=w1600`** for
   full resolution → `public/images/`. Step 4 below already does this; it is the MAIN image source
   for Stitch-built sites. No image-gen API needed.
3. **HF z-image-turbo** — generate ONLY for genuinely empty slots (or the section-library
   fallback path where there are no Stitch images). Use `gr1_z_image_turbo_generate` (HF). Feed it
   the `<img data-alt="...">` prompt Stitch baked in, or a per-business-type prompt.
4. **Programmatic** — OG card + favicon via Next `ImageResponse` (no key needed).

**⚠️ DEPRECATED — do NOT use Gemini image-gen.** The `gemini-2.0-flash-exp-image-generation`
calls below are DEAD (quota 0 / stale model name, verified 2026-06-01). Treat every Gemini
`generateContent` image-gen block in this phase as **replaced by HF z-image-turbo**. Mike's
decision: image-gen stays on HF.

### Prerequisites
- An image generator for empty slots = **HF z-image-turbo** (`gr1_z_image_turbo_generate`). Gemini image-gen is dead — do not require `GEMINI_API_KEY`.
- Phase 5 (Build Pages) must be complete — we need to know which pages exist
- `.brand/logo.png` (or `.brand/logo.svg`) must exist from Phase 1.5

### Step 0: Logo + favicon (NEW — non-negotiable)

```bash
PROJECT_DIR=~/Websites/<project>
mkdir -p "$PROJECT_DIR/public"

# Copy logo as canonical /logo.png (Navbar.tsx references this path)
if [ -f "$PROJECT_DIR/.brand/logo.svg" ]; then
    cp "$PROJECT_DIR/.brand/logo.svg" "$PROJECT_DIR/public/logo.svg"
    # Also rasterize a PNG fallback for OG/social
    convert -background none -density 300 "$PROJECT_DIR/.brand/logo.svg" \
        -resize 512x -define png:color-type=6 "$PROJECT_DIR/public/logo.png"
elif [ -f "$PROJECT_DIR/.brand/logo.png" ]; then
    cp "$PROJECT_DIR/.brand/logo.png" "$PROJECT_DIR/public/logo.png"
else
    echo "GATE FAIL: no logo file in $PROJECT_DIR/.brand/"
    exit 1
fi

# Generate favicon set from logo (force white background for transparent logos)
SOURCE_FOR_ICONS="$PROJECT_DIR/public/logo.png"
convert "$SOURCE_FOR_ICONS" -background white -alpha remove -alpha off -resize 16x16   "$PROJECT_DIR/public/favicon-16x16.png"
convert "$SOURCE_FOR_ICONS" -background white -alpha remove -alpha off -resize 32x32   "$PROJECT_DIR/public/favicon-32x32.png"
convert "$SOURCE_FOR_ICONS" -background white -alpha remove -alpha off -resize 180x180 "$PROJECT_DIR/public/apple-touch-icon.png"
convert "$SOURCE_FOR_ICONS" -background white -alpha remove -alpha off -resize 192x192 "$PROJECT_DIR/public/icon-192.png"
convert "$SOURCE_FOR_ICONS" -background white -alpha remove -alpha off -resize 512x512 "$PROJECT_DIR/public/icon-512.png"
convert "$PROJECT_DIR/public/favicon-32x32.png" "$PROJECT_DIR/public/favicon.ico"

# Web app manifest
cat > "$PROJECT_DIR/public/site.webmanifest" <<EOF
{
  "name": "<businessName from intake>",
  "short_name": "<businessName from intake>",
  "icons": [
    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ],
  "theme_color": "<primary hex from .brand/colors.json>",
  "background_color": "#ffffff",
  "display": "standalone"
}
EOF

# Sanity gate: Navbar must reference Logo component
if ! grep -q '<Logo ' "$PROJECT_DIR/src/components/sections/Navbar.tsx" 2>/dev/null; then
    if ! grep -q 'logoSrc=' "$PROJECT_DIR/src/app/layout.tsx" 2>/dev/null; then
        echo "GATE FAIL: Navbar.tsx does not reference <Logo /> and layout.tsx doesn't pass logoSrc"
        exit 1
    fi
fi
```

### Step 1: Read intake for brand context
```bash
cat ~/Websites/<project>/.intake.json
cat ~/Websites/<project>/.claude/CLAUDE.md
```
Extract: business name, industry, niche, brand colors (primary, secondary, accent), tone, business type, and description. These drive every prompt.

### Step 2: Create image directories
```bash
mkdir -p ~/Websites/<project>/public/images
mkdir -p ~/Websites/<project>/public/og
```

### Step 2.5: SUPPLIED MEDIA WINS — install user-supplied assets FIRST

Per RULE 6: every image slot the user supplied via the canvas form is installed BEFORE any AI generation. AI generation only fills slots the user did NOT supply.

```bash
PROJECT_DIR=~/Websites/<project>
INTAKE="$PROJECT_DIR/.intake.json"

# 1. Hero image — intake.heroImage (URL)
HERO_URL=$(python3 -c "import json;print(json.load(open('$INTAKE')).get('heroImage') or '')")
if [ -n "$HERO_URL" ]; then
    if [[ "$HERO_URL" == http* ]]; then
        curl -fsSL "$HERO_URL" -o "$PROJECT_DIR/public/images/hero.jpg" && echo "hero: installed from intake.heroImage"
    elif [ -f "$HERO_URL" ]; then
        cp "$HERO_URL" "$PROJECT_DIR/public/images/hero.jpg" && echo "hero: installed from local intake.heroImage"
    fi
fi

# 2. Team image — intake.teamImage (URL, optional)
TEAM_URL=$(python3 -c "import json;print(json.load(open('$INTAKE')).get('teamImage') or '')")
if [ -n "$TEAM_URL" ] && [[ "$TEAM_URL" == http* ]]; then
    curl -fsSL "$TEAM_URL" -o "$PROJECT_DIR/public/images/team.jpg" && echo "team: installed"
fi

# 3. Gallery — intake.gallery[] (array of URLs / paths)
python3 <<'PYEOF'
import json, os, urllib.request, shutil
proj = os.path.expanduser('~/Websites/<project>')
intake = json.load(open(f"{proj}/.intake.json"))
gallery = intake.get('gallery') or []
if gallery:
    os.makedirs(f"{proj}/public/images/gallery", exist_ok=True)
    for i, item in enumerate(gallery):
        url = item if isinstance(item, str) else item.get('url') or item.get('src')
        if not url: continue
        ext = os.path.splitext(url)[1].split('?')[0] or '.jpg'
        dest = f"{proj}/public/images/gallery/g{i+1}{ext}"
        try:
            if url.startswith('http'):
                urllib.request.urlretrieve(url, dest)
            elif os.path.exists(url):
                shutil.copy(url, dest)
            print(f"gallery: g{i+1}{ext}")
        except Exception as e:
            print(f"gallery {i}: SKIP {e}")
PYEOF

# 4. Stitch-referenced images — every <img src="..."> in .stitch-pages/*.html
# Stitch designs reference image URLs (CDN). Download them as canonical
# /images/<slot>.<ext> so the built pages don't depend on Stitch's CDN at runtime.
python3 <<'PYEOF'
import json, os, re, urllib.request, glob, hashlib
proj = os.path.expanduser('~/Websites/<project>')
img_re = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']')
seen = set()
manifest = {}
for html_path in sorted(glob.glob(f"{proj}/.stitch-pages/*.html")):
    page = os.path.basename(html_path)[:-5]
    text = open(html_path).read()
    page_imgs = []
    for src in img_re.findall(text):
        if not src.startswith('http'): continue
        if src in seen: continue
        seen.add(src)
        h = hashlib.md5(src.encode()).hexdigest()[:8]
        ext = os.path.splitext(src.split('?')[0])[1] or '.jpg'
        dest_name = f"stitch-{page}-{h}{ext}"
        dest = f"{proj}/public/images/{dest_name}"
        # AIDA/googleusercontent URLs serve a downscaled preview by default — append
        # =w1600 for full resolution (the bare URL is ~40x512). See stitch skill.
        dl = src
        if 'googleusercontent.com/aida' in src and '=w' not in src.split('/')[-1]:
            dl = src + '=w1600'
        try:
            urllib.request.urlretrieve(dl, dest)
            page_imgs.append({'original': src, 'local': f'/images/{dest_name}'})
        except Exception as e:
            print(f"stitch-img {page}: SKIP {src[:60]}... ({e})")
    if page_imgs:
        manifest[page] = page_imgs
        print(f"stitch-img {page}: downloaded {len(page_imgs)}")

if manifest:
    open(f"{proj}/.stitch-pages/image-manifest.json", 'w').write(json.dumps(manifest, indent=2))
PYEOF

# At this point public/images/ contains: hero.jpg (if supplied), team.jpg (if supplied),
# gallery/g*.{jpg,png,webp} (if supplied), stitch-<page>-<hash>.{jpg,png} (Stitch CDN images downloaded)
ls -la "$PROJECT_DIR/public/images/" 2>/dev/null
```

**After Step 2.5, AI generation in Steps 3-5 only fills slots that are still empty:**
- If `public/images/hero.jpg` exists from supplied media → SKIP Step 3 (Hero generation)
- If `public/images/team.jpg` exists → SKIP team generation
- For service-detail icon images: only generate if no Stitch image was downloaded for that page

### Step 3: Generate Hero Image (SKIP if supplied)

**For SERVICE_LOCAL** — a realistic industry photo:
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Professional photograph of <INDUSTRY> work in progress, <DESCRIPTION>, clean modern composition, natural lighting, warm tones with <PRIMARY_COLOR> accent elements, high quality, photorealistic, 16:9 aspect ratio, no text or watermarks"}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for p in d['candidates'][0]['content']['parts']:
    if 'inlineData' in p:
        with open('$HOME/Websites/<project>/public/images/hero.png', 'wb') as f:
            f.write(base64.b64decode(p['inlineData']['data']))
        print('Hero image saved')
    elif 'text' in p:
        print(p['text'])
"
```

**For SAAS_PRODUCT** — abstract tech visualization:
```
Professional abstract technology visualization, dark background with <PRIMARY_COLOR> and <ACCENT_COLOR> glowing elements, modern SaaS product aesthetic, clean geometric shapes, subtle grid pattern, high quality, 16:9 aspect ratio, no text or watermarks
```

**For PROFESSIONAL_SERVICES** — clean corporate:
```
Professional corporate photography, modern office environment, <INDUSTRY> consulting aesthetic, clean composition, neutral tones with <PRIMARY_COLOR> accents, high quality, photorealistic, 16:9 aspect ratio, no text or watermarks
```

**Update status message:** `phases.assets.message: "Hero image generated, creating OG image..."`

### Step 4: Generate OG Image (Social Sharing Card)

Generate a 1200x630 social card with the business name:
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Social media sharing card, 1200x630 pixels, dark <PRIMARY_COLOR> gradient background, the text \"<BUSINESS_NAME>\" in large bold white font centered, \"<TAGLINE_OR_DESCRIPTION>\" in smaller text below, clean modern professional design, no stock photos, graphic design only"}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for p in d['candidates'][0]['content']['parts']:
    if 'inlineData' in p:
        with open('$HOME/Websites/<project>/public/og/default.png', 'wb') as f:
            f.write(base64.b64decode(p['inlineData']['data']))
        print('OG image saved')
"
```

### Step 5: Generate Favicon / App Icon

Generate a simple monogram or icon:
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Simple minimal app icon, the letter \"<FIRST_LETTER>\" on a <PRIMARY_COLOR> background, bold modern sans-serif font, square format, flat design, suitable for favicon, no gradients, no 3D effects, clean edges"}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for p in d['candidates'][0]['content']['parts']:
    if 'inlineData' in p:
        with open('$HOME/Websites/<project>/public/images/icon.png', 'wb') as f:
            f.write(base64.b64decode(p['inlineData']['data']))
        print('Icon saved')
"
```

Then convert to favicon formats:
```bash
cd ~/Websites/<project>/public
# Create favicon.ico (32x32) and apple-touch-icon (180x180) from the generated icon
python3 -c "
from PIL import Image
import io
img = Image.open('images/icon.png')
# Favicon
ico = img.resize((32, 32), Image.LANCZOS)
ico.save('favicon.ico', format='ICO', sizes=[(32, 32)])
# Apple touch icon
apple = img.resize((180, 180), Image.LANCZOS)
apple.save('apple-touch-icon.png', format='PNG')
print('Favicon and apple-touch-icon created')
" 2>/dev/null || echo "PIL not available — keeping icon.png as fallback, Next.js icon.tsx handles favicon"
```

If PIL is not available, create a Next.js `src/app/icon.tsx` that uses ImageResponse to render the monogram programmatically (see `images.md` Favicon Generation section).

**Update status message:** `phases.assets.message: "Favicon created, generating service images..."`

### Step 6: Generate Service/Section Images (SERVICE_LOCAL and PROFESSIONAL_SERVICES only)

For each major service listed in the intake, generate one image:
```bash
# Repeat for each service — max 4 images to stay within rate limits
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "Professional photograph of <SERVICE_NAME> work, <INDUSTRY> business, clean modern composition, natural lighting, warm professional tones, high quality, photorealistic, 4:3 aspect ratio, no text or watermarks"}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for p in d['candidates'][0]['content']['parts']:
    if 'inlineData' in p:
        with open('$HOME/Websites/<project>/public/images/<service-slug>.png', 'wb') as f:
            f.write(base64.b64decode(p['inlineData']['data']))
        print('<SERVICE_NAME> image saved')
"
```

**Rate limit awareness:** Gemini free tier allows ~15 requests/minute. If generating 4+ service images, add a 5-second sleep between calls:
```bash
sleep 5
```

If any Gemini call returns 429 (rate limited), wait 60 seconds and retry once. If it fails again, skip that image and note it in the status message.

### Step 7: Wire images into components

After all images are generated, update the page components to use them:

**Hero component** — update the hero on the home page:
```tsx
// In src/app/page.tsx, update the Hero component props:
heroImage="/images/hero.png"
```

**OG metadata** — should already point to `/og/default.png` from Phase 4. Verify:
```bash
grep 'og/default.png' ~/Websites/<project>/src/app/layout.tsx || echo "⚠️ OG image not referenced in layout.tsx — add it"
```

**Service pages** — for each service page that has a generated image:
```tsx
// Add to the service page's hero or header section:
<Image src="/images/<service-slug>.png" alt="<Service Name>" width={800} height={600} className="rounded-lg" />
```

**Favicon** — verify layout.tsx references it:
```bash
grep 'favicon' ~/Websites/<project>/src/app/layout.tsx || echo "⚠️ Favicon not referenced — add icons metadata"
```

### Step 8: Verify and commit

```bash
cd ~/Websites/<project>
echo "=== Generated images ==="
ls -lh public/images/ public/og/ 2>/dev/null
echo "=== Image references in code ==="
grep -rn 'images/hero\|images/icon\|og/default\|favicon' src/ --include='*.tsx' --include='*.ts' | head -20
```

Verify at least these exist:
- `public/images/hero.png` — hero background/photo
- `public/og/default.png` — social sharing card
- `public/favicon.ico` OR `src/app/icon.tsx` — favicon

```bash
cd ~/Websites/<project> && git add -A && git commit -m "feat: generate brand images — hero, OG card, favicon, service photos"
```

**Update status:** `phases.assets.status: "complete"`, `phases.assets.message: "X images generated and wired into pages"`

### Error Handling

- **Gemini 429 (rate limit):** Wait 60s, retry once. If still 429, skip that image and continue. Note skipped images in the status message.
- **Gemini 400 (bad prompt):** Simplify the prompt — remove specific color references and retry with a more generic description.
- **No GEMINI_API_KEY:** Skip image generation entirely. Create a Next.js `opengraph-image.tsx` and `icon.tsx` using ImageResponse as fallback (these don't need an API key). Update status message: "Image generation skipped — no API key. Using programmatic OG image and favicon."
- **PIL not available for favicon conversion:** Create `src/app/icon.tsx` with Next.js ImageResponse instead. This is equally valid.

### Images NOT to generate

- **Testimonial avatars** — never generate fake person photos. Use initials or Lucide icons.
- **Client logos** — the client provides their own logo. If `hasLogo` is "no" in intake, generate a text-based logo using the monogram from Step 5.
- **Stock photography of people** — AI-generated people look uncanny. Use abstract/environmental photos instead.

---

## Phase 7: QUALITY GATE (inline, ~3-5 minutes, FUNCTIONAL) — was Phase 6

**Update status:** `currentPhase: "quality-gate"`, `phases.quality-gate.status: "in_progress"`, `phases.quality-gate.message: "Running functional quality gates..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/quality-checklist.md`

**Read the BUSINESS_TYPE** from `.claude/CLAUDE.md` before running type-specific checks.

**This phase has TWO halves:** (A) FUNCTIONAL gates that produce JSON reports under `.quality-gate/`, and (B) static sweeps for content rules. Both must pass — A first because it catches the show-stoppers (broken build, 500 errors, forbidden colors). The build halts at the first hard failure.

### A1. Production build inside the webdev container (NOT in openclaw)

```bash
PROJECT=<project>
CLIENT=$(echo $HOSTNAME | sed 's/openclaw-//')
WEBDEV_CONTAINER="webdev-${CLIENT}"  # may have a -1 suffix; verify with docker ps from host

# Build is run from outside the openclaw container — the watcher invokes:
#   docker exec $WEBDEV_CONTAINER sh -c "cd /app/websites/$PROJECT && pnpm build 2>&1 | tail -40"
# Exit non-zero on any compilation error or RSC boundary violation.
# Inside this skill, write the gate-report stub and let the watcher fill it:
mkdir -p ~/Websites/$PROJECT/.quality-gate
echo '{"build": "pending — webdev container will run pnpm build"}' > ~/Websites/$PROJECT/.quality-gate/build.json
```

NOTE for the watcher: After Phase 7 hands off, the watcher MUST run `docker exec $WEBDEV_CONTAINER pnpm build` and write `.quality-gate/build.json` with `{success: bool, errors: [...]}`. If success=false, mark `phases.quality-gate.status='failed'` and HALT.

### A2. HTTP 200 check on every sitemap URL

```bash
PROJECT_DIR=~/Websites/$PROJECT
mkdir -p "$PROJECT_DIR/.quality-gate"

# Read sitemap routes (sitemap.ts exports an array; we extract paths via a Node one-liner OR fall back to a glob of src/app/**/page.tsx)
URLS_FILE="$PROJECT_DIR/.quality-gate/urls.txt"
find "$PROJECT_DIR/src/app" -name 'page.tsx' -not -path '*/api/*' | \
    sed -E "s|$PROJECT_DIR/src/app||; s|/page.tsx||; s|^$|/|" | sort -u > "$URLS_FILE"
echo "Routes to verify:"; cat "$URLS_FILE"

# The webdev container serves from http://localhost:3000 inside its network.
# The watcher hits the host port. Inside openclaw, we ask the watcher to populate this report.
echo '{"urls": "pending — webdev container will curl each route after pnpm start"}' > "$PROJECT_DIR/.quality-gate/urls.json"
```

NOTE for the watcher: After A1 succeeds, run `docker exec $WEBDEV_CONTAINER sh -c "cd /app/websites/$PROJECT && pnpm start &"`, then for each line in `urls.txt`, `curl -s -o /dev/null -w '%{http_code}\n'` against the host port. Write `.quality-gate/urls.json` with `[{url, status}]`. If ANY status != 200, fail this phase.

### A3. Color allowlist (no purple, no indigo)

```bash
python3 /mnt/shared-skills/website-builder/tools/color-allowlist-check.py "$PROJECT_DIR"
```

If exit non-zero, set `phases.quality-gate.status='failed'` with `message="forbidden colors at $(jq -r '.violations[0].file + \":\" + (.violations[0].line|tostring)' $PROJECT_DIR/.quality-gate/color-allowlist.json)"` and HALT.

### A4. Stitch fidelity gate

```bash
python3 /mnt/shared-skills/website-builder/tools/stitch-fidelity-check.py "$PROJECT_DIR" --threshold 0.85
```

If exit non-zero, set `phases.quality-gate.status='failed'` with the report path in `message` and HALT. Phase 5 was supposed to enforce this — if it failed here, Phase 5 lied about completion.

### A5. Logo + favicon presence

```bash
[ -f "$PROJECT_DIR/public/logo.png" -o -f "$PROJECT_DIR/public/logo.svg" ] || { echo "GATE FAIL: missing /logo.{png,svg}"; exit 1; }
[ -f "$PROJECT_DIR/public/favicon.ico" -o -f "$PROJECT_DIR/src/app/icon.tsx" ] || { echo "GATE FAIL: missing favicon"; exit 1; }
grep -q '<Logo ' "$PROJECT_DIR/src/components/sections/Navbar.tsx" || \
    grep -q 'logoSrc=' "$PROJECT_DIR/src/app/layout.tsx" || \
    { echo "GATE FAIL: Navbar does not reference <Logo /> and layout doesn't pass logoSrc"; exit 1; }
```

### A6. Visual Quality Officer gate (rendered-DOM — the part HTTP can't see)

This is the gate that catches **light-on-light / dark-on-dark text, invisible buttons, mobile overflow (squished content), and broken/missing images** — the failures that pass every check above and still look broken to a human. It renders each route in headless Chromium at mobile + desktop and checks computed styles.

**Playwright + Chromium live on the HOST, not in this build container** (same as A1's `pnpm build` and A2's URL curls). So you **request** the gate and the host build-watchdog runs it against the serving site, then stamps the result back. Pattern is identical to `githubPush`.

```bash
# The webdev container is already serving this project at .devUrl (Phase 6 made it
# the active project). Request the visual gate by flagging .build-status.json.
python3 - "$PROJECT_DIR" <<'PY'
import json, sys
sf = sys.argv[1] + "/.build-status.json"
d = json.load(open(sf))
d["visualGate"] = {"status": "requested", "viewports": "390,1440"}  # routes auto-resolve from .quality-gate/urls.txt
json.dump(d, open(sf, "w"), indent=2)
print("visualGate.status=requested — host watchdog will run visual-check.py")
PY
```

NOTE for the host: `jambot-build-watchdog.sh` detects `visualGate.status=="requested"` and runs `tools/visual-gate.sh "$project_dir"` (resolves the URL from `.devUrl`, routes from `.quality-gate/urls.txt`, viewports 390/1440), writes `.quality-gate/visual/visual-review.json` + full-page screenshots, and stamps `visualGate.status` back to `pass` or `fail` with `top_findings`.

**LOOP-BACK ON FAIL (do not ship a visual fail):** after requesting, poll `.build-status.json` until `visualGate.status` is `pass` or `fail`.
- `pass` → proceed to section B.
- `fail` → read `.quality-gate/visual/visual-review.json`, FIX each finding (raise contrast to ≥4.5:1 / ≥3:1 large; kill the horizontal overflow so the page fits 390px; replace the broken `<img>`; fill the empty section), re-run the relevant build step, set `visualGate.status="requested"` again, and re-poll. **Loop until `pass`.** A `fail` left unresolved means the build is NOT done — never advance to deploy/report-done on a visual fail.

---

### B (legacy, content sweeps — run after A1-A6 ALL pass)

### 0. Image asset check (run FIRST):
```bash
echo "=== Image assets ===" && \
[ -f ~/Websites/<project>/public/images/hero.png ] && echo "✓ Hero image" || echo "✗ Hero image MISSING — run Phase 5 asset generation" && \
[ -f ~/Websites/<project>/public/og/default.png ] && echo "✓ OG image" || echo "✗ OG image MISSING" && \
([ -f ~/Websites/<project>/public/favicon.ico ] || [ -f ~/Websites/<project>/src/app/icon.tsx ]) && echo "✓ Favicon" || echo "✗ Favicon MISSING" && \
grep -rn 'heroImage\|images/hero' ~/Websites/<project>/src/app/page.tsx > /dev/null 2>&1 && echo "✓ Hero image wired into page" || echo "✗ Hero image NOT referenced in home page"
```
If hero image exists but is not wired into the Hero component, add `heroImage="/images/hero.png"` to the Hero props in `src/app/page.tsx`.

### 1. Placeholder / Template sweep:
```bash
cd ~/Websites/<project> && grep -rn 'example\.com\|placeholder\|TODO\|FIXME\|Lorem\|project-name\|Your Headline\|000-0000\|hello@example\|Service One\|UPDATE:\|acme\|Acme\|REPLACE:' src/ --include='*.tsx' --include='*.ts' || echo "CLEAN"
```
Fix any matches — replace with real content from intake/research.

### 2. Fake testimonial check:
```bash
cd ~/Websites/<project> && grep -rn 'Alex Chen\|Sarah Martinez\|David Kim\|John Smith\|Jane Doe\|Michael Johnson\|Emily Wilson\|Chris Taylor' src/ --include='*.tsx' || echo "CLEAN"
```
If ANY match found — remove the testimonials section entirely and replace with a UseCases or HowItWorks section. Do not substitute different fake names.

### 3. Broken external link check:
```bash
cd ~/Websites/<project> && grep -rn 'github\.com/openvoiceui\|github\.com/acme\|twitter\.com/example\|linkedin\.com/example' src/ --include='*.tsx' || echo "CLEAN"
```
All external links must come from intake. Fix any placeholder URLs.

### 4. Required files check:
```bash
echo "=== Checking required files ===" && \
[ -f ~/Websites/<project>/src/app/privacy/page.tsx ] && echo "✓ /privacy" || echo "✗ /privacy MISSING" && \
[ -f ~/Websites/<project>/src/app/terms/page.tsx ] && echo "✓ /terms" || echo "✗ /terms MISSING" && \
[ -f ~/Websites/<project>/public/robots.txt ] && echo "✓ robots.txt" || echo "✗ robots.txt MISSING" && \
[ -f ~/Websites/<project>/src/app/sitemap.ts ] && echo "✓ sitemap.ts" || echo "✗ sitemap.ts MISSING" && \
[ -f ~/Websites/<project>/public/og/default.png ] || [ -f ~/Websites/<project>/src/app/opengraph-image.tsx ] && echo "✓ OG image" || echo "✗ OG image MISSING" && \
[ -f ~/Websites/<project>/public/favicon.ico ] || [ -f ~/Websites/<project>/src/app/icon.tsx ] && echo "✓ Favicon" || echo "✗ Favicon MISSING"
```
Create any missing files before proceeding.

### 5. Per-page metadata check:
```bash
cd ~/Websites/<project> && grep -rL 'export const metadata' src/app/*/page.tsx 2>/dev/null || echo "All pages have metadata"
```
Any page missing a `metadata` export — add one with a unique title and description.

### 6. metadataBase check:
```bash
cd ~/Websites/<project> && grep 'metadataBase' src/app/layout.tsx | grep -v 'localhost\|dev-test-dev\|jam-bot' || echo "CHECK metadataBase manually"
```
Must point to the intake domain, not the dev server.

### 7. Contact form API route check:
```bash
[ -f ~/Websites/<project>/src/app/api/contact/route.ts ] && echo "✓ /api/contact exists" || echo "✗ /api/contact MISSING — contact form will 404"
```
If missing, create a basic route handler.

### 8. Navbar business name check:
```bash
cd ~/Websites/<project> && grep -n 'logo=' src/app/*/page.tsx src/app/page.tsx 2>/dev/null | grep -v "$(cat ~/Websites/<project>/.intake.json | python3 -c 'import json,sys; print(json.load(sys.stdin)["businessName"])')" | head -5 || echo "✓ Business name looks correct"
```

### 9. Footer real contact info check:
Verify footer includes at least one of: phone, email, or address from intake.

### 10. Pricing reality check:
```bash
cd ~/Websites/<project> && grep -n 'Start.*Trial\|Contact Sales\|Buy Now\|Subscribe' src/app/pricing/page.tsx 2>/dev/null | head -5
```
If paid tier CTAs exist, verify they either link to a real payment URL from intake or are marked Coming Soon.

### 11. SERVICE_LOCAL specific checks (run ONLY if BUSINESS_TYPE is SERVICE_LOCAL):

```bash
# Phone in Navbar check
grep -n 'phone=' ~/Websites/<project>/src/app/page.tsx | grep "Navbar" && echo "✓ Phone in Navbar" || echo "⚠️  Phone missing from Navbar — add phone prop to <Navbar>"

# Phone in Hero check
grep -n 'phone=' ~/Websites/<project>/src/app/page.tsx | grep "Hero" && echo "✓ Phone in Hero" || echo "⚠️  Phone missing from Hero — add phone prop to <Hero>"

# White background check
grep 'background:' ~/Websites/<project>/src/app/globals.css | grep -E '0 0% 100%|100%' && echo "✓ White background confirmed" || echo "⚠️  Background may not be white — SERVICE_LOCAL MUST use light backgrounds"

# Section count check — ONLY enforced when TIER 1 = generate (no Stitch)
TIER1=$(python3 -c "import json;d=json.load(open(\"$HOME/Websites/<project>/.intake.json\"));print('stitch' if d.get('stitchScreens') else ('template' if d.get('designTemplate') else 'generate'))")
if [ "$TIER1" = "generate" ]; then
    section_count=$(grep -c '<section' ~/Websites/<project>/src/app/page.tsx 2>/dev/null || echo 0)
    echo "Sections on home page (1.C): $section_count"
    [ "$section_count" -lt 7 ] && echo "⚠️  1.C SERVICE_LOCAL requires 8+ sections on home page — current: $section_count" || echo "✓ Section count OK (1.C)"
else
    # 1.A/1.B → section count comes from supplied Stitch / template; check fidelity instead (already done)
    echo "✓ Section count: deferring to Stitch fidelity check (TIER 1 = $TIER1, supplied design has authority)"
fi

# Floating orbs check
grep -rn 'blur-\[100px\]\|floating.*orb\|animate.*float\|w-\[500px\].*rounded-full\|w-\[400px\].*rounded-full' ~/Websites/<project>/src/components/ --include='*.tsx' 2>/dev/null && echo "⚠️  Floating orb pattern found — REMOVE for SERVICE_LOCAL" || echo "✓ No floating orbs"

# Dark background check
grep -rn 'bg-gray-900\|bg-slate-900\|bg-zinc-900\|bg-neutral-900\|bg-black' ~/Websites/<project>/src/app/page.tsx 2>/dev/null && echo "⚠️  Dark background class found in home page — SERVICE_LOCAL must use light backgrounds" || echo "✓ No hardcoded dark backgrounds"

# Hero layout check
grep -n 'layout=' ~/Websites/<project>/src/app/page.tsx | grep "Hero" && echo "✓ Hero has layout prop" || echo "⚠️  Hero missing layout prop — SERVICE_LOCAL should use layout='split-right'"

# TrustBar check
grep -n 'TrustBar\|trust-bar\|trust_bar' ~/Websites/<project>/src/app/page.tsx 2>/dev/null && echo "✓ TrustBar found" || echo "⚠️  TrustBar missing — SERVICE_LOCAL needs trust signals below hero"

# CTA section phone check
grep -A 20 'CTA\|cta' ~/Websites/<project>/src/app/page.tsx | grep -i 'phone\|tel:' && echo "✓ Phone in CTA section" || echo "⚠️  Phone missing from CTA section"
```

Fix any warnings from these checks before proceeding.

### 12. Final type-check (do NOT run pnpm build — webdev container handles compilation):
```bash
cd ~/Websites/<project> && pnpm tsc --noEmit 2>&1 | head -30 || echo "Type errors found — fix before proceeding"
```

### 13. Commit fixes:
```bash
cd ~/Websites/<project> && git add -A && git commit -m "fix: quality gate cleanup" || echo "Nothing to commit"
```

**Update status:** `phases.quality-gate.status: "complete"`, `phases.quality-gate.message: "All quality checks passed"`

---

## Phase 8: DEPLOY (exec, ~60 seconds) — was Phase 7

**Update status:** `currentPhase: "deploy"`, `phases.deploy.status: "in_progress"`, `phases.deploy.message: "Reconciling webdev container env, recreating service..."`

**Why this phase changed:** Writing `~/Websites/.active-project` alone does NOT switch the webdev container — the compose env var `WEBDEV_PROJECT_NAME` always wins. Phase 8 now calls `webdev-deploy.sh` which rewrites compose, ensures `.env.local`, recreates the container, and HTTP 200-checks before marking complete.

1. **Type-check only (do NOT run pnpm build):**
```bash
cd ~/Websites/<project> && pnpm tsc --noEmit 2>&1 | head -30
```
Fix any TypeScript errors. The webdev container handles compilation — you do not need a clean build here.

2. **Remove any stale `.next` directory** (partial builds cause `routes-manifest.json` errors in dev mode):
```bash
[ -d ~/Websites/<project>/.next ] && mv ~/Websites/<project>/.next ~/Websites/<project>/.next.bak || true
```

2.5. **Snapshot the intake into the project repo** (per RULE 9 — the design brief lives with the code so future Mike + future agents know what was originally requested):
```bash
PROJ=~/Websites/<project>
mkdir -p "$PROJ/docs"
cp "$PROJ/.intake.json" "$PROJ/docs/website-intake-snapshot.json"
# Also produce a human-readable summary
python3 <<'PYEOF' > "$PROJ/docs/website-intake-summary.md"
import json, os
d = json.load(open(os.path.expanduser("~/Websites/<project>/.intake.json")))
def f(k, default=""): return d.get(k) or default
print(f"# {f('businessName')} — Build Brief")
print(f"\n**Project slug:** `{f('projectName')}`  ")
print(f"**Domain:** {f('domain')}  ")
print(f"**Industry:** {f('industry')}  ")
print(f"**Owner:** {f('ownerName')}  ")
print(f"**Phone:** {f('phone')}  ")
print(f"**Email:** {f('email')}  ")
print(f"**Address:** {f('address')}  ")
print(f"**Hours:** {f('hours')}  ")
print(f"**Years in business:** {f('yearsInBusiness')}  ")
print(f"**License:** {f('license')}  ")
print(f"**Geographic scope:** {f('geographicScope')}  ")
print(f"\n## Description\n{f('description')}\n")
print(f"## About\n{f('about')}\n")
print(f"## Services\n" + "\n".join(f"- {s}" for s in (d.get('services') or [])))
print(f"\n## Target markets\n" + "\n".join(f"- {m}" for m in (d.get('targetMarkets') or [])))
print(f"\n## Pages\n" + "\n".join(f"- {p}" for p in (d.get('pages') or [])))
print(f"\n## Primary keywords (intake-supplied; see ai/research/keywords.md for DFS data)\n" + "\n".join(f"- {k}" for k in (d.get('primaryKeywords') or [])))
print(f"\n## Competitors\n" + "\n".join(f"- {c}" for c in (d.get('competitors') or [])))
print(f"\n## Selling points\n" + "\n".join(f"- {p}" for p in (d.get('sellingPoints') or [])))
print(f"\n## Stitch design source\n")
print(f"- Project title: {f('stitchProjectTitle')}")
ss = d.get('stitchScreens') or []
if ss:
    print(f"- Screens supplied ({len(ss)}):")
    for s in ss:
        print(f"  - {s.get('name')} (id `{s.get('id')}`)")
else:
    print("- (none — generated from brand controls)")
print(f"\n## Notes\n{f('notes')}\n")
PYEOF
cd "$PROJ" && git add docs/ && git commit -m "docs: snapshot website-setup intake into repo" || echo "(nothing to commit in docs/)"
```

3. **Set active project AND run the host-side deploy reconciliation.**

   The `~/Websites/.active-project` file is still written so the watcher can detect the change, BUT the actual reconciliation happens via the watcher invoking the host-side script:
   ```bash
   echo "<project>" > ~/Websites/.active-project
   ```
   The watcher (running on the host) sees the change and runs:
   ```bash
   bash /mnt/system/base/skills/website-builder/tools/webdev-deploy.sh <client> <project>
   ```
   That script: backs up compose, rewrites `WEBDEV_PROJECT_NAME` and `env_file` to point at the new project, ensures `.env.local` exists, runs `docker compose up -d --no-deps webdev`, waits for HTTP 200 (60s timeout), optionally verifies the page title contains the business name. Exit 0 = success, exit 1 = rollback to previous compose.

4. **Verify the active project file was written:**
```bash
cat ~/Websites/.active-project
```
Should output: `<project>`

5. **Wait for the watcher's deploy report.** The watcher writes `.quality-gate/deploy.json` with `{success: bool, hostPort: int, finalUrl: str}`. Read it:
```bash
cat ~/Websites/<project>/.quality-gate/deploy.json
```
If `success: false`, set `phases.deploy.status='failed'` with the watcher's error message and HALT.

6. **Update final status:**

Read the current status file, then write:
```json
{
  "status": "complete",
  "completedAt": "<current ISO timestamp>",
  "currentPhase": "deploy",
  "phases": { "deploy": { "status": "complete", "message": "Live at <devUrl from deploy.json> — webdev container reconciled" } }
}
```

7. **Tell the user:**
"Your website is live! The webdev container has been reconciled to the new project. Check it here: [CANVAS_URL:<devUrl from deploy.json>]

**Pages built:**
- List every page that was created (Home, About, Services, individual service pages, Contact, Privacy, Terms, etc.)

**Business type detected:** [SERVICE_LOCAL / SAAS_PRODUCT / PROFESSIONAL_SERVICES / etc.]

**Client action items before going live:**
- [ ] Review all content for accuracy — especially years in business, certifications, service descriptions
- [ ] Add real customer testimonials (or confirm the social proof section)
- [ ] Verify all stats and numbers match reality
- [ ] Set up contact email and test the contact form
- [ ] Review Privacy Policy and Terms of Service for accuracy
- [ ] Replace AI-generated images with real business photos when available (hero, team, services)
- [ ] Verify phone number and business hours in header, hero, CTA, and footer"

---

## Phase 8.5: GITHUB PUSH (exec, ~30 seconds) — host-assisted, AUTOMATIC

**Purpose:** Per RULE 10, the build is not complete until the code is on GitHub — durable, reviewable, recoverable.

**Why this phase only COMMITS + FLAGS (does not push directly):** the build runs *inside* the openclaw container, which has **no GitHub auth**. `gh` is authed on the **host** as `MCERQUA`. So the container commits locally and raises a flag; the host (`jambot-build-watchdog.sh`, cron) detects the flag and runs `scripts/jambot-website-github-push.sh <tenant> <project>`, which creates the private repo (if needed) and pushes `HEAD → main` via a token URL. The flag-then-host-push design means the push naturally captures the FINAL committed state — including any Phase 9 verification fixes and Phase 9.5 SEO-review fixes committed after this phase.

**Step 1 — Configure git identity + commit everything (idempotent):**
```bash
cd ~/Websites/<project>
git config user.email "agent@$(hostname).jam-bot.com"
git config user.name "JamBot Build Agent"
git add -A
git commit -m "feat: build <project> — pages, blog, assets, SEO" 2>/dev/null || echo "nothing new to commit"
```

**Step 2 — Raise the push-request flag** in `.build-status.json` so the host watchdog picks it up:
```bash
python3 - <<'PY'
import json, os
f = os.path.expanduser('~/Websites/<project>/.build-status.json')
d = json.load(open(f)) if os.path.exists(f) else {}
d['githubPush'] = {"status": "requested", "org": "MCERQUA"}
json.dump(d, open(f, 'w'), indent=2)
print("githubPush: requested — host watchdog will push HEAD->main")
PY
```

**Do NOT run `gh` or `git push` from inside the container — it has no auth and will fail the gate.**

**Mark this phase:** `phases.github-push.status: "requested"`, `message: "Committed locally; host will push to github.com/MCERQUA/<project>"`. (The watchdog flips `githubPush.status` to `pushed` with the SHA once the host push completes — within one watchdog cycle. A later interaction can read `.build-status.json -> githubPush` to confirm the live repo URL + SHA.)

> **Manual / immediate push** (host operator, e.g. to push right after a watched build instead of waiting for the cron cycle): `bash /home/mike/MIKE-AI/scripts/jambot-website-github-push.sh <tenant> <project>`.

---

## Phase 9: VERIFICATION (inline checklist, ~2 minutes) — was Phase 8

**This is the gatekeeper. Nothing is "done" until every check passes.**

**Update status:** `currentPhase: "verification"`, add `"verification": { "status": "in_progress", "message": "Running final HTTP + content verification..." }` to `phases`.

### A. Inline HTTP checklist (run from openclaw — uses curl against the deployed dev URL)

Read the deployed URL from `.quality-gate/deploy.json` (Phase 8 wrote it):
```bash
DEV_URL=$(python3 -c "import json; print(json.load(open('$HOME/Websites/<project>/.quality-gate/deploy.json'))['finalUrl'])")
BUSINESS_NAME=$(python3 -c "import json; print(json.load(open('$HOME/Websites/<project>/.intake.json'))['businessName'])")
PRIMARY_HEX=$(python3 -c "import json; print(json.load(open('$HOME/Websites/<project>/.brand/colors.json'))['primary'])")
```

Run each step in sequence; halt on first failure:

| Step | Check | How |
|------|-------|-----|
| 1 | Home page returns 200 with business name in title | `curl -fsSL "$DEV_URL/" \| grep -qi "<title>.*$BUSINESS_NAME" \|\| { echo "FAIL: title missing business name"; exit 1; }` |
| 2 | Every sitemap URL returns 200 | for each line in `.quality-gate/urls.txt`: `curl -sS -o /dev/null -w '%{http_code}' "$DEV_URL$line"` must be 200 |
| 3 | `/logo.png` (or `/logo.svg`) returns image | `curl -sS -o /dev/null -w '%{content_type}' "$DEV_URL/logo.png"` must start with `image/` |
| 4 | `/favicon.ico` returns image | same pattern |
| 5 | Section count fidelity | parse home page rendered HTML, count `<section>`, compare to `.stitch-pages/structure.json → home.sectionCount` (within ±1) |
| 6 | Render-time forbidden colors | download home page HTML + CSS, scan for `#4F46E5`, `oklch(...purple...)`, `bg-purple-`, `bg-indigo-`, `bg-violet-`, `bg-fuchsia-` — must be zero matches |
| 7 | Primary brand color rendered | rendered HTML/CSS must contain `$PRIMARY_HEX` (or its HSL equivalent) at least once |

Each step has its own pass/fail. Write `~/Websites/<project>/.quality-gate/verification.json`:
```json
{
  "passed": true,
  "checks": [
    {"step": 1, "name": "home-200-with-title", "passed": true},
    {"step": 2, "name": "sitemap-urls-200", "passed": true, "details": "12/12 URLs"},
    ...
  ]
}
```

If ANY check fails, set `phases.verification.status='failed'` with `message="step <N> failed: <name>"`, set top-level `status='failed'`, and HALT. Do NOT proceed to the legacy sub-agent block below.

---

### B. (Legacy — only run if A passes) Sub-agent deep content review

**Spawn a sub-agent** with fresh context and the following instructions:

```
You are the VERIFICATION AGENT for website project: <project-name>.
The HTTP checklist (Phase 9 step A) has already passed. Your job is to verify content quality and SEO completeness.
If anything is broken, YOU fix it before reporting done.

The project is at: ~/Websites/<project-name>/
The intake is at: ~/Websites/<project-name>/.intake.json

Read the intake file first for business details.

## VERIFICATION CHECKLIST — Do ALL of these:

### 1. COMPILATION CHECK
Run: pnpm tsc --noEmit 2>&1
If there are ANY TypeScript errors, fix them ALL. Do not proceed until this is clean.

### 2. EVERY PAGE LOADS
Check every page.tsx file in src/app/. For EACH page:
- Read the file
- Verify it has real content (not template defaults, not "REPLACE:", not "Lorem ipsum")
- Verify it has a metadata export with a real title and description
- Verify it imports and uses Navbar and Footer
- Verify all Lucide icon imports are valid (no typos, no non-existent icons)
- If it's a "use client" page, verify it doesn't pass React components as props from server context

### 3. POSTCSS / TAILWIND CONFIG
- postcss.config.mjs must use 'tailwindcss' and 'autoprefixer' (NOT '@tailwindcss/postcss' which is v4-only)
- tailwind.config.ts must reference the correct content paths
- globals.css must have @tailwind base/components/utilities directives

### 4. IMAGES EXIST AND ARE WIRED IN
Check public/images/ and public/og/:
- Hero image exists (hero.webp or hero.png) — if missing, generate it using Gemini API
- OG image exists at public/og/default.png — if missing, generate it
- Favicon exists — if missing, generate icon.png
- Hero component in page.tsx has heroImage="/images/hero.webp" prop — if missing, add it
- layout.tsx openGraph.images points to existing file

### 5. NAVIGATION WORKS
- Read the Navbar component — verify desktop nav items render (hidden md:flex pattern)
- Verify every href in navItems has a corresponding page in src/app/
- Verify the mobile menu works (hamburger toggle pattern)
- Check for any broken internal links across ALL pages

### 6. FAQ QUALITY
- Home page FAQ section must have at least 15 FAQ items
- Dedicated /faq page must have at least 30 FAQ items
- All FAQ content must be specific to this business (not generic)
- FAQ answers must be detailed (minimum 2-3 sentences each)

### 7. SEO COMPLETE
- layout.tsx has metadataBase pointing to the real domain (from intake)
- Every page exports metadata with unique title and description
- sitemap.ts exists and lists all pages
- robots.txt exists
- Structured data (JSON-LD) in layout.tsx for the business

### 8. CONTACT & BUSINESS INFO
- Contact page has a working form (API route at /api/contact/route.ts exists)
- Phone number appears in: Navbar, Hero, CTA section, Footer
- Email and address appear in Footer
- Business name is correct everywhere (matches intake)

### 9. CONTENT QUALITY
- Zero placeholder text anywhere (grep for TODO, FIXME, Lorem, REPLACE, example.com, 000-0000)
- Zero fake testimonial names (grep for Alex Chen, Sarah Martinez, John Smith, Jane Doe, etc.)
- All service descriptions are specific and detailed (not one-liners)
- About page has real company narrative
- Privacy and Terms pages exist with real content

### 10. VISUAL/CODE QUALITY
- No unused imports in any file
- No console.log statements left in production code
- All components use consistent styling (same border radius, spacing patterns)
- SERVICE_LOCAL: white/light backgrounds, no floating orbs, phone prominent

## FIX EVERYTHING YOU FIND

Do NOT just report issues — FIX them. Generate missing images. Write missing FAQ items. Fix broken imports. Add missing metadata. Create missing pages. Wire in missing props.

After fixing everything, run pnpm tsc --noEmit one final time to confirm zero errors.

Then commit: git add -A && git commit -m "fix: verification agent — all checks passed"

Report what you checked, what you fixed, and confirm the site is ready.
```

**After the sub-agent completes:**
1. Read its report
2. Update status: `phases.verification.status: "complete"`, `phases.verification.message: "<summary of checks passed and fixes applied>"`
3. If the sub-agent reported it couldn't fix something critical, set status to `"failed"` instead

**Update the time estimate table:**

---

## Phase 9.5: FINAL SEO REVIEW (inline crawl + fix, ~2-3 minutes)

**Purpose:** Close the loop between "we researched X in Phase 1" and "the built site actually does X." This is an ON-PAGE audit of the *deployed* site (not external rank data — that was Phase 1). It catches the gap where research targeted keywords the build never surfaced. Findings are **fix-forward** (the site is already live on the dev URL) — fix the cheap misses inline, log the rest as TODOs; only a total SEO collapse (no titles/sitemap anywhere) HALTs.

**Update status:** `currentPhase: "seo-review"`, `phases.seo-review.status: "in_progress"`.

**Step 1 — Crawl the deployed routes and extract on-page signals:**
```bash
PROJ=~/Websites/<project>
DEV_URL=$(python3 -c "import json; print(json.load(open('$PROJ/.quality-gate/deploy.json'))['finalUrl'])")
python3 <<PY
import json, os, re, urllib.request, glob
proj = os.path.expanduser('~/Websites/<project>')
base = "$DEV_URL".rstrip('/')
# routes from page-map + the blog post
routes = [p['route'] for p in json.load(open(f"{proj}/ai/page-map.json"))['pages']]
try:
    seed = json.load(open(f"{proj}/.blog-seed.json")); routes.append(f"/blog/{seed['slug']}")
except Exception: pass
# target keywords from research
kw = []
kf = f"{proj}/ai/research/keywords.md"
if os.path.exists(kf):
    kw = [w.strip().lower() for w in re.findall(r'^\s*[-*\d.]+\s+([A-Za-z][^|\n]{3,60})', open(kf).read(), re.M)][:25]
def fetch(u):
    try:
        req = urllib.request.Request(u, headers={'User-Agent':'jambot-seo-audit'})
        return urllib.request.urlopen(req, timeout=15).read().decode('utf-8','ignore')
    except Exception as e:
        return f"__ERR__{e}"
report, issues = [], []
for r in routes:
    u = base + ('' if r=='/' else r)
    html = fetch(u)
    if html.startswith('__ERR__'):
        issues.append(f"{r}: UNREACHABLE ({html[7:60]})"); continue
    title = (re.search(r'<title>([^<]*)</title>', html, re.I) or [None,''])[1].strip()
    desc  = (re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)', html, re.I) or [None,''])[1].strip()
    h1s   = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.I|re.S)
    has_ld = 'application/ld+json' in html
    has_canon = bool(re.search(r'rel=["\']canonical["\']', html, re.I))
    body = re.sub(r'<[^>]+>',' ', html).lower()
    kw_hits = [k for k in kw if k in body]
    if not title: issues.append(f"{r}: missing <title>")
    elif len(title) > 65: issues.append(f"{r}: title too long ({len(title)} chars)")
    if not desc: issues.append(f"{r}: missing meta description")
    elif len(desc) > 160: issues.append(f"{r}: meta description too long ({len(desc)})")
    if len(h1s) != 1: issues.append(f"{r}: has {len(h1s)} <h1> (want exactly 1)")
    if not has_ld: issues.append(f"{r}: no JSON-LD schema")
    report.append({"route":r,"title":title,"desc":desc[:120],"h1":len(h1s),"jsonld":has_ld,"canonical":has_canon,"kw_hits":kw_hits})
# sitemap + robots reachable
for path in ("/sitemap.xml","/robots.txt"):
    if fetch(base+path).startswith('__ERR__'): issues.append(f"{path}: NOT served")
# keyword coverage across the whole site
covered = sorted(set(k for p in report for k in p['kw_hits']))
missing_kw = [k for k in kw if k not in covered]
out = {"devUrl":base,"pagesAudited":len(report),"issues":issues,
       "keywordsTargeted":len(kw),"keywordsCovered":len(covered),"keywordsMissing":missing_kw[:15],
       "pages":report}
json.dump(out, open(f"{proj}/ai/seo-final-review.json","w"), indent=2)
md = [f"# Final SEO Review — {base}", "",
      f"- Pages audited: {len(report)}",
      f"- On-page issues: {len(issues)}",
      f"- Target keywords covered: {len(covered)}/{len(kw)}", ""]
if issues: md += ["## Issues (fix-forward)"] + [f"- {i}" for i in issues] + [""]
if missing_kw: md += ["## Target keywords NOT surfaced anywhere"] + [f"- {k}" for k in missing_kw[:15]] + [""]
md += ["## Per-page"] + [f"- `{p['route']}` — title:{'Y' if p['title'] else 'N'} desc:{'Y' if p['desc'] else 'N'} h1:{p['h1']} jsonld:{'Y' if p['jsonld'] else 'N'} kw:{len(p['kw_hits'])}" for p in report]
open(f"{proj}/ai/seo-final-review.md","w").write("\n".join(md))
print(f"SEO review: {len(report)} pages, {len(issues)} issues, {len(covered)}/{len(kw)} keywords covered")
print("CRITICAL" if (len(report)==0 or all(not p['title'] for p in report)) else "OK")
PY
```

**Step 2 — Act on the findings:**
- If the last line printed `CRITICAL` (zero pages reachable, or NO page has a title): set `phases.seo-review.status: "failed"`, surface to canvas console, HALT — something is structurally broken.
- Otherwise: fix the **cheap, safe** misses inline (missing/overlong title or meta description, missing JSON-LD, >1 `<h1>`) by editing the relevant `page.tsx`, then `pnpm build` to confirm, commit `fix: SEO review — titles/meta/schema`. Log keyword-coverage gaps and anything structural to `ai/seo-final-review.md` as fix-forward TODOs (do NOT block the build on them — they become next-iteration content work).

**Mark complete:** `phases.seo-review.status: "complete"`, `message: "<N> pages audited, <X> issues fixed, <Y>/<Z> keywords covered — report at ai/seo-final-review.md"`.

---

## Error Handling

If ANY phase fails:
1. Update `.build-status.json`:
   - Set the failing phase to `"failed"` with error description
   - Set top-level `status` to `"failed"`
   - Set `error`: `{ "phase": "<name>", "message": "<what went wrong>", "at": "<iso>" }`
2. Tell the user what failed and how to fix it
3. Do NOT proceed to the next phase

## Resuming a Failed Build

If the user says "resume the build" or "retry", or you see a `.build-status.json` with `status: "failed"`:
1. Read the status file
2. Find which phase failed
3. Resume from that phase (skip completed phases)
4. Reuse existing research/design files

## Time Estimates

| Phase | Duration | Method |
|-------|----------|--------|
| Research | 3-5 min | Sub-agent with web_search |
| Scaffold | 1-2 min | Exec (pnpm install is the bottleneck) |
| Design System | ~1 min | Inline file edits |
| Build Pages | 5-10 min | Sub-agent |
| Assets | 2-3 min | Inline (Gemini API calls) |
| Quality Gate | ~2-3 min | Inline checks + fixes |
| Deploy | ~30 sec | Exec |
| Verification | 5-10 min | Sub-agent (fresh context, checks + fixes everything) |
| **Total** | **~22-33 min** | |
