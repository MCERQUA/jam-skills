# WEBSITE-BUILD.md — Automated Website Build Workflow

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

You receive a message from the automated build pipeline asking you to execute a 6-phase website build.

**Triggered by:** A message containing `Read WEBSITE-BUILD.md and execute the full 6-phase automated build for project: <project-name>`

The intake data is at: `~/Websites/<project-name>/.intake.json`
The status file is at: `~/Websites/<project-name>/.build-status.json`

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

## DESIGN RULES BY BUSINESS TYPE — NON-NEGOTIABLE

These rules exist because a dark SaaS aesthetic on a local plumber's website destroys trust and drives customers away. The aesthetic MUST match customer expectations for the industry.

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

**Create research directory:**
```
~/Websites/<project>/ai/research/
```

**Before spawning, copy intake for sub-agent access:**
```bash
cp ~/Websites/<project>/.intake.json ~/Websites/<project>/ai/.intake-copy.json
```

**Spawn a sub-agent:**
```
sessions_spawn({
  task: "You are a market researcher. Read the business intake at ~/Websites/<PROJECT>/ai/.intake-copy.json.

Your job: Research this business's market and competitors. Write findings to ~/Websites/<PROJECT>/ai/research/.

TASKS (do all 5):

1. COMPETITOR ANALYSIS — web_search for '<industry> <location>' and '<industry> near <location>'. Find 5-10 competitors. For each: name, URL, strengths, weaknesses, what they do well on their website. Save to: ai/research/competitors.md

2. KEYWORD RESEARCH — web_search for what customers search when looking for this service. Find 20-30 keywords grouped by intent (informational, commercial, transactional). Include estimated difficulty. Save to: ai/research/keywords.md

3. MARKET ANALYSIS — Summarize the local market: how competitive is it, what's the opportunity, what gaps exist. Save to: ai/research/market-analysis.md

4. CONTENT STRATEGY — Based on keywords and competitor gaps, recommend: which pages to build, what topics to cover, what questions to answer (FAQ). For SERVICE_LOCAL businesses, every individual service must be its own recommended page. Save to: ai/research/content-strategy.md

5. DESIGN NOTES — Based on competitor websites: what visual patterns work in this industry, what's overused, what would differentiate this business. Color and layout observations. IMPORTANT: note the BUSINESS_TYPE and whether competitor sites use light or dark backgrounds. Save to: ai/research/design-notes.md

IMPORTANT: After completing ALL tasks, update ~/Websites/<PROJECT>/.build-status.json:
- Set phases.research.status to 'complete'
- Set phases.research.message to 'Research complete — X competitors analyzed, Y keywords found'
- Set updatedAt to current time

End with: OUTPUT_SAVED: ai/research/",
  label: "website-research-<project>"
})
```

**After sub-agent completes:** Read `ai/research/competitors.md` to verify it exists.

---

## Phase 2: SCAFFOLD (exec, ~1-2 minutes)

**Update status:** `currentPhase: "scaffold"`, `phases.scaffold.status: "in_progress"`, `phases.scaffold.message: "Copying templates and installing dependencies..."`

The project directory already exists (canvas created it). Do these steps:

1. **Copy project template files:**
```bash
cp -r /mnt/shared-skills/website-builder/templates/project/* ~/Websites/<project>/
cp /mnt/shared-skills/website-builder/templates/project/.gitignore ~/Websites/<project>/
cp /mnt/shared-skills/website-builder/templates/project/.env.local.example ~/Websites/<project>/
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

## Phase 3: DESIGN SYSTEM (inline, ~1 minute)

**Update status:** `currentPhase: "design-system"`, `phases.design-system.status: "in_progress"`, `phases.design-system.message: "Configuring brand colors and typography..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/design-system.md`

**Read the BUSINESS_TYPE** from `.claude/CLAUDE.md` before touching any file in this phase.

### Step 1: Set CSS variables in `src/app/globals.css`

