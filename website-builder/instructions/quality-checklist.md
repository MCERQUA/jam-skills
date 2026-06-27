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
- [ ] AEO capture: every lead form has hidden `traffic_source` + `landing_url` fields with the set-on-load script (and, for Netlify Forms, declared in `__forms.html`) — see forms-backend.md

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

## Local Service Sites (Home Service / Contractors) — Run if site type is "Local Service"

Most local service sites convert under 1%. This checklist targets 3–5%.

### Above the Fold
- [ ] Headline follows `"[Service] in [City]"` or `"[City]'s Trusted [Service]"` format — NOT generic tagline
- [ ] Phone number is top-right, large, and **wired directly to `tel:` link** — no modal, no popup, no confirmation step
- [ ] Phone number is sticky — stays visible as user scrolls (sticky header or persistent top bar)
- [ ] Trust bar includes: star rating + review count + years in business + license number + service area
- [ ] Primary CTA is `"Call Now"` or `"Get Free Quote"` — phone number visible on or near the button
- [ ] Hero image uses REAL photos (team, trucks, jobs) — NOT stock photos of smiling homeowners

### Phone Visibility
- [ ] Sticky header shows phone at all scroll depths on mobile
- [ ] Sticky footer bar on mobile has `"Call Now"` (tel: link) + `"Book Online"` always in view
- [ ] No modal or confirmation step between tap and dialer launch on mobile

### Forms
- [ ] Contact/quote form has 4 fields MAX: Name, Phone, Service (dropdown), Address
- [ ] No email field, no "how did you hear about us", no "best time to call", no comments box
- [ ] Service field is a dropdown (not free text) — reduces friction and helps routing

### Mobile Speed
- [ ] PageSpeed mobile score ≥ 70 (check at pagespeed.web.dev)
- [ ] Page loads in < 2 seconds on mobile (throttled connection)
- [ ] Hero image is ≤ 400KB (never 2–3MB)
- [ ] No auto-playing video in hero section
- [ ] Third-party widgets (live chat, social embeds, review aggregators) load lazily or are removed if not essential

### Social Proof Placement
- [ ] Review count + star rating visible above the fold (`"4.9 stars · 312 Google reviews"`)
- [ ] 2–3 short review pull quotes in or near the hero section
- [ ] Service pages have reviews that mention that specific service
- [ ] Proof appears at multiple scroll depths (not just in one testimonials section)

### Photos
- [ ] At least one photo of real team members (branded shirts, job site, or truck) — not stock
- [ ] No obvious stock photos anywhere on the page (smiling generic family, generic tool photos, etc.)

### First-Visit UX
- [ ] No popup or modal on first visit — immediate back-button trigger on mobile
- [ ] No auto-playing video or audio

### Financing (if applicable — any service with tickets $5K+)
- [ ] Financing partner logo visible above the fold on relevant service pages
- [ ] Callout text present: `"0% financing available"` or `"Payments as low as $X/month"`
- [ ] Separate financing page linked from main nav (if high-ticket services are core)

---

## How to Audit

### Quick visual scan:
1. Open site at 375px — scroll entire page
2. Open site at 1440px — scroll entire page
3. Tab through every interactive element — verify focus rings
4. Hover every button and card — verify hover states
5. Click every link — verify navigation works
6. Submit every form — verify validation and submission

### Code scan (MANDATORY — run every grep, fix every match):

```bash
# 1. Placeholder sweep — MUST return zero results
grep -rn "REPLACE:\|example\.com\|placeholder\|TODO\|FIXME\|Lorem\|project-name\|UPDATE:\|000-0000\|hello@\|Service One\|Service Two\|Service Three\|A short description\|Your Headline\|Business Name\.\|Sarah Johnson\|Mike Chen\|Lisa Rodriguez" src/ --include="*.tsx" --include="*.ts"

# 2. Broken links
grep -rn 'href="#"' src/ --include="*.tsx" --include="*.ts"

# 3. Debug code
grep -rn "console\.log" src/ --include="*.tsx" --include="*.ts"
```

Every match from grep #1 is a FAILURE. Fix before presenting.

4. Check every `<img>` and `<Image>` has descriptive `alt`
5. Check every `<input>` has a `<label>`
6. Verify navbar shows real business name (not "Logo" or "REPLACE:")
7. Verify footer has real phone, email, address — not placeholder values
8. Verify every testimonial has full name + company + location (not generic names)
9. Verify every page has at least one real image (not just Lucide icons)
10. Verify phone `tel:` links match the displayed phone number text
11. Verify all CTA buttons say something specific (not "Submit" or "Learn More")
12. Verify no page renders 100% default section props (About, Services especially)
