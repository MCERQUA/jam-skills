---
name: maintenance-programs
description: "Design, price, and sell maintenance agreements and membership programs for local service businesses. Use when the owner mentions 'maintenance agreement,' 'service contract,' 'membership program,' 'maintenance plan,' 'recurring revenue,' 'annual tune-up,' 'service plan tiers,' 'seasonal service,' 'preventative maintenance,' or wants to build recurring revenue through service agreements. For selling/upselling maintenance plans during a service call, see sales-scripts. For seasonal campaign messaging, see customer-comms."
metadata:
  version: 1.0.0
---

# Maintenance Programs & Membership Plans

Design, price, implement, and grow recurring revenue through maintenance agreements and membership programs for local service businesses.

---

## 1. Initial Assessment

Before designing any maintenance program, gather critical context about the business.

### Check Existing Context

Look for existing business information:

1. **Product Marketing Context** — Check if `product-marketing-context` skill has already captured the business profile (services, market, competitors).
2. **Business Config** — Check for `business/config.json` in the workspace for stored business details.
3. **Pricing Data** — Check if `pricing-job-costing` skill has cost/margin data we can reference.

### Discovery Questions

Ask the business owner these questions (skip any already answered in existing context):

**Business Fundamentals:**
- What services do you provide? (HVAC, plumbing, electrical, pest control, roofing, landscaping, cleaning, etc.)
- What is your average service ticket size?
- How many active customers do you have in your database?
- What is your geographic service area (radius, zip codes, city)?
- How many techs/crews do you run daily?

**Current Maintenance Programs:**
- Do you currently offer any maintenance plans or service agreements?
- If yes: How many active members? What do they pay? What's included? What's your renewal rate?
- If no: Have you tried before? What stopped you?
- Are customers asking for ongoing service or calling back repeatedly?

**Competitive Landscape:**
- What do your top 3 competitors offer for maintenance plans?
- What do they charge? (If unknown, we can research this together.)
- Is there a dominant player in your market with a well-known program?
- What would make your program stand out?

**Operational Software:**
- What software do you use for scheduling, dispatch, and invoicing?
  - ServiceTitan, Housecall Pro, Jobber, FieldEdge, Service Fusion, GorillaDesk, PestRoutes, etc.
- Does your software support recurring billing and membership tracking?
- Do you have a CRM or customer database?
- How do you currently collect payments (card on file, invoice, etc.)?

**Revenue Goals:**
- What is your current annual revenue?
- What percentage of revenue comes from repeat customers vs. new?
- What is your target for monthly recurring revenue (MRR) in Year 1?
- How many new members per month is realistic given your call volume?

---

## 2. Core Principles

These principles are non-negotiable. Every maintenance program must follow them.

### Recurring Revenue Transforms a Service Business

The difference between a struggling service business and a thriving one is predictable revenue. Without maintenance agreements, you live on the feast/famine cycle: slammed in peak season, starving in the off-season. A healthy maintenance program smooths out revenue, fills the schedule during slow months, and creates a predictable base you can plan around.

### A Maintenance Plan Customer Is Worth 5-7x a One-Time Customer

The math is simple. A one-time customer pays for one job and may never call again. A maintenance plan customer pays monthly for years, calls you first for repairs (not your competitor), replaces equipment through you, and refers friends because they feel like an insider. Lifetime value: one-time customer ~$500-800, maintenance member ~$3,000-6,000+.

### Target: 20-30% of Customers on a Plan Within Year 1

This is aggressive but achievable if you pitch consistently. Most businesses that "try" maintenance plans pitch them sometimes, to some customers, when they remember. That gets 3-5% adoption. To hit 20-30%, every tech pitches every job, every estimate includes the plan, and marketing reinforces the message seasonally.

### Plans Must Be Profitable on Their Own

A maintenance plan is NOT a loss leader. It is NOT a discount card. The plan itself — the recurring fee minus the cost of delivering the included services — must generate profit. If you lose money on every member and hope to make it up on repairs, you have a bad plan. Price it right.

### The Plan Is a RELATIONSHIP, Not a Transaction

Customers do not buy maintenance plans for the tune-up. They buy peace of mind, priority treatment, the feeling that someone is looking out for them. Every touchpoint — the reminder call, the tech at the door, the invoice — reinforces that they made the right decision. Treat members like VIPs and they will never leave.

### Sell Peace of Mind, Not a Checklist of Tasks

Never lead with "you get a 21-point inspection." Lead with "you'll never have to worry about your [system] breaking down unexpectedly." The checklist is proof of value. Peace of mind is the value.

---

## 3. Program Design Framework

### Tier Structure

Offer 2-3 tiers. Never more than 3. More than 3 creates decision paralysis and kills conversion rates.

| Tier | Name Ideas | Target Customer | Pricing Model |
|------|-----------|----------------|---------------|
| Basic | Essential / Bronze / Comfort / Standard | Price-sensitive customers, minimal needs, rental properties | $[X]/month or $[X]/year |
| Premium | Preferred / Silver / Complete / Plus | Most customers — best value tier, this is what you want 60-70% of members on | $[X]/month or $[X]/year |
| VIP | Priority / Gold / Ultimate / Elite | High-value customers who want everything, large homes, multiple systems | $[X]/month or $[X]/year |

