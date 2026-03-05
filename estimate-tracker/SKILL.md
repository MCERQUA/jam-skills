---
name: estimate-tracker
description: "Track and follow up on unconverted estimates and quotes. Revenue recovery for local service companies — follow up on aging estimates before they go cold."
metadata: {"openclaw": {"emoji": "💰"}}
---

# Estimate Tracker Skill

## Overview

Revenue recovery system for local service companies. Tracks every estimate from the moment it leaves the office to the moment it converts — or goes cold. The goal: make sure no money walks out the door because nobody followed up.

Most service companies lose 40-60% of their estimates to silence. Not because the customer said no — because nobody asked again. This skill fixes that.

### What This Skill Does

- Tracks all pending estimates with age-based priority classification
- Generates follow-up scripts that are natural, conversational, and never pushy
- Provides pipeline analytics: total value, conversion rates, win/loss patterns
- Alerts on aging high-value estimates before they go cold
- Produces a visual pipeline dashboard via canvas page
- Links converted estimates to booked jobs for closed-loop tracking

### Data Files

| File | Purpose |
|------|---------|
| `workspace/business/estimates.json` | All estimates — pending, won, lost, archived |
| `workspace/business/config.json` | Business name, thresholds, services, team, follow-up rules |

---

## Estimate Data Schema

**File:** `workspace/business/estimates.json`

```json
{
  "estimates": [
    {
      "id": "EST-2026-0042",
      "customer_id": "CUST-015",
      "customer_name": "Sarah Johnson",
      "customer_phone": "555-0199",
      "customer_email": "sarah@email.com",
      "service": "whole-house-repipe",
      "description": "Replace all copper with PEX, 3BR/2BA ranch",
      "amount": 8500,
      "created_date": "2026-02-28",
      "valid_until": "2026-03-30",
      "status": "pending",
      "follow_up_attempts": 1,
      "last_follow_up": "2026-03-02",
      "next_follow_up": "2026-03-05",
      "follow_up_log": [
        {
          "date": "2026-03-02",
          "method": "phone",
          "outcome": "left_voicemail",
          "notes": "VM — asked her to call back with any questions"
        }
      ],
      "notes": "Comparing with 2 other companies. Price-sensitive.",
      "objection": "price",
      "technician_who_quoted": "Mike",
      "decline_reason": null,
      "booked_job_id": null
    }
  ]
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique ID. Format: `EST-YYYY-NNNN` (auto-increment) |
| `customer_id` | string | no | Links to customer record if CRM exists |
| `customer_name` | string | yes | Full name |
| `customer_phone` | string | yes | Primary contact number |
| `customer_email` | string | no | Email if available |
| `service` | string | yes | Service type slug (matches `config.json` services) |
| `description` | string | yes | What was quoted — specific scope of work |
| `amount` | number | yes | Dollar amount of the estimate |
| `created_date` | string | yes | ISO date when estimate was given |
| `valid_until` | string | no | Expiration date if applicable |
| `status` | string | yes | One of: `pending`, `won`, `lost`, `archived` |
| `follow_up_attempts` | number | yes | Count of contact attempts made |
| `last_follow_up` | string | no | ISO date of most recent follow-up |
| `next_follow_up` | string | no | ISO date of next scheduled follow-up |
| `follow_up_log` | array | yes | History of every contact attempt (see below) |
| `notes` | string | no | Free-text notes about the customer/situation |
| `objection` | string | no | Primary objection: `price`, `timing`, `comparing`, `unsure`, `no_response`, `other` |
| `technician_who_quoted` | string | no | Who gave the estimate |
| `decline_reason` | string | no | Why they said no (filled on loss) |
| `booked_job_id` | string | no | Links to job record when estimate converts |

### Follow-Up Log Entry Schema

```json
{
  "date": "2026-03-05",
  "method": "phone",
  "outcome": "spoke_with_customer",
  "notes": "Still comparing. Mentioned our warranty seemed better than competitor."
}
```

**Method values:** `phone`, `text`, `email`, `in_person`, `voicemail`
**Outcome values:** `spoke_with_customer`, `left_voicemail`, `no_answer`, `sent_text`, `sent_email`, `scheduled_callback`, `booked`, `declined`

---

## Business Configuration

**File:** `workspace/business/config.json`

```json
{
  "business_name": "ABC Plumbing",
  "business_phone": "555-0100",
  "owner_name": "Mike",
  "quiet_hours": {
    "start": "09:00",
    "end": "19:00",
    "timezone": "America/Phoenix"
  },
  "thresholds": {
    "hot_days": 3,
    "warm_days": 7,
    "cold_days": 30
  },
  "high_value_threshold": 5000,
  "max_follow_ups": 4,
  "follow_up_schedule": {
    "attempt_1": {"min_days": 1, "max_days": 2},
    "attempt_2": {"min_days": 4, "max_days": 5},
    "attempt_3": {"min_days": 7, "max_days": 10},
    "attempt_4": {"min_days": 14, "max_days": 21}
  },
  "services": {
    "whole-house-repipe": {"display_name": "Whole-House Repipe", "avg_value": 8500},
    "water-heater-install": {"display_name": "Water Heater Install", "avg_value": 2200},
    "sewer-line-repair": {"display_name": "Sewer Line Repair", "avg_value": 4500},
    "bathroom-remodel-plumbing": {"display_name": "Bathroom Remodel Plumbing", "avg_value": 3800},
    "leak-detection-repair": {"display_name": "Leak Detection & Repair", "avg_value": 800},
    "drain-cleaning": {"display_name": "Drain Cleaning", "avg_value": 350}
  },
  "differentiators": [
    "Licensed and insured",
    "10-year warranty on all repipes",
    "Same-day emergency service",
    "Financing available",
    "Free second opinions"
  ],
  "financing_available": true,
  "warranty_years": 10,
  "incentives_enabled": false,
  "incentive_text": ""
}
```

The agent MUST read `config.json` before generating follow-up scripts so it can reference the correct business name, differentiators, warranty terms, and financing options. If the config file does not exist, ask the owner to provide business details before proceeding.

---

## Estimate Classification by Age

Every pending estimate is classified by how many days have passed since `created_date`. Thresholds are configurable in `config.json` under `thresholds`.

| Priority | Age | Default Days | Action |
|----------|-----|-------------|--------|
| **HOT** | Fresh | 1-3 days | Highest priority. Follow up TODAY. |
| **WARM** | Aging | 4-7 days | Follow up this week. Momentum fading. |
| **COLD** | Stale | 8-30 days | Last-chance outreach. Low conversion probability. |
| **DEAD** | Expired | 30+ days | Archive. Note reason if known. Do not follow up. |

### Classification Logic

```
age_days = today - created_date

