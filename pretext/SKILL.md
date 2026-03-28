---
name: pretext
description: "Pretext (@chenglou/pretext) — pure JS/TS text measurement library. ~500x faster than getBoundingClientRect. Use for virtualized lists, chat bubbles, responsive multi-column layouts, canvas text rendering, auto-growing textareas, shrink-to-fit containers. Zero dependencies. Works in DOM, Canvas, SVG. TRIGGER when: text measurement, text layout, virtualization, masonry layout, chat bubbles, multi-column text, shrink-to-fit, text height calculation, variable-height list items, canvas text rendering."
---

# Pretext — High-Performance Text Measurement & Layout

`@chenglou/pretext` is a pure JavaScript/TypeScript library for pixel-perfect multiline text measurement **without DOM reads or CSS layout reflow**. It replaces `getBoundingClientRect`, `offsetHeight`, and all DOM measurement patterns with pure arithmetic — ~500x faster.

## Installation

**Next.js / Node projects:**
```bash
pnpm add @chenglou/pretext
```

**Canvas pages (inline HTML, no bundler):**
```html
<script type="module">
import { prepare, layout, prepareWithSegments, layoutWithLines, walkLineRanges, layoutNextLine }
  from 'https://cdn.jsdelivr.net/npm/@chenglou/pretext/+esm';
// Use the APIs below
</script>
```

---

## Core Concept

Two-phase workflow:

1. **`prepare(text, font)`** — one-time work: segments text, measures via canvas, caches widths. ~19ms for 500 texts.
2. **`layout(prepared, maxWidth, lineHeight)`** — pure arithmetic, returns `{ height, lineCount }`. ~0.0002ms per text.

This separation means resize/scroll handlers call `layout()` thousands of times per frame with zero DOM access.

---

## API Reference

### Use Case 1: Measure Height Without DOM

```ts
import { prepare, layout } from '@chenglou/pretext'

const prepared = prepare('Your text here with multilingual support', '16px Inter')
const { height, lineCount } = layout(prepared, containerWidth, 24) // 24px line-height
// height = exact pixel height matching what CSS would produce
```

**`prepare()` options:**
- `{ whiteSpace: 'pre-wrap' }` — preserve spaces, tabs, newlines (textarea-like)

### Use Case 2: Manual Line Layout (Canvas, SVG, Custom Rendering)

```ts
import { prepareWithSegments, layoutWithLines } from '@chenglou/pretext'

const prepared = prepareWithSegments('Text for manual rendering', '18px "Helvetica Neue"')
const { lines } = layoutWithLines(prepared, 320, 26)
// lines = [{ text: 'Text for manual', width: 182.5, start, end }, ...]

// Render to Canvas:
for (let i = 0; i < lines.length; i++) {
  ctx.fillText(lines[i].text, 0, i * 26)
}
```

### Use Case 3: Shrink-to-Fit (Chat Bubbles)

```ts
import { prepareWithSegments, walkLineRanges } from '@chenglou/pretext'

const prepared = prepareWithSegments(messageText, '15px Inter')
let maxLineWidth = 0
walkLineRanges(prepared, maxBubbleWidth, line => {
  if (line.width > maxLineWidth) maxLineWidth = line.width
})
// maxLineWidth = tightest container width that still fits — true shrink-wrap
bubble.style.width = `${Math.ceil(maxLineWidth) + padding}px`
```

### Use Case 4: Variable-Width Flow (Text Around Images)

```ts
import { prepareWithSegments, layoutNextLine } from '@chenglou/pretext'

const prepared = prepareWithSegments(articleText, '16px Georgia')
let cursor = { segmentIndex: 0, graphemeIndex: 0 }
let y = 0

while (true) {
  const width = y < image.bottom ? columnWidth - image.width : columnWidth
  const line = layoutNextLine(prepared, cursor, width)
  if (line === null) break
  ctx.fillText(line.text, 0, y)
  cursor = line.end
  y += lineHeight
}
```

### Helpers

```ts
clearCache()          // Release internal caches (for apps cycling many fonts)
setLocale('ko-KR')    // Set locale for segmentation (default: browser locale)
```