**Naming Rules:**
- Use names that feel like status levels, not product SKUs
- Avoid "Basic" — it sounds cheap. Use "Essential" or "Comfort" instead
- The middle tier should sound like the obvious smart choice
- The top tier should feel exclusive
- Match the brand voice (luxury brand = Gold/Platinum; friendly brand = Comfort/Complete/Family)

**Design Rules:**
- Each tier must have at least ONE clear upgrade reason over the tier below
- The jump from Basic to Premium should feel like an obvious deal
- The jump from Premium to VIP should feel premium but justifiable for the right customer
- Never give everything away in the Basic tier — it should leave customers wanting more
- The VIP tier can include aspirational benefits that cost you little but feel high-value (priority scheduling, after-hours access, dedicated account manager)

---

### Trade-Specific Program Designs

#### HVAC Maintenance Plans

| Benefit | Essential ($15/mo) | Preferred ($25/mo) | Priority ($40/mo) |
|---------|-------------------|--------------------|--------------------|
| AC tune-up (spring) | 1 | 1 | 1 |
| Heating tune-up (fall) | -- | 1 | 1 |
| Repair discount | 10% | 15% | 20% |
| Priority scheduling | -- | Yes (next business day) | Yes (same day) |
| After-hours/weekend fee waived | -- | -- | Yes |
| Indoor air quality check | -- | -- | Annual |
| Filter delivery | -- | -- | Quarterly (standard sizes) |
| Equipment replacement credit | -- | -- | $500 toward new system |
| No diagnostic fee | -- | Yes | Yes |
| Annual safety inspection | -- | -- | Yes (CO, gas leak) |
| Transferable to new homeowner | -- | -- | Yes |

**Typical HVAC Plan Economics:**
- AC tune-up labor + materials cost: $65-85
- Heating tune-up labor + materials cost: $65-85
- Essential: $180/year revenue, ~$75 cost = $105 gross profit
- Preferred: $300/year revenue, ~$160 cost = $140 gross profit + captured repairs
- Priority: $480/year revenue, ~$210 cost = $270 gross profit + captured repairs + equipment sales

**Multi-System Pricing:**
- 2 systems: add 60-75% of single-system price per additional system
- 3+ systems: add 50-60% per additional system
- Example: Preferred single system = $25/mo; 2 systems = $40/mo; 3 systems = $52/mo

---

#### Plumbing Maintenance Plans

| Benefit | Essential ($12/mo) | Preferred ($22/mo) | Priority ($35/mo) |
|---------|-------------------|--------------------|--------------------|
| Annual whole-home inspection | 1 | 1 | 2 (spring + fall) |
| Water heater flush & inspection | -- | 1 | 1 |
| Drain cleaning (main line) | -- | 1 | All drains annual |
| Repair discount | 10% | 15% | 20% |
| Priority scheduling | -- | Yes | Yes (same day) |
| Emergency/after-hours fee waived | -- | -- | Yes |
| Water quality test | -- | -- | Annual |
| Fixture inspection & tightening | -- | Yes | Yes |
| Sewer camera inspection | -- | -- | Annual |
| No trip/diagnostic fee | -- | Yes | Yes |
| Hose bib winterization | -- | -- | Annual (fall) |
| Leak detection scan | -- | -- | Annual |

**Typical Plumbing Plan Economics:**
- Annual inspection labor cost: $50-70
- Water heater flush cost: $40-60
- Main line drain cleaning cost: $80-120
- Essential: $144/year revenue, ~$60 cost = $84 gross profit
- Preferred: $264/year revenue, ~$170 cost = $94 gross profit + captured repairs
- Priority: $420/year revenue, ~$280 cost = $140 gross profit + captured repairs + re-pipe/water heater sales

---

#### Pest Control Maintenance Plans

| Benefit | Essential ($30/mo) | Preferred ($45/mo) | Priority ($65/mo) |
|---------|-------------------|--------------------|--------------------|
| Quarterly treatments | 4 | 4 | 4 + unlimited callbacks |
| Interior treatment | -- | Yes | Yes |
| Exterior perimeter treatment | Yes | Yes | Yes |
| Re-treatment guarantee | 30 days | 60 days | Unlimited between visits |
| Rodent monitoring stations | -- | Yes (exterior) | Yes (interior + exterior) |
| Termite monitoring | -- | -- | Yes (Sentricon/Trelona) |
| Mosquito yard treatment | -- | -- | Apr-Oct (seasonal) |
| Spider web removal (exterior) | -- | Yes | Yes |
| Attic/crawl space inspection | -- | -- | Annual |
| Wasp/nest removal | -- | -- | Included |
| De-webbing (eaves, porches) | Yes | Yes | Yes |
| Free initial treatment | -- | Yes (waived setup fee) | Yes (waived setup fee) |

**Typical Pest Control Plan Economics:**
- Quarterly treatment labor + materials: $35-50 per visit
- Rodent monitoring cost: $15-20/quarter
- Essential: $360/year revenue, ~$160 cost = $200 gross profit
- Preferred: $540/year revenue, ~$260 cost = $280 gross profit
- Priority: $780/year revenue, ~$400 cost = $380 gross profit