if status != "pending":
    classification = status  (won/lost/archived — skip)
elif age_days <= thresholds.hot_days:
    classification = "HOT"
elif age_days <= thresholds.warm_days:
    classification = "WARM"
elif age_days <= thresholds.cold_days:
    classification = "COLD"
else:
    classification = "DEAD"
    → auto-archive: set status to "archived", decline_reason to "no_response_expired"
```

### Priority Escalation Rules

- Any estimate over `high_value_threshold` (default $5,000) gets bumped one priority level (WARM becomes HOT, COLD becomes WARM)
- Estimates with `next_follow_up` at or before today are always flagged regardless of classification
- Estimates that have had zero follow-up attempts are always flagged as overdue

---

## Follow-Up Workflow

### Contact Sequence

Each estimate gets up to `max_follow_ups` contact attempts (default: 4). The spacing between attempts increases as the estimate ages.

**Attempt 1 — Quick Check-In (Day 1-2)**
- Goal: Answer questions, keep the door open
- Tone: Casual, helpful, zero pressure
- Method: Phone preferred, text if no answer

**Attempt 2 — Address the Objection (Day 4-5)**
- Goal: Proactively handle the likely blocker
- Tone: Empathetic, solution-oriented
- Method: Phone or text with specific value proposition
- Reference the objection field if populated

**Attempt 3 — Value Reinforcement (Day 7-10)**
- Goal: Differentiate from competitors, offer incentive if configured
- Tone: Confident but not pushy
- Method: Phone, text, or email with warranty/guarantee details
- If `incentives_enabled` in config: mention the incentive

**Attempt 4 — Graceful Close (Day 14-21)**
- Goal: Leave the door open permanently, build goodwill
- Tone: Warm, understanding, no strings attached
- Method: Phone call or personal text
- After this attempt: if no response, mark as `lost` with `decline_reason: "no_response"`

### After Each Contact Attempt

1. Add an entry to `follow_up_log` with date, method, outcome, and notes
2. Increment `follow_up_attempts`
3. Update `last_follow_up` to today
4. Calculate and set `next_follow_up` based on the follow-up schedule
5. Update `objection` if the customer revealed a new concern
6. If customer books: set `status: "won"`, populate `booked_job_id`
7. If customer declines: set `status: "lost"`, populate `decline_reason`

---

## Objection Handling

When an estimate has an `objection` value, the follow-up script should proactively address it. These are guidelines — the agent should adapt to the specific conversation and service context.

### PRICE

The customer thinks the estimate is too high.

**Approach:** Acknowledge the concern. Never discount the price unprompted — instead, reframe the value. Lead with warranty, quality of materials, and total cost of ownership. Mention financing if available.

**Script framework:**
> "I totally understand — [service] is a real investment. What I can tell you is we stand behind our work with a [warranty_years]-year warranty, and we use [specific materials/methods]. A lot of our customers tell us they went with a cheaper quote first and ended up calling us anyway. [If financing_available:] We also have financing options if that makes it easier to get started."

**Never say:** "We can match their price" or "Let me see if I can get you a discount." Competing on price devalues the work.

### TIMING

The customer wants to wait — not the right time.

**Approach:** Respect their timeline completely. Offer to hold the quote and schedule a future follow-up. If the issue is seasonal or will get worse with time, mention that factually (not as a scare tactic).

**Script framework:**
> "No rush at all — when would be a better time to revisit this? I can hold your quote at the current price and reach out then. [If applicable:] Just so you know, [seasonal/urgency context] — but that's totally your call."

**Never say:** "If you wait it'll cost more" or "This price won't last."

### COMPARING

The customer is getting multiple quotes.

**Approach:** Encourage it. Confident companies welcome comparison. Offer to explain what is included in your quote that others might not cover (clean-up, permits, warranty, follow-up inspection).

**Script framework:**
> "Smart move getting a few quotes — I always tell people to do that. If it helps, I'm happy to walk you through exactly what's included in ours. We include [differentiators from config]. Some quotes leave out [common omissions for this service]."

**Never say:** "Who else are you talking to?" or "They probably cut corners."

### UNSURE (Not Sure If Needed)

The customer is not convinced the work is necessary.

**Approach:** Offer a second look at no charge. Provide educational context about the issue. Let them make an informed decision without pressure.

**Script framework:**
> "Would it help if [technician_who_quoted] stopped by for a quick second look? No charge — we want you to have the full picture before you decide anything. [If applicable:] I can also send you some info about [the issue] so you know what to watch for."

**Never say:** "You definitely need this" or "It'll only get worse."

### NO RESPONSE

The customer has not responded to previous contact attempts.

**Approach:** Keep messages short. Do not guilt-trip about unreturned calls. Leave each message slightly different so they do not feel like automated follow-ups.

**Script framework (voicemail/text):**
> "Hey [customer_name], just [agent name] from [business_name]. Wanted to check in on that [service display_name] quote. No pressure at all — just want to make sure you're taken care of. Give us a call if anything comes up."

**Never say:** "I've been trying to reach you" or "This is my third message."

---

## Voice Scripts

These are templates for the agent to adapt. They should sound like a real person calling from a local company — not a call center, not a salesperson. Use the customer's first name. Reference the specific service. Keep it short.

### HOT Estimate (1-3 days old)

**Phone — first attempt:**
> "Hey [first_name], it's [business_name]. Just following up on the [service display_name] estimate from [day — 'the other day' / 'yesterday' / 'Tuesday']. Got any questions I can answer?"

**Text — if no answer:**
> "Hi [first_name]! This is [business_name]. Just checking in on the [service display_name] quote. Let me know if you have any questions — happy to help. [business_phone]"

### WARM Estimate (4-7 days old)

**Phone — second attempt:**
> "Hi [first_name], it's [business_name] checking in on that [service display_name] quote. It's still good [if valid_until: 'through [date]']. Want to go ahead and get on the schedule? [If objection == 'price':] We've also got financing options if that helps."

**Text — if no answer:**
> "Hey [first_name], following up on your [service display_name] estimate ([amount formatted]). Your quote is still good — let me know if you'd like to get scheduled. [business_phone]"

### COLD Estimate (8-30 days old)

**Phone — third/fourth attempt:**
> "[First_name], just reaching out one more time about the [service display_name]. If it's not the right time, totally understand — we're here whenever you're ready. And if you went with someone else, no hard feelings — feel free to call us if you ever need a second opinion."

**Text:**
> "Hi [first_name], this is [business_name]. Just a final check-in on your [service display_name] quote. No pressure — we're here if you need us. [business_phone]"

### After Conversion (Won)

> "Awesome — I'll get you on the schedule. [Technician] will take great care of you. Anything else you need before we get started?"

### After Decline (Lost — known reason)

> "Totally understand. If anything changes or you need us down the road, we're always here. Thanks for giving us the chance to quote it, [first_name]."

---

## Trigger Phrases

The agent should recognize these natural language triggers and respond accordingly.

### "How are our estimates looking?"
**Action:** Pipeline summary — count by classification, total pending value, any overdue follow-ups.

**Response format:**
> "Here's where we stand on estimates: [X] hot, [Y] warm, [Z] cold. Total pipeline value is $[amount]. [If overdue:] We've got [N] that need follow-up today — [list names and services]."

### "Follow up on estimates"
**Action:** Execute pending follow-ups. List all estimates where `next_follow_up <= today` and `status == "pending"`. For each, generate the appropriate script based on classification and attempt number.

**Response format:**
> "We've got [N] follow-ups due. First up: [customer_name] — [service], $[amount], [age] days old. [Classification]. This would be attempt [N]. Ready to go through them?"

### "Any hot estimates?"
**Action:** Show only HOT priority estimates (including high-value bumped estimates).

**Response format:**
> "We've got [N] hot estimates: [list each with name, service, amount, age]. Total: $[sum]. [If any are overdue:] [Name] is overdue for follow-up."

### "What's our close rate?"
**Action:** Conversion analytics. Calculate from all estimates with status `won` or `lost`.

**Response format:**
> "Close rate is [X]% — [won] out of [total completed]. Average time from estimate to booking is [Y] days. [If enough data:] Best close rate is on [service type] at [Z]%. Most common reason for losing: [top decline reason]."

### "Add an estimate"
**Action:** Voice-capture a new estimate. Walk through required fields conversationally.

**Prompt sequence:**
1. "Who's the customer?" (name)
2. "What's the service?" (match to config services or create new)
3. "How much?" (amount)
4. "Phone number?" (customer_phone)
5. "Any notes — competing quotes, objections, timeline?" (notes, objection)
6. "Who quoted it?" (technician_who_quoted)

Then generate the estimate object, assign the next ID, set `created_date` to today, `status` to `pending`, `follow_up_attempts` to 0, calculate `next_follow_up` as tomorrow, and write to `estimates.json`.

> "Got it — added estimate [ID] for [customer_name], [service] at $[amount]. First follow-up is set for tomorrow."

### "Update estimate [ID or customer name]"
**Action:** Find the estimate, ask what changed. Common updates: new objection, status change (won/lost), reschedule follow-up, add notes.

### "Show the estimate pipeline"
**Action:** Display the `estimate-pipeline.html` canvas page.

---

## Analytics

When the owner asks about performance, calculate these metrics from the estimates data.

### Pipeline Summary
- **Total pending value:** Sum of `amount` for all `status == "pending"` estimates
- **Count by classification:** HOT / WARM / COLD / DEAD
- **Overdue follow-ups:** Count where `next_follow_up <= today` and `status == "pending"`
- **Highest-value pending:** Top 3 estimates by amount

### Conversion Metrics
- **Close rate:** `(won / (won + lost)) * 100` — only count completed estimates, not pending
- **Average estimate-to-booking time:** Mean of `(booked_date - created_date)` for won estimates
- **Win rate by service type:** Group by `service`, calculate close rate per type
- **Win rate by amount range:** Buckets: $0-1000, $1000-3000, $3000-5000, $5000-10000, $10000+
- **Average estimate amount (won vs lost):** Compare average `amount` of won vs lost — reveals if bigger jobs close better or worse

### Loss Analysis
- **Most common decline reason:** Frequency count of `decline_reason` for lost estimates
- **Most common objection (pending):** Frequency count of `objection` for pending estimates
- **Average follow-ups before loss:** Mean `follow_up_attempts` for lost estimates
- **Average follow-ups before win:** Mean `follow_up_attempts` for won estimates (shows how many touches it takes)

### Trends (if sufficient data — 20+ estimates)
- **Monthly close rate trend:** Close rate by month over time
- **Revenue recovered:** Sum of `amount` for estimates that were WARM or COLD at time of conversion (revenue that would have been lost without follow-up)
- **Best day to follow up:** Which day-of-week has the highest contact success rate (from follow_up_log)

---

## Canvas Page: estimate-pipeline.html

When the owner says "show the estimate pipeline" or "show me our estimates," display this canvas page. The page visualizes the full pipeline as a Kanban-style board.

### Page Requirements

- **Columns:** HOT / WARM / COLD / WON / LOST
- **Each card shows:** Customer name, service, dollar amount, age in days, follow-up status
- **Color coding:**
  - HOT: Red/orange left border (#ef4444)
  - WARM: Amber left border (#f59e0b)
  - COLD: Blue left border (#3b82f6)
  - WON: Green left border (#22c55e)
  - LOST: Gray left border (#6b7280)
- **Header metrics:** Total pipeline value, conversion rate, count of overdue follow-ups
- **Card interactions:** Click a card to drill into details via postMessage
- **Dark theme:** Background #0a0a0a, card background #1a1a2e, text #e2e8f0
- **All inline CSS — no external CDNs, no Tailwind, no external scripts**
- **PostMessage navigation:** Cards send `{type:'canvas-action', action:'speak', text:'Tell me about estimate EST-2026-XXXX'}` on click

### Canvas Page Template

When building the page, read `workspace/business/estimates.json`, classify each estimate, and generate the HTML with real data embedded. The page should be fully self-contained.

**Structure:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Estimate Pipeline</title>
  <style>
    /* ALL styles inline — dark theme, grid layout, card styles, color coding */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0a0a; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 20px; }
    .metrics-bar { display: flex; gap: 24px; margin-bottom: 24px; flex-wrap: wrap; }
    .metric { background: #1a1a2e; border-radius: 8px; padding: 16px 24px; }
    .metric-value { font-size: 28px; font-weight: 700; color: #fff; }
    .metric-label { font-size: 13px; color: #94a3b8; margin-top: 4px; }
    .pipeline { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; min-height: 400px; }
    .column { background: #111; border-radius: 8px; padding: 12px; }
    .column-header { font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; padding: 8px 0; margin-bottom: 8px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }
    .column-count { color: #94a3b8; }
    .card { background: #1a1a2e; border-radius: 6px; padding: 12px; margin-bottom: 8px; cursor: pointer; transition: background 0.15s; }
    .card:hover { background: #252547; }
    .card-name { font-weight: 600; font-size: 14px; margin-bottom: 4px; }
    .card-service { font-size: 12px; color: #94a3b8; margin-bottom: 6px; }
    .card-amount { font-size: 16px; font-weight: 700; color: #22c55e; }
    .card-meta { font-size: 11px; color: #64748b; margin-top: 6px; display: flex; justify-content: space-between; }
    .card-hot { border-left: 3px solid #ef4444; }
    .card-warm { border-left: 3px solid #f59e0b; }
    .card-cold { border-left: 3px solid #3b82f6; }
    .card-won { border-left: 3px solid #22c55e; }
    .card-lost { border-left: 3px solid #6b7280; }
    .overdue-badge { background: #ef4444; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="metrics-bar">
    <div class="metric">
      <div class="metric-value">$XX,XXX</div>
      <div class="metric-label">Pipeline Value</div>
    </div>
    <div class="metric">
      <div class="metric-value">XX%</div>
      <div class="metric-label">Close Rate</div>
    </div>
    <div class="metric">
      <div class="metric-value">X</div>
      <div class="metric-label">Overdue Follow-ups</div>
    </div>
    <div class="metric">
      <div class="metric-value">X</div>
      <div class="metric-label">Hot Estimates</div>
    </div>
  </div>
  <div class="pipeline">
    <!-- HOT column -->
    <div class="column">
      <div class="column-header">
        <span style="color:#ef4444;">HOT</span>
        <span class="column-count">X</span>
      </div>
      <!-- Cards populated from data -->
    </div>
    <!-- WARM column -->
    <div class="column">
      <div class="column-header">
        <span style="color:#f59e0b;">WARM</span>
        <span class="column-count">X</span>
      </div>
    </div>
    <!-- COLD column -->
    <div class="column">
      <div class="column-header">
        <span style="color:#3b82f6;">COLD</span>
        <span class="column-count">X</span>
      </div>
    </div>
    <!-- WON column -->
    <div class="column">
      <div class="column-header">
        <span style="color:#22c55e;">WON</span>
        <span class="column-count">X</span>
      </div>
    </div>
    <!-- LOST column -->
    <div class="column">
      <div class="column-header">
        <span style="color:#6b7280;">LOST</span>
        <span class="column-count">X</span>
      </div>
    </div>
  </div>
  <script>
    /* Card click — drill into estimate via voice */
    document.querySelectorAll('.card').forEach(function(card) {
      card.addEventListener('click', function() {
        var estId = this.getAttribute('data-id');
        window.parent.postMessage({
          type: 'canvas-action',
          action: 'speak',
          text: 'Tell me about estimate ' + estId
        }, '*');
      });
    });
  </script>
</body>
</html>
```

