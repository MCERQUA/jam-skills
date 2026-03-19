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
    "build-pages":   { "status": "not_started", "message": null },
    "quality-gate":  { "status": "not_started", "message": null },
    "deploy":        { "status": "not_started", "message": null }
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

SECTION TEMPLATES are already at: ~/Websites/<PROJECT>/src/components/sections/
ANIMATION WRAPPERS are at: ~/Websites/<PROJECT>/src/components/animations/

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
   Then create a simple OG image at `public/og/default.png` — copy the banner/logo image from intake heroImage if available, or create a Next.js `opengraph-image.tsx` using ImageResponse with the business name and tagline on a branded background.

4. Add favicon: copy a relevant logo/icon from intake assets to `public/favicon.ico` (convert if needed) and `public/apple-touch-icon.png`. If no logo is available, create a minimal `src/app/icon.tsx` using Next.js ImageResponse.

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

## Phase 5: QUALITY GATE (inline, ~2-3 minutes)

**Update status:** `currentPhase: "quality-gate"`, `phases.quality-gate.status: "in_progress"`, `phases.quality-gate.message: "Running quality checks..."`

**Read:** `/mnt/shared-skills/website-builder/instructions/quality-checklist.md`

**Read the BUSINESS_TYPE** from `.claude/CLAUDE.md` before running type-specific checks.

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

## Phase 6: DEPLOY (exec, ~30 seconds)

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
- [ ] Add real photos (replace any placeholder images in the hero graphic panel and team section)
- [ ] Verify phone number and business hours in header, hero, CTA, and footer"

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
| Quality Gate | ~2-3 min | Inline checks + fixes |
| Deploy | ~30 sec | Exec |
| **Total** | **~15-20 min** | |