**Pest Control Note:** Pest control is inherently recurring — most customers already expect quarterly service. The plan structure here is about locking in commitment, adding value, and preventing price-shopping between visits.

---

#### Roofing Maintenance Plans

| Benefit | Essential ($10/mo) | Preferred ($18/mo) |
|---------|-------------------|--------------------|
| Annual roof inspection | 1 | 2 (spring + fall) |
| Minor repair credits | $100/year | $250/year |
| Gutter cleaning | -- | 2x/year |
| Photo documentation report | Yes | Yes (with comparison to prior year) |
| Priority storm response | -- | Yes (within 48 hours) |
| Transferable to new owner | -- | Yes |
| Flashing & sealant check | Yes | Yes |
| Valley & penetration check | Yes | Yes |
| Attic ventilation check | -- | Yes |
| Debris removal | -- | Yes |

**Roofing Plan Note:** Roofing maintenance plans have low delivery cost and high customer retention because homeowners fear surprise roof problems. The photo documentation is extremely high-value — it builds trust and creates a record for insurance claims. Two tiers is sufficient for most roofing companies.

**Typical Roofing Plan Economics:**
- Inspection labor cost: $40-60 per visit
- Minor repair credit risk: ~$60-80 actually used per year
- Essential: $120/year revenue, ~$100 cost = $20 gross profit + captured re-roofs
- Preferred: $216/year revenue, ~$180 cost = $36 gross profit + captured re-roofs + gutter jobs
- The real money is re-roof sales — maintenance members replace through you 90%+ of the time

---

#### Landscaping Maintenance Plans

| Benefit | Essential ($150/mo) | Preferred ($250/mo) | Priority ($400/mo) |
|---------|--------------------|--------------------|---------------------|
| Weekly mowing (growing season) | Yes | Yes | Yes |
| Edging & blowing | Yes | Yes | Yes |
| Seasonal cleanups | 2 (spring + fall) | 4 (quarterly) | 4 (quarterly) |
| Mulching | -- | Annual (spring) | 2x/year |
| Fertilization | -- | 4 rounds | 6 rounds + weed control |
| Shrub/hedge trimming | -- | 2x/year | 4x/year |
| Irrigation startup & shutdown | -- | -- | Yes (spring + fall) |
| Irrigation monitoring/adjustment | -- | -- | Monthly (growing season) |
| Aeration & overseeding | -- | -- | Annual (fall) |
| Snow removal (if applicable) | -- | -- | Included (per event) |
| Landscape bed maintenance | -- | -- | Monthly weeding |
| Annual landscape consultation | -- | -- | Yes (design review) |

**Landscaping Plan Note:** Landscaping is already a recurring service for most providers. The plan structure here upgrades one-off mowing customers into full-property-care members. The upsell path is clear: mowing only -> mowing + treatments -> full property management.

**Typical Landscaping Plan Economics:**
- Weekly mowing cost: $30-50/visit, ~30 visits/year = $900-1,500
- Essential: $1,800/year revenue, ~$1,100 cost = $700 gross profit
- Preferred: $3,000/year revenue, ~$1,900 cost = $1,100 gross profit
- Priority: $4,800/year revenue, ~$3,200 cost = $1,600 gross profit

---

#### Electrical Maintenance Plans

| Benefit | Essential ($10/mo) | Preferred ($20/mo) | Priority ($35/mo) |
|---------|-------------------|--------------------|---------------------|
| Annual electrical safety inspection | 1 | 1 | 2 |
| Panel inspection & tightening | Yes | Yes | Yes |
| Surge protector check | -- | Yes | Yes |
| Repair discount | 10% | 15% | 20% |
| Priority scheduling | -- | Yes | Yes (same day) |
| After-hours fee waived | -- | -- | Yes |
| Smoke/CO detector battery replacement | -- | Yes | Yes |
| GFCI/AFCI testing | -- | Yes | Yes |
| Whole-home surge protector (installed) | -- | -- | Included |
| Generator maintenance (if applicable) | -- | -- | Annual |
| No diagnostic/trip fee | -- | Yes | Yes |
| Thermal imaging scan | -- | -- | Annual |

---

#### Cleaning Services (Residential) Maintenance Plans

| Benefit | Essential ($120/mo) | Preferred ($200/mo) | Priority ($350/mo) |
|---------|--------------------|--------------------|---------------------|
| Bi-weekly standard cleaning | Yes | Yes | Yes |
| Kitchen deep clean | Quarterly | Monthly | Monthly |
| Bathroom deep clean | Quarterly | Monthly | Monthly |
| Interior windows | -- | Quarterly | Monthly |
| Baseboards & trim detail | -- | Yes (every visit) | Yes (every visit) |
| Oven/appliance deep clean | -- | Quarterly | Monthly |
| Refrigerator cleanout | -- | -- | Monthly |
| Laundry (wash/fold) | -- | -- | Each visit |
| Organizing session | -- | -- | Quarterly (2 hours) |
| Same cleaning team guaranteed | -- | Yes | Yes |
| Holiday/party prep clean | -- | -- | 2 included/year |
| Priority rescheduling | -- | -- | Yes |

---

### Custom Program Builder

For trades not listed above, use this framework:

1. **List all services** the business provides
2. **Categorize** them: Preventive (inspections, tune-ups), Corrective (repairs), Enhancement (upgrades)
3. **Identify which preventive services** should be done on a schedule (annual, semi-annual, quarterly, monthly)
4. **Calculate the delivery cost** of each included service (labor + materials)
5. **Price each tier** using the formula in Section 4
6. **Add soft benefits** that cost nothing: priority scheduling, waived fees, dedicated contact
7. **Add aspirational benefits** to the top tier: credits toward big jobs, transferability, free emergency calls

---

## 4. Pricing Strategy

### Monthly vs. Annual Billing

Always offer both options:

- **Monthly billing** is easier to sell — lower perceived commitment, fits in a household budget
- **Annual prepaid** gets a 10-15% discount — improves your cash flow dramatically
- **Present annual as the "smart" option**: "Most of our members choose annual because they save $[X] — that's basically a free month"
- **Never offer quarterly** — it is the worst of both worlds (high admin cost, low commitment)

### Pricing Formula

```
Plan Price = (Cost of Included Services + Overhead Allocation + Target Profit Margin)

Where:
  Cost of Included Services = labor hours x loaded labor rate + materials for each included visit
  Overhead Allocation = 10-15% of direct cost (covers scheduling, billing, reminders, admin)
  Target Profit Margin = 30-50% markup on total cost
```

**Worked Example (HVAC Preferred Plan):**
```
AC tune-up:     1.5 hours x $45/hr loaded rate = $67.50 + $15 materials = $82.50
Heating tune-up: 1.5 hours x $45/hr loaded rate = $67.50 + $15 materials = $82.50
Total service cost: $165.00
Overhead (12%):     $19.80
Subtotal:           $184.80
Margin (40%):       $73.92
Annual price:       $258.72 -> round to $264 ($22/month) or $250 (annual prepaid)
```

### Multiple Systems / Properties

- Second system: 60-75% of single-system price
- Third+ system: 50-60% of single-system price
- Multiple properties: custom quote, but start at 80% per additional property
- Commercial properties: separate pricing tier entirely (higher cost, different SLA)

### Price Anchoring

When presenting tiers, always show the VIP tier first (highest price). This anchors the customer's perception. Then show Preferred — it looks like a deal by comparison. Basic is the fallback.

**Price presentation order: VIP -> Preferred -> Essential** (not the other way around).

### Competitor Price Matching

- Do NOT match competitors on price — match or exceed on value
- If a competitor is cheaper, your plan must visibly include more
- If a competitor is more expensive, position your plan as better value
- Never badmouth competitors; instead, ask: "What does their plan include?" and show how yours compares

### Introductory Pricing

- Launch discount: 15-20% off for first 90 days (creates urgency)
- "Founding member" pricing: Lock in a lower rate for early adopters (first 50 members)
- Seasonal specials: Tie plan sign-ups to tune-up season ("Sign up with today's tune-up and your first month is free")
- NEVER discount more than 20% — it trains customers to wait for deals

### Break-Even Analysis

Most plans break even on the included tune-ups alone. The real profit comes from:
1. **Captured repairs** — members call you first, not your competitor
2. **Equipment replacement** — members buy through you 85-95% of the time
3. **Referrals** — members refer 2-3x more than one-time customers
4. **Reduced acquisition cost** — you stop spending marketing dollars to win them back each year

---

## 5. Contract Terms

### Essential Clauses

Every maintenance agreement MUST include these elements. See `references/contract-templates.md` for full contract templates.

**1. Term Length**
- Standard: 12 months, auto-renewing
- Month-to-month option if required by market (weaker retention but lower barrier)
- Start date and renewal date clearly stated

**2. Cancellation Policy**
- 30-day written notice required for cancellation
- Pro-rated refund for annual prepaid (if canceling mid-term) OR no refund (state laws vary)
- Check state consumer protection laws — some states require pro-rated refunds
- If services have been rendered that exceed the pro-rated amount paid, customer may owe the difference at retail pricing

**3. Included Services (Specific)**
- List exactly what is included in the plan by name and frequency
- "Annual AC tune-up includes: [specific checklist items]"
- Include seasonal windows: "AC tune-up scheduled March-May; Heating tune-up scheduled September-November"

**4. Excluded Services**
- Explicitly state what is NOT covered: "This agreement does not cover: equipment replacement, refrigerant recharging, ductwork modification, new installations, damage caused by third parties, acts of God"
- If repairs are discounted, cap the discount: "Repair discount applies to the first $[X] of parts and labor per visit"

**5. Repair Discount Terms**
- Maximum discount per visit (e.g., "15% off up to $500 in parts and labor per service call")
- Does the discount apply to parts, labor, or both?
- Does it apply to emergency/after-hours calls?
- Does it stack with other promotions? (Usually no)

**6. Geographic Service Area**
- Define the covered area (radius from shop, zip codes, city/county)
- Out-of-area surcharge if applicable

**7. Response Time Commitments**
- Priority members: "Next business day" or "Same day" (be specific)
- Standard members: "Within [X] business days"
- Emergency response: "Within [X] hours" for VIP/Priority tier
- What counts as an "emergency"

**8. What Voids the Agreement**
- Non-payment (grace period: 15-30 days past due)
- Abusive or unsafe conditions
- Unauthorized modifications to equipment
- Denial of access to equipment/property
- Fraud or misrepresentation

