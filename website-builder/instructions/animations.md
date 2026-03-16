# Animation Patterns

15+ ready-to-use animation patterns using Motion.dev (React), GSAP, and CSS.
Copy the animation wrapper components from `templates/animations/` and use these patterns.

---

## Motion.dev Fundamentals

```bash
pnpm add motion
```

```tsx
"use client";
import { motion } from "motion/react";
```

### Spring presets (use instead of duration-based timing):
```tsx
// Smooth, no bounce — section entrances, page transitions
{ type: "spring", damping: 25, stiffness: 120 }

// Snappy — button hovers, small interactions
{ type: "spring", damping: 20, stiffness: 300 }

// Bouncy — playful brands, attention-grabbing
{ type: "spring", damping: 8, stiffness: 100 }

// Heavy — luxury brands, dramatic reveals
{ type: "spring", damping: 30, stiffness: 60, mass: 2 }
```

---

## Pattern 1: Fade In + Slide Up (most common)

Use for: section entrances, card reveals, any content appearing on scroll.

```tsx
<motion.div
  initial={{ opacity: 0, y: 30 }}
  whileInView={{ opacity: 1, y: 0 }}
  viewport={{ once: true, margin: "-100px" }}
  transition={{ type: "spring", damping: 25, stiffness: 120 }}
>
  {children}
</motion.div>
```

**Key:** `viewport.once: true` — animate only on first appearance, not every scroll pass. `margin: "-100px"` triggers slightly before element enters viewport.

---

## Pattern 2: Staggered Children

Use for: feature grids, card lists, navigation items, any repeated elements.

```tsx
const container = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.1 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", damping: 25, stiffness: 120 },
  },
};

<motion.div
  variants={container}
  initial="hidden"
  whileInView="visible"
  viewport={{ once: true, margin: "-50px" }}
  className="grid grid-cols-1 md:grid-cols-3 gap-8"
>
  {items.map((item, i) => (
    <motion.div key={i} variants={item}>
      <Card>{item.content}</Card>
    </motion.div>
  ))}
</motion.div>
```

---

## Pattern 3: Scale + Spring Hover

Use for: buttons, cards, interactive elements.

```tsx
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
  transition={{ type: "spring", damping: 15, stiffness: 300 }}
  className="px-8 py-3 bg-primary text-primary-foreground rounded-lg cursor-pointer"
>
  Get Started
</motion.button>
```

For cards with lift effect:
```tsx
<motion.div
  whileHover={{ y: -8, boxShadow: "0 20px 40px rgba(0,0,0,0.3)" }}
  transition={{ type: "spring", damping: 20, stiffness: 200 }}
  className="p-8 bg-card rounded-xl border border-border cursor-pointer"
>
  Card content
</motion.div>
```

---

## Pattern 4: Typewriter Text

Use for: hero headlines, emphasis text, loading states.

```tsx
"use client";
import { useState, useEffect } from "react";
import { motion } from "motion/react";

function Typewriter({ text, speed = 50, delay = 0 }: {
  text: string;
  speed?: number;
  delay?: number;
}) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    const timeout = setTimeout(() => {
      let i = 0;
      const interval = setInterval(() => {
        setDisplayed(text.slice(0, i + 1));
        i++;
        if (i >= text.length) clearInterval(interval);
      }, speed);
      return () => clearInterval(interval);
    }, delay);
    return () => clearTimeout(timeout);
  }, [text, speed, delay]);

  return (
    <span>
      {displayed}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
      >
        |
      </motion.span>
    </span>
  );
}
```

---

## Pattern 5: Animated Counter

Use for: stats sections, KPIs, numeric highlights.

```tsx
"use client";
import { useEffect, useRef, useState } from "react";
import { useInView, animate } from "motion/react";

function Counter({ target, suffix = "", duration = 2 }: {
  target: number;
  suffix?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    const controls = animate(0, target, {
      duration,
      onUpdate: (v) => setValue(Math.round(v)),
    });
    return controls.stop;
  }, [isInView, target, duration]);

  return (
    <span ref={ref}>
      {value.toLocaleString()}{suffix}
    </span>
  );
}

// Usage:
<Counter target={500} suffix="+" />     // "500+"
<Counter target={99} suffix="%" />      // "99%"
<Counter target={15000} suffix="" />    // "15,000"
```

---

## Pattern 6: Text Reveal (word by word)

Use for: hero subheadings, testimonial quotes, impactful statements.

```tsx
function TextReveal({ text, className }: { text: string; className?: string }) {
  const words = text.split(" ");

  return (
    <motion.p
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true }}
      className={className}
    >
      {words.map((word, i) => (
        <motion.span
          key={i}
          className="inline-block mr-[0.25em]"
          variants={{
            hidden: { opacity: 0, y: 10, filter: "blur(4px)" },
            visible: {
              opacity: 1,
              y: 0,
              filter: "blur(0px)",
              transition: {
                delay: i * 0.08,
                type: "spring",
                damping: 25,
                stiffness: 120,
              },
            },
          }}
        >
          {word}
        </motion.span>
      ))}
    </motion.p>
  );
}
```

---

## Pattern 7: Infinite Marquee

Use for: logo tickers, client lists, feature highlights.

```tsx
function InfiniteMarquee({ children, speed = 30 }: {
  children: React.ReactNode;
  speed?: number;
}) {
  return (
    <div className="overflow-hidden">
      <div
        className="flex gap-8 animate-marquee"
        style={{ "--speed": `${speed}s` } as React.CSSProperties}
      >
        {children}
        {children} {/* Duplicate for seamless loop */}
      </div>
    </div>
  );
}
```