Use the intake's `colorPrimary`, `colorSecondary`, `colorAccent`. If no colors provided, use research `design-notes.md` to pick appropriate colors.

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
  /* Primary, secondary, accent come from intake brand colors */
}
/* Do NOT add a .dark { } block for SERVICE_LOCAL — no dark mode */
```

**For SAAS_PRODUCT or PROFESSIONAL_SERVICES:** Set background, surface, border, text, muted colors appropriate to their theme. Dark is acceptable for SAAS_PRODUCT only.

### Step 2: Configure tailwind.config.ts
- Set `colors.primary`, `colors.secondary`, `colors.accent` to the brand colors
- Set `fontFamily.heading` and `fontFamily.body` from intake fonts (or defaults)

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

### Step 5: Git commit
```bash
cd ~/Websites/<project> && git add -A && git commit -m "style: apply brand design system"
```

**Update status:** `phases.design-system.status: "complete"`, `phases.design-system.message: "Design system configured"`

---

## Phase 3.5: STITCH PAGES (inline, ~2-4 minutes per page)

Generate detailed HTML mockups for each site page using Google Stitch. The build-pages sub-agent in Phase 4 will read these as design references — they ARE NOT copied verbatim, they GUIDE the layout, sectioning, and visual hierarchy decisions.

**Update status:** `currentPhase: "stitch-pages"`, `phases.stitch-pages.status: "in_progress"`, `phases.stitch-pages.message: "Generating page layouts with Stitch..."`

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

If the response contains an error, mark `phases.stitch-pages.status: "failed"` with the error message AND continue to Phase 4 anyway — the build-pages sub-agent can still build pages from scratch. Stitch is enhancement, not a hard dependency.

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

**Run the generation:**

```bash
exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh generate_screen_from_text '{\"projectId\": \"<PID>\", \"deviceType\": \"DESKTOP\", \"modelId\": \"GEMINI_3_PRO\", \"prompt\": \"<escaped-prompt>\"}'")
```

Critical JSON-escape rules: replace `"` with `\"` and newlines with `\\n` inside the prompt before embedding.

### Step 5 — Poll for the screen, then download HTML

After `generate_screen_from_text` returns (it may return success before the screen is indexed):

1. Wait 60 seconds.
2. Call `list_screens`:
   ```bash
   exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh list_screens '{\"projectId\": \"<PID>\"}'")
   ```
3. Find the new screen (compare against the screen IDs you've already processed for this project — the new one is whichever wasn't there before).
4. If the screen list is still empty or unchanged, wait 30 more seconds and retry. Up to 3 retries.
5. Once you have the new screen ID, call `get_screen`:
   ```bash
   exec("bash /home/node/.openclaw/workspace/skills/stitch/stitch-mcp.sh get_screen '{\"name\": \"projects/<PID>/screens/<SID>\", \"projectId\": \"<PID>\", \"screenId\": \"<SID>\"}'")
   ```
6. The response includes `htmlCode.downloadUrl` — download it:
   ```bash
   mkdir -p ~/Websites/<project>/.stitch-pages
   curl -L -s -o ~/Websites/<project>/.stitch-pages/<page>.html '<htmlCode.downloadUrl>'
   ```
7. Save the screenshot too if you want it for debugging:
   ```bash
   curl -L -s -o ~/Websites/<project>/.stitch-pages/<page>.png '<screenshot.downloadUrl>'
   ```

### Step 6 — Failure handling per page

If a page fails after 3 retries OR `generate_screen_from_text` returns an error:
- Append the page name to a `failed` list
- Continue to the next page — do NOT abort the whole phase
- After all pages: update `phases.stitch-pages.message` to `"<N> pages generated, <M> skipped: <names>"`

### Step 7 — Mark phase complete

After all pages have been attempted:

- `phases.stitch-pages.status: "complete"` (even if some pages failed — partial success is success)
- `phases.stitch-pages.message: "<N> page layouts generated"`
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

If the WHOLE phase failed (e.g. create_project failed) — mark `phases.stitch-pages.status: "failed"` but DO NOT abort the build. Phase 4 will detect missing `.stitch-pages/` and build from scratch.

---

## Phase 4: BUILD PAGES (sub-agent, ~5-10 minutes)

**Update status:** `currentPhase: "build-pages"`, `phases.build-pages.status: "in_progress"`, `phases.build-pages.message: "Building pages with real content..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/animations.md`