**9. Transferability**
- Can the plan transfer if the customer sells their home/property?
- If yes: transferable with written notice and no fee (VIP/Priority perk)
- If no: plan terminates upon sale, pro-rated refund per cancellation terms

**10. Payment Terms**
- Monthly: auto-pay via credit card or ACH on [date] of each month
- Annual: full payment due at sign-up, renewable on anniversary date
- Late payment: [X] days grace, then service suspended until current
- Failed payment: [X] retry attempts, then cancellation notice sent

**11. Liability Limitations**
- "Company's liability under this agreement shall not exceed the total fees paid by Customer in the current term"
- "Company is not liable for pre-existing conditions, normal wear and tear, or equipment failure unrelated to maintenance performed"
- Indemnification clause for property access

**12. Dispute Resolution**
- Mediation first, then binding arbitration (or small claims court)
- Governing law: state where business operates

---

## 6. Selling the Plan

### When to Pitch

**At Job Completion (Highest Close Rate: 25-40%)**

This is the single best moment to sell a maintenance plan. The customer just experienced a problem, you fixed it, trust is at its peak, and the pain of the bill is fresh. They do not want to go through this again.

**During Estimate Presentation (Close Rate: 15-25%)**

Include the maintenance plan as a line item or add-on in every estimate. If using Good-Better-Best (GBB) pricing, the Better and Best options should include the maintenance plan bundled in.

**Post-Service Follow-Up, Day 3-5 (Close Rate: 8-15%)**

Send a follow-up email with a comparison table of plan tiers. Subject line: "Protect your [system] — exclusive offer for recent customers." Include a limited-time incentive (first month free, waived enrollment fee).

**Seasonal Marketing Campaigns (Close Rate: 5-10%)**

"Time for your spring tune-up — maintenance plan members are already on the schedule. Join now and skip the wait: [link]." Tie plan sign-ups to the seasonal rush when customers are already thinking about their systems.

**New Installation / Equipment Replacement (Close Rate: 40-60%)**

The single highest-converting moment. Customer just spent $5,000-15,000 on a new system. They want to protect that investment. Offer the plan bundled with the installation at a discount. "We include the first year of our Preferred maintenance plan with every new system installation."

### Sales Scripts

**Script A — At Job Completion (Any Trade)**

> "Mr./Ms. [Name], everything's running great now. Before I head out, I want to mention something that a lot of our customers love. We have a maintenance plan that covers your annual [tune-up / inspection / treatment] and gives you [X]% off any repairs — like the one we did today. It works out to [$X] a month, and honestly it pays for itself just with the [tune-up / inspection] alone. Plus, you get priority scheduling, so next time you won't have to wait [X] days to get us out here. Can I get you signed up today?"

**Script B — In the Estimate (Bundled)**

> "I'm including our [Preferred/Complete] maintenance plan in the Better and Best options because it's the best way to protect your investment. It covers your annual [tune-ups / inspections] for the life of the [equipment / system] and locks in your [X]% repair discount starting today. Most of our customers tell us it's a no-brainer once they see the savings."

**Script C — The "If You Had This Today" Close**

> "Just so you know — if you'd had our maintenance plan before today, this visit would have cost you [$X less]. The plan is [$X] a month, so it basically pays for itself in situations like this. And you'd have been at the top of the list instead of waiting [X] days. Want me to get you set up so you're covered going forward?"

**Script D — Post-Service Follow-Up Email**

> Subject: Protect Your [System] — Exclusive Offer for [Business Name] Customers
>
> Hi [Name],
>
> Thanks for choosing [Business Name] for your recent [service type]. We hope everything is working great!
>
> We wanted to let you know about our maintenance plan — it's the easiest way to keep your [system] running efficiently and avoid unexpected breakdowns.
>
> Here's what our members get:
>
> [Insert 3-tier comparison table]
>
> As a recent customer, we're offering you [incentive: first month free / waived enrollment / 10% off annual]. This offer is valid through [date].
>
> Ready to join? Call us at [phone] or reply to this email.
>
> — The [Business Name] Team

**Script E — New Installation Bundle**

> "Congratulations on your new [system]. To keep it running at peak efficiency and protect your warranty, I'd recommend our maintenance plan. We actually include the first year of our [Preferred] plan free with every new installation. After the first year, it's just [$X] a month to keep the coverage going. All I need is a card on file and you're all set."

**Script F — Overcoming Objections**

*"I don't need a plan, I'll just call when something breaks."*
> "Absolutely, and we'll be here when you need us. The thing is, most breakdowns happen because of something a tune-up would have caught. Our plan members have 70% fewer emergency calls than non-members. But it's totally up to you — just know the offer is always here."

*"That's too expensive."*
> "I totally understand. Let me break it down — the [tune-up / inspection] alone would cost [$X] if you called us for it separately. The plan is [$X/year], so you're basically getting the tune-up at cost and everything else — the discount, priority scheduling, waived fees — is free. Most members save [$X] in the first year."

*"I'll think about it."*
> "Of course, take your time. I'll leave this info sheet with you. Just know that if you sign up within [X] days, [incentive]. My number is on the card — call anytime."

