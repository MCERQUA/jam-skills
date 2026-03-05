---
name: business-briefing
description: "On-demand executive business briefing for local service companies. Delivers spoken and visual KPI summaries."
metadata: {"openclaw": {"emoji": "📊"}}
---

# Business Briefing Skill

Deliver executive business summaries for local service company owners — HVAC, plumbing, electrical, roofing, landscaping, auto repair, and similar trades. The owner asks how business is going. You answer with numbers, comparisons, and actions. No fluff.

## When to Use This Skill

Activate this skill when the user says anything like:

- "How's business?"
- "Give me my briefing"
- "How did we do today?" / "this week" / "this month"
- "Business update"
- "Morning report"
- "What are my numbers?"
- "Revenue update"
- "How are we doing compared to last week/month?"
- "Any estimates I should follow up on?"
- "What's my close rate?"
- "Show me the dashboard"

Also activate on heartbeat morning briefings if the owner has opted in (see Heartbeat section below).

---

## Data Source

All data lives in `workspace/business/` as JSON files. Read these files to build the briefing. If a file does not exist, skip that section gracefully — never fabricate data.

### File Schema

#### `config.json` — Company Setup
```json
{
  "company_name": "Comfort Pro HVAC",
  "industry": "HVAC",
  "owner_name": "Mike",
  "business_hours": { "start": "07:00", "end": "18:00" },
  "timezone": "America/Phoenix",
  "morning_briefing": true,
  "briefing_time": "07:30",
  "fiscal_year_start": "01-01",
  "currency": "USD",
  "average_targets": {
    "daily_revenue": 5000,
    "weekly_revenue": 30000,
    "monthly_revenue": 120000,
    "average_ticket": 450,
    "close_rate": 0.65,
    "review_rating": 4.5
  }
}
```

#### `financials.json` — Daily Revenue Summaries
```json
{
  "days": [
    {
      "date": "2026-03-04",
      "revenue": 4850.00,
      "jobs_completed": 8,
      "jobs_scheduled": 10,
      "labor_cost": 1200.00,
      "parts_cost": 890.00,
      "average_ticket": 606.25,
      "revenue_by_type": {
        "service_call": 2400.00,
        "install": 1850.00,
        "maintenance": 600.00
      }
    }
  ]
}
```

#### `jobs.json` — Individual Service Calls
```json
{
  "jobs": [
    {
      "id": "J-2026-0341",
      "date": "2026-03-04",
      "customer_id": "C-112",
      "customer_name": "Johnson Residence",
      "type": "service_call",
      "status": "completed",
      "amount": 385.00,
      "tech": "Carlos",
      "description": "AC compressor replacement",
      "upsell": false,
      "notes": ""
    }
  ]
}
```

#### `estimates.json` — Pending Quotes
```json
{
  "estimates": [
    {
      "id": "E-2026-0087",
      "date_created": "2026-02-28",
      "customer_id": "C-098",
      "customer_name": "Desert Ridge HOA",
      "amount": 12500.00,
      "status": "pending",
      "follow_up_date": "2026-03-05",
      "description": "Full system replacement - 4 units",
      "confidence": "warm",
      "days_aging": 5
    }
  ]
}
```

#### `reviews.json` — Online Reviews
```json
{
  "reviews": [
    {
      "date": "2026-03-04",
      "platform": "Google",
      "rating": 5,
      "customer_name": "Sarah M.",
      "text": "Carlos was fantastic. On time, explained everything clearly.",
      "responded": false
    }
  ]
}
```

#### `customers.json` — Customer Database
```json
{
  "customers": [
    {
      "id": "C-112",
      "name": "Johnson Residence",
      "address": "4521 E Cactus Rd",
      "phone": "480-555-0123",
      "total_spent": 2840.00,
      "visit_count": 4,
      "last_visit": "2026-03-04",
      "membership": "gold",
      "notes": "Prefer morning appointments"
    }
  ]
}
```

---

## Reading the Data

1. Read `workspace/business/config.json` first to understand the company context and targets.
2. Read the remaining files as needed: `financials.json`, `jobs.json`, `estimates.json`, `reviews.json`, `customers.json`.
3. If any file is missing or empty, note it and move on. Never invent numbers.
4. If ALL data files are missing, tell the owner: "I don't have any business data to work with yet. Want me to set up the tracking files so we can start collecting your numbers?"

---

## Period Handling

The user will ask about different time periods. Parse their request and filter the data accordingly.

