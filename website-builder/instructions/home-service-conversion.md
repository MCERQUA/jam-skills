# Home Service Website Conversion Rules

Source: Noah Igler (@noahiglerSEO) — audits hundreds of home service sites.
Most home service sites convert under 1%. These rules push to 3-5%.

**Apply this document when building any site for:** HVAC, plumbing, roofing, electrical,
landscaping, pest control, drain cleaning, appliance repair, or any residential service business
where phone calls and booked jobs are the primary conversion goal.

---

## 1. Above the Fold — Win or Lose in 3 Seconds

Within 3 seconds of landing, the visitor must know:
- What you do
- Where you do it
- That you're trustworthy
- How to call you right now

**Mandatory above-the-fold elements:**

| Element | Rule |
|---------|------|
| Headline | `"[Service] in [City]"` or `"[City]'s Trusted [Service] Company"` — NOT "Your Trusted Home Service Partner Since 2003" |
| Phone | Top-right corner, large, clickable `tel:` link (see §2 below), sticky on scroll |
| Subheadline / Trust Stack | Review count + star rating + years in business + license number + service area |
| Primary CTA | "Call Now" or "Get Free Quote" — phone number visible on the button or immediately adjacent |
| Hero Image | Real photos: your team in branded shirts, your trucks at job sites — NOT stock photos of smiling families |

**Headline formula examples:**
```
✅ "Dallas HVAC Repair — Same-Day Service"
✅ "Phoenix's Trusted Roofing Contractor"
✅ "Austin Plumbers — Licensed, Insured, Available 24/7"
❌ "Your Trusted Home Service Partner Since 2003"
❌ "Quality Service You Can Count On"
❌ "Welcome to Our Website"
```

---

## 2. Phone Number — The Single Biggest Conversion Lever

**CRITICAL: Wire the phone number to a clean `tel:` link that opens the dialer directly.**

```html
<!-- CORRECT -->
<a href="tel:+15551234567">(555) 123-4567</a>

<!-- WRONG — never do this -->
<button onClick={() => setModalOpen(true)}>Call Us</button>
```

A modal confirmation step ("tap to confirm you want to call") causes a 30% drop in inbound calls. No modal, no popup, no extra confirmation step. One tap → dialer opens.

**Phone must appear:**
- Top-right of navbar (desktop and mobile)
- Sticky header that stays visible as the visitor scrolls
- Primary CTA button (or directly adjacent to it)
- Footer

**Sticky mobile phone implementation:**
```tsx
// Sticky header — always shows phone
// Sticky footer bar on mobile — two buttons side by side
<div className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-primary">
  <a href="tel:+15551234567" className="flex-1 py-4 text-center text-white font-bold">
    Call Now
  </a>
  <a href="/contact" className="flex-1 py-4 text-center text-white font-bold border-l">
    Book Online
  </a>
</div>
```

---

## 3. Contact Forms — Minimal Fields Only

**Every field you add costs ~10% of conversions.**

**For home service sites, the form should have exactly 4 fields:**
1. Name
2. Phone (required — this is the conversion, not email)
3. Service needed (dropdown — list actual services, not "Other")
4. Address (needed for scheduling and service area check)

```tsx
// CORRECT — 4 fields max
<form>
  <input name="name" placeholder="Your Name" required />
  <input name="phone" type="tel" placeholder="Phone Number" required />
  <select name="service" required>
    <option value="">Select Service</option>
    <option value="ac-repair">AC Repair</option>
    <option value="ac-install">AC Installation</option>
    <option value="heating">Heating Repair</option>
    <option value="other">Other</option>
  </select>
  <input name="address" placeholder="Service Address" />
</form>

// WRONG — never ask these on a home service lead form
// ❌ Email (optional, not conversion-critical)
// ❌ "How did you hear about us?"
// ❌ "Best time to call"
// ❌ Comments / message box
// ❌ Upload files
```

**Never hide the phone number to "force" form fills.** Visitors just leave instead.

---

## 4. Mobile Page Speed — Non-Negotiable

| PageSpeed Score | Impact |
|-----------------|--------|
| Below 50 | Lose 2-3 Map Pack positions |
| Below 70 | Lose 20-30% of mobile visitors before page loads |
| 70-90 | Acceptable |
| 90+ | Competitive advantage |

**Speed rules:**
- Hero images: 200-400KB max (most sites ship 2-3MB — compress everything)
- Use WebP format for all images
- Lazy load everything below the fold
- No auto-playing video in the hero section (kills speed AND annoys visitors)
- No pop-ups on first visit (immediate back button on mobile)
- Minimize third-party widgets: chat boxes, social embeds, review aggregators each add load time
- Use a real CDN (not just whatever the host bundles)
- Target: page loads in under 2 seconds

