# Home-Service Website Conversion Rules (MANDATORY for every client build)

> Source: Noah Igler (noahiglerseo) audit, incorporated 2026-06-11 per Mike. Our clients
> ARE home-service businesses (roofing, spray foam, insurance, concrete, HVAC, etc.) —
> these rules are non-optional. Most home-service sites convert <1%; applying these gets
> 3–5%. Same traffic, 3–5× the leads. **Apply every rule below on every build; the QA
> pass must verify them.**

## 1. Above the fold wins or loses 80% of conversions
Within 3 seconds a visitor must know: what you do, where, that you're trustworthy, how to call NOW. Required in the hero zone:
- **Headline:** `[Service] in [City]` or `[City]'s Trusted [Service]`. NEVER vague ("Your Trusted Home Service Partner Since 2003").
- **Phone number top-right, large, clickable, sticky** — wired to a real `tel:` link (the actual dialer). NO modal/popup/confirmation step.
- **Trust-stack subheadline:** review count + star rating, years in business, license #, service area.
- **Primary CTA button:** "Call Now" or "Get Free Quote" with the phone number visible.
- **Hero image = REAL** techs / trucks / a real job. NEVER a stock photo of a smiling family.

## 2. Phone visibility is the single biggest lever
`tel:` link straight to the dialer — no modal (a client lost 30% of inbound calls to a "tap → confirm modal" before the dialer launched). Keep it sticky as they scroll.

## 3. Forms: 4 fields MAX (each extra field ≈ −10% conversions)
Ask ONLY: **Name · Phone · Service needed (dropdown) · Address.** Nothing else. You're getting them to call back, not running a credit app. The 8-field form (email, best-time, how-heard, comments…) is the death zone.

## 4. Mobile speed is non-negotiable
Target PageSpeed **>70** mobile, load **<2s**. Below 50 costs 2–3 Map-Pack spots; below 70 loses 20–30% of mobile visitors. Fixes: hero images **200–400KB** (not 2–3MB), drop unnecessary plugins/tracking, real CDN, lazy-load below the fold, minimize third-party widgets (chat/social/review embeds).

## 5. Reviews/proof at EVERY scroll depth (not one section)
- Above the fold: count + rating ("4.9 stars from 312 Google reviews").
- Hero: 2–3 short pull-quotes from real reviews (dynamic from GBP where possible).
- Service pages: a section pulling reviews that mention THAT service.
By the form, they've seen proof 5–6 times — the trust compounds.

## 6. Real photos + before/afters (stock photos flip trust NEGATIVE)
Real team in branded shirts on real job sites · trucks in driveways with the house behind · before/after for jobs where it lands (roof replacements, panel work, AC/ductwork, drain) · photos of license docs, certifications, insurance certs.

## 7. Financing visible on every service page (for $5K+ tickets ~60% want it)
Partner logo (Synchrony/GreenSky/Wisetack) above the fold on service pages · "0% financing" / "Payments as low as $89/month" callouts · a financing page in the nav · pre-qual widget on high-ticket service pages.

## 8. Sticky CTAs — never more than one tap from calling (+15–25% calls)
Sticky header phone (always visible mobile) · sticky mobile footer bar ("Call Now" + "Book Online") · floating action button on long pages.

## NEVER do these (instant conversion killers)
- Longer forms to "qualify" leads (you lose them, not qualify them).
- Hiding the phone to "force" the form (they just leave).
- Auto-playing hero video (kills mobile speed + annoys).
- First-visit pop-ups (immediate back-button on mobile).
- Live-chat widgets that load slowly or cover the phone number.

**QA gate:** a build does not pass until items 1–8 are present and rule "NEVER" is clean. Run these against the live URL on mobile viewport.