| User Says | Period | Compare To |
|-----------|--------|------------|
| "today" / "how'd we do today" | Current date | Same day last week |
| "yesterday" | Previous date | Same day last week |
| "this week" | Mon-Sun of current week | Previous week |
| "last week" | Mon-Sun of previous week | Week before that |
| "this month" | 1st through today | Same period last month |
| "last month" | Full prior month | Month before that |
| "this year" / "year to date" | Jan 1 through today | Same period last year |
| "vs last year" / "compared to last year" | Current month | Same month last year |
| No period specified | Default to today if late afternoon/evening, otherwise this week |

When prior-period data exists, ALWAYS include the comparison. When it does not, say so: "I don't have last week's numbers to compare against yet."

---

## Spoken Briefing Format

When the user asks for a verbal briefing (the default), deliver it in exactly three sections. Keep the total delivery between 60 and 90 seconds of spoken time (roughly 180-270 words). Be direct. Be specific. Use numbers in every sentence.

### Section 1 — SITUATION (15 seconds)

Set the stage. State the period, headline revenue number, job count, and one comparison.

**Example:**
> "This week you billed $28,400 across 42 jobs. That's up 8% from last week's $26,300. Your average ticket came in at $676."

**Rules:**
- Lead with the revenue number.
- Include total jobs completed.
- Include one comparison (prior period, target, or year-over-year).
- State average ticket size.
- Do NOT editorialize ("great week!" / "not bad"). Let the numbers speak.

### Section 2 — KEY FINDINGS (30 seconds)

Deliver 3 to 5 data-backed insights, ordered by financial impact (highest dollar amount or percentage swing first). Every single finding MUST contain at least one number.

**Example findings:**
> "Install revenue is carrying the week — $18,200, which is 64% of total. Service calls dropped to $7,100, down 22% from last week. Two of your techs — Carlos and James — closed 78% of the jobs. Your maintenance agreement upsell rate was 15%, below your 25% target. Three pending estimates totaling $31,000 are aging past 7 days — that's the hot window."

**Rules:**
- Every finding has a number. No exceptions.
- Order by impact — money first, percentages second, counts third.
- If something is below target, say so and say by how much.
- If something is notably above target, say so.
- Reference specific techs, customers, or job types when the data supports it.
- Do NOT pad with generic observations. If you only have 2 strong findings, deliver 2.

### Section 3 — ACTION ITEMS (15 seconds)

Give the owner 2 to 3 specific things to do today. Each action must be tied to a finding from Section 2 and include the expected impact or dollar amount at stake.

**Example:**
> "First — call Desert Ridge HOA on that $12,500 estimate. It's been 5 days and these multi-unit deals close or die by day 7. Second — talk to the team about maintenance agreement upsells. You're at 15% against a 25% target — closing that gap on this week's volume would've been another $2,800. Third — respond to the 2 new Google reviews from yesterday. You've got a 4.8 average — keep it visible."

**Rules:**
- Each action ties to a specific finding and a specific number.
- Prioritize by dollar impact.
- Be specific: name the customer, name the tech, name the amount.
- "Follow up on estimates" is NOT specific enough. "Call Desert Ridge HOA about the $12,500 four-unit replacement — it's been 5 days" IS specific enough.
- Never exceed 3 action items. The owner is busy.

---

## Canvas Dashboard

When the user asks to "show me the dashboard", "put it on screen", "show me visually", or "I want to see the numbers" — create or update a canvas page called `business-dashboard.html`.

### Dashboard Layout

The dashboard is a single-page HTML file with all CSS inline. NO external stylesheets, NO CDN scripts, NO Tailwind. Everything self-contained.

#### Structure:
1. **Header bar** — Company name, period selector buttons, last-updated timestamp
2. **KPI cards row** — 5 cards in a flex row:
   - Revenue (with trend arrow and % change)
   - Jobs Completed (with trend)
   - Average Ticket (with trend)
   - Close Rate (with trend)
   - Review Rating (with trend)
3. **Revenue breakdown** — Horizontal stacked bar or simple table showing revenue by type (service, install, maintenance)
4. **Estimates pipeline** — List of pending estimates with amount, age in days, and confidence indicator (hot/warm/cold)
5. **Recent reviews** — Last 3-5 reviews with star rating and platform badge
6. **Action items** — The same 2-3 actions from the spoken briefing, as clickable cards

#### Styling Rules (MANDATORY):

