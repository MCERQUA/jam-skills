---
name: canvas-web-design
description: Premium canvas page design system for iframe-sandboxed HTML. Animations, glassmorphism, gradient text, layered backgrounds — all vanilla CSS. No CDN, no npm. Read this before building any canvas page with z-code.
---

# Canvas Web Design — Premium Design System

You are building canvas pages that run inside an iframe in the JamBot voice assistant. These are **NOT** regular websites. They must work with zero external dependencies and deliver **AAA-quality visual output** every time.

---

## THE ENVIRONMENT (Non-Negotiable Constraints)

- **Sandboxed iframe** — No `<script src="https://...">`, no CDN, no npm packages
- **Google Fonts `@import` in `<style>` is OK** — always falls back to `sans-serif`
- **All CSS inline** in a `<style>` tag in `<head>`
- **All JS inline** in a `<script>` tag at body end
- **Interactivity only via postMessage** — `nav(page)` and `speak(text)` functions (always include these)
- **Always start from** `/app/runtime/canvas-template.html` — copy the FULL `<style>` block first

---

## DESIGN PHILOSOPHY

Every canvas page must feel like **premium enterprise software**. Not a template, not a demo — something a Fortune 500 company would actually ship.

### The Standard
- Multi-layered visual depth: ambient orbs, border gradients, card shadows, glows
- Meaningful animation: staggered entrance, hover micro-interactions, living status indicators
- Strong typography hierarchy: massive numbers, bold labels, readable secondary text
- Color with purpose: semantic colors signal meaning, not just decoration
- Real content: every value, label, and button reflects the actual task — no placeholders

### What "Bad" Looks Like — Never Do This
- White text on dark background, zero hierarchy — "flat and forgettable"
- Static pages with no animation — "it just... appeared"
- Cards that are just a border around text
- Buttons with no hover state
- Purple/pink gradients — the most overused AI default in existence
- Emoji as decorative icons

---

## COLOR SYSTEM

Use CSS variables from the design system. **Never hardcode hex values** that duplicate the vars.

```css
/* Backgrounds */
--bg: #0d0f17          /* page background */
--surface: #141620     /* card fills */
--surface-2: #1a1d2e   /* deeper card fills */
--surface-hover: #1f2235  /* hover state */

/* Brand */
--brand: #3b82f6       /* primary blue */
--brand-light: #60a5fa /* lighter blue for text */
--cyan: #22d3ee        /* accent cyan */
--amber: #f59e0b       /* energy, warnings */

/* Semantic */
--success: #34d399     /* green — positive */
--warning: #fbbf24     /* yellow — caution */
--danger: #f87171      /* red — alerts */

/* Text */
--text: #e8eaf0        /* primary */
--text-secondary: #9498ab  /* secondary */
--text-muted: #5f6380  /* labels, hints */
```

### BANNED Colors — Instant Rejection
- Any purple: `#764ba2`, `#667eea`, `#8b5cf6`, `#a855f7`
- Pink / magenta as primary
- `linear-gradient(135deg, #667eea, #764ba2)` — the world's most overused AI gradient

---

## TYPOGRAPHY

```css
/* Hero KPI — massive, bold */
font-size: 36px; font-weight: 900; letter-spacing: -2px;

/* Section headings */
font-size: 18px; font-weight: 800; letter-spacing: -0.4px;

/* Card titles */
font-size: 14px; font-weight: 700;

/* Body / description text */
font-size: 13px; color: var(--text-secondary); line-height: 1.6;

/* Uppercase labels */
font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted);
```

---

## ANIMATION LIBRARY

The v2.0 template includes all these keyframes. Use the utility classes — don't rewrite them.

### Entrance Animations — Apply to Every Major Section

```html
<!-- Stagger sections for a fluid cascade effect -->
<div class="page-header anim-fade"></div>
<div class="card-hero anim-scale"></div>
<div class="kpi-grid anim-slide-up delay-1"></div>
<div class="section-label anim-fade delay-2"></div>
<div class="card anim-slide-up delay-3"></div>
<div class="card anim-slide-up delay-4"></div>
<div class="action-grid anim-slide-up delay-5"></div>
```