**Spawn a sub-agent:**
```
sessions_spawn({
  task: "You are a website builder. Build all pages for the <PROJECT> website.

READ THESE FILES FIRST — IN THIS ORDER:
1. ~/Websites/<PROJECT>/.claude/CLAUDE.md (brand config + BUSINESS_TYPE — THIS IS YOUR NORTH STAR)
2. ~/Websites/<PROJECT>/ai/research/content-strategy.md (what pages and content to build)
3. ~/Websites/<PROJECT>/ai/research/keywords.md (SEO keywords to target in headings)
4. ~/Websites/<PROJECT>/ai/research/competitors.md (what to differentiate from)
5. /mnt/shared-skills/website-builder/instructions/animations.md (animation patterns)
6. /mnt/shared-skills/website-builder/instructions/images.md (image strategy — required images per page, sizing, alt text rules)
7. ~/Websites/<PROJECT>/.stitch-pages/manifest.json IF IT EXISTS — lists per-page Stitch HTML mockups generated in Phase 3.5

STITCH MOCKUPS — IF .stitch-pages/manifest.json EXISTS:
  For every page you build, FIRST read ~/Websites/<PROJECT>/.stitch-pages/<page>.html as a DESIGN REFERENCE.
  - The Stitch HTML shows the intended layout, section order, hierarchy, and visual treatment for that page
  - Use it to decide: WHICH sections to include, in WHAT order, with WHAT visual emphasis
  - DO NOT copy the Stitch HTML verbatim. It is Tailwind/HTML, not Next.js. You build with the section components in src/components/sections/, and use the Stitch HTML as a layout blueprint
  - DO match the section count, section order, and visual hierarchy of the Stitch mockup
  - DO match the headline tone and CTA wording style (but use real keywords from research)
  - If a Stitch HTML for a specific page is missing from .stitch-pages/, build that page from scratch using the standard section templates
  - The compactDesignMd in manifest.json contains brand rules — apply them to ALL pages (color treatment, signature elements, do/don't rules)

SECTION TEMPLATES are already at: ~/Websites/<PROJECT>/src/components/sections/
ANIMATION WRAPPERS are at: ~/Websites/<PROJECT>/src/components/animations/

IMAGE PREP: Phase 5 (Assets) will generate images AFTER you finish. When building Hero components, include the heroImage prop pointing to '/images/hero.png' — the file will be created in Phase 5. For service pages, use '/images/<service-slug>.png'. These paths will be populated with real AI-generated images.

THE BUSINESS_TYPE in CLAUDE.md controls EVERYTHING about visual design.
Read it. Follow it. Do not deviate.

---

## CONTENT RULES (Follow exactly — these prevent the most common build failures)

### URLs and Links
- ALL external links (GitHub, social, etc.) must come from the intake's `socials` field
- If a social URL is not in intake, do NOT guess it — use `#` or omit the link
- Never use placeholder URLs like github.com/openvoiceui, twitter.com/example, etc.
- The GitHub link in Navbar and Footer must be: intake.socials.github (or omitted if missing)

### Social Proof (Testimonials)
NEVER generate fake testimonials with made-up names and fake job titles.

Instead, pick ONE of these approaches based on the intake:
a) **Open source project**: Replace Testimonials with a GitHub Stats section — show star count, fork count, contributor count (use shields.io badges or GitHub API data from research)
b) **New business (no reviews yet)**: Use a 'How It Works' section or a Use Cases section instead of testimonials. Include a note: <!-- CLIENT: Add real customer quotes here before launch -->
c) **Established business**: Only include testimonials if the intake provides real customer names and quotes in the `notes` or a dedicated field

### Stats
Stats must be accurate and verifiable:
- Only include a stat if you can confirm it from intake data or research
- If the stat is an estimate, round conservatively
- Common bad stats to avoid: made-up years in business, inflated job counts, fake review ratings
- If no real stats are available, replace the Stats section with an additional service card or service area callout

### Feature Descriptions
Every feature description MUST include a concrete example in plain language.

Bad: 'Extensible skill system for adding integrations'
Good: 'Skill System — Add new capabilities without touching core code. Example: connect your CRM so your AI can look up customer history mid-call.'

---

## PAGE COMPOSITION BY BUSINESS TYPE

### SERVICE_LOCAL — HOME PAGE (minimum 8 sections, in this order)

1. **Navbar** — pass `logo`, `phone`, `navItems`, `cta` props. Phone MUST be passed.
   ```tsx
   <Navbar
     logo="<Business Name>"
     phone="<phone from intake>"
     navItems={[...]}
     cta={{ label: 'Get a Free Quote', href: '/contact' }}
   />
   ```

2. **Hero** — pass `layout="split-right"`, `phone`, `badge`, `title`, `subtitle`, primary and secondary CTAs. Phone MUST be passed.
   ```tsx
   <Hero
     layout="split-right"
     badge="<trust signal — e.g. 'Licensed & Insured · 20+ Years Experience'>"
     title="<main headline targeting primary keyword>"
     titleAccent="<accent phrase>"
     subtitle="<1-2 sentence description with location and service>"
     phone="<phone from intake>"
     primaryCTA="Get a Free Quote"
     primaryHref="/contact"
     secondaryCTA="See Our Services"
     secondaryHref="/services"
     heroImage="<heroImage from intake if available>"
   />
   ```