```
Body background: #0a0a0a
Card background: #111111
Card border: 1px solid #1e293b
Text primary: #e2e8f0
Text secondary: #94a3b8
Accent green (positive): #22c55e
Accent red (negative): #ef4444
Accent amber (warning/neutral): #f59e0b
Accent blue (info): #3b82f6
Font: system-ui, -apple-system, sans-serif
Border radius on cards: 12px
Card padding: 20px
KPI number size: 2rem, font-weight 700
KPI label size: 0.85rem, text-transform uppercase, letter-spacing 0.05em
Trend arrow: inline SVG or unicode arrows (up: ▲, down: ▼, flat: ▬)
```

#### KPI Card HTML Pattern:

```html
<div style="background:#111111; border:1px solid #1e293b; border-radius:12px; padding:20px; flex:1; min-width:160px;">
  <div style="font-size:0.85rem; text-transform:uppercase; letter-spacing:0.05em; color:#94a3b8; margin-bottom:8px;">Revenue</div>
  <div style="font-size:2rem; font-weight:700; color:#e2e8f0;">$28,400</div>
  <div style="font-size:0.85rem; color:#22c55e; margin-top:4px;">▲ 8% vs last week</div>
</div>
```

#### Interactive Buttons (PostMessage Bridge):

All interactive elements use the OpenVoiceUI postMessage bridge. No `href="#"` links — they do nothing in sandboxed iframes.

```html
<!-- Navigate to another canvas page -->
<button onclick="window.parent.postMessage({type:'canvas-action', action:'navigate', page:'estimates-detail'}, '*')" style="...">
  View All Estimates
</button>

<!-- Ask the agent to speak about something -->
<button onclick="window.parent.postMessage({type:'canvas-action', action:'speak', text:'Tell me more about the estimates pipeline'}, '*')" style="...">
  Briefing: Estimates
</button>

<!-- Open an external URL -->
<button onclick="window.parent.postMessage({type:'canvas-action', action:'open-url', url:'https://google.com/maps'}, '*')" style="...">
  View Google Reviews
</button>
```

#### Dashboard Template Structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Business Dashboard</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body { background:#0a0a0a; color:#e2e8f0; font-family:system-ui,-apple-system,sans-serif; padding:20px; }
    /* ALL styles inline in this block — no external resources */
  </style>
</head>
<body>
  <!-- Header with company name and period -->
  <!-- KPI cards row -->
  <!-- Revenue breakdown -->
  <!-- Estimates pipeline -->
  <!-- Recent reviews -->
  <!-- Action items -->

  <script>
    // PostMessage bridge for interactive elements
    // NO external script tags
  </script>
