# Brand Intake — Client Discovery Questions

Ask these questions BEFORE writing any code. The answers drive every design decision.

---

## Required Questions

### 1. Business Identity
> "What's your business name, and what do you do in one sentence?"

Use for: hero headline, meta description, structured data.

### 2. Industry & Niche
> "What industry are you in? Any specific niche?"

Use for: color palette selection (via ui-ux-pro-max), imagery style, section choices.

### 3. Target Customer
> "Who's your ideal customer? Age range, profession, what problem are they solving?"

Use for: tone, copy voice, CTA wording, page structure.

### 4. Brand Colors & Logo
> "Do you have brand colors or a logo? If so, share them. If not, any color preferences?"

Use for: CSS variables, tailwind config, gradient directions.
- If they have colors: use them as primary/secondary
- If they have preferences: build palette around them
- If no preference: use `ui-ux-pro-max search.py` with their industry

### 5. Tone & Personality
> "How should your site feel? Pick one: Professional / Friendly / Bold / Playful / Luxury / Technical"

Use for: typography weight, animation intensity, spacing, copy style.

| Tone | Typography | Animation | Spacing |
|------|-----------|-----------|---------|
| Professional | Clean sans-serif, moderate weight | Subtle fades, slow springs | Generous, airy |
| Friendly | Rounded sans-serif, varied weight | Bouncy springs, playful | Balanced |
| Bold | Heavy sans-serif, high contrast | Quick snappy entrances | Tight, impactful |
| Playful | Mix of serif/sans, fun pairings | Bouncy, overshooting springs | Relaxed |
| Luxury | Elegant serif + thin sans | Slow, smooth reveals | Very generous |
| Technical | Monospace + clean sans | Precise, mechanical | Structured grid |

### 6. Reference Sites
> "Any websites you like the look or feel of? Share 2-3 URLs."

Use for: layout inspiration, animation style, section ordering. Do NOT copy — extract the principles.

### 7. Pages Needed
> "What pages do you need? Here's what most businesses start with: Home, About, Services, Contact, Blog. Want all of these, or different ones?"

Use for: routing structure, navigation items, section planning.

### 8. Special Features
> "Any specific features? Examples: booking form, portfolio gallery, team page, pricing table, FAQ, newsletter signup, e-commerce"

Use for: dependency choices (Prisma for DB, Stripe for payments, etc.), additional section templates.

### 9. Content Readiness
> "Do you have content ready — text copy, images, testimonials, team photos? Or do we need to create placeholder content for now?"

Use for: deciding whether to write real copy or mark sections for content replacement.

### 10. Primary Call-to-Action
> "What's the ONE thing you want visitors to do? Book a call / Get a quote / Shop now / Sign up / Contact us"

Use for: hero CTA button, repeated CTA sections, navigation emphasis.

### 11. SEO & Search Goals
> "What do you want people to find you for on Google? What would your ideal customer type into a search engine?"

Use for: keyword research in Phase 2, headline writing, meta descriptions.

### 12. Competitors
> "Who are your top 2-3 competitors? Share their website URLs if you know them."

Use for: competitor analysis in Phase 2, identifying gaps and opportunities.

### 13. Geographic Scope
> "Do you serve a specific area (city/state/region) or are you nationwide/online?"

Use for: local SEO keywords, service area pages, structured data.

### 14. Site Type
> "What's the main purpose of your site?"
> - **SEO Leadgen** — rank on Google and capture form submissions (insurance, professional services)
> - **Local Service** — get phone calls and appointment bookings (plumber, HVAC, contractor)
> - **Portfolio** — showcase your work and build authority (designer, photographer, agency)
> - **SaaS / Product** — get signups and sales (software, online product)

Use for: section selection, copy style, page structure decisions. This choice drives the entire build.

---

## After Intake

1. Summarize answers back to the client for confirmation
2. Fill in `templates/config/claude-project.md` with the answers
3. Save as `.claude/CLAUDE.md` in the project directory
4. Reference this file throughout the build — every design decision traces back to these answers