*"I'm selling the house soon."*
> "That's actually a great reason to have a plan. A documented maintenance history increases your home's value, and our [Preferred/Priority] plan is transferable to the new owner — it's a selling point."

### Tech Incentives

Techs sell more plans when they are incentivized:

- **Spiff per sign-up:** $25-50 per new member signed in the field
- **Monthly bonus:** Top plan seller gets a bonus ($100-250)
- **Team target:** If the team hits [X] sign-ups this month, everyone gets [reward]
- **Leaderboard:** Track and display sign-ups per tech weekly
- **Training:** Role-play the scripts in team meetings until they are natural

---

## 7. Renewal & Retention

### Auto-Renewal Process

- Send a 60-day renewal notice (required by law in many states)
- Send a 30-day reminder
- Process renewal on anniversary date
- Send confirmation: "Your plan has been renewed for another year. Your next scheduled visit is [date]."

### Renewal Communication Templates

**60-Day Notice:**

> Hi [Name],
>
> Just a heads-up — your [Business Name] [Plan Tier] maintenance plan renews on [Date]. No action is needed on your part.
>
> Here's what's coming up:
> - Your next [service type] is scheduled for [Month]
> - You've saved [$X] this year through your member discount
> - Your plan rate stays the same: [$X/month or $X/year]
>
> If you have any questions or want to upgrade your plan, give us a call at [Phone].
>
> Thank you for being a valued member!
>
> — [Business Name]

**Lapsed Member Re-Engagement (30 days after lapse):**

> Hi [Name],
>
> We noticed your [Business Name] maintenance plan expired [X] days ago and we miss having you as a member!
>
> Since you left, here's what you're missing:
> - [X]% off all repairs
> - Priority scheduling (members get seen first)
> - Your annual [tune-up / inspection] — which is coming up in [Month]
>
> Rejoin this month and we'll waive the $[X] reactivation fee. Just call [Phone] or reply to this email.
>
> We'd love to have you back.
>
> — [Business Name]

**Win-Back (90 days after lapse):**

> Hi [Name],
>
> It's been a few months since your maintenance plan ended, and we wanted to check in. We've made some improvements to our plans:
>
> [List 1-2 new benefits or improvements]
>
> As a returning member, we're offering you [special incentive — discounted first 3 months, free tune-up on sign-up, etc.].
>
> Call [Phone] to rejoin, or reply to this email and we'll set everything up.
>
> — [Business Name]

### Retention Metrics

Track these monthly:

- **Churn rate target:** Under 15% annually (under 1.5% monthly)
- **Renewal rate target:** 85%+ for annual plans
- **Upgrade rate:** 10-15% of members should upgrade tiers annually
- **Average member tenure:** Target 3+ years

### Exit Survey

When a member cancels, always ask why:

> "We're sorry to see you go. To help us improve, would you mind sharing why you're canceling?"
> (a) Moving out of the service area
> (b) Budget constraints
> (c) Not seeing enough value
> (d) Switching to another company
> (e) Selling the property
> (f) Other: ____________

Track exit reasons monthly. If "not seeing value" exceeds 20%, your plan needs more visible benefits or better communication of existing ones.

---

## 8. Revenue Tracking & KPIs

### Core Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| Total Active Members | Number of customers with an active maintenance plan | Growing monthly |
| Monthly Recurring Revenue (MRR) | Total plan fees collected per month | $[Revenue Goal] |
| Annual Recurring Revenue (ARR) | MRR x 12 | $[Revenue Goal] |
| Plan Mix | % of members on each tier | 15% Essential / 65% Preferred / 20% VIP |
| Conversion Rate | Plans pitched vs. plans signed | 20-30% at job completion |
| Monthly Churn Rate | Members lost / total members | Under 1.5% |
| Annual Churn Rate | Members lost over 12 months / average members | Under 15% |
| Revenue Per Member | Total revenue from member (plan + repairs + replacements) / year | 2-3x plan price |
| Member vs Non-Member Ticket | Average repair ticket for members vs non-members | Members 15-25% higher |
| Lifetime Value (LTV) | Average revenue per member x average tenure in years | $3,000-6,000+ |
| Cost to Serve | Average cost of delivering plan benefits per member per year | Below 65% of plan price |

### Revenue Dashboard

When the business owner asks for a dashboard, create a canvas page showing:

1. **MRR and ARR** — current month and trend (last 6 months)
2. **Total active members** — with breakdown by tier
3. **Monthly sign-ups vs. cancellations** — net growth
4. **Churn rate** — monthly trend
5. **Conversion rate** — by channel (at job, in estimate, follow-up email, seasonal campaign)
6. **Top-performing techs** — by plan sign-ups this month
7. **Revenue per member** — plan fees + additional work captured

Use charts and clear numbers. Update monthly or on request.

### Software Integration

Most field service platforms support recurring billing and membership tracking:

- **ServiceTitan:** Memberships module — tiers, auto-billing, renewal tracking, tech attribution
- **Housecall Pro:** Service plans with recurring billing, can track by customer
- **Jobber:** Recurring invoicing (manual plan tracking, less automated)
- **FieldEdge:** Service agreements with built-in scheduling and billing
- **Service Fusion:** Maintenance contracts with recurring invoices
- **PestRoutes / GorillaDesk:** Built for recurring pest control plans
- **Zuper:** Custom service plans with workflow automation