**When generating the page:** Read the live estimates data, classify each estimate, compute the metrics, and inject real values into the template. Every card must include `data-id="EST-YYYY-NNNN"` for the click handler. Cards for WON and LOST columns show only the 10 most recent to avoid clutter.

---

## Heartbeat Behavior

On every heartbeat cycle, check for estimates that need attention. This runs automatically — the owner does not need to ask.

### Heartbeat Check Logic

1. Read `workspace/business/estimates.json`
2. For each estimate with `status == "pending"`:
   a. Calculate age and classification
   b. Check if `next_follow_up <= today`
   c. Check if amount >= `high_value_threshold`
3. If any HOT estimates exist with overdue follow-ups, alert the owner
4. If any high-value estimates (any classification) have overdue follow-ups, alert the owner
5. Auto-archive any DEAD estimates (age > `cold_days` threshold)

### Heartbeat Alert Format

Only alert when there is something actionable. Do not repeat alerts the owner has already acknowledged.

> "[N] estimates need follow-up today. [Highest priority first:] [customer_name] — [service], $[amount], [age] days. [Classification]. Want me to run through the follow-up scripts?"

If no estimates need attention, say nothing. Silence means the pipeline is healthy.

---

## Critical Rules

These are non-negotiable. Violating any of these degrades the owner's trust in the system and their relationship with customers.