Available classes: `anim-fade`, `anim-slide-up`, `anim-slide-left`, `anim-scale`
Delay classes: `delay-1` through `delay-8` (0.1s increments)

### Hover Micro-Interactions — Every Clickable Element

```css
/* Standard lift + shadow */
.my-element { transition: all 0.25s ease; }
.my-element:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.3);
  border-color: var(--border-light);
}

/* Horizontal slide (status lists, links) */
.my-item:hover { transform: translateX(3px); }

/* Scale down on click */
.my-btn:active { transform: translateY(0) scale(0.98); }

/* Glow on hover */
.my-cta:hover { box-shadow: 0 0 30px var(--brand-glow); }
```

### Continuous Animations

```html
<!-- Floating element (icons, avatars, hero graphics) -->
<div class="anim-float">...</div>

<!-- Pulsing glow (call-to-action cards) -->
<div class="anim-glow card-glow">...</div>

<!-- Living status dot — already built in -->
<div class="status-dot dot-running"></div>
```

### Animated Progress Bar

```html
<div class="progress-track">
  <!-- Set --fill-w to match the percentage. CSS animates from 0 to that value. -->
  <div class="progress-fill" style="width: 72%; --fill-w: 72%;"></div>
</div>
```

---

## LAYERED BACKGROUND SYSTEM

Wrap ALL body content in `.bg-orbs` to add animated ambient orbs behind everything:

```html
<body>
<div class="bg-orbs">
  <!-- ALL page content here — cards, grids, header, everything -->
</div>
</body>
```

The orbs use `position: fixed` with `filter: blur(90px)` at 11% opacity — atmospheric, not distracting.

**Custom orb colors** for non-blue themes:
```css
.bg-orbs::before { background: var(--success); }  /* green orb */
.bg-orbs::after  { background: var(--amber); }    /* amber orb */
```

---

## GLASSMORPHISM

Use `.card-glass` inside `.bg-orbs` wrappers for the frosted-glass effect:

```html
<div class="bg-orbs">
  <div class="card-glass anim-scale">
    <h3>Glass Card</h3>
    <p>Semi-transparent, blurred background, subtle border.</p>
  </div>
</div>
```

Custom glassmorphism for hero sections:
```css
.glass-hero {
  background: rgba(20, 22, 32, 0.55);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 28px;
}
```

---

## GRADIENT TEXT

Make primary headings and KPI values pop:

```html
<h1 class="gradient-text">$48,750</h1>              <!-- blue → cyan -->
<h2 class="gradient-text-warm">Action Required</h2> <!-- amber → red -->
<h2 class="gradient-text-success">Goal Achieved</h2><!-- green → cyan -->
```

Custom gradients:
```css
.my-gradient {
  background: linear-gradient(135deg, #60a5fa, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

---

## HERO CARD PATTERN

For dashboards, always open with a hero card showing the primary metric:

```html
<div class="card-hero anim-scale">
  <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin-bottom: 10px;">Monthly Revenue</div>
  <div style="font-size: 44px; font-weight: 900; letter-spacing: -2.5px; line-height: 1;" class="gradient-text">$48,750</div>
  <div style="font-size: 12px; color: var(--success); font-weight: 600; margin-top: 8px;">▲ +12.4% vs last month</div>
  <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">23 jobs completed this month</div>
</div>
```

---

## ICON SYSTEM — No Emoji

Use Unicode symbols or inline SVG. Never emoji.

```html
<!-- Direction / navigation -->
▲ ▼ → ← ↑ ↓ ↗ ↙

<!-- Status indicators -->
● ○ ◆ ◇ ■ □

<!-- Actions -->
+ − × ÷ ✓ ✗

<!-- SVG checkmark (inline, no external file) -->
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
  <polyline points="20 6 9 17 4 12"></polyline>
</svg>

<!-- SVG arrow right -->
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
  <line x1="5" y1="12" x2="19" y2="12"></line>
  <polyline points="12 5 19 12 12 19"></polyline>
</svg>

<!-- Department icon glyphs (text in agent-icon div) -->
<div class="agent-icon">$</div>    <!-- finance -->
<div class="agent-icon">+</div>    <!-- sales, new -->
<div class="agent-icon">&#9654;</div>  <!-- dispatch, ops -->
<div class="agent-icon">&#9733;</div>  <!-- marketing, highlight -->
<div class="agent-icon">&#9998;</div>  <!-- builder, creative -->
```

---

## INTERACTIVE BUTTONS (postMessage)

**Every button must use `nav()` or `speak()`. Never `href="#"`.** The page runs in an iframe — `#` does nothing.