CSS (add to globals.css):
```css
@keyframes marquee {
  from { transform: translateX(0); }
  to { transform: translateX(-50%); }
}
.animate-marquee {
  animation: marquee var(--speed, 30s) linear infinite;
  width: max-content;
}
```

---

## Pattern 8: Parallax Scroll Offset

Use for: background images, decorative elements, depth effects.

```tsx
"use client";
import { useScroll, useTransform, motion } from "motion/react";
import { useRef } from "react";

function Parallax({ children, offset = 50 }: {
  children: React.ReactNode;
  offset?: number;
}) {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], [offset, -offset]);

  return (
    <motion.div ref={ref} style={{ y }}>
      {children}
    </motion.div>
  );
}
```

---

## Pattern 9: Gradient Background Shift

Use for: hero backgrounds, ambient section backgrounds.

```css
/* Add to globals.css */
@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.animate-gradient {
  background-size: 200% 200%;
  animation: gradient-shift 8s ease infinite;
}
```

```tsx
<div className="animate-gradient bg-gradient-to-br from-primary/20 via-accent/10 to-background">
  <Hero />
</div>
```

---

## Pattern 10: Magnetic Hover (cursor follow)

Use for: CTA buttons, featured cards, hero elements.

```tsx
"use client";
import { motion, useMotionValue, useSpring } from "motion/react";
import { useRef } from "react";

function MagneticHover({ children, strength = 0.3 }: {
  children: React.ReactNode;
  strength?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { damping: 20, stiffness: 200 });
  const springY = useSpring(y, { damping: 20, stiffness: 200 });

  const handleMouse = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    x.set((e.clientX - centerX) * strength);
    y.set((e.clientY - centerY) * strength);
  };

  const reset = () => { x.set(0); y.set(0); };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      style={{ x: springX, y: springY }}
    >
      {children}
    </motion.div>
  );
}
```

---

## Pattern 11: Card 3D Tilt

Use for: feature cards, portfolio items, pricing cards.

```tsx
"use client";
import { motion, useMotionValue, useSpring, useTransform } from "motion/react";
import { useRef } from "react";

function TiltCard({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0.5);
  const y = useMotionValue(0.5);

  const rotateX = useSpring(useTransform(y, [0, 1], [8, -8]), { damping: 20, stiffness: 150 });
  const rotateY = useSpring(useTransform(x, [0, 1], [-8, 8]), { damping: 20, stiffness: 150 });

  const handleMouse = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    x.set((e.clientX - rect.left) / rect.width);
    y.set((e.clientY - rect.top) / rect.height);
  };

  const reset = () => { x.set(0.5); y.set(0.5); };

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      style={{ rotateX, rotateY, transformPerspective: 1000 }}
      className="p-8 bg-card rounded-xl border border-border"
    >
      {children}
    </motion.div>
  );
}
```

---

## Pattern 12: Blur-In Text

Use for: subheadings, taglines, secondary text entrances.

```tsx
<motion.p
  initial={{ opacity: 0, filter: "blur(10px)", y: 10 }}
  whileInView={{ opacity: 1, filter: "blur(0px)", y: 0 }}
  viewport={{ once: true }}
  transition={{ duration: 0.8, ease: "easeOut" }}
  className="text-lg text-muted-foreground"
>
  Your subheading text here
</motion.p>
```

---

## Pattern 13: SVG Path Draw

Use for: logo reveals, icon animations, decorative line art.

```tsx
<motion.svg viewBox="0 0 100 100" className="w-24 h-24">
  <motion.path
    d="M10 80 Q 50 10 90 80"
    fill="none"
    stroke="currentColor"
    strokeWidth={2}
    initial={{ pathLength: 0 }}
    whileInView={{ pathLength: 1 }}
    viewport={{ once: true }}
    transition={{ duration: 1.5, ease: "easeInOut" }}
  />
</motion.svg>
```

---

## Pattern 14: Floating Background Orbs

Use for: ambient backgrounds, hero sections, decorative depth.

```tsx
function FloatingOrbs() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <motion.div
        className="absolute w-96 h-96 rounded-full bg-primary/10 blur-3xl"
        animate={{
          x: [0, 30, -20, 0],
          y: [0, -40, 20, 0],
          scale: [1, 1.1, 0.9, 1],
        }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        style={{ top: "10%", left: "20%" }}
      />
      <motion.div
        className="absolute w-80 h-80 rounded-full bg-accent/10 blur-3xl"
        animate={{
          x: [0, -25, 35, 0],
          y: [0, 30, -25, 0],
          scale: [1, 0.9, 1.1, 1],
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        style={{ top: "50%", right: "15%" }}
      />
    </div>
  );
}
```

---

## Pattern 15: Page Transition (Layout Animation)

Use for: page-level transitions in Next.js.

```tsx
// src/app/template.tsx
"use client";
import { motion } from "motion/react";

export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
```

---

## Reduced Motion

**ALWAYS** wrap motion patterns with reduced-motion support. The animation wrapper components in `templates/animations/` handle this automatically. If writing custom animations:

```tsx
import { useReducedMotion } from "motion/react";

function MyAnimation({ children }) {
  const prefersReduced = useReducedMotion();

  return (
    <motion.div
      initial={prefersReduced ? false : { opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
    >
      {children}
    </motion.div>
  );
}
```

Or use CSS:
```css
@media (prefers-reduced-motion: reduce) {
  .animate-marquee { animation: none; }
  .animate-gradient { animation: none; }
}
```