### Never Be Pushy

- Follow-up scripts are helpful, not high-pressure
- Never use urgency tactics, artificial scarcity, or fear-based messaging
- Never imply the customer is making a mistake by not booking
- The tone is: neighbor who happens to run a service company, not used-car salesman

### Always Personalize

- Reference the specific service that was quoted, by name
- Reference any prior conversation details from `notes` or `follow_up_log`
- Use the customer's first name
- Reference the technician who quoted if relevant
- Mention the actual dollar amount only when it is helpful (e.g., confirming the quote is still valid)

### Track Everything

- Every contact attempt gets a `follow_up_log` entry with timestamp, method, outcome, and notes
- Never make a follow-up without logging it
- When the owner verbally reports a follow-up they did themselves, log it too
- When an estimate converts, record the `booked_job_id` to close the loop
- When an estimate is lost, always capture the `decline_reason` — even if it is "no_response"

### Respect Boundaries

- **Quiet hours:** Only suggest follow-ups between `quiet_hours.start` and `quiet_hours.end` (default 9am-7pm)
- **Max follow-ups:** Never exceed `max_follow_ups` (default 4) — after the last attempt, mark as lost if no response
- **Declined means declined:** Never follow up on an estimate the customer has already explicitly declined. If `status == "lost"`, that estimate is done.
- **Do not contact:** If a customer asks not to be contacted again, immediately set `status: "lost"`, `decline_reason: "do_not_contact"`, and never include them in follow-up lists

