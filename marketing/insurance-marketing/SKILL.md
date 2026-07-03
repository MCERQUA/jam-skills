---
name: insurance-marketing
description: When the user is marketing an insurance agency, independent agent, or insurance-related business. Also use when the user mentions "insurance marketing," "insurance agent website," "insurance leads," "quote funnel," "Medicare marketing," "AEP," "OEP," "insurance compliance," "insurance copy," "policy renewal," "cross-sell," "upsell insurance," "carrier appointments," "insurance referrals," "insurance landing page," "Google LSA insurance," "insurance SEO," or "E&O." Use this for any marketing task specific to insurance agents and agencies. For general local SEO, see local-seo. For general copywriting, see copywriting. For general form optimization, see form-cro.
metadata:
  version: 1.0.0
---

# Insurance Marketing

You are an expert in marketing for independent insurance agents and agencies. Your goal is to help agents generate leads, retain clients, grow through referrals, and market compliantly across all lines of business.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing-context.md` exists (or `.claude/product-marketing-context.md` in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before building an insurance marketing strategy, understand:

1. **Agency Profile**
   - Independent agent or captive?
   - Lines of business (P&C, life, health, Medicare, commercial, surety)?
   - Number of carriers appointed with?
   - Which states are you licensed in?
   - Single agent or multi-producer agency?

2. **Current State**
   - Where do leads come from today? (referrals, website, cold calls, purchased leads?)
   - Do you have a website? Is it generating quotes?
   - What's your policy count and retention rate?
   - Do you have a CRM (Applied, HawkSoft, EZLynx, etc.)?

3. **Goals**
   - New business growth vs. retention improvement?
   - Specific lines to grow?
   - Target market (personal, commercial, Medicare, group benefits)?
   - Geographic focus?

---

## Core Principles

### 1. Compliance First
Insurance marketing is regulated. Every state has advertising rules. Medicare has CMS guidelines. Copy must include required disclaimers. Always check state-specific requirements before publishing any marketing materials.

### 2. Trust Is the Product
People buy insurance from people they trust. Every marketing touchpoint must build trust: credentials, carrier badges, licenses, real photos, community involvement, client stories, claims experience.

### 3. The Relationship Is the Moat
Unlike commodity products, insurance agents win through relationships. Marketing should reinforce the relationship — not just generate leads. Retention marketing (renewals, cross-sells, referrals) has 5-10x the ROI of new lead generation.

### 4. Local > National
Independent agents beat national carriers on local presence. Lean into community, accessibility, and "I live here, I know your risks" messaging.

---

## Trust Signals for Insurance Websites

### Must-Have Trust Elements

| Signal | Where to Display | Why It Matters |
|--------|-----------------|----------------|
| License number(s) | Footer, about page | Legal requirement in most states |
| Carrier appointment badges | Homepage, sidebar | Shows access to multiple options |
| E&O coverage mention | About page | Shows professionalism |
| Years in business | Homepage hero | Experience = trust |
| IIABA / PIA membership | Footer, about page | Industry credibility |
| BBB rating | Homepage, footer | Consumer trust signal |
| Google review score | Homepage hero, sidebar | Social proof |
| Real team photos | About page, homepage | Human connection |
| Client count or households | Homepage | Scale = stability |
| Community involvement | About page, blog | Local roots |
| Claims support messaging | Homepage, service pages | "We're here when it matters" |

### Insurance-Specific Schema

```json
{
  "@context": "https://schema.org",
  "@type": "InsuranceAgency",
  "name": "[Agency Name]",
  "description": "Independent insurance agency serving [City/Area] with [lines of business]",
  "url": "https://example.com",
  "telephone": "+1-555-555-5555",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[Address]",
    "addressLocality": "[City]",
    "addressRegion": "[State]",
    "postalCode": "[ZIP]",
    "addressCountry": "US"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "[Lat]",
    "longitude": "[Long]"
  },
  "areaServed": ["[City 1]", "[City 2]"],
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "09:00",
      "closes": "17:00"
    }
  ],
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.9",
    "reviewCount": "85"
  },
  "priceRange": "Varies"
}
```

Note: `InsuranceAgency` is a valid schema.org subtype of `LocalBusiness`. Use it instead of generic `LocalBusiness` for insurance agencies.

---

## Quote Funnel Optimization

### Multi-Step Form Design

Insurance quote forms are complex. Progressive disclosure keeps conversion rates high.

**Step 1 — Low Friction Entry (3-4 fields)**
- Type of insurance needed (dropdown)
- ZIP code
- Name
- Phone or email

**Step 2 — Basic Details**
- Full address
- Date of birth (for personal lines)
- Current carrier (if any)
- Policy renewal date

**Step 3 — Coverage Details (varies by line)**
- Auto: vehicles, drivers, coverage levels
- Home: property details, coverage amounts
- Commercial: business type, revenue, employee count
- Life: coverage amount, health questions

**Design rules:**
- Show progress indicator (Step 1 of 3)
- Save partial submissions — even Step 1 is a lead
- Click-to-call option on every step ("Prefer to talk? Call us")
- Mobile-first design (most insurance searches are mobile)
- Don't ask for SSN in online forms (compliance risk)
- Show trust signals next to the form (rating, carrier logos, license #)

### Quote Landing Page Template

```
H1: [Insurance Type] Quotes in [City] — Compare & Save
Subhead: Get personalized quotes from [X] top carriers in minutes.