If the business uses a platform with membership features, configure the plans there. If not, set up recurring billing through their payment processor (Stripe, Square) and track members in a spreadsheet or CRM until they adopt a platform.

---

## 9. Seasonal Campaign Calendar

This calendar coordinates maintenance plan marketing with seasonal service demand. Customize to the business's trade and region.

### HVAC Seasonal Calendar

| Month | Service Activity | Marketing Focus | Plan Push |
|-------|-----------------|----------------|-----------|
| January | Heating repairs peak | "Is your heater ready for the cold?" | Push Preferred — "includes fall tune-up you missed" |
| February | Heating repairs continue | Early bird AC tune-up booking | "Book your spring tune-up now — members get first priority" |
| March | AC tune-ups begin | "Spring tune-up season is here" | Sign-up drive — "first month free with tune-up" |
| April | Peak AC tune-ups | "Don't wait — schedule your AC tune-up" | Highest conversion month — pair sign-up with tune-up |
| May | AC season starts | "Summer is coming — is your AC ready?" | Last chance messaging before summer rush |
| June | Emergency AC repairs spike | "Beat the heat — members skip the line" | Convert emergency callers to members |
| July | Peak cooling demand | Slow on marketing — focus on service delivery | Pitch at every repair call |
| August | Early bird heating tune-ups | "Schedule your fall tune-up now" | "Members are already booked for October" |
| September | Heating tune-ups begin | "Fall maintenance season" | Sign-up drive for heating coverage |
| October | Peak heating tune-ups | "Winter is coming — tune up now" | Pair sign-up with tune-up (second peak) |
| November | Plan renewal season | "Thank you for being a member" | Renewal notices + upgrade offers |
| December | End-of-year push | "New year, new peace of mind" | Gift certificates, annual prepaid discounts |

### Plumbing Seasonal Calendar

| Month | Service Activity | Marketing Focus | Plan Push |
|-------|-----------------|----------------|-----------|
| January | Frozen pipe emergencies | "Prevent frozen pipes — call now" | Convert emergency callers |
| February | Water heater failures (cold water demand) | "Is your water heater over 8 years old?" | Water heater plan upsell |
| March | Spring inspection season | "Post-winter plumbing check" | Sign-up drive with spring inspection |
| April | Outdoor faucet / irrigation startup | "Spring plumbing checklist" | Pair sign-ups with outdoor service |
| May | Sump pump season (spring rains) | "Is your sump pump ready?" | Push Preferred (includes sump check) |
| June-July | Sewer line issues (tree roots active) | "Slow drains? Don't ignore it" | Pitch at drain/sewer calls |
| August | Back-to-school rush (bathroom remodels) | Remodel promotions | Bundle plan with remodel projects |
| September | Fall inspection push | "Pre-winter plumbing inspection" | Sign-up drive for winterization |
| October | Winterization starts | "Protect your pipes before the freeze" | Push Priority (includes winterization) |
| November | Water heater demand increases | "Hot water — don't take it for granted" | Annual plan renewals |
| December | Holiday hosting = plumbing stress | "Holiday plumbing survival guide" | Gift membership promotions |

### Pest Control Seasonal Calendar

| Month | Service Activity | Marketing Focus | Plan Push |
|-------|-----------------|----------------|-----------|
| January | Indoor rodent peak | "Mice moving in for winter?" | Annual plan renewals + rodent add-on |
| February | Pre-spring prep | "Spring bugs are coming — get ahead" | Early sign-up discount |
| March | Ant season begins | "First ants spotted — act now" | Q1 treatment + sign-up bundle |
| April | Termite swarm season | "Termite swarming season is here" | Push Priority (includes termite monitoring) |
| May | Mosquito season starts | "Take back your yard" | Push Priority (includes mosquito treatment) |
| June | Peak general pest season | Q2 treatment cycle | Pitch plan at every one-time call |
| July | Callback season (re-treatments) | "Still seeing bugs? Upgrade your plan" | Upgrade Essential -> Preferred |
| August | Late summer pest surge | "End-of-summer pest blitz" | Convert one-time summer customers |
| September | Rodent season prep (fall) | "Rodents looking for a winter home" | Push Preferred (includes rodent monitoring) |
| October | Fall perimeter treatments | Q3 treatment + fall prep | Sign-up drive before winter |
| November | Indoor pest migration | "Keep pests outside where they belong" | Push plans as holiday gift for homeowners |
| December | Treatment cycle wraps | Q4 treatment + year-end recap | Renewal + referral bonus |

### Landscaping Seasonal Calendar

| Month | Service Activity | Marketing Focus | Plan Push |
|-------|-----------------|----------------|-----------|
| January | Planning season (off-season) | "Plan your 2026 landscape now" | Annual plan pre-sales |
| February | Early spring prep | "Spring is 6 weeks away" | Founding member pricing |
| March | Spring cleanups begin | "Spring cleanup + weekly service" | Peak sign-up month — pair cleanup with plan |
| April | Mowing season starts | "Your lawn starts here" | First-mow sign-up bundle |
| May | Full service season | Fertilization round 1-2 | Upgrade Essential customers to Preferred |
| June | Peak mowing season | Irrigation + drought tips | Push Priority (includes irrigation) |
| July | Mowing + treatment season | Weed control focus | Mid-season upsell |
| August | Late summer stress management | Aeration + overseeding prep | Push Priority for fall aeration |
| September | Fall aeration + overseeding | "Best month for lawn improvement" | Capture one-time aeration customers |
| October | Fall cleanups | "Leaf cleanup + winterization" | Last call for annual sign-ups |
| November | Snow prep (if applicable) | "Snow removal — members are first on the list" | Push Priority (includes snow) |
| December | Off-season | Holiday gift certificates | Pre-sell spring plans |

