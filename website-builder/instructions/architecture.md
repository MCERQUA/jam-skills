# Next.js Architecture Guide

Standard project structure and conventions for all website builds.

---

## App Router Structure

```
src/
├── app/
│   ├── layout.tsx          ← Root layout: fonts, metadata, SmoothScroll provider
│   ├── page.tsx            ← Home page
│   ├── globals.css         ← CSS variables, base styles
│   ├── about/
│   │   └── page.tsx
│   ├── services/
│   │   └── page.tsx
│   ├── contact/
│   │   └── page.tsx
│   └── blog/
│       ├── page.tsx        ← Blog index
│       └── [slug]/
│           └── page.tsx    ← Individual blog post
├── components/
│   ├── ui/                 ← shadcn components (auto-installed via CLI)
│   ├── sections/           ← Page sections (Hero, Navbar, Footer, Features, etc.)
│   ├── animations/         ← Animation wrappers (FadeIn, Stagger, etc.)
│   └── shared/             ← Reusable: Logo, ThemeToggle, SocialLinks
├── lib/
│   ├── utils.ts            ← cn() helper, formatters
│   └── fonts.ts            ← Google font configuration
└── content/                ← MDX blog posts (if blog is needed)
    └── posts/
```

---

## Key Conventions

### File naming
- Components: PascalCase (`Hero.tsx`, `Navbar.tsx`)
- Utilities: camelCase (`utils.ts`, `fonts.ts`)
- Pages: always `page.tsx` (Next.js convention)
- Layouts: always `layout.tsx`

### Component organization
- **`sections/`** — Full-width page sections. Each is self-contained with its own styles.
- **`animations/`** — Wrapper components that add motion. Used around or inside sections.
- **`ui/`** — shadcn components. Never edit these directly — customize via CSS variables.
- **`shared/`** — Small reusable components used across multiple sections.

### Imports
Always use the `@/` path alias:
```tsx
import { Hero } from "@/components/sections/Hero";
import { FadeIn } from "@/components/animations/FadeIn";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
```

---

## Root Layout Pattern

```tsx
// src/app/layout.tsx
import type { Metadata } from "next";
import { headingFont, bodyFont } from "@/lib/fonts";
import { SmoothScroll } from "@/components/animations/SmoothScroll";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Business Name — Tagline",
    template: "%s | Business Name",
  },
  description: "One-sentence business description for SEO.",
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "Business Name",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${headingFont.variable} ${bodyFont.variable}`}>
      <body className="bg-background text-foreground font-body antialiased">
        <SmoothScroll>
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}
```

---

## Page Composition Pattern

Each page file composes sections:

```tsx
// src/app/page.tsx
import { Navbar } from "@/components/sections/Navbar";
import { Hero } from "@/components/sections/Hero";
import { Features } from "@/components/sections/Features";
import { Stats } from "@/components/sections/Stats";
import { Testimonials } from "@/components/sections/Testimonials";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";

export default function HomePage() {
  return (
    <main>
      <Navbar />
      <Hero />
      <Features />
      <Stats />
      <Testimonials />
      <CTA />
      <Footer />
    </main>
  );
}
```

---

## Server vs Client Components

**Default to Server Components** (no `"use client"` directive). Only add `"use client"` when the component needs:
- `useState`, `useEffect`, `useRef`
- Event handlers (`onClick`, `onChange`)
- Browser APIs (`window`, `document`)
- Animation libraries (Motion, Lenis)

**Pattern:** Keep the page as a server component. Import client components for interactive parts.

```tsx
// Server component (page.tsx) — handles data, metadata
// Client component (Hero.tsx) — handles animations, interactions
```

---

## Data Flow

### Static content (most business sites):
- Hardcode content in section components
- Or import from `content/` directory (MDX, JSON)
- No API calls needed — site is fully static at build time

### Dynamic content (blog, products):
- Use server components with `async` to fetch data
- Use Next.js `generateStaticParams()` for static generation of dynamic routes
- Use server actions for form submissions

---

## Git Workflow

1. All work happens on `web-dev` branch
2. Never push directly to `main`
3. Commit after each meaningful change (not after every file)
4. Push to GitHub regularly
5. Production deploys via PR: `web-dev` → `main`

### Commit message style:
```
feat: add hero section with scroll animations
fix: navbar mobile menu z-index overlap
style: update color palette to match brand guidelines
content: add about page copy and team photos
```