3. **TrustBar** — horizontal strip immediately below hero with trust signals. Use real data from intake/research ONLY.
   - Years in business
   - Jobs completed or clients served (if available from intake)
   - Review rating + platform (Google, BBB — only if available)
   - Certifications, licenses (list real ones from intake)
   - Licensed / Bonded / Insured (if applicable)
   This section builds immediate credibility. Do NOT put placeholder numbers here.

4. **Services section** — label it 'Our Services'. List 4-6 specific named services with real descriptions. Each card links to that service's dedicated page (e.g., `/spray-foam-insulation`). Add a short concrete example for each. Do NOT use generic descriptions like 'Professional service with attention to detail.'

5. **How It Works** — 3-4 numbered steps showing exactly how the client engages this business. Make the steps specific to their process, not generic. Example for a contractor: '1. Free on-site estimate → 2. We provide a written proposal → 3. Work begins on your schedule → 4. Final walkthrough & satisfaction guarantee.'

6. **Social proof section** — choose ONE:
   - If intake has real customer quotes: Testimonials with real names, real locations, real text
   - If no reviews yet: Results / Case Studies section with specific project outcomes (without invented client names)
   - Comment: <!-- CLIENT: Add real customer reviews here before launch -->

7. **Stats** — ONLY if real numbers are available from intake:
   - Years in business, number of jobs, number of cities served, etc.
   If NO real stats are available from intake, SKIP this section and replace with an additional services callout or service area grid.

8. **CTA section** — strong call to action with:
   - Headline: 'Ready to Get Started?'
   - Subtext: mention free estimate or quick response time if that's in the intake
   - Phone number displayed large (same `Phone` icon + `tel:` link pattern as Hero)
   - 'Get a Free Quote' button linking to `/contact`
   - Do NOT add a secondary CTA here — one clear action only

9. **Footer** — include: business name, phone, email, address, hours, nav links, service links, copyright, privacy + terms links

---

### SERVICE_LOCAL — SERVICE PAGES (one page per service)

Each service gets its own route (e.g., `/spray-foam-insulation`, `/hvac-repair`, `/general-liability-insurance`).
Source the service list from intake `services` field + content-strategy.md recommendations.

Each service page must have these sections IN ORDER:
1. Navbar (with phone)
2. Hero — smaller than home hero, focused on this specific service. `layout="centered"` OK here. Include service name in title, target the service-specific keyword.
3. 'What's Included' — detailed breakdown of what this service covers. Use real specifics from intake or research. 4-6 bullet points minimum.
4. 'Who It's For / Use Cases' — 3-4 specific scenarios where a customer would need this service
5. 'Our Process' — 3-4 steps specific to delivering this service
6. 'Why Choose [Business Name] for [Service]' — differentiators: certifications, experience, warranty, response time, local knowledge
7. FAQ — 4-6 questions specific to this service. Source from keyword research (people also ask). Real questions, specific answers.
8. CTA with phone number
9. Footer

---

### SERVICE_LOCAL — ABOUT PAGE

Sections IN ORDER:
1. Navbar (with phone)
2. Hero (centered, simpler — 'About [Business Name]')
3. Story section — when founded, by whom, why. Be specific — generic 'passion for excellence' copy is not acceptable.
4. Credentials — real licenses, certifications, memberships, awards
5. Team section (if intake has team info) — real names and roles only, no stock photos
6. 'Why Choose Us' — 4-6 specific differentiators that actually distinguish this business
7. CTA with phone
8. Footer

---

### SERVICE_LOCAL — CONTACT PAGE

1. Navbar (with phone)
2. Contact section with:
   - Working contact form (POST to `/api/contact` or mailto fallback)
   - Phone number displayed prominently
   - Email address
   - Physical address (if in intake)
   - Business hours (if in intake)
3. Footer

---

### SERVICE_LOCAL — ADDITIONAL PAGES (create these if not already in intake pages list)

- `/faq` — Frequently asked questions. Source from keyword research 'people also ask' section + research/content-strategy.md. Organize by category.
- `/service-area` — If location-based business: list cities/counties served, include a note about radius or travel distance
- `/privacy` — Always required (see Required Pages below)
- `/terms` — Always required (see Required Pages below)