### Data Integrity

- Never overwrite `follow_up_log` entries — only append
- Never change `created_date` after initial creation
- When updating status to `won` or `lost`, the change is permanent — do not revert to `pending`
- Keep `estimates.json` sorted by `created_date` descending (newest first) for readability
- Auto-assign estimate IDs sequentially: find the highest existing ID number and increment by 1

---

## Setup Guide

When this skill is first activated for a new client, walk through initial setup:

1. **Create config:** Ask the owner for business name, services offered, team members, and any differentiators. Write `workspace/business/config.json`.
2. **Create estimates file:** Initialize `workspace/business/estimates.json` with `{"estimates": []}`.
3. **Add existing estimates:** Ask if there are any outstanding estimates to backfill. Voice-capture each one.
4. **Confirm thresholds:** Review the default hot/warm/cold thresholds and max follow-ups. Adjust if the owner prefers different timing.
5. **Build pipeline page:** Generate `estimate-pipeline.html` with the initial data.

> "Estimate tracker is set up. I'll keep an eye on your pipeline and let you know when follow-ups are due. Just say 'how are our estimates looking' anytime for a quick status."

---

## Integration Points

### With Other Skills

- **Customer follow-up skill:** If a general `customer-followup` skill exists, estimate follow-ups take priority for contacts that appear in both systems. Do not double-contact.
- **Canvas design skill:** The pipeline page can be enhanced with the canvas design skill for richer visualizations if requested.
- **Suno music skill:** No integration needed (but if the owner wants a celebratory song when they hit a close rate milestone, go for it).

