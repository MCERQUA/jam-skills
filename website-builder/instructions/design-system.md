# Design System Setup

Set up the visual foundation before building any pages.

---

## Step 1: Color Palette

### If client provided brand colors:
Use their colors as primary. Build supporting palette:
- **Primary:** Client's main brand color
- **Secondary:** Complementary or analogous to primary
- **Accent:** High-contrast pop color for CTAs and highlights
- **Background:** Dark (`#0a0a0a` to `#0d1117`) or light (`#fafafa` to `#ffffff`)
- **Surface:** Slightly lighter than background for cards (`#111827`, `#1a1d2e`)
- **Text:** High contrast (`#e2e8f0` on dark, `#0f172a` on light)
- **Muted:** De-emphasized text (`#94a3b8`)
- **Border:** Subtle separation (`#1e293b` on dark, `#e2e8f0` on light)

### If no brand colors:
Query the design system database:
```bash
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<industry> <tone>" --domain color
```

Or use a `theme-factory` preset:
```
Read /mnt/shared-skills/theme-factory/SKILL.md
```

### BANNED colors (never as primary or dominant):
- Purple: `#764ba2`, `#667eea`, `#8b5cf6`, `#7c3aed`
- Pink: `#ec4899`, `#f472b6`
- Magenta: `#d946ef`, `#a855f7`

### Recommended accent colors:
- Blue: `#3b82f6` — trust, technology
- Cyan: `#06b6d4` — modern, fresh
- Amber: `#f59e0b` — energy, attention
- Emerald: `#10b981` — growth, success
- Orange: `#f97316` — action, warmth
- Red: `#ef4444` — urgency (use sparingly)

---

## Step 2: Typography

### Font pairing query:
```bash
python3 /mnt/shared-skills/ui-ux-pro-max/scripts/search.py "<tone> <industry>" --domain typography
```

### Recommended pairings by tone:

| Tone | Heading | Body | Import |
|------|---------|------|--------|
| Professional | Inter (700/800) | Inter (400/500) | `@next/font/google` |
| Friendly | Plus Jakarta Sans (700) | Inter (400) | `@next/font/google` |
| Bold | Space Grotesk (700) | DM Sans (400) | `@next/font/google` |
| Luxury | Playfair Display (700) | Lato (300/400) | `@next/font/google` |
| Technical | JetBrains Mono (700) | Inter (400) | `@next/font/google` |
| Modern | Outfit (700/800) | Inter (400/500) | `@next/font/google` |

### Type scale:
```
Hero H1:      text-5xl md:text-7xl  (48-72px) font-bold/black
Section H2:   text-3xl md:text-5xl  (30-48px) font-bold
Card title:   text-xl md:text-2xl   (20-24px) font-semibold
Body:         text-base md:text-lg  (16-18px) font-normal
Small/meta:   text-sm               (14px)    font-medium text-muted
```

### Line heights:
- Headings: `leading-tight` (1.25)
- Body: `leading-relaxed` (1.625)
- UI text: `leading-normal` (1.5)

---

## Step 3: CSS Variables

Set in `src/app/globals.css`. Use the `design-tokens.css` template and fill in:

```css
:root {
  /* Brand colors */
  --primary: <client primary>;
  --primary-foreground: <contrast text on primary>;
  --secondary: <secondary color>;
  --accent: <accent color>;

  /* Backgrounds */
  --background: #0a0a0a;
  --foreground: #e2e8f0;
  --card: #111827;
  --card-foreground: #e2e8f0;

  /* Borders & muted */
  --border: #1e293b;
  --muted: #1e293b;
  --muted-foreground: #94a3b8;

  /* Radius */
  --radius: 0.75rem;
}
```

These variables are consumed by shadcn/ui components automatically.

---

## Step 4: Tailwind Config

Extend `tailwind.config.ts` to reference CSS variables:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        heading: ["var(--font-heading)"],
        body: ["var(--font-body)"],
      },
    },
  },
};

export default config;
```

---

## Step 5: Spacing Rules

Consistent spacing prevents the "amateur" look:

| Element | Spacing | Tailwind |
|---------|---------|----------|
| Page sections | 96-128px vertical | `py-24 md:py-32` |
| Section content max-width | 1280px | `max-w-7xl mx-auto` |
| Section horizontal padding | 16-24px | `px-4 md:px-6` |
| Card padding | 24-32px | `p-6 md:p-8` |
| Grid gaps | 24-32px | `gap-6 md:gap-8` |
| Between headings and content | 16-24px | `mt-4 md:mt-6` |
| Between sections internally | 48-64px | `space-y-12 md:space-y-16` |

**Common mistake:** Using `py-8` or `gap-4` for major sections. This makes the site feel cramped. Professional sites use generous whitespace.