---

### SAAS_PRODUCT — HOME PAGE (5-6 sections)

1. Navbar (logo, navItems, cta — no phone required unless intake has one)
2. Hero (centered or split — both OK, animated bg OK)
3. Features — 3-4 key features with concrete examples
4. Social proof — GitHub stats OR real user testimonials OR use cases
5. CTA section
6. Footer

SAAS additional pages: `/pricing` (if applicable), `/docs` or `/getting-started`, `/about`, `/contact`, `/privacy`, `/terms`

---

### PROFESSIONAL_SERVICES — HOME PAGE (6-7 sections)

1. Navbar (with phone)
2. Hero (split-right preferred)
3. Services offered — with specific descriptions
4. Results / Case studies — specific outcomes not generic praise
5. Team / Credentials
6. CTA section (with phone)
7. Footer

---

## FOR EACH PAGE in the intake's pages list:
1. Create src/app/<page>/page.tsx (or src/app/page.tsx for Home)
2. Export a `metadata` object with a unique title and description for that page:
   ```typescript
   export const metadata: Metadata = {
     title: 'Page Title — Business Name',
     description: 'Unique 150-char description targeting that page\\'s keywords',
   };
   ```
3. Import section components and compose the page
4. Pass REAL content as props — business name, real descriptions, real features
   DO NOT use template defaults. Every piece of text must be specific to this business.
5. Target keywords from keyword research in headings (H1, H2)
6. Apply FadeIn, StaggerChildren animations to sections (fade-in only for SERVICE_LOCAL)
7. Use the brand's primary CTA text on all CTA buttons

## layout.tsx — Required Updates
1. Set `metadataBase` to the intake domain:
   ```typescript
   metadataBase: new URL('https://<intake.domain>'),
   ```
   NOT a hardcoded URL or the dev server URL.

2. Add JSON-LD structured data appropriate to the business type:
   - SERVICE_LOCAL → LocalBusiness schema (include address, telephone, openingHours, areaServed)
   - SAAS_PRODUCT → SoftwareApplication schema
   - PROFESSIONAL_SERVICES → ProfessionalService schema
   Include: name, url, description, email, telephone (if in intake), sameAs (social URLs from intake)

3. Add OG image metadata pointing to `/og/default.png`:
   ```typescript
   openGraph: {
     images: [{ url: '/og/default.png', width: 1200, height: 630 }],
   }
   ```
   (Phase 5 Assets will generate the actual OG image file — just set the metadata reference here.)

4. Add favicon metadata (Phase 5 Assets will generate the actual favicon file):
   ```typescript
   icons: {
     icon: '/favicon.ico',
     apple: '/apple-touch-icon.png',
   }
   ```

## sitemap.xml and robots.txt
After all pages are built, create:

`public/robots.txt`:
```
User-agent: *
Allow: /
Sitemap: https://<intake.domain>/sitemap.xml
```

`src/app/sitemap.ts` (Next.js sitemap):
```typescript
import { MetadataRoute } from 'next'
export default function sitemap(): MetadataRoute.Sitemap {
  const base = 'https://<intake.domain>'
  return [
    { url: base, lastModified: new Date(), changeFrequency: 'weekly', priority: 1 },
    // one entry per page in intake.pages
  ]
}
```

## Required Pages (Always Create)
These pages must exist or footer links will 404:
- `/privacy` — Privacy Policy (generate a basic GDPR-compliant boilerplate using the intake's business name, email, and domain)
- `/terms` — Terms of Service (generate basic ToS boilerplate)
If these pages aren't in the intake's `pages` list, create them anyway as minimal pages — they are legally required for any site with a contact form.

## Pricing Page
If the intake does not include a working payment system or Stripe integration:
- Free tier: show as normal with CTA
- Any paid tiers (Pro, Enterprise): mark with a 'Coming Soon' badge, grey out the CTA button, do NOT link to a checkout page
- Add a note below: 'Paid plans launching soon. Join the waitlist:' + email field (mailto link)

## Contact Form
The ContactForm component must work. Choose:
a) If intake has an email address: implement `/api/contact/route.ts` that sends email via the configured SMTP/Resend/etc, OR make the form submit to a `mailto:` link as a fallback
b) Minimum acceptable: `<form action='mailto:<email>' method='post' enctype='text/plain'>` — at least something happens when they click submit
c) Create `src/app/api/contact/route.ts` with a basic handler that returns a JSON response (even if it just logs for now — the form should not 404)

