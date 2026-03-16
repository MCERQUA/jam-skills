---
name: website-builder
description: "Build production-ready Next.js 15 websites from scratch. Use when the user asks to build a new website, create a site for their business, or start a new web project. Full 10-phase workflow: brand intake, SEO research, scaffold, design system, content planning, page building, images, forms, quality gate, deployment."
---

# Website Builder — Complete Next.js Website Skill

> Build production-ready, modern Next.js websites from scratch with consistent quality.

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

1. **NEVER deliver a page with template defaults.** If you see "Logo", "(555) 000-0000", "hello@example.com", "A short description", "Service One", "Sarah Johnson, Homeowner" — you FAILED. Every character of text must be real content for this specific business.
2. **NEVER write copy without keyword research first.** Phase 2 (Research) must complete before Phase 5 (Content & Pages). Every headline must target specific keywords.
3. **NEVER skip images.** A text-only site is not a deliverable. Generate or source images during page building.
4. **NEVER use scare tactics or fear-based headlines** for service/insurance/professional businesses. Write benefit-focused, SEO-targeted copy. "Comprehensive Insurance for Epoxy Contractors" beats "One Job Goes Wrong And You're Out of Business".
5. **ALWAYS run the placeholder sweep grep** before presenting any site. Zero tolerance.
6. **ALWAYS customize every section.** If a section renders its built-in defaults, you forgot to pass props.

---

## Site Types

Identify the site type during intake — it changes everything:

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
| **Tailwind CSS v3** | `tailwindcss` | Utility-first styling (v3 — NOT v4, v4 has PostCSS issues with Next.js) |
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

## 10-Phase Workflow

Follow these phases IN ORDER. Do not skip phases.

### Phase 1: DISCOVER
**Read:** `instructions/brand-intake.md`

Ask the client the brand intake questions BEFORE writing any code. Includes:
- Business identity, industry, target customer
- Brand colors, tone, personality
- **SEO goals: what they want to rank for, who competitors are, what customers search for**
- Pages needed, special features, primary CTA
- Site type (SEO leadgen, local service, portfolio, SaaS)

**Deliverable:** Completed intake answers saved to `.claude/CLAUDE.md`

### Phase 2: RESEARCH & PLAN
**Read:** `instructions/research-plan.md`

**This phase is MANDATORY. Do not skip it.**

1. **Keyword research** — Identify 10-20 target keywords
   - Primary (high-volume, core services): 3-5
   - Secondary (specific services, locations): 5-10
   - Long-tail (questions, how-to): 5-10
   - Use web search to verify relevance

2. **Competitor scan** — Look at top 3-5 competing sites
   - What pages do they have? What keywords in their titles?
   - What sections work well? What's missing?

3. **Content plan** — Map keywords to pages:
   | Page | H1 (with keyword) | Sections | Target Keywords |
   |------|----|----|----|
   | Home | ... | Hero, TrustBar, Stats, ... | primary + secondary |
   | Services | ... | Hero, CoverageGrid, ... | service keywords |
   | About | ... | Hero, Story, Values, ... | brand + trust keywords |
   | Contact | ... | Hero, Form, Info | quote/contact keywords |
   | Blog | ... | Hero, BlogGrid | informational keywords |

4. **Write every H1 BEFORE building any page.** Every H1 must:
   - Contain the primary keyword for that page
   - Be benefit-focused (not fear-based)
   - Be specific to this business (not generic)

**Deliverable:** Content plan document with keywords, page map, all H1s drafted

### Phase 3: SCAFFOLD
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

### Phase 4: DESIGN SYSTEM
**Read:** `instructions/design-system.md`
**Use:** `templates/config/design-tokens.css`

1. Select color palette based on brand intake answers
   - Use: `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<industry> <tone>" --domain color --design-system`
2. Select font pairing
   - Use: `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<tone> <industry>" --domain typography`
3. Set CSS variables in `globals.css`
4. Configure `tailwind.config.ts` with brand colors
5. If client has no brand preferences, use `theme-factory` skill for a pre-set theme

### Phase 5: CONTENT & PAGES (the bulk of the work)
**Read:** `instructions/content-writing.md`, `instructions/animations.md`, `instructions/scroll-effects.md`
**Use:** `templates/sections/`, `templates/animations/`, `templates/pages/`

**For EACH page, follow this exact sequence:**

1. **Review the content plan** from Phase 2 — keywords, sections, H1
2. **Write ALL the copy first** — headlines, paragraphs, bullets, CTAs, testimonials, FAQ answers
   - Every headline targets a keyword from Phase 2
   - Every paragraph is benefit-focused and industry-specific
   - No generic "we deliver quality" filler — use real numbers, real scenarios, real language
   - See `instructions/content-writing.md` for guidelines by site type
3. **Select section templates** from `templates/sections/`
4. **Pass ALL content via props** — do NOT leave any template defaults in place
5. **Generate/source images** as you build each page (not later!)
   - Read `instructions/images.md`
   - Every page needs at least one real image
6. **Apply animations** — entrance animations, hover effects, scroll reveals

**Section selection by site type:**

| Site Type | Required Sections |
|-----------|-------------------|
| SEO Leadgen | Navbar + Hero + TrustBar + Stats + CoverageGrid/Features + HowItWorks + Testimonials + FAQ + CTA + Footer |
| Local Service | Navbar + Hero + TrustBar + Services + ServiceAreas + Stats + Reviews + FAQ + CTA + Footer |
| Portfolio | Navbar + Hero + ProjectGrid + About + Process + CTA + Footer |
| SaaS | Navbar + Hero + Features + Pricing + Testimonials + FAQ + CTA + Footer |

