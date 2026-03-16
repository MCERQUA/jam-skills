# Quality Checklist — Pre-Delivery Audit

Run EVERY check before presenting the site to the client. Fix all failures.

---

## Critical (must pass)

### Accessibility
- [ ] Color contrast ratio >= 4.5:1 for body text, >= 3:1 for large text
- [ ] All images have descriptive `alt` attributes
- [ ] All form inputs have associated `<label>` elements
- [ ] Focus states visible on all interactive elements (buttons, links, inputs)
- [ ] Keyboard navigation works (Tab through all interactive elements)
- [ ] `aria-label` on icon-only buttons
- [ ] Page has exactly one `<h1>`, headings in descending order
- [ ] `lang` attribute on `<html>` element

### Responsive
- [ ] No horizontal scroll at any viewport width
- [ ] Readable at 375px (iPhone SE) — no overlapping, no cut-off text
- [ ] Navigation works on mobile (hamburger menu, touch targets)
- [ ] Touch targets >= 44x44px on mobile
- [ ] Images scale properly (no overflow, no pixelation)
- [ ] Text readable at 768px (tablet)
- [ ] Full layout at 1024px and 1440px

### Content
- [ ] ZERO placeholder text — no "Lorem ipsum", no "Coming soon", no "[Insert text]"
- [ ] All links point to real destinations (no `href="#"`)
- [ ] Business name, phone, address are correct
- [ ] CTA buttons have clear action text ("Get a Free Quote" not "Submit")
- [ ] No broken images (all `src` paths resolve)

---

## High Priority (should pass)

### SEO
- [ ] `<title>` tag set with business name + description
- [ ] `<meta name="description">` on every page (150-160 chars)
- [ ] Open Graph tags (title, description, image)
- [ ] `sitemap.ts` exists and lists all pages
- [ ] `robots.ts` exists
- [ ] Structured data (JSON-LD) for business type
- [ ] One `<h1>` per page, descriptive and keyword-relevant

### Performance
- [ ] Hero image uses `priority` prop
- [ ] All images have `width` and `height` set
- [ ] Fonts use `next/font` with `display: "swap"`
- [ ] Heavy components use dynamic imports
- [ ] No layout shift visible during page load

### UX & Interaction
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states on all buttons and cards (color change, scale, or shadow)
- [ ] Hover states don't shift surrounding layout
- [ ] Active/pressed states on buttons
- [ ] Loading states on form submissions
- [ ] Error messages on form validation
- [ ] Smooth scroll between sections (Lenis working)
- [ ] Navigation highlights current page

### Animation
- [ ] `prefers-reduced-motion` respected (animations disabled or reduced)
- [ ] Animations use `transform` and `opacity` only (no layout-triggering)
- [ ] Scroll animations trigger `whileInView` (not on page load)
- [ ] No janky or stuttering animations
- [ ] Animation durations 200-800ms (not too fast, not too slow)
- [ ] Stagger delays feel natural (50-150ms between items)

---

## Medium Priority (nice to have)

### Visual Polish
- [ ] Consistent spacing (sections use `py-24 md:py-32`, not random values)
- [ ] Consistent border radius (use `--radius` CSS variable)
- [ ] Icons from Lucide React only (no emoji, no mixed icon sets)
- [ ] Gradients are subtle, not overwhelming
- [ ] Background has depth (gradient or subtle pattern, not flat solid)
- [ ] Cards have subtle border or shadow for definition

### Code Quality
- [ ] No TypeScript errors
- [ ] No ESLint warnings
- [ ] No unused imports or variables
- [ ] Consistent naming conventions
- [ ] Components are reasonably sized (< 200 lines each)
- [ ] No hardcoded colors — all via CSS variables or Tailwind config

### Git
- [ ] All changes committed to `web-dev` branch
- [ ] Pushed to GitHub
- [ ] No sensitive data in commits (API keys, passwords)
- [ ] `.env.local` is in `.gitignore`

---

## How to Audit

### Quick visual scan:
1. Open site at 375px — scroll entire page
2. Open site at 1440px — scroll entire page
3. Tab through every interactive element — verify focus rings
4. Hover every button and card — verify hover states
5. Click every link — verify navigation works
6. Submit every form — verify validation and submission

### Code scan:
1. Search for `Lorem` or `ipsum` — should find zero results
2. Search for `href="#"` — should find zero results
3. Search for `console.log` — should find zero results
4. Check every `<img>` and `<Image>` has `alt`
5. Check every `<input>` has a `<label>`
