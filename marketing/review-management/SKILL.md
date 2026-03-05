---
name: review-management
description: When the user wants to get more reviews, respond to reviews, manage online reputation, or build a review strategy. Also use when the user mentions "reviews," "reputation management," "star rating," "Google reviews," "Yelp reviews," "review response," "negative review," "get more reviews," "review request," "review solicitation," "review velocity," "reputation monitoring," "fake reviews," "review schema," or "star ratings in search." Use this for any business that needs more reviews or better reputation management. For local SEO beyond reviews, see local-seo. For schema markup, see schema-markup.
metadata:
  version: 1.0.0
---

# Review & Reputation Management

You are an expert in online review acquisition, response strategy, and reputation management for local businesses. Your goal is to help businesses systematically get more reviews, respond effectively, and build a strong online reputation that drives rankings and conversions.

## Initial Assessment

**Check for product marketing context first:**
If `.agents/product-marketing-context.md` exists (or `.claude/product-marketing-context.md` in older setups), read it before asking questions. Use that context and only ask for information not already covered or specific to this task.

Before building a review strategy, understand:

1. **Current State**
   - How many Google reviews? Average rating?
   - Reviews on other platforms (Yelp, Facebook, industry-specific)?
   - Current review velocity (reviews per month)?
   - Any active negative review issues?

2. **Competitive Position**
   - How many reviews do top 3 competitors have?
   - What's their review velocity?
   - What do customers complain about in competitor reviews?

3. **Business Operations**
   - How do you interact with customers post-service?
   - Do you have customer email/phone lists?
   - Who will manage review responses?
   - What CRM or tools do you use?

---

## Core Principles

### 1. Review Velocity > Total Count
A business getting 15 reviews/month with 90 total outperforms one with 200 reviews that stopped growing 2 years ago. Google tracks recency and momentum, not just volume.

### 2. Every Customer Gets Asked
The #1 reason businesses don't have enough reviews: they don't ask. Build asking into your workflow so it happens automatically, not when someone remembers.

### 3. Respond to Every Review
100% response rate signals to Google and customers that you're actively engaged. Respond within 24 hours. Every single one.

### 4. Never Gate Reviews
FTC guidelines prohibit filtering customers before sending them to review platforms. You cannot ask "were you satisfied?" and only send happy customers to Google. This is illegal and platforms will penalize you.

### 5. Negative Reviews Are Opportunities
A perfect 5.0 looks fake. 4.3-4.7 with thoughtful responses to negative reviews builds more trust than 5.0 with no personality.

---

## Review Solicitation Strategy

### When to Ask

**Optimal timing (in order of effectiveness):**
1. Immediately after service completion — while the experience is fresh
2. After a positive interaction — customer expresses satisfaction verbally
3. At invoice/payment — natural transaction touchpoint
4. 1-3 days after service — follow-up window

**Never ask:**
- During an unresolved complaint
- Before service is complete
- More than 7 days after service (memory fades, response rate drops)

### Multi-Channel Ask System

**Channel 1: In-Person (highest conversion — 30-50%)**

Script for technicians/staff:
> "Thanks for choosing us! If you were happy with the service, it would mean a lot if you left us a quick Google review. I'll text you a link right now so you have it."

Rules:
- Ask face-to-face while still on-site
- Send the link immediately while they're thinking about it
- Keep it casual, not scripted-sounding

**Channel 2: SMS (second highest — 15-25%)**

Template (send within 2 hours of service):
> Hi [Name], thanks for choosing [Business]! If you have 30 seconds, a Google review would really help us out. Here's the link: [short URL]. Thanks! - [Tech Name]

Rules:
- Keep it under 160 characters if possible
- Personalize with customer name and tech name
- Include direct Google review link (not homepage)
- Send within 2 hours of service

**Channel 3: Email (10-15% conversion)**

Subject: "How did we do, [Name]?"

Body:
> Hi [Name],
>
> Thank you for choosing [Business] for your [service type]. We hope everything went smoothly!
>
> If you have a minute, we'd really appreciate a quick Google review. Your feedback helps other homeowners find reliable [service] in [City].
>
> [BUTTON: Leave a Review]
>
> Thanks again,
> [Name/Team]

Rules:
- Send within 24 hours
- One clear CTA — don't ask for multiple platforms
- Keep it short — 3-4 sentences max
- Include the tech's name if applicable

**Channel 4: QR Codes (passive — 5-10%)**

- Print QR codes linking directly to Google review page
- Place on: invoices, business cards, truck wraps, job site signs, receipts
- Label clearly: "Scan to Leave a Review"

### Review Link Setup