---

## When to Use Pretext

| Problem | Pretext Solution |
|---------|-----------------|
| Virtualized list needs variable row heights | `prepare()` once per item, `layout()` on resize — instant heights, no DOM |
| Masonry/Pinterest grid | Measure all text blocks in <1ms, compute perfect positions |
| Chat bubbles waste space (CSS max-width too wide) | `walkLineRanges()` finds exact tight width — true shrink-to-fit |
| Auto-growing textarea | `layout()` returns exact height for current text + width |
| Responsive multi-column layout | `layoutNextLine()` flows text with variable widths per line |
| Canvas/WebGL text rendering | `layoutWithLines()` gives you line-broken text to draw manually |
| Layout shift on content load | Pre-compute heights to reserve space before rendering |
| Label overflow detection | Check if button/card text wraps to next line before rendering |
| Balanced text (no widows/orphans) | Binary search width with `walkLineRanges()` until line count is "nice" |

---

## Practical Patterns

### Virtualized List with Perfect Heights

```ts
const items = allTexts.map(text => ({
  text,
  prepared: prepare(text, '14px Inter'),
}))

function getItemHeight(index, containerWidth) {
  return layout(items[index].prepared, containerWidth - padding, 20).height + padding
}
// Feed getItemHeight to your virtualizer (react-window, tanstack-virtual, custom)
```

### Responsive Dashboard Card Text

```ts
// Measure KPI label to decide font size or truncation
const prepared = prepare(kpiLabel, '24px Inter')
const { lineCount } = layout(prepared, cardWidth - 32, 28)
if (lineCount > 1) {
  // Switch to smaller font or truncate
}
```

### Canvas Page Chat Interface

```html
<script type="module">
import { prepare, layout, prepareWithSegments, walkLineRanges }
  from 'https://cdn.jsdelivr.net/npm/@chenglou/pretext/+esm';

const FONT = '15px Inter, system-ui, sans-serif';
const LINE_HEIGHT = 22;
const PADDING = 12;

function createBubble(text, maxWidth) {
  const prepared = prepareWithSegments(text, FONT);
  let maxLineWidth = 0;
  walkLineRanges(prepared, maxWidth - PADDING * 2, line => {
    if (line.width > maxLineWidth) maxLineWidth = line.width;
  });
  const { height } = layout(prepared, maxWidth - PADDING * 2, LINE_HEIGHT);
  return {
    width: Math.ceil(maxLineWidth) + PADDING * 2,
    height: height + PADDING * 2,
  };
}
</script>
```

---

## i18n & Edge Cases

Pretext handles all of these correctly:
- **CJK** (Chinese, Japanese, Korean) — per-character line breaking
- **RTL** (Arabic, Hebrew) — full bidi support with mixed LTR/RTL
- **Emoji** — including multi-codepoint sequences (flags, skin tones, ZWJ)
- **Mixed scripts** — Korean with embedded Arabic and emoji in one paragraph
- **Variable fonts** — weight, width, slant all supported
- **Browser quirks** — trained on Chrome/Firefox/Safari differences

**Caveat:** Avoid `system-ui` as the font — use named fonts (`Inter`, `Helvetica Neue`, etc.) for guaranteed accuracy.

---

## Performance

| Operation | Time |
|-----------|------|
| `prepare()` — 500 texts | ~19ms total |
| `layout()` — 500 texts | ~0.09ms total (~0.0002ms each) |
| DOM `getBoundingClientRect` — 500 texts | ~100ms+ (with forced reflows) |

This means 120fps virtualization of thousands of text blocks is achievable.

---

## Links

- **npm:** `@chenglou/pretext`
- **Repo:** github.com/chenglou/pretext
- **Live demos:** chenglou.me/pretext/
  - Masonry occlusion: chenglou.me/pretext/masonry/
  - Chat bubbles: chenglou.me/pretext/bubbles/
  - Dynamic columns: chenglou.me/pretext/dynamic-layout/
  - Accordion: chenglou.me/pretext/demos/accordion.html
  - ASCII art: chenglou.me/pretext/demos/variable-typographic-ascii.html