AFTER ALL PAGES:
1. Update src/app/layout.tsx with metadataBase, JSON-LD, OG metadata, favicon
2. Run a TypeScript type-check (lighter than full build): cd ~/Websites/<PROJECT> && pnpm tsc --noEmit 2>&1 | head -40
3. FIX any TypeScript errors found — do NOT run pnpm build (the webdev container handles compilation)
4. Commit: git add -A && git commit -m 'feat: build all pages with content'

Update ~/Websites/<PROJECT>/.build-status.json when done:
- phases.build-pages.status = 'complete'
- phases.build-pages.message = 'X pages built, compilation verified'

End with: OUTPUT_SAVED: src/app/page.tsx",
  label: "website-pages-<project>"
})
```

**After sub-agent completes:** Run `pnpm tsc --noEmit 2>&1 | head -30` to check for type errors. Fix any errors found. Do NOT run `pnpm build`.

---

## Phase 5: ASSETS (inline, ~2-3 minutes)

**Update status:** `currentPhase: "assets"`, `phases.assets.status: "in_progress"`, `phases.assets.message: "Generating brand images..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/images.md`

This phase generates real images for the website using the Gemini image API, replacing placeholder graphics with brand-specific visuals. Every image is saved to `public/images/` or `public/og/` in the project — never held in memory or skipped.

### Prerequisites
- `GEMINI_API_KEY` must be set in the environment (injected via `.platform-keys.env`)
- Phase 4 (Build Pages) must be complete — we need to know which pages exist

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

### Step 3: Generate Hero Image

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

## Phase 6: QUALITY GATE (inline, ~2-3 minutes)

**Update status:** `currentPhase: "quality-gate"`, `phases.quality-gate.status: "in_progress"`, `phases.quality-gate.message: "Running quality checks..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/quality-checklist.md`

**Read the BUSINESS_TYPE** from `.claude/CLAUDE.md` before running type-specific checks.

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

# Section count check
section_count=$(grep -c '<section' ~/Websites/<project>/src/app/page.tsx 2>/dev/null || echo 0)
echo "Sections on home page: $section_count"
[ "$section_count" -lt 7 ] && echo "⚠️  SERVICE_LOCAL requires 8+ sections on home page — current: $section_count" || echo "✓ Section count OK"

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

## Phase 7: DEPLOY (exec, ~30 seconds)

**Update status:** `currentPhase: "deploy"`, `phases.deploy.status: "in_progress"`, `phases.deploy.message: "Deploying to dev server..."`

1. **Type-check only (do NOT run pnpm build):**
```bash
cd ~/Websites/<project> && pnpm tsc --noEmit 2>&1 | head -30
```
Fix any TypeScript errors. The webdev container handles compilation — you do not need a clean build here.

2. **Remove any stale `.next` directory** (partial builds cause `routes-manifest.json` errors in dev mode):
```bash
[ -d ~/Websites/<project>/.next ] && mv ~/Websites/<project>/.next ~/Websites/<project>/.next.bak || true
```

3. **Set active project** (the build watcher restarts the webdev container and reinstalls dependencies automatically — do NOT run pnpm install in webdev yourself):
```bash
echo "<project>" > ~/Websites/.active-project
```

4. **Verify the file was written:**
```bash
cat ~/Websites/.active-project
```
Should output: `<project>`

5. **Update final status:**

Read the current status file, then write:
```json
{
  "status": "complete",
  "completedAt": "<current ISO timestamp>",
  "currentPhase": "deploy",
  "phases": { "deploy": { "status": "complete", "message": "Live at dev-test-dev.jam-bot.com — dev server restarting" } }
}
```

6. **Tell the user:**
"Your website is live! The dev server is restarting to pick up the new project (~15s). Check it here: [CANVAS_URL:https://dev-test-dev.jam-bot.com]

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

## Phase 8: VERIFICATION AGENT (sub-agent, ~5-10 minutes)

**This is the gatekeeper. Nothing is "done" until this agent confirms it.**

**Update status:** `currentPhase: "verification"`, add `"verification": { "status": "in_progress", "message": "Verification agent checking every page..." }` to `phases`.

**Spawn a sub-agent** with fresh context and the following instructions:

```
You are the VERIFICATION AGENT for website project: <project-name>.
Your job is to verify that EVERY aspect of this website is complete, working, and high quality.
You are the last gate — if you pass this, it ships. If anything is broken, YOU fix it before reporting done.

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