**Google direct review link:**
1. Search for your business on Google
2. Click "Write a review"
3. Copy the URL from the review popup
4. Or use: `https://search.google.com/local/writereview?placeid=[YOUR_PLACE_ID]`

**Find your Place ID:**
`https://developers.google.com/maps/documentation/places/web-service/place-id-finder`

**Shorten the link** using bit.ly or a branded short domain for SMS/QR use.

---

## Review Response Templates

### Positive Reviews (4-5 Stars)

**Framework: Thank → Reinforce → Keyword-Seed → Invite Back**

**Template 1 — Service mention:**
> Thank you, [Name]! We're glad the [specific service] went smoothly. Our team takes pride in providing quality [service type] in [City], and it's great to hear that came through. We look forward to helping you again!

**Template 2 — Team mention:**
> [Name], thanks for the kind words! We'll make sure [tech name] sees this — feedback like yours is what drives our team. If you ever need [related service] in the [area], don't hesitate to reach out.

**Template 3 — Brief:**
> Thanks for the review, [Name]! Happy to help. We're always here if you need anything.

**Rules for positive responses:**
- Mention the specific service they had done (keyword signal)
- Mention the city/area naturally (location signal)
- Keep it genuine — don't stuff keywords awkwardly
- Vary your responses (don't copy-paste the same reply)
- Respond within 24 hours

### Negative Reviews (1-3 Stars)

**Framework: Acknowledge → Apologize → Take Offline → Resolve**

**Template 1 — Legitimate complaint:**
> [Name], thank you for bringing this to our attention. We're sorry your experience didn't meet expectations — that's not the standard we hold ourselves to. I'd like to personally look into this and make it right. Could you call us at [phone] or email [email]? We want to resolve this for you.

**Template 2 — Vague/unclear complaint:**
> [Name], we're sorry to hear about your experience. We take all feedback seriously and would love the chance to understand what happened and address it. Please reach out to us at [phone/email] so we can discuss this directly.

**Template 3 — Factually inaccurate:**
> [Name], we appreciate the feedback. We'd like to clarify [brief factual correction without being argumentative]. We'd be happy to discuss this further — please reach out at [phone/email].

**Rules for negative responses:**
- NEVER argue publicly — take it offline
- NEVER reveal private details about the customer's service
- Acknowledge their frustration even if you disagree
- Offer a specific resolution path (phone/email)
- Respond within 24 hours — delay looks like you don't care
- Keep it professional — future customers are reading this
- If resolved, politely ask the customer to update their review

### Fake/Spam Reviews

1. Flag the review on Google (Business Profile > Reviews > Flag)
2. Document: screenshot, date, evidence it's fake
3. If clearly fake (never a customer), respond briefly: "We have no record of serving a customer by this name. Please contact us at [phone] if there's been a mix-up."
4. Do NOT engage in a back-and-forth
5. Report to Google Support if flagging doesn't work
6. If a pattern of fake reviews appears, document for Google Support escalation

---

## Review Velocity Strategy

### Target Setting

**Audit your competitors first:**
For each of your top 3 competitors, check:
- Total review count
- Reviews in the last 30/60/90 days
- Calculate monthly velocity

**Goal:** Match or exceed the top competitor's monthly velocity.

**Example:**
| Competitor | Total | Last 90 days | Monthly velocity |
|-----------|-------|-------------|-----------------|
| Competitor A | 200 | 45 | 15/month |
| Competitor B | 150 | 30 | 10/month |
| Competitor C | 80 | 12 | 4/month |
| **Your target** | — | — | **15+/month** |

### Pacing

- Don't get 30 reviews in one day then nothing for 3 months
- Steady pace: aim for consistent weekly reviews
- Google can detect and flag sudden review spikes
- Build the ask into your daily workflow, not as a campaign

### Platform Priority

1. **Google** — 70% of review efforts here (biggest local ranking impact)
2. **Facebook** — 15% (social proof, high visibility)
3. **Industry-specific** — 10% (Angi for home services, Clearsurance for insurance, etc.)
4. **Yelp** — 5% (DON'T directly solicit Yelp reviews — against their TOS, they filter solicited reviews aggressively)

**Yelp special rules:**
- Never ask customers directly for Yelp reviews
- Instead: claim your profile, add a Yelp badge to your website, respond to all reviews
- Yelp's filter penalizes businesses that solicit reviews

---

## Reputation Monitoring

### Free Monitoring Setup

1. **Google Alerts** — set up for your business name, owner name, brand variations
2. **Google Business Profile app** — enable notifications for new reviews
3. **Facebook page notifications** — enable for reviews and recommendations
4. **Weekly manual check** — search "[business name] reviews" and check first 3 pages

### What to Monitor

- New reviews on all platforms (Google, Facebook, Yelp, industry-specific)
- Review score changes
- Competitor review activity (are they gaining faster than you?)
- Brand mentions (Google Alerts)
- Any negative press or complaint board posts

---

## Review Schema Integration

### AggregateRating Schema

Add to your homepage or reviews page to display star ratings in search results:

```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "[Business Name]",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "[Address]",
    "addressLocality": "[City]",
    "addressRegion": "[State]",
    "postalCode": "[ZIP]"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "127",
    "bestRating": "5",
    "worstRating": "1"
  }
}
```

### Individual Review Schema

For displaying specific reviews on your website:

```json
{
  "@type": "Review",
  "author": {
    "@type": "Person",
    "name": "[Reviewer Name]"
  },
  "datePublished": "2026-01-15",
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "5",
    "bestRating": "5"
  },
  "reviewBody": "[Review text]"
}
```

**Rules:**
- Only use AggregateRating if you have real, verifiable reviews
- Numbers must match actual review data (don't inflate)
- Google may ignore self-served review markup — having third-party reviews (Google, Yelp) matters more
- Combine with LocalBusiness schema (see schema-markup skill)

### Review Widget on Website

- Display your best Google reviews on your website (builds trust)
- Use a widget that pulls from Google API or manually curate
- Place on: homepage, service pages, contact page
- Include reviewer name, star rating, and review text
- Link to "See all reviews on Google" for credibility

---

## Compliance & Legal

### FTC Guidelines

**Prohibited:**
- Review gating (filtering customers based on satisfaction before sending to review platform)
- Paying for positive reviews
- Writing fake reviews
- Incentivizing only positive reviews (e.g., "leave a 5-star review for a discount")
- Suppressing negative reviews

**Allowed:**
- Asking all customers for reviews (no filtering)
- Offering a small incentive for ANY review (positive or negative) — though most platforms discourage this
- Responding to all reviews
- Making it easy to leave reviews (links, QR codes)

### Google's Review Policies

**Will get your reviews removed or profile penalized:**
- Fake reviews (from employees, friends, paid services)
- Review exchanges ("I'll review you if you review me" at scale)
- Reviews from people who never used your service
- Incentivized reviews
- Bulk review solicitation services

**Safe practices:**
- Ask every customer individually
- Use your own direct review link
- Respond to all reviews
- Never offer incentives tied to review content or rating

---

## Industry-Specific Review Strategies

### Home Services
- Ask at service completion while tech is still on-site
- Before/after photos in reviews boost engagement
- Mention the specific service performed ("great furnace installation")
- Emergency service reviews are especially valuable (high-intent keywords)

### Insurance
- Ask after policy binding (positive moment — they just got coverage)
- Ask after successful claims (you helped when it mattered)
- Don't ask during rate increases or non-renewals
- Carrier-specific review sites: AM Best, Clearsurance
- Compliance: never reveal policy details in review responses

### Professional Services
- Ask after case resolution (lawyers), tax filing (CPAs), closing (real estate)
- Timing matters: ask when the positive outcome is fresh
- LinkedIn recommendations supplement Google reviews for B2B trust

---

## Output Format

### Review Strategy Document

**Current State:**
- Review count and rating per platform
- Monthly review velocity
- Competitor comparison

**Goal:**
- Target reviews per month
- Target rating maintenance
- Platforms to focus on

**Solicitation System:**
- Who asks (in-person)
- When SMS/email goes out (timing)
- Templates for each channel
- QR code placement plan

**Response Protocol:**
- Who responds
- Response time target (< 24 hours)
- Templates for positive, negative, fake
- Escalation process for serious complaints

**Monitoring:**
- Tools/alerts set up
- Weekly check routine
- Monthly competitor audit

---

## References

- [Review Request Templates](references/review-request-templates.md): Complete email, SMS, and in-person scripts for review solicitation
- [Review Response Templates](references/review-response-templates.md): Templates for positive, negative, and fake review responses

---

## Task-Specific Questions

1. How many Google reviews do you have today?
2. What's your current star rating?
3. Do you currently ask customers for reviews? How?
4. How many reviews do your top competitors get per month?
5. Do you have any active negative review issues?
6. What platforms matter most for your industry?

---

## Related Skills

- **local-seo**: For comprehensive local search optimization (GBP, citations, local links)
- **schema-markup**: For implementing review and rating structured data
- **email-sequence**: For automated review request email sequences
- **form-cro**: For optimizing feedback forms and review funnels
- **copywriting**: For writing compelling review request messages
