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

## Tech Stack (every project)

| Tool | Package | Purpose |
|------|---------|---------|
| **Next.js 15** | `next` | App Router, server components, server actions |
| **React 19** | `react` | UI framework |
| **TypeScript** | `typescript` | Type safety |
| **Tailwind CSS v4** | `tailwindcss` | Utility-first styling |
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

## 6-Phase Workflow

Follow these phases IN ORDER. Do not skip phases.

### Phase 1: DISCOVER
**Read:** `instructions/brand-intake.md`

Ask the client the brand intake questions BEFORE writing any code. Fill in the answers — you'll use them in every subsequent phase. Do not assume brand colors, tone, or page structure.

### Phase 2: SCAFFOLD
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

### Phase 3: DESIGN SYSTEM
**Read:** `instructions/design-system.md`
**Use:** `templates/config/design-tokens.css`

1. Select color palette based on brand intake answers
   - Use: `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<industry> <tone>" --domain color --design-system`
2. Select font pairing
   - Use: `python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<tone> <industry>" --domain typography`
3. Set CSS variables in `globals.css`
4. Configure `tailwind.config.ts` with brand colors
5. If client has no brand preferences, use `theme-factory` skill for a pre-set theme

### Phase 4: BUILD PAGES
**Read:** `instructions/animations.md`, `instructions/scroll-effects.md`
**Use:** `templates/sections/`, `templates/animations/`, `templates/pages/`

For each page:
1. Copy relevant section templates from `templates/sections/`
2. Copy animation wrappers from `templates/animations/`
3. Customize: swap colors, fonts, copy, images to match brand
4. Compose the page from sections (reference `templates/pages/` for layout order)
5. Apply entrance animations, hover effects, scroll reveals
6. Test responsive at 375px, 768px, 1024px, 1440px

**Section selection by page type:**

| Page | Sections |
|------|----------|
| Home | Navbar + Hero + Features + Stats + Testimonials + CTA + Footer |
| About | Navbar + HeroSplit + Story + Team + Values + CTA + Footer |
| Services | Navbar + Hero + Features/ServiceCards + Process + FAQ + CTA + Footer |
| Contact | Navbar + ContactForm + Map/Info + Footer |
| Blog | Navbar + BlogList + Sidebar/Categories + Footer |

### Phase 5: IMAGES & ASSETS
**Read:** `instructions/images.md`

1. Gather client images or generate with gemini-image skill
2. Generate OG image for social sharing (`public/og/default.png`)
3. Create favicon from logo (or generate monogram)
4. Save all images to `public/images/` in WebP format
5. Verify every `<Image>` has real `src`, `alt`, `width`, `height`

### Phase 6: FORMS & BACKEND
**Read:** `instructions/forms-backend.md`

1. Wire up contact form with server action (Resend email, AgentMail, or file fallback)
2. Test form submission end-to-end (submit → confirm → email/save)
3. Add newsletter signup to footer if needed
4. Add error handling and validation messages

### Phase 7: BLOG (if needed)
**Read:** `instructions/blog-setup.md`

1. Install MDX dependencies
2. Create `src/lib/blog.ts` utility
3. Create blog index and `[slug]` dynamic route
4. Write 2-3 starter blog posts as `.mdx` files
5. Add blog posts to sitemap

### Phase 8: CONTENT & SEO
**Read:** `instructions/seo.md`, `instructions/performance.md`
**Reference:** `/mnt/shared-skills/marketing/copywriting/SKILL.md`, `/mnt/shared-skills/marketing/page-cro/SKILL.md`

1. Set up metadata in `layout.tsx` (title, description, OG images)
2. Create `sitemap.ts` and `robots.ts`
3. Add structured data (JSON-LD) for business type
4. Copy `templates/sections/NotFound.tsx` → `src/app/not-found.tsx`
5. Copy `templates/sections/ErrorPage.tsx` → `src/app/error.tsx`
6. Review all copy — no placeholder text, real content everywhere
7. Optimize images per `instructions/performance.md`

### Phase 9: QUALITY GATE
**Read:** `instructions/quality-checklist.md`

Run the full checklist BEFORE presenting to client. Fix every failure. Do not present a site that fails any critical check.

### Phase 10: DEPLOYMENT
**Read:** `instructions/deployment.md`

1. Run `pnpm build` — fix any errors
2. Push all changes to `web-dev` branch on GitHub
3. Tell user: site is ready for deployment
4. For JamBot clients: admin runs `jambot-add-website.sh`
5. For external: deploy via Vercel, Netlify, or Docker

---

## Style Rules

**REQUIRED:**
- Dark mode as default design (light mode optional addition)
- Professional dark palette: backgrounds `#0a0a0a` / `#0d1117`, text `#e2e8f0`
- Brand accent colors via CSS variables (not hardcoded)
- All interactive elements: hover state + `cursor-pointer`
- Animations respect `prefers-reduced-motion`
- Mobile-first responsive (375px → up)
- SVG icons from `lucide-react` only

**BANNED:**
- Purple (`#764ba2`, `#667eea`, `#8b5cf6`), pink, magenta as primary colors
- Emoji as UI icons
- Lorem ipsum or placeholder text in delivered pages
- `href="#"` on buttons (use `<button>` or real links)
- External CDN scripts (Tailwind CDN, Bootstrap CDN, etc.)
- Inline styles (use Tailwind classes or CSS modules)

---

## Fetching Fresh Docs (On Demand)

When you need current API reference for any library, fetch its docs:

```bash
# shadcn/ui — component list, installation, API
curl -s https://ui.shadcn.com/llms.txt | head -200

# Next.js — App Router, server components, API routes
curl -s https://nextjs.org/docs/llms.txt | head -200

# Tailwind CSS — utility classes, configuration
curl -s https://tailwindcss.com/docs/llms.txt | head -200
```

Only fetch when you need specific API details. The templates and instructions in this skill cover 90% of what you need.

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
  brand-intake.md        — Questions to ask before building
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
  sections/              — 15 section components (Navbar, Hero, Features, Pricing, etc.)
  animations/            — 9 reusable wrappers (FadeIn, Stagger, Parallax, etc.)
  pages/                 — 5 full page compositions (Home, About, Services, Contact, Blog)
  config/                — Project CLAUDE.md template, CSS design tokens

tools/
  scaffold.sh            — Create project, copy templates, install deps, git init
  github-setup.sh        — Create private repo, push, set up web-dev branch
```
