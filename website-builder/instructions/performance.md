# Performance Optimization

Core Web Vitals and loading performance rules.

---

## Images

### Always use Next.js Image component:
```tsx
import Image from "next/image";

<Image
  src="/images/hero-bg.webp"
  alt="Descriptive alt text"
  width={1920}
  height={1080}
  priority  // Only for above-the-fold images
  className="object-cover"
/>
```

### Rules:
- **Always provide `width` and `height`** — prevents Cumulative Layout Shift (CLS)
- **Use `priority` on hero images** — preloads them
- **Use WebP format** when possible (smaller than PNG/JPG)
- **Use `sizes` for responsive images:**
  ```tsx
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
  ```
- **Never use `fill` without a sized container** — causes layout shift

### Image domains (next.config.ts):
```typescript
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      // Add client's image CDN here
    ],
  },
};
```

---

## Fonts

### Use `next/font/google` — automatic optimization:
```typescript
// src/lib/fonts.ts
import { Inter, Space_Grotesk } from "next/font/google";

export const bodyFont = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

export const headingFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "600", "700"],
  display: "swap",
});
```

- `display: "swap"` prevents invisible text during load
- `subsets: ["latin"]` reduces font file size
- `variable` creates CSS custom property for Tailwind

---

## Code Splitting

Next.js App Router handles this automatically. Help it by:

### Dynamic imports for heavy components:
```tsx
import dynamic from "next/dynamic";

const Map = dynamic(() => import("@/components/sections/Map"), {
  loading: () => <div className="h-96 bg-card animate-pulse rounded-lg" />,
  ssr: false,  // Maps don't need server rendering
});
```

### Use dynamic imports for:
- Map components (Leaflet, Google Maps)
- Chart libraries
- 3D components (Three.js)
- Heavy animation sequences
- Components that use `window` or `document`

---

## Animation Performance

### Use `transform` and `opacity` only:
These properties are GPU-accelerated and don't trigger layout recalculation:
- `transform: translateX/Y/Z, scale, rotate`
- `opacity`
- `filter` (blur, brightness)

### Avoid animating:
- `width`, `height` (triggers layout)
- `top`, `left`, `right`, `bottom` (triggers layout)
- `margin`, `padding` (triggers layout)
- `border-width` (triggers layout)
- `font-size` (triggers layout)

### Motion.dev handles this automatically:
```tsx
// Good — Motion animates transform under the hood
<motion.div animate={{ x: 100, opacity: 1 }} />

// Bad — directly animating layout properties
<motion.div animate={{ width: "100%", marginLeft: 20 }} />
```

### Respect reduced motion:
```tsx
import { useReducedMotion } from "motion/react";

function AnimatedComponent() {
  const prefersReduced = useReducedMotion();

  return (
    <motion.div
      initial={prefersReduced ? false : { opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
    >
      Content
    </motion.div>
  );
}
```

---

## Lazy Loading

### Below-fold sections:
Wrap heavy below-fold sections in Suspense:
```tsx
import { Suspense } from "react";

<Suspense fallback={<div className="h-96 animate-pulse bg-card" />}>
  <Testimonials />
</Suspense>
```

### Intersection Observer for animations:
Motion.dev's `whileInView` handles this — animations only trigger when visible. Don't preload animation states.

---

## Bundle Size Checklist

Before delivery, verify:
- [ ] No unused dependencies in `package.json`
- [ ] Dynamic imports for map/chart/3D components
- [ ] No full lodash import (use specific: `lodash/debounce`)
- [ ] Images optimized (WebP, proper dimensions)
- [ ] Fonts subset to `latin` only (unless other scripts needed)
- [ ] No `console.log` statements in production code