**Hero image compression command:**
```bash
# Compress hero image before adding to project
ffmpeg -i hero-original.jpg -q:v 2 hero.webp
# Or use: npx @squoosh/cli --webp '{"quality": 80}' hero-original.jpg
```

**No-autoplay rule in JSX:**
```tsx
// WRONG
<video autoPlay muted loop src="/hero.mp4" />

// CORRECT — show static image, let user opt into video
<Image src="/hero.webp" alt="[Your team at a job site]" priority />
```

---

## 5. Reviews and Trust — Show at Every Scroll Depth

A single testimonial section halfway down the page is not enough. Visitors must see proof at every scroll depth.

**Review placement map:**
```
[Above the fold]  → "4.9 stars · 312 Google reviews" (count + rating, linked to GBP)
[Hero section]    → 2-3 short pull quotes from real reviews
[Service pages]   → Reviews mentioning that specific service
[Near the form]   → "Join 500+ happy customers in [city]"
[Footer]          → Star rating badge
```

**Pull quote format:**
```tsx
// Short, specific, service-and-location relevant
"Fixed our AC same day in 100° heat. Best plumber in Phoenix." — John M., Scottsdale
```

**TrustBar / subheadline component should show:**
- Star rating (e.g., ⭐ 4.9/5)
- Review count (e.g., "from 312 Google reviews")
- Years in business (e.g., "15+ years serving Dallas")
- License number or "Licensed & Insured"
- Service area cities

---

## 6. Photos — Real Over Stock

Stock photos hurt trust. Visitors identify them instantly and the trust signal flips negative.

**Use real photos:**
- Team members in branded shirts at job sites
- Your trucks parked in customers' driveways (homeowner's house visible = local proof)
- Before-and-after shots for high-impact jobs (drain cleaning, panel installs, roof replacements, AC installs)
- Photos of license documents, manufacturer certifications, insurance certificates

**Image naming for SEO:**
```
hvac-team-dallas-tx.webp          ← service + city
roof-replacement-phoenix-before.webp
ac-installation-scottsdale.webp
```

---

## 7. Financing — Display on High-Ticket Service Pages

For replacement-level jobs ($5K+), roughly 60% of customers want financing options. Displaying it converts deal you'd otherwise never even get to quote.

**Add to service pages for big-ticket work:**
- Financing partner logo above the fold (Synchrony, GreenSky, Wisetack)
- "0% financing available" or "Payments as low as $89/month"
- Link to a dedicated /financing page in the main navigation
- Pre-qualification widget on high-ticket service pages

---

## 8. Sticky CTAs — Always One Tap Away

The visitor should never be more than one tap from calling you.

**Sticky elements to implement:**
- Sticky header: phone number visible at all times on mobile
- Sticky footer bar on mobile: "Call Now" + "Book Online" side by side (adds 15-25% to call volume)
- Floating action button on long-scroll pages

---

## 9. Things to NEVER Build on Home Service Sites

| Anti-pattern | Why |
|--------------|-----|
| Phone number in a modal | 30% drop in calls. Wire tel: directly. |
| Hiding phone to force form | They just leave. Show the phone. |
| Auto-playing video in hero | Kills PageSpeed, annoys visitors. |
| Pop-ups on first visit | Immediate back button on mobile. |
| Live chat widgets loading >2s | Cover the phone number = lost calls. |
| Contact form with 5+ fields | Each field costs ~10% conversions. |
| Stock photos of families | Trust flip — looks like every other site. |
| Vague headline | "Trusted Partner Since 2003" tells them nothing. |

---

## 10. Quality Gate Additions for Home Service Sites

Add these checks to the Phase 12 quality gate:

```bash
# Phone number must be a direct tel: link
grep -rn "tel:" src/ --include="*.tsx" | wc -l  # must be > 0

# No modal on phone click
grep -rn "onClick.*modal\|setModal.*phone\|phone.*modal" src/ --include="*.tsx"  # must be 0
```

Manual checks:
- [ ] Phone number opens dialer directly on mobile (no modal, no confirmation)
- [ ] Phone is sticky and visible on all scroll positions
- [ ] Form has 4 fields max (Name, Phone, Service dropdown, Address)
- [ ] No autoplay video anywhere
- [ ] No pop-up on first page visit
- [ ] Hero image is under 400KB (check with `ls -lh public/`)
- [ ] Trust stack visible above the fold: stars + review count + years + license
- [ ] Hero uses real photo, not stock photo
- [ ] Sticky mobile footer bar: Call Now + Book Online
- [ ] Reviews appear in at least 3 scroll positions on homepage
- [ ] Google PageSpeed mobile score ≥70