**Prop rules:**
- ALL data through props — never edit component internals for content
- Template defaults are obviously wrong (e.g., "REPLACE: Your Headline") — they MUST be replaced
- `icon` prop accepts Lucide strings: `"shield"`, `"zap"`, `"heart"`, `"clock"`, `"award"`, `"users"`, `"truck"`, etc.
- ContactForm accepts `fields` array for industry-specific forms
- Footer accepts navigation/contact props — always customize

### Phase 5b: COMPILE CHECK (required)

```bash
cd <project-dir> && pnpm build
```
Fix all errors before moving on.

### Phase 6: FORMS & BACKEND
**Read:** `instructions/forms-backend.md`

1. Build industry-specific form fields (NOT generic name/email/message)
2. Create `/api/contact` route (file-based JSON storage)
3. Test form submission end-to-end
4. Add newsletter signup to footer if needed

### Phase 7: BLOG (if needed)
**Read:** `instructions/blog-setup.md`

1. Install MDX dependencies
2. Create blog index and `[slug]` dynamic route
3. Write 2-3 starter posts targeting long-tail keywords from Phase 2
4. Add to sitemap

### Phase 8: SEO FINALIZATION
**Read:** `instructions/seo.md`, `instructions/performance.md`

1. Metadata in `layout.tsx` — use keywords from Phase 2
2. Per-page metadata with page-specific keywords
3. `sitemap.ts` and `robots.ts`
4. Structured data (JSON-LD) for business type
5. Error/404 pages
6. Image optimization

### Phase 9: QUALITY GATE (MANDATORY)
**Read:** `instructions/quality-checklist.md`

**Placeholder sweep — MUST RUN, zero tolerance:**
```bash
grep -rn "example\.com\|placeholder\|TODO\|FIXME\|Lorem\|project-name\|REPLACE:\|UPDATE:\|000-0000\|hello@\|Service One\|Service Two\|Service Three\|A short description\|Your Headline\|Business Name\.\|Sarah Johnson\|Mike Chen\|Lisa Rodriguez" src/ --include="*.tsx" --include="*.ts"
```
**Every match = failure. Fix before proceeding.**

Also manually verify:
- [ ] Navbar logo = real business name (NOT "Logo")
- [ ] Footer = real contact info (NOT placeholder phone/email/address)
- [ ] Every section heading = specific to this business (NOT generic defaults)
- [ ] Every testimonial = realistic, industry-specific (NOT generic names/quotes)
- [ ] `package.json` name matches the project
- [ ] All images point to files that actually exist
- [ ] Every page has at least one real image (not just icons)
- [ ] Phone `tel:` links match displayed text
- [ ] CTA buttons link to correct destinations
- [ ] No page uses 100% default section props

### Phase 10: DEPLOYMENT
**Read:** `instructions/deployment.md`

1. `pnpm build` — fix any errors
2. Commit, push to `web-dev` branch

**JamBot:** `cd Websites/<name> && pnpm install && pnpm build`, then canvas URL.
**No container:** Tell user admin needs `jambot-add-website.sh`.
**External:** Vercel/Netlify/Docker per `instructions/deployment.md`.

---

## Copy Guidelines (Quick Reference)

### Headlines — DO vs DON'T
| DO (keyword + benefit) | DON'T (scare tactic / generic) |
|---|---|
| "Comprehensive Insurance for Epoxy Flooring Contractors" | "One Job Goes Wrong And You're Out of Business" |
| "Licensed Plumber Serving Phoenix Since 2005" | "Your Pipes Could Burst Any Minute" |
| "Professional Garage Floor Coatings in Tampa Bay" | "Transform Your Space Today" |
| "Fast, Reliable HVAC Repair — Same-Day Service" | "Don't Suffer Another Hot Night" |

### Body Copy Rules
- Use industry-specific language the customer would search for
- Mention specific services by name, not vague categories
- Include real numbers: "20+ years", "1,000+ customers", "50 states", "same-day"
- Every paragraph advances toward the CTA — no filler
- Write for humans first, keywords second (but keywords must be present)

### Testimonials
- Realistic names + company name + location ("Marcus Thompson, Elite Epoxy Solutions, FL")
- Reference specific services or outcomes
- Vary focus: one about price, one about quality, one about speed
- Never use generic "Great service, highly recommend!" quotes

### FAQ (critical for SEO leadgen)
- Every question = a long-tail keyword people actually search
- Answers: 3-5 sentences minimum with industry-specific details
- Include cost ranges, timeframes, requirements — specific helpful info
- Link to relevant pages within answers

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
  brand-intake.md        — Discovery questions (includes SEO + competitor questions)
  research-plan.md       — Keyword research, competitor analysis, content planning (NEW)
  content-writing.md     — Copy guidelines by site type, tone, and industry (NEW)
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
  sections/              — 18 section components (Navbar, Hero, Features, FAQ, HowItWorks, TrustBar, etc.)
  animations/            — 9 reusable wrappers (FadeIn, Stagger, Parallax, etc.)
  pages/                 — 5 full page compositions (Home, About, Services, Contact, Blog)
  config/                — Project CLAUDE.md template, CSS design tokens

tools/
  scaffold.sh            — Create project, copy templates, install deps, git init
  github-setup.sh        — Create private repo, push, set up web-dev branch
```
