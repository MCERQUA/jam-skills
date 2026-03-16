# Scroll Effects

Lenis smooth scroll setup + scroll-triggered animation patterns.

---

## Lenis Setup

```bash
pnpm add lenis
```

### SmoothScroll Provider (wrap entire app)

```tsx
// src/components/animations/SmoothScroll.tsx
"use client";
import { ReactLenis } from "lenis/react";

export function SmoothScroll({ children }: { children: React.ReactNode }) {
  return (
    <ReactLenis
      root
      options={{
        lerp: 0.1,        // Smoothness (0.05=very smooth, 0.15=more responsive)
        duration: 1.2,     // Scroll duration
        smoothWheel: true, // Smooth mouse wheel
      }}
    >
      {children}
    </ReactLenis>
  );
}
```

Use in `layout.tsx`:
```tsx
<body>
  <SmoothScroll>
    {children}
  </SmoothScroll>
</body>
```

### Lenis options by site type:
| Site Type | lerp | duration | Notes |
|-----------|------|----------|-------|
| Portfolio / luxury | 0.06 | 1.5 | Very smooth, deliberate feel |
| Business / professional | 0.1 | 1.2 | Balanced default |
| E-commerce / fast | 0.15 | 0.8 | Responsive, quick |

---

## Scroll-Triggered Section Reveals

### Basic scroll reveal (most common):
```tsx
<motion.section
  initial={{ opacity: 0, y: 40 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-100px" }}
  transition={{ type: "spring", damping: 25, stiffness: 100 }}
  className="py-24 md:py-32"
>
  <div className="max-w-7xl mx-auto px-4 md:px-6">
    Section content
  </div>
</motion.section>
```

### Scroll-linked progress (for progress bars, fill effects):
```tsx
"use client";
import { useScroll, useTransform, motion } from "motion/react";

function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const width = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <motion.div
      className="fixed top-0 left-0 h-1 bg-primary z-50"
      style={{ width }}
    />
  );
}
```

---

## Parallax Patterns

### Background image parallax:
```tsx
"use client";
import { useScroll, useTransform, motion } from "motion/react";
import { useRef } from "react";
import Image from "next/image";

function ParallaxHero() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], ["0%", "30%"]);

  return (
    <section ref={ref} className="relative h-screen overflow-hidden">
      <motion.div style={{ y }} className="absolute inset-0">
        <Image
          src="/images/hero-bg.webp"
          alt="Hero background"
          fill
          className="object-cover"
          priority
        />
      </motion.div>
      <div className="relative z-10 flex items-center justify-center h-full">
        <h1 className="text-7xl font-bold">Hero Title</h1>
      </div>
    </section>
  );
}
```

### Multi-layer parallax (depth effect):
```tsx
function DepthParallax() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  const y1 = useTransform(scrollYProgress, [0, 1], [0, -100]); // Slow (far)
  const y2 = useTransform(scrollYProgress, [0, 1], [0, -200]); // Medium
  const y3 = useTransform(scrollYProgress, [0, 1], [0, -300]); // Fast (near)

  return (
    <div ref={ref} className="relative h-[200vh]">
      <motion.div style={{ y: y1 }} className="absolute ...">Background layer</motion.div>
      <motion.div style={{ y: y2 }} className="absolute ...">Middle layer</motion.div>
      <motion.div style={{ y: y3 }} className="absolute ...">Foreground layer</motion.div>
    </div>
  );
}
```

---

## Scroll-Triggered Text Animations

### Heading reveal on scroll:
```tsx
function ScrollHeading({ text }: { text: string }) {
  return (
    <motion.h2
      initial={{ opacity: 0, y: 20, filter: "blur(8px)" }}
      whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="text-3xl md:text-5xl font-heading font-bold"
    >
      {text}
    </motion.h2>
  );
}
```

### Line-by-line paragraph reveal:
```tsx
function ScrollParagraph({ lines }: { lines: string[] }) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-50px" }}
    >
      {lines.map((line, i) => (
        <motion.p
          key={i}
          variants={{
            hidden: { opacity: 0, x: -20 },
            visible: {
              opacity: 1, x: 0,
              transition: { delay: i * 0.15, duration: 0.5 },
            },
          }}
          className="text-lg text-muted-foreground"
        >
          {line}
        </motion.p>
      ))}
    </motion.div>
  );
}
```

---

## Sticky + Scroll Patterns

### Sticky section with scrolling content:
```tsx
function StickyFeatures() {
  return (
    <section className="relative">
      {/* Sticky visual */}
      <div className="sticky top-0 h-screen flex items-center justify-center">
        <div className="w-1/2">
          <Image src="/images/product.png" alt="Product" width={600} height={400} />
        </div>
      </div>

      {/* Scrolling content alongside */}
      <div className="absolute top-0 right-0 w-1/2 space-y-screen">
        {features.map((feature, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ amount: 0.5 }}
            className="h-screen flex items-center p-12"
          >
            <div>
              <h3 className="text-2xl font-bold">{feature.title}</h3>
              <p className="text-muted-foreground mt-4">{feature.description}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
```

---

## Scroll Snap (Full-Page Sections)

For sites where each section fills the viewport:

```css
/* globals.css */
html {
  scroll-snap-type: y mandatory;
}

.snap-section {
  scroll-snap-align: start;
  min-height: 100vh;
}
```

```tsx
<main>
  <section className="snap-section"><Hero /></section>
  <section className="snap-section"><Features /></section>
  <section className="snap-section"><CTA /></section>
</main>
```

**Note:** Scroll snap works WITH Lenis. Set `lenis.options.syncTouch: true` for mobile.

---

## Performance Notes

- `whileInView` uses IntersectionObserver (efficient, no scroll listener)
- `useScroll` uses scroll listeners — use sparingly (1-3 per page max)
- Parallax on mobile: consider disabling or reducing offset (GPU-intensive)
- `viewport.once: true` on all entrance animations (don't re-animate on scroll back)
- Avoid parallax on elements with `will-change: transform` already set by Motion