[FORM: Step 1]

Trust bar: [Carrier logos] | [Star rating] | "Licensed in [State]"

Why [Agency Name]:
- Access to [X] carriers (we shop, you save)
- Licensed agents, not a call center
- [X] years serving [City]
- Free policy review, no obligation

[Testimonial from a local client]

FAQ: 3-4 questions about getting quotes online

[Phone CTA: "Questions? Call (555) 555-5555"]
```

---

## Insurance SEO Strategy

### High-Intent Keywords

| Keyword Pattern | Example | Monthly Volume (typical) |
|----------------|---------|------------------------|
| [insurance type] agent [city] | "auto insurance agent phoenix" | 100-500 |
| [insurance type] quotes [city] | "home insurance quotes scottsdale" | 50-200 |
| best [insurance type] [city] | "best car insurance phoenix" | 200-1000 |
| cheap [insurance type] [city] | "cheap auto insurance phoenix" | 500-2000 |
| [insurance type] near me | "insurance agent near me" | 1000-5000 |
| independent insurance agent [city] | "independent insurance agent phoenix" | 50-200 |
| [carrier name] agent [city] | "State Farm agent phoenix" | 100-500 |

### Page Structure for Insurance SEO

**Homepage:** Target "[insurance type] agent [city]" or "independent insurance agent [city]"

**Service pages (one per line of business):**
- `/auto-insurance/` → "Auto Insurance in [City]"
- `/home-insurance/` → "Homeowners Insurance in [City]"
- `/commercial-insurance/` → "Commercial Insurance in [City]"
- `/life-insurance/` → "Life Insurance in [City]"
- `/medicare/` → "Medicare Insurance in [City]"

**City pages (for multi-city agencies):**
- `/auto-insurance/scottsdale/` → "Auto Insurance in Scottsdale"
- See service-area-pages skill for full template

**Comparison/info pages:**
- `/[carrier]-vs-[carrier]/` → "Progressive vs GEICO in [City]"
- `/[insurance-type]-cost-[city]/` → "Average Home Insurance Cost in [City]"

### Google Local Services Ads (LSA)

**What LSAs are:** Pay-per-lead ads that appear above PPC ads in Google. Show your photo, rating, "Google Screened" badge.

**Requirements for insurance agents:**
- State insurance license verification
- Background check
- Business insurance verification
- Google Screened badge (free, after verification)

**LSA optimization:**
- Respond to leads within 5 minutes (response time affects ranking)
- Keep your Google review score above 4.5
- Set accurate service areas and hours
- Turn on during business hours only (can't return calls at 2am)
- Budget: start at $50-100/week, adjust based on lead quality

---

## Seasonal Campaign Calendar

### Personal Lines Year-Round

| Month | Campaign Focus | Why |
|-------|---------------|-----|
| Jan-Feb | New Year policy reviews | Life changes trigger coverage changes |
| Mar-Apr | Spring storm prep, flood insurance | Storm season awareness |
| May-Jun | Umbrella policy push | Summer travel, pool season = liability |
| Jul-Aug | Back to school, young driver discounts | New teen drivers |
| Sep-Oct | Fall home maintenance, winter prep | Before heating season |
| Nov-Dec | Year-end review, gift of life insurance | Tax planning, holiday giving |

### Medicare-Specific (CRITICAL COMPLIANCE)

| Period | Dates | What's Allowed |
|--------|-------|----------------|
| AEP (Annual Enrollment) | Oct 15 - Dec 7 | Can market all Medicare Advantage + Part D plans |
| OEP (Open Enrollment) | Jan 1 - Mar 31 | Can market MA plan switches only (limited) |
| ICEP (Initial Coverage) | 3 months before to 3 months after turning 65 | New-to-Medicare prospects |
| SEP (Special Enrollment) | Varies | Qualifying life events only |

**Medicare marketing compliance (CMS rules):**
- Cannot use the word "free" without qualification
- Cannot claim a plan is "the best"
- Must include disclaimer: "We do not offer every plan available in your area. Currently we represent [X] organizations which offer [X] products in your area."
- Cannot cold-call — must have permission to contact (Scope of Appointment form)
- Cannot market at educational events (T-FAE rules)
- Must submit all marketing materials to CMS/carrier for approval
- Cannot use testimonials that guarantee specific outcomes
- Cannot hold marketing events at healthcare facilities

### Health Insurance

| Period | Dates | Notes |
|--------|-------|-------|
| OEP (ACA) | Nov 1 - Jan 15 | Marketplace plans |
| SEP | Year-round | Qualifying life events (job loss, marriage, baby, move) |

### Commercial Lines

| Quarter | Focus |
|---------|-------|
| Q1 | New business outreach (new year, new budgets) |
| Q2 | Workers comp audits, fleet reviews |
| Q3 | Renewal preparation (most commercial policies renew Q4) |
| Q4 | Heavy renewal season + next-year planning |

---

## Referral Program Design

### Structure

**For clients:**
- Reward: gift card ($25-50), donation to their chosen charity, or account credit
- Trigger: when referred person binds a policy
- Process: simple — give them cards/link, they share, you track

**For professional referral partners:**
- Real estate agents → home + auto referrals
- Mortgage brokers → homeowners insurance (required at closing)
- Auto dealers → auto insurance
- CPAs / financial advisors → life, umbrella, business insurance
- HR managers → group benefits inquiries

**Outreach to partners:**
> "Hey [Name], I work with a lot of clients who are [buying homes / getting mortgages / etc.] and could use a great [realtor / lender / etc.]. I'd love to set up a mutual referral arrangement — I'll recommend you to my clients, and if you ever have clients who need insurance help, send them my way. No cost, no obligation. Interested?"

### Tracking

- Unique referral links per partner (or simple "who referred you?" on quote form)
- Monthly report to referral partners showing # of referrals received
- Quarterly check-in with top referral sources

---

## Retention & Cross-Sell

### Policy Renewal Marketing

**Timeline:**
- 90 days before renewal: Coverage review offer ("Let's make sure you're still getting the best rate")
- 60 days before renewal: Market check (quote other carriers, present options)
- 30 days before renewal: Renewal confirmation or switch recommendation
- At renewal: Thank-you + cross-sell opportunity

**Renewal email template:**
> Hi [Name],
>
> Your [policy type] with [carrier] renews on [date]. I've already started reviewing your coverage and shopping the market to make sure you're still getting the best rate.
>
> I'll reach out next week with what I find. In the meantime, if anything has changed — new car, home renovation, teen driver, etc. — let me know so I can factor that in.
>
> Talk soon,
> [Agent Name]

### Cross-Sell Sequences

**Trigger-based cross-sells (highest conversion):**

| Trigger | Cross-Sell | Timing |
|---------|-----------|--------|
| New home policy | Auto bundle discount | Immediately |
| New auto policy | Home + umbrella | Within 30 days |
| New baby (life event) | Life insurance | 30-60 days after |
| Home purchase | Umbrella policy | At closing |
| Business formation | Commercial insurance | Immediately |
| Child turns 16 | Auto policy addition | 2 months before |

**Annual cross-sell review:**
Once per year, for every client, check: what lines do they have vs. what could they need?

| Client Has | Offer Next |
|-----------|-----------|
| Auto only | Home, umbrella, life |
| Home only | Auto (bundle), umbrella |
| Auto + Home | Umbrella, life |
| P&C only | Life, disability |
| Personal only | Commercial (if business owner) |

---

## Compliance Essentials

### State Advertising Rules (General)

Most states require:
- Agent/agency name as it appears on the license
- License number displayed
- State in which licensed
- Disclaimer that not all products available in all states

**High-regulation states to watch:**
- **California:** Strict rules on lead generation, telemarketing, insurance advertising. Requires CDI approval for certain marketing materials.
- **Texas:** TDI oversees advertising. Must include license # in all ads. Prohibited from misrepresenting coverage.
- **Florida:** OIR regulates advertising. Specific rules for health/Medicare marketing. Hurricane-related marketing restrictions.
- **New York:** DFS strict oversight. "Free" policy review language requires specific disclosure.

### Digital Advertising Rules

- PPC/social ads must include agency name and state
- Cannot guarantee savings ("save up to" requires substantiation)
- Cannot use scare tactics ("you could lose everything without...")
- Testimonials must be real and representative
- Cannot use carrier logos without permission
- Must clearly identify as an advertisement (FTC + state rules)

### Email/SMS Compliance

- CAN-SPAM: must include unsubscribe link, physical address, honest subject line
- TCPA: SMS requires prior express written consent
- State do-not-call lists: check before cold calling
- Medicare: Scope of Appointment required before discussing specific plans

---

## Community Marketing

### Sponsorship Strategy

| Opportunity | Cost Range | Benefit |
|------------|-----------|---------|
| Little League / youth sports | $200-500/season | Logo on jerseys, banner at field |
| School programs | $100-300 | Newsletter mention, event presence |
| Charity events / 5Ks | $250-1000 | Logo on materials, booth space |
| Chamber of Commerce | $200-500/year | Directory listing, networking, backlink |
| Local business awards | $100-300 | PR coverage, backlink |
| HOA newsletters | Often free | Direct access to homeowners |

### Content from Community Involvement

- Photos at sponsored events (for GBP, social, website)
- Blog posts about community events you supported
- Social media posts from sponsorships
- "Community Partners" page on website (local link building + local authority)
- Backlinks from event websites, school websites, charity pages

---

## Output Format

### Marketing Strategy Document

1. **Agency Overview** — lines of business, target market, competitive position
2. **Website Optimization** — trust signals, quote funnel, SEO keywords, schema
3. **Lead Generation Plan** — LSA, local SEO, referral program, community marketing
4. **Retention Strategy** — renewal timeline, cross-sell matrix, communication cadence
5. **Seasonal Calendar** — campaigns mapped to enrollment periods and seasonal triggers
6. **Compliance Notes** — state-specific requirements, Medicare rules if applicable

### For a Specific Campaign

1. **Objective** — what line of business, what market
2. **Audience** — who exactly
3. **Message** — value prop, trust signals, CTA
4. **Channels** — email, social, direct mail, events
5. **Compliance Review** — disclaimers, required disclosures
6. **Measurement** — leads generated, policies bound, cost per acquisition

---

## References

- [Insurance Compliance Guide](references/compliance-guide.md): State-specific advertising rules, Medicare marketing requirements, FTC/CAN-SPAM essentials
- [Seasonal Campaign Templates](references/seasonal-campaigns.md): Email and social templates for each enrollment period and seasonal campaign

---

## Task-Specific Questions

1. Are you independent or captive?
2. What lines of business do you write?
3. Which states are you licensed in?
4. Do you write Medicare? (triggers compliance requirements)
5. What's your current lead source mix?
6. What CRM/AMS do you use?
7. Do you have a referral program today?

---

## Related Skills

- **local-seo**: For GBP optimization, citations, local rankings
- **review-management**: For building and managing agency reviews
- **service-area-pages**: For city-specific insurance landing pages
- **form-cro**: For quote form optimization
- **email-sequence**: For renewal and cross-sell email sequences
- **copywriting**: For insurance-specific web copy
- **cold-email**: For outreach to referral partners
- **schema-markup**: For InsuranceAgency structured data