---

## 10. Implementation Checklist

When building a maintenance program from scratch, follow this sequence:

### Phase 1: Design (Week 1-2)
- [ ] Complete Initial Assessment (Section 1)
- [ ] Choose tier structure and names
- [ ] Define included services per tier
- [ ] Calculate delivery costs per tier
- [ ] Set pricing using the formula (Section 4)
- [ ] Research competitor plans
- [ ] Draft contract terms (Section 5, use templates from references/)
- [ ] Have contract reviewed by attorney (recommend, do not skip)

### Phase 2: Setup (Week 2-3)
- [ ] Configure plans in field service software (or set up recurring billing)
- [ ] Create plan comparison sheet (PDF or webpage)
- [ ] Create sign-up forms (digital + paper for field use)
- [ ] Train techs on scripts (Section 6 — role-play in team meeting)
- [ ] Set up spiff/incentive tracking for techs
- [ ] Create email templates for renewal, lapsed, and follow-up (Section 7)
- [ ] Set up auto-renewal billing and notification workflow

### Phase 3: Launch (Week 3-4)
- [ ] Announce to existing customers (email blast + social media)
- [ ] Offer "founding member" pricing for first 30-90 days
- [ ] Begin pitching at every service call
- [ ] Track sign-ups daily for first 30 days
- [ ] Collect feedback from first 10 members

### Phase 4: Optimize (Month 2+)
- [ ] Review conversion rates by channel (at-job, estimate, email, marketing)
- [ ] Adjust scripts based on tech feedback
- [ ] Analyze churn — conduct exit surveys
- [ ] Review plan economics — are you profitable per member?
- [ ] Add/adjust benefits based on member feedback
- [ ] Increase marketing during seasonal peaks (Section 9)
- [ ] Set monthly KPI review cadence (Section 8)

---

## 11. Advanced Strategies

### Referral Programs for Members

Members are your best source of referrals. Incentivize them:

- "$25 credit toward your next service for every friend who signs up"
- "Refer 3 friends and get a free [service]"
- Referral cards (physical or digital) with member's name and tracking code
- Announce top referrers in monthly member newsletter or email

### Member Appreciation

Keep members feeling special:

- Annual "member appreciation" event (BBQ, open house, charity drive)
- Birthday or membership anniversary card/email
- Exclusive early access to seasonal promotions
- Member-only pricing on equipment upgrades
- Year-end "member savings report" — show them how much they saved

### Upsell Paths

Map out how members progress to higher tiers and additional services:

```
Essential Member
  -> Needs repair, sees discount value -> Upgrades to Preferred
  -> Preferred Member
    -> Has emergency, values priority -> Upgrades to VIP
    -> VIP Member
      -> Equipment ages out -> Buys replacement through you (highest margin sale)
      -> Refers friends -> More members
```

### Commercial / Multi-Property Programs

For businesses with commercial clients or property managers:

- Custom pricing per property (based on system count, square footage)
- Dedicated account manager
- Quarterly service reports
- SLA with response time guarantees and penalties
- Net-30 or Net-60 billing terms
- Volume discount (10+ properties)

### Bundled Trade Programs

For businesses offering multiple trades (or partnering with other trades):

- "Total Home Care" plan: HVAC + Plumbing + Electrical under one membership
- Premium pricing: $55-85/month for combined coverage
- One point of contact, one bill, total peace of mind
- Cross-selling opportunity: HVAC company partners with a plumber for a joint plan

---

## Related Skills

| Skill | When to Use |
|-------|------------|
| `sales-scripts` | For in-field selling techniques and objection handling beyond maintenance plans |
| `customer-comms` | For seasonal email campaigns, SMS marketing, and customer communication templates |
| `customer-followup` | For post-service follow-up sequences and reactivation campaigns |
| `pricing-job-costing` | For calculating service costs, labor rates, and margins that feed into plan pricing |
| `business-briefing` | For understanding the business's overall strategy and how maintenance plans fit in |
| `product-marketing-context` | For market positioning and competitive analysis of maintenance offerings |

---

## Output Guidelines

When creating maintenance programs:

1. **Always produce a tier comparison table** — visual, easy to compare, ready to show a customer
2. **Always include specific dollar amounts** — use the pricing formula, never leave blanks unless the owner hasn't provided cost data yet
3. **Always draft at least one sales script** customized to their trade and pricing
4. **Always include a seasonal calendar** relevant to their trade and region
5. **Always recommend tracking KPIs** from day one — what gets measured gets managed
6. **Store the plan design** in the workspace for future reference and iteration
7. **Create a canvas page** if the owner wants a member-facing comparison or dashboard
8. **Reference contract templates** in `references/contract-templates.md` for agreement language
