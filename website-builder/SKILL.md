---
name: website-builder
description: "Build production-ready Next.js 15 websites from scratch. Research-first workflow: discovery → folder setup → deep research (keywords, competitors, content strategy, topical map, conversion patterns) → design planning (visual audit, style direction, component plan, wireframes) → scaffold → build → deploy. Use when the user asks to build a new website, create a site for their business, or start a new web project."
---

# Website Builder — Complete Next.js Website Skill

> Research-driven, design-intentional website building. Every decision backed by data, every section justified by research.

## When to Use This Skill

**TRIGGER when the user asks to:**
- Build a new website
- Create a website for their business
- Start a new web project
- "Make me a site"

**DO NOT USE for:**
- Canvas pages (use `canvas-web-design` skill instead)
- Editing an existing website project (follow that project's `.claude/CLAUDE.md`)
- Remotion video projects (use `remotion-video` skill)

---

## NON-NEGOTIABLE RULES

1. **NEVER write code before completing research and design planning.** Phases 1-4 produce zero code. That's correct.
2. **NEVER deliver a page with template defaults.** If you see "Logo", "(555) 000-0000", "hello@example.com", "Service One" — you FAILED.
3. **NEVER write copy without keyword research.** Every headline targets a specific keyword from Phase 3.
4. **NEVER skip the design plan.** Every section, color, and animation must have a documented REASON.
5. **NEVER use scare tactics or fear-based headlines.** Write benefit-focused, SEO-targeted copy.
6. **ALWAYS run the placeholder sweep** before presenting any site. Zero tolerance.
7. **ALWAYS customize every section.** If a section renders built-in defaults, you forgot to pass props.

---

## Site Types

Identify during intake — it changes everything:

| Type | Goal | Key Sections | Copy Style |
|------|------|-------------|------------|
| **SEO Leadgen** | Rank + capture leads | Hero + TrustBar + CoverageGrid + HowItWorks + FAQ + Testimonials + CTA | Keyword-rich, benefit-focused, professional |
| **Local Service** | Phone calls + forms | Hero + TrustBar + Services + ServiceAreas + Reviews + CTA | Direct, trust-building, location-targeted |
| **Portfolio** | Showcase work | Hero + ProjectGrid + About + Process + Contact | Visual, minimal copy, let work speak |
| **SaaS / Product** | Signups / trials | Hero + Features + Pricing + Testimonials + FAQ + CTA | Benefit-focused, comparison-driven |

---

## Tech Stack (every project)

| Tool | Package | Purpose |
|------|---------|---------|
| **Next.js 15** | `next` | App Router, server components, server actions |
| **React 19** | `react` | UI framework |
| **TypeScript** | `typescript` | Type safety |
| **Tailwind CSS v3** | `tailwindcss` | Utility-first styling (v3 — NOT v4, v4 has PostCSS issues) |
| **shadcn/ui** | `shadcn` (CLI) | Component library (Radix + Tailwind) |
| **Motion** | `motion` | Animations (spring physics, scroll, layout) |
| **Lenis** | `lenis` | Smooth scroll (< 4kb, accessible) |
| **Lucide React** | `lucide-react` | SVG icons |

### Optional (install when needed)
| Tool | Package | When |
|------|---------|------|
| **GSAP** | `gsap` | Complex scroll sequences, SplitText, MorphSVG |
| **Three.js** | `three` + `@react-three/fiber` | 3D backgrounds or hero elements |
| **MDX** | `@next/mdx` | Blog with rich content |
| **Prisma** | `prisma` | Database access |

---

## 13-Phase Workflow

Follow these phases IN ORDER. Do not skip phases. Phases 1-4 produce ZERO code — they produce research and a plan. That's the point.

### Phase 1: DISCOVER
**Read:** `instructions/brand-intake.md`

Ask the client the brand intake questions BEFORE anything else:
- Business identity, industry, target customer
- Brand colors, tone, personality
- SEO goals, competitors, what customers search for
- Pages needed, special features, primary CTA
- Site type (SEO leadgen, local service, portfolio, SaaS)

**Deliverable:** Completed intake answers

### Phase 2: SETUP
**Read:** `instructions/folder-setup.md`

Create the `ai/` folder structure inside the project directory:
1. Create all research directories (01-07)
2. Create design, content, and blog-research directories
3. Initialize `research-status.json`
4. Populate `01-business-profile/profile.md` from intake answers

**Deliverable:** Complete `ai/` folder structure with business profile filled in

### Phase 3: RESEARCH (the foundation — DO NOT RUSH)
**Read:** `instructions/research-plan.md`

Six research tasks that inform EVERYTHING that follows:

1. **Keyword research** — Find 50-100+ keywords across primary, secondary, long-tail, location categories. Document in `ai/research/02-keyword-research/`. Search Google, capture PAA questions, build keyword clusters.

2. **Competitor deep analysis** — Review 5-10 competitor sites in detail. For each one: document their homepage sections, hero layout, CTAs, visual design, typography, animations, content quality, strengths, weaknesses. Create per-competitor review files in `ai/research/03-competitor-analysis/site-reviews/`. Then synthesize into `pattern-analysis.md` (common patterns across niche) and `gaps-opportunities.md` (what we exploit).

3. **Content strategy** — Map every page: URL, keywords, sections, H1, meta tags. Create per-page content briefs in `ai/research/04-content-strategy/content-briefs/`. Research FAQ questions from PAA, Reddit, forums.

4. **Topical map** — Build topic cluster architecture: pillar pages, cluster content, internal linking strategy. Document in `ai/research/05-topical-map/`.

5. **Local SEO** (if applicable) — Target service areas, local competitors, city-specific keywords. Document in `ai/research/06-local-seo/`.

6. **Conversion patterns** — Analyze competitor CTAs, trust signals, social proof patterns. Map the conversion funnel. Document in `ai/research/07-conversion-patterns/`.

**Deliverable:** 20-40 research files across 7 directories. Update `research-status.json`.

### Phase 4: DESIGN PLAN (the thinking phase — every decision intentional)
**Read:** `instructions/design-plan.md`

This is where a site goes from "another template" to something that WORKS. Six design documents:

1. **Competitor visual audit** (`ai/design/competitor-visual-audit.md`) — Review all competitor sites for visual patterns: hero types, section ordering, color schemes, typography, animations, photography style. Rank them by visual quality. Identify what to beat.

2. **Style direction** (`ai/design/style-direction.md`) — Choose aesthetic with reasoning. Colors, fonts, dark/light mode, spacing — every choice traced to brand intake + competitor analysis + industry context.

3. **Component plan** (`ai/design/component-plan.md`) — Every component needed, in order, with its purpose. Why this hero layout? Why this trust bar style? Why these sections in this order? Map to the conversion funnel.

4. **Animation plan** (`ai/design/animation-plan.md`) — What moves, why, how. Entrance animations, hover states, scroll effects. Intentional motion, not random decoration.

5. **Page wireframes** (`ai/design/page-wireframes.md`) — Section-by-section layout for every page. ASCII wireframes showing structure.

6. **Design brief** (`ai/design/design-brief.md`) — Master document. Summarizes all design decisions, lists what makes this site "pop" vs competitors, connects every choice to research.

**Deliverable:** 6 design documents. The design brief is the reference for the entire build.

### Phase 5: SCAFFOLD
**Read:** `instructions/architecture.md`
**Use:** `templates/project/` directory

1. Copy `templates/project/` to `Websites/<project-name>/`
2. Run `pnpm install`
3. Install shadcn: `pnpm dlx shadcn@latest init`
4. Install core shadcn components: `pnpm dlx shadcn@latest add button card badge separator input textarea label`
5. Install animation deps: `pnpm add motion lenis`
6. Initialize git, commit scaffold
7. Create private GitHub repo, push, create `web-dev` branch
8. Fill in `.claude/CLAUDE.md` using `templates/config/claude-project.md`

### Phase 6: DESIGN SYSTEM
**Read:** `instructions/design-system.md`
**Use:** `templates/config/design-tokens.css`

Apply the style direction from Phase 4:
1. Set color palette (chosen in design plan, not random)
2. Set font pairing (chosen in design plan, not random)
3. Configure CSS variables in `globals.css`
4. Configure `tailwind.config.ts` with brand colors
5. Cross-reference: `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py`

### Phase 7: CONTENT WRITING
**Read:** `instructions/content-writing.md`

Write ALL copy BEFORE building pages. Save to `ai/content/` — one file per page:
1. Reference content briefs from Phase 3
2. Write every headline, paragraph, bullet, CTA, testimonial, FAQ answer
3. Every headline targets a keyword from Phase 3
4. Every paragraph is benefit-focused and industry-specific
5. No generic filler — real numbers, real scenarios, real language
6. Review against competitor gaps — our content must be MORE specific

**Deliverable:** Complete copy files in `ai/content/` for every page

### Phase 8: BUILD PAGES
**Read:** `instructions/animations.md`, `instructions/scroll-effects.md`
**Use:** `templates/sections/`, `templates/animations/`, `templates/pages/`

Now — and ONLY now — you write code. For each page:
1. Follow the wireframe from Phase 4
2. Select section templates from `templates/sections/`
3. Pass ALL content from Phase 7 via props — NO template defaults
4. Apply animations from the animation plan (Phase 4)
5. Generate/source images as you build (read `instructions/images.md`)

**Section selection by site type:**

| Site Type | Required Sections |
|-----------|-------------------|
| SEO Leadgen | Navbar + Hero + TrustBar + Stats + CoverageGrid/Features + HowItWorks + Testimonials + FAQ + CTA + Footer |
| Local Service | Navbar + Hero + TrustBar + Services + ServiceAreas + Stats + Reviews + FAQ + CTA + Footer |
| Portfolio | Navbar + Hero + ProjectGrid + About + Process + CTA + Footer |
| SaaS | Navbar + Hero + Features + Pricing + Testimonials + FAQ + CTA + Footer |

### Phase 8b: COMPILE CHECK (required)
```bash
cd <project-dir> && pnpm build
```
Fix all errors before moving on.

### Phase 9: FORMS & BACKEND
**Read:** `instructions/forms-backend.md`

1. Build industry-specific form fields (NOT generic name/email/message)
2. Create `/api/contact` route (file-based JSON storage)
3. Test form submission end-to-end

### Phase 10: BLOG (if needed)
**Read:** `instructions/blog-setup.md`

1. Install MDX dependencies
2. Create blog index and `[slug]` dynamic route
3. Write 2-3 starter posts targeting long-tail keywords from Phase 3
4. Add to sitemap

### Phase 11: SEO FINALIZATION
**Read:** `instructions/seo.md`, `instructions/performance.md`

1. Metadata in `layout.tsx` — use keywords from Phase 3
2. Per-page metadata with page-specific keywords
3. `sitemap.ts` and `robots.ts`
4. Structured data (JSON-LD) for business type
5. Error/404 pages
6. Image optimization

### Phase 12: QUALITY GATE (MANDATORY)
**Read:** `instructions/quality-checklist.md`

**Placeholder sweep — zero tolerance:**
```bash
grep -rn "example\.com\|placeholder\|TODO\|FIXME\|Lorem\|project-name\|REPLACE:\|UPDATE:\|000-0000\|hello@\|Service One\|Service Two\|Service Three\|A short description\|Your Headline\|Business Name\.\|Sarah Johnson\|Mike Chen\|Lisa Rodriguez" src/ --include="*.tsx" --include="*.ts"
```
**Every match = failure.**

Also verify:
- [ ] Navbar logo = real business name
- [ ] Footer = real contact info
- [ ] Every section heading specific to this business
- [ ] Every testimonial realistic and industry-specific
- [ ] All images point to existing files
- [ ] Every page has at least one real image
- [ ] CTA buttons link to correct destinations
- [ ] No page uses default section props
- [ ] Design matches the design brief from Phase 4
- [ ] Animation plan from Phase 4 fully implemented

### Phase 13: DEPLOYMENT
**Read:** `instructions/deployment.md`

1. `pnpm build` — fix any errors
2. Commit, push to `web-dev` branch

**JamBot:** `cd Websites/<name> && pnpm install && pnpm build`, then canvas URL.
**No container:** Tell user admin needs `jambot-add-website.sh`.
**External:** Vercel/Netlify/Docker per `instructions/deployment.md`.

---

## Style Rules

**REQUIRED:**
- Dark mode as default (light mode optional)
- Professional dark palette: backgrounds `#0a0a0a` / `#0d1117`, text `#e2e8f0`
- Brand accent colors via CSS variables (not hardcoded)
- All interactive elements: hover state + `cursor-pointer`
- Animations respect `prefers-reduced-motion`
- Mobile-first responsive (375px → up)
- SVG icons from `lucide-react` only

**CLOUDFLARE COMPATIBILITY (critical for JamBot dev sites):**
- Cloudflare "Email Address Obfuscation" breaks React hydration
- Do not render bare email addresses in JSX — use `onClick` handlers or encode

**BANNED:**
- Purple (`#764ba2`, `#667eea`, `#8b5cf6`), pink, magenta as primary colors
- Emoji as UI icons
- Lorem ipsum or placeholder text in delivered pages
- `href="#"` on buttons (use `<button>` or real links)
- External CDN scripts
- Inline styles (use Tailwind classes)
- Fear-based / scare-tactic headlines
- Generic "we deliver quality service" copy without specifics

---

## Fetching Fresh Docs (On Demand)

```bash
curl -s https://ui.shadcn.com/llms.txt | head -200      # shadcn/ui
curl -s https://nextjs.org/docs/llms.txt | head -200      # Next.js
curl -s https://tailwindcss.com/docs/llms.txt | head -200  # Tailwind
```

---

## Cross-Skill References (DO NOT DUPLICATE)

| Need | Command |
|------|---------|
| Color palettes | `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<query>" --domain color` |
| Font pairings | `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<query>" --domain typography` |
| UX rules | `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<query>" --domain ux` |
| Full design system | `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<industry> <type>" --design-system` |
| Copywriting | Read `/mnt/shared-skills/marketing/copywriting/SKILL.md` |
| Site architecture | Read `/mnt/shared-skills/marketing/site-architecture/SKILL.md` |
| CRO / conversion | Read `/mnt/shared-skills/marketing/page-cro/SKILL.md` |
| SEO | Read `/mnt/shared-skills/marketing/local-seo/SKILL.md` |
| Theme presets | Read `/mnt/shared-skills/theme-factory/SKILL.md` |

---

## File Index

```
instructions/
  brand-intake.md        — Discovery questions (SEO + competitor questions included)
  folder-setup.md        — /ai/ directory structure initialization
  research-plan.md       — Deep foundational research: keywords, competitors, content, topical map, conversion
  design-plan.md         — Design thinking: visual audit, style direction, component plan, wireframes
  content-writing.md     — Copy guidelines by site type, tone, and industry
  design-system.md       — Color, typography, theme setup
  architecture.md        — Next.js project structure and conventions
  animations.md          — 15 animation patterns with Motion.dev/GSAP/CSS code
  scroll-effects.md      — Lenis + scroll-triggered animations + parallax
  images.md              — Image strategy, OG images, favicons, optimization
  blog-setup.md          — Full MDX blog system with dynamic routing
  forms-backend.md       — Contact form server actions (Resend/AgentMail/file)
  seo.md                 — Metadata, OG, sitemap, structured data, robots
  performance.md         — Image optimization, fonts, code splitting, Core Web Vitals
  deployment.md          — JamBot dev server, static build, Vercel, Netlify, Docker
  quality-checklist.md   — 40+ point pre-delivery audit
  references.md          — llms.txt URLs, ui-ux-pro-max queries, component reference

templates/
  project/               — Full Next.js 15 starter (copy to scaffold)
  sections/              — 18 section components (Navbar, Hero, Features, FAQ, etc.)
  animations/            — 9 reusable wrappers (FadeIn, Stagger, Parallax, etc.)
  pages/                 — 5 full page compositions (Home, About, Services, Contact, Blog)
  config/                — Project CLAUDE.md template, CSS design tokens

tools/
  scaffold.sh            — Create project, copy templates, install deps, git init
  github-setup.sh        — Create private repo, push, set up web-dev branch
```
