# On-Demand Documentation References

Fetch these when you need current API details. The templates and instructions cover 90% of cases — only fetch docs for edge cases or unfamiliar APIs.

---

## llms.txt Files (Optimized for AI)

These are curated documentation designed for AI context windows. Fetch with curl:

```bash
# shadcn/ui — components, installation, theming, CLI
curl -s https://ui.shadcn.com/llms.txt | head -300

# Next.js — App Router, API routes, server components, metadata
curl -s https://nextjs.org/docs/llms.txt | head -300

# Next.js (full, very large) — only when you need deep API reference
curl -s https://nextjs.org/docs/llms-full.txt | head -500

# Tailwind CSS — utility classes, configuration, plugins
curl -s https://tailwindcss.com/docs/llms.txt | head -300

# Clerk — authentication (if project needs auth)
curl -s https://clerk.com/llms.txt | head -200
```

---

## NPM Package Docs

When you need specific API for a package:

```bash
# Motion.dev — animation API, hooks, components
# No llms.txt available. Use the patterns in instructions/animations.md.
# For edge cases, check: https://motion.dev/docs

# Lenis — scroll API, options, events
# No llms.txt. Use instructions/scroll-effects.md.
# For edge cases, check: https://lenis.darkroom.engineering/docs

# Lucide React — icon names and usage
# Search for an icon: https://lucide.dev/icons
# Usage: import { IconName } from "lucide-react";
```

---

## ui-ux-pro-max Design Database

Query the local design database for palettes, typography, UX rules:

```bash
# Full design system for a project type
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "plumbing service business" --design-system

# Color palettes by industry/mood
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "modern tech blue" --domain color

# Font pairings by style
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "professional clean" --domain typography

# UX best practices
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "form validation" --domain ux

# Landing page patterns
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "hero section" --domain landing

# Chart types (if dashboard-like pages)
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "bar chart" --domain chart
```

---

## Related Skills (read when needed)

| Need | Skill Path |
|------|-----------|
| Copywriting for web pages | `/mnt/shared-skills/marketing/copywriting/SKILL.md` |
| Page conversion optimization | `/mnt/shared-skills/marketing/page-cro/SKILL.md` |
| Site architecture & navigation | `/mnt/shared-skills/marketing/site-architecture/SKILL.md` |
| Local SEO for service businesses | `/mnt/shared-skills/marketing/local-seo/SKILL.md` |
| Pre-set color/font themes | `/mnt/shared-skills/theme-factory/SKILL.md` |
| AI image generation (for site assets) | `/mnt/shared-skills/gemini-image/SKILL.md` |
| Icon generation | `/mnt/shared-skills/icon-generation/SKILL.md` |

---

## Component Library Quick Reference

### shadcn/ui components (install with CLI):
```bash
pnpm dlx shadcn@latest add <component>
```

Most commonly needed for websites:
- `button` — CTAs, navigation, forms
- `card` — feature cards, testimonials, pricing
- `badge` — labels, tags, status indicators
- `separator` — section dividers
- `input` — form fields
- `textarea` — contact form message
- `label` — form labels
- `select` — dropdowns
- `dialog` — modals, popups
- `sheet` — mobile navigation slide-out
- `accordion` — FAQ sections
- `tabs` — tabbed content (pricing toggle, service categories)
- `avatar` — team member photos, testimonials
- `navigation-menu` — desktop navigation with dropdowns
- `toast` — form submission feedback

### Lucide React icons (import directly):
```tsx
import { ArrowRight, Check, Star, Phone, Mail, MapPin, Menu, X } from "lucide-react";

// Usage:
<ArrowRight className="w-5 h-5" />
```

Common icons for business sites:
- Navigation: `Menu`, `X`, `ChevronDown`, `ArrowRight`
- Contact: `Phone`, `Mail`, `MapPin`, `Clock`
- Features: `Check`, `Star`, `Shield`, `Zap`, `Heart`, `Award`
- Social: `Github`, `Twitter`, `Linkedin`, `Facebook`, `Instagram`
- Actions: `Download`, `ExternalLink`, `Copy`, `Search`