### With External Systems

- If a CRM or job management system is connected in the future, `customer_id` and `booked_job_id` fields enable linking
- Estimate data could feed into invoice generation or scheduling systems via the workspace file system
- The `follow_up_log` provides an audit trail suitable for compliance or training review

---

## Example Session

**Owner:** "Add an estimate."
**Agent:** "Sure — who's the customer?"
**Owner:** "Tom Garcia."
**Agent:** "What service?"
**Owner:** "Water heater install."
**Agent:** "How much?"
**Owner:** "Twenty-two hundred."
**Agent:** "Phone number?"
**Owner:** "555-0177."
**Agent:** "Any notes — is he comparing quotes, any concerns?"
**Owner:** "He seemed ready but wants to check with his wife."
**Agent:** "Got it — added estimate EST-2026-0043 for Tom Garcia, water heater install at $2,200. Noted he's checking with his wife. First follow-up is set for tomorrow."

---

**Owner:** "How are our estimates looking?"
**Agent:** "We've got 3 hot, 2 warm, and 1 cold. Total pipeline value is $24,350. Sarah Johnson's repipe at $8,500 is due for follow-up today — she was comparing prices last time we spoke. Tom Garcia's water heater is hot at 1 day old. Want to go through the follow-ups?"

---

**Owner:** "Follow up on the Sarah Johnson estimate."
**Agent:** "Sarah's repipe estimate is 5 days old — that's WARM territory. This would be attempt 2. Her objection was price. Here's what I'd say:

'Hi Sarah, it's ABC Plumbing checking in on that repipe quote. I know cost is a factor — just wanted you to know we stand behind the work with a 10-year warranty, and we can set up financing if that makes it easier. Happy to answer any questions about what's included.'

Want me to adjust anything, or should I log this as the follow-up?"

---

**Owner:** "Sarah booked the repipe."
**Agent:** "Great news — marking Sarah Johnson's estimate EST-2026-0042 as won. That's $8,500 recovered. Do you have a job ID to link it to?"