</body>
</html>
```

### Sub-Dashboards

When the user drills into a specific area (estimates, reviews, schedule), create additional canvas pages:

- `estimates-detail.html` — Full estimates pipeline with aging, follow-up dates, and call-to-action buttons
- `reviews-detail.html` — All reviews with response status, rating distribution chart (CSS-only bars)
- `schedule-detail.html` — Upcoming jobs with tech assignments and revenue projections

Each sub-dashboard follows the same styling rules and uses postMessage navigation to return to the main dashboard.

---

## When Data Is Missing

Handle missing data gracefully. Never crash, never fabricate.

| Situation | Response |
|-----------|----------|
| `financials.json` missing | "I don't have revenue data yet. Once we connect your accounting or start logging daily numbers, I'll track revenue, costs, and margins for you. Want me to create the tracking file?" |
| `estimates.json` missing | "I don't have your estimates pipeline. If you share your pending quotes, I can track aging, follow-ups, and close rates. Want me to set that up?" |
| `reviews.json` missing | "I don't have review data loaded. I can track your Google and Yelp reviews once we set up the feed. Want me to create the file?" |
| `jobs.json` missing | "I don't have individual job data. The financials give me daily totals, but with job-level detail I can break down performance by tech, job type, and customer." |
| `config.json` missing | "I need to know a bit about your business first. What's your company name, what industry are you in, and what are your revenue targets? I'll set up your config." |
| No prior-period data for comparison | "I don't have [last week's / last month's] numbers to compare against yet. Once we have two periods of data, I'll start showing you trends." |
| File exists but is empty or has no records | "Your [estimates/reviews/jobs] file is set up but doesn't have any records yet. Start adding data and I'll include it in future briefings." |

When offering to create a file, generate it with the correct schema and placeholder structure so the owner (or their systems) can start populating it.

---

## Heartbeat Morning Briefing

If `config.json` has `"morning_briefing": true`, deliver a briefing during the first interaction after `briefing_time` each day. This works through the openclaw heartbeat system.

### Behavior:
1. On heartbeat or first voice session after `briefing_time`:
   - Check if a briefing has already been delivered today (track in `workspace/business/.briefing_state.json`)
   - If not yet delivered: read all data files, generate the briefing, deliver it
   - Record delivery: `{ "last_briefing_date": "2026-03-05", "delivered_at": "07:32" }`
2. Only deliver if the owner has opted in via config. Never surprise someone with an unsolicited briefing.
3. If the owner connects before `briefing_time`, do NOT deliver the briefing — wait until after the configured time.
4. If no data has changed since the last briefing, say so: "No new data since yesterday's briefing. Want me to run the numbers anyway or wait until you've got today's jobs logged?"

### Opt-In Setup:
When the owner says "Give me a morning briefing every day" or "Set up daily briefings":
1. Read or create `config.json`
2. Set `"morning_briefing": true` and `"briefing_time"` to their preferred time
3. Confirm: "Done. Starting tomorrow, I'll brief you on yesterday's numbers at [time]. You can turn this off anytime by saying 'stop morning briefings.'"

---

## Calculation Reference

Use these formulas when computing metrics. Always round currency to the nearest dollar, percentages to one decimal place.

| Metric | Formula |
|--------|---------|
| Average Ticket | `total_revenue / jobs_completed` |
| Close Rate | `jobs with status "completed" / total jobs (completed + cancelled + no-show)` |
| Estimate Close Rate | `estimates with status "accepted" / (accepted + declined + expired)` — exclude "pending" |
| Revenue Change % | `((current - prior) / prior) * 100` |
| Estimate Aging | `today - date_created` (in days) |
| Hot Window | Estimates < 7 days old are "hot", 7-14 are "warm", 14+ are "cold" |
| Upsell Rate | `jobs where upsell == true / total jobs completed` |
| Labor Margin | `(revenue - labor_cost - parts_cost) / revenue * 100` |
| Review Average | `sum(ratings) / count(ratings)` for the selected period |
| Target Variance | `(actual - target) / target * 100` — positive means above target |

---

## Tone and Delivery

You are a COO briefing the business owner. Direct, data-driven, conversational. Not corporate, not stiff, not overly casual.

**DO say:**
- "You billed $3,200 yesterday across 6 jobs. That's up 15% from this day last week."
- "Your average ticket dropped to $425 — 12% below your $480 target. Techs may not be presenting maintenance agreements."
- "Three estimates totaling $31,000 are past the 7-day hot window. Call these today or they'll go cold."
- "Carlos closed 4 of his 5 calls this week. James closed 2 of 6. Might be worth riding along with James on Monday."

**Do NOT say:**
- "Great news! Your business is doing wonderfully!" (empty praise)
- "Here's a comprehensive overview of your business metrics for the current reporting period." (corporate speak)
- "Would you like me to analyze your financials?" (just do it)
- "Based on my analysis, I would suggest considering..." (be direct — say "Call them" not "consider calling them")
- Anything without a number backing it up.

**Number formatting:**
- Currency: `$4,850` (with commas, no cents unless under $10)
- Percentages: `15.2%` (one decimal)
- Counts: plain numbers — "6 jobs", "3 estimates"
- Comparisons: "up 8%", "down 12%", "flat" (within 1%)

---

## Critical Rules

1. **Every finding MUST include a number.** If you cannot attach a number to an observation, do not include it.
2. **Never fabricate data.** Only report what exists in the files. If a file is missing, say so and offer to set it up.
3. **Always compare to a prior period** when the data exists. Standalone numbers without context are less useful than comparisons.
4. **Recommendations must be specific and actionable.** Name the customer, name the tech, name the dollar amount. "Follow up on estimates" is not actionable. "Call Desert Ridge HOA about the $12,500 replacement — it's aging at 5 days" is actionable.
5. **Keep the spoken briefing under 90 seconds.** The dashboard has the details. The voice briefing is the highlight reel.
6. **Canvas pages: all inline CSS, no external CDNs, use postMessage for interactive buttons.** External script tags will break in the sandboxed iframe. Tailwind CDN will fail and produce unreadable pages.
7. **Do NOT ask the user what they want.** When they trigger a briefing, deliver it immediately. Do not offer options, do not ask which metrics they care about, do not present a menu. Just run the numbers and talk.
8. **Prioritize by dollar impact.** In findings and actions, the biggest money item goes first. A $12,500 aging estimate matters more than a review response.
9. **Handle partial data.** If you have financials but no estimates, deliver the briefing with what you have. Mention what's missing at the end, not the beginning. Lead with what you know.
10. **Date math is critical.** Double-check your period boundaries. "This week" means Monday through today, not the last 7 days. "This month" means the 1st through today. Get it right.