```html
<!-- Navigate to another canvas page -->
<button class="action-btn primary" onclick="nav('sales-pipeline')">
  <span class="label">Sales Pipeline</span>
  <span class="desc">View all active estimates</span>
</button>

<!-- Trigger an AI voice response -->
<button class="btn btn-primary" onclick="speak('Show me this week\'s revenue breakdown')">
  Revenue Report
</button>

<!-- Glowing CTA -->
<button class="btn btn-glow" onclick="speak('Create a new estimate')">
  + New Estimate
</button>

<!-- Open canvas menu -->
<button class="back-btn" onclick="nav('office-hub')">Office</button>
```

---

## COMPLETE DASHBOARD PATTERN

Full example combining all patterns for a business dashboard:

```html
<body>
<div class="bg-orbs">

  <!-- Header -->
  <div class="page-header anim-fade">
    <div>
      <h1 class="gradient-text">Revenue Dashboard</h1>
      <div class="subtitle">Real-time business performance</div>
    </div>
    <button class="back-btn" onclick="nav('office-hub')">Office</button>
  </div>

  <!-- Hero metric -->
  <div class="card-hero anim-scale">
    <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--text-muted);margin-bottom:8px;">Month-to-Date Revenue</div>
    <div style="font-size:44px;font-weight:900;letter-spacing:-2px;" class="gradient-text">$48,750</div>
    <div style="font-size:12px;color:var(--success);font-weight:600;margin-top:6px;">▲ +12.4% vs last month</div>
  </div>

  <!-- KPI grid -->
  <div class="kpi-grid anim-slide-up delay-2">
    <div class="kpi kpi-success">
      <div class="kpi-label">Jobs Complete</div>
      <div class="kpi-value">23</div>
      <div class="kpi-sub">This month</div>
    </div>
    <div class="kpi kpi-warning">
      <div class="kpi-label">Open Estimates</div>
      <div class="kpi-value">7</div>
      <div class="kpi-sub">Awaiting decision</div>
    </div>
  </div>

  <div class="section-label anim-fade delay-3">Quick Actions</div>

  <!-- Action grid -->
  <div class="action-grid anim-slide-up delay-4">
    <button class="action-btn primary" onclick="speak('Show me aging estimates that need follow-up')">
      <span class="label">Follow-Up Queue</span>
      <span class="desc">3 estimates need attention</span>
    </button>
    <button class="action-btn" onclick="nav('agent-bookkeeper')">
      <span class="label">Finance Agent</span>
      <span class="desc">Invoices & expenses</span>
    </button>
  </div>

  <!-- Status list with glass cards -->
  <div class="section-label anim-fade delay-5">Jobs In Progress</div>
  <div class="status-list anim-slide-up delay-6">
    <div class="status-item" onclick="speak('Tell me about the Johnson AC install job')">
      <div class="status-dot dot-running"></div>
      <div style="flex:1">
        <div style="font-size:13px;font-weight:700;">AC Install — Johnson</div>
        <div style="font-size:11px;color:var(--text-muted);">Tech: Mike · Est. completion 2:30 PM</div>
      </div>
      <span class="status-badge badge-running">In Progress</span>
    </div>
  </div>

</div><!-- end bg-orbs -->
</body>
```

---

## THE Z-CODE CANVAS BUILD PROMPT

When the Builder agent spawns z-code, the prompt should follow this structure:

```
ROLE: You are a premium web designer building a canvas page for the JamBot AI voice assistant.
The page runs inside an iframe — no CDN scripts, no npm, all CSS/JS must be inline.

READ THESE FILES IN ORDER BEFORE WRITING ANYTHING:
1. /home/node/.openclaw/workspace/canvas-template.html  — full design system (copy the <style> block verbatim)
2. /mnt/shared-skills/canvas-web-design/SKILL.md — animation patterns, glassmorphism, examples

TASK: [exact description from user — purpose, data to show, actions, desired feel]

OUTPUT FILE: /app/runtime/canvas-pages/[filename].html

REQUIRED — every page must have ALL of these:
- Full <style> block copied from canvas-template.html (do not rewrite it, do not trim it)
- At least one entrance animation (anim-slide-up, anim-fade, or anim-scale) on major sections
- Staggered delays (delay-1 through delay-5) on sequential elements
- Hover micro-interactions on every clickable element (transition, transform, box-shadow)
- Gradient text on the primary heading or KPI value
- Real, specific content — NO placeholder text like "Content goes here"
- All buttons use nav() or speak() — never href="#"
- Page header with descriptive title and back-to-office button
- At least 3 distinct content sections

FOR DASHBOARDS — also required:
- bg-orbs wrapper div around all content
- card-hero with gradient-text for the primary KPI metric
- kpi-grid with 2-4 real metric values using semantic kpi-* classes
- At least one glassmorphism element (card-glass inside bg-orbs)
- action-grid with 2-4 speak() buttons that trigger relevant AI queries

BANNED — never use these:
- Purple, pink, or magenta colors (any shade)
- Emoji as icons — use SVG or Unicode symbols only
- External CDN scripts or stylesheets
- href="#" on any element
- Placeholder text
- Inline style values that duplicate existing CSS variable values

When finished, output exactly:
FILE_WRITTEN: /app/runtime/canvas-pages/[filename].html
```

---

## TEXT MEASUREMENT — Pretext

For any canvas page that needs precise text layout — virtualized lists, chat interfaces, auto-sizing cards, masonry grids, or canvas/SVG text rendering — use `@chenglou/pretext`. It's ~500x faster than DOM measurements (no layout reflow) and handles CJK, RTL, emoji, and mixed scripts.

```html
<script type="module">
import { prepare, layout, prepareWithSegments, walkLineRanges }
  from 'https://cdn.jsdelivr.net/npm/@chenglou/pretext/+esm';

// Measure text height without DOM
const prepared = prepare(text, '16px Inter');
const { height } = layout(prepared, containerWidth, 22);

// Shrink-to-fit (chat bubbles, dynamic cards)
const seg = prepareWithSegments(text, '15px Inter');
let maxW = 0;
walkLineRanges(seg, maxWidth, line => { if (line.width > maxW) maxW = line.width; });
// maxW = tightest container width that still fits
</script>
```

Full API, patterns, and canvas rendering examples: `/mnt/shared-skills/pretext/SKILL.md`

---

## SKILL REFERENCES

Read these skills for additional design intelligence when building complex pages:

- `/mnt/shared-skills/ui-ux-pro-max/SKILL.md` — color palettes, typography pairs, chart patterns
- `/mnt/shared-skills/premium-web-design/SKILL.md` — Fortune 500 design principles, hero sections, layered backgrounds
- `/mnt/shared-skills/pretext/SKILL.md` — DOM-free text measurement for virtualized lists, chat bubbles, masonry grids, canvas text

When using premium-web-design: skip the React/Tailwind sections — they don't apply in iframe context.
Translate Tailwind utilities to equivalent vanilla CSS (e.g. `backdrop-blur-xl` → `backdrop-filter: blur(24px)`).

---

## QUALITY CHECKLIST

Before declaring a canvas page complete, verify every item:

**Every page:**
- [ ] Full canvas-template.html `<style>` block is present (not trimmed or rewritten)
- [ ] Page header with title and back button (`onclick="nav('office-hub')"`)
- [ ] Entrance animations on header and at least 2 more sections
- [ ] Hover state on every clickable element (card, button, status-item)
- [ ] No placeholder text anywhere — all content is real and task-specific
- [ ] No purple/pink/magenta
- [ ] No emoji as icons
- [ ] No CDN scripts
- [ ] No `href="#"` anywhere
- [ ] nav() and speak() functions in the `<script>` block at body end
- [ ] Mobile-readable (no horizontal overflow at 375px)

**Dashboard pages additionally:**
- [ ] `.bg-orbs` wrapper around all content
- [ ] `card-hero` with gradient-text primary metric
- [ ] `kpi-grid` with real semantic values
- [ ] At least one `card-glass` element
- [ ] `action-grid` with contextual speak() buttons
- [ ] Primary heading uses `gradient-text`
