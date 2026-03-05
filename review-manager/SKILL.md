---
name: review-manager
description: "Online reputation management — monitor reviews across Google, Yelp, Facebook, and BBB. Alert on new reviews, draft responses, track rating trends. Critical for local service companies."
metadata: {"openclaw": {"emoji": "⭐"}}
---

# Review Manager Skill

Online reputation management system for local service companies. Monitors reviews across every platform that matters, alerts on negative reviews immediately, drafts owner-approved responses, tracks rating trends over time, and provides weekly reputation reports.

For a local service company, online reviews ARE the marketing department. A single unanswered 1-star review costs more than a month of ad spend. This skill makes sure nothing slips through.

## When to Use This Skill

Activate when the user says anything like:

- "Check my reviews" / "Any new reviews?"
- "How's our rating?" / "What's our Google rating?"
- "Show me negative reviews" / "Any bad reviews?"
- "Draft a response to [reviewer name]"
- "Review report" / "Reputation update"
- "Show reputation dashboard"
- "How many reviews do we have?"
- "What are people saying about us?"
- "Respond to that review"
- "Weekly reputation report"

Also activate on heartbeat cycles for scheduled review monitoring (see Heartbeat Behavior section).

---

## Review Sources (Priority Order)

Monitor these platforms in order of impact on local search visibility and customer trust:

| Priority | Platform | Why It Matters |
|----------|----------|----------------|
| 1 | **Google Business Profile** | Directly impacts local search ranking. Most visible to potential customers. |
| 2 | **Yelp** | High domain authority. Often appears in organic search results for service queries. |
| 3 | **Facebook** | Social proof. Customers check Facebook pages before calling. |
| 4 | **BBB (Better Business Bureau)** | Trust signal for older demographics. Complaint resolution matters. |
| 5 | **Angi / HomeAdvisor** | Lead generation platform. Reviews here affect lead quality and cost. |
| 6 | **Nextdoor** | Neighborhood recommendations. Hyperlocal trust — one recommendation reaches hundreds of neighbors. |

### Monitoring Method

Use the **serper-search** skill to check for new reviews. Search queries by platform:

```
Google:    "[company name] reviews" OR site:google.com/maps "[company name]"
Yelp:      site:yelp.com "[company name]" "[city]"
Facebook:  site:facebook.com "[company name]" reviews
BBB:       site:bbb.org "[company name]"
Angi:      site:angi.com "[company name]"
Nextdoor:  "[company name]" site:nextdoor.com
```

When checking reviews, compare results against the `reviews` array in `reviews.json` to identify new entries. Any review not already in the file is new and should be added with `response_status: "pending"`.

**Serper credit awareness:** Review checks use API credits. Batch platform checks into as few queries as possible. The 2x daily heartbeat check should use at most 2-3 Serper calls per cycle (combine platforms when possible). If the user requests a manual check, run all platforms.

---

## Data Files

### Primary Data File

**File:** `workspace/business/reviews.json`

```json
{
  "summary": {
    "total_reviews": 127,
    "average_rating": 4.7,
    "rating_distribution": { "5": 89, "4": 22, "3": 8, "2": 5, "1": 3 },
    "last_checked": "2026-03-05T14:30:00",
    "platforms": {
      "google": { "count": 85, "avg": 4.8, "url": "https://g.page/abc-plumbing" },
      "yelp": { "count": 32, "avg": 4.5, "url": "" },
      "facebook": { "count": 10, "avg": 4.9, "url": "" }
    }
  },
  "reviews": [
    {
      "id": "REV-001",
      "source": "google",
      "reviewer_name": "John Smith",
      "customer_id": "CUST-001",
      "rating": 5,
      "text": "Mike was fantastic! Fixed our water heater same day. Professional and clean.",
      "date": "2026-03-02",
      "detected_date": "2026-03-02",
      "response_status": "responded",
      "response_text": "Thank you, John! We're glad Mike took great care of you. That same-day service is what we aim for every time. Call us anytime you need anything!",
      "response_date": "2026-03-02",
      "response_approved_by": "owner",
      "sentiment": "positive",
      "topics": ["speed", "professionalism", "cleanliness"],
      "service_mentioned": "water-heater",
      "technician_mentioned": "Mike"
    }
  ],
  "response_templates_used": []
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique ID. Format: `REV-NNN` (auto-increment) |
| `source` | string | yes | Platform: `google`, `yelp`, `facebook`, `bbb`, `angi`, `nextdoor` |
| `reviewer_name` | string | yes | Name as shown on the review |
| `customer_id` | string | no | Links to customer record in `customers.json` if identifiable |
| `rating` | number | yes | 1-5 stars |
| `text` | string | yes | Full review text (empty string if rating-only review) |
| `date` | string | yes | ISO date the review was posted |
| `detected_date` | string | yes | ISO date when we first found this review |
| `response_status` | string | yes | One of: `pending`, `draft_ready`, `approved`, `responded`, `no_response_needed` |
| `response_text` | string | no | The drafted or posted response |
| `response_date` | string | no | ISO date the response was posted |
| `response_approved_by` | string | no | Who approved: `owner`, `manager`, `auto` |
| `sentiment` | string | yes | `positive`, `negative`, `mixed`, `neutral` |
| `topics` | array | yes | Extracted themes: `speed`, `professionalism`, `cleanliness`, `price`, `quality`, `communication`, `punctuality`, `knowledge`, `friendliness`, `follow-up` |
| `service_mentioned` | string | no | Service type slug if identifiable from review text |
| `technician_mentioned` | string | no | Technician name if mentioned |

### Response Status Flow

```
NEW REVIEW DETECTED
    |
    v
[pending] — Review found, no response drafted yet
    |
    v
[draft_ready] — Response drafted, awaiting owner approval
    |
    +-- Owner approves --> [approved] --> Owner posts it --> [responded]
    |
    +-- Owner edits draft --> update response_text --> [approved] --> [responded]
    |
    +-- Owner rejects draft --> redraft --> [draft_ready]
    |
    +-- Rating-only review with no text --> [no_response_needed]
```

### Configuration File

**File:** `workspace/business/config.json`

The review-manager reads business configuration from the shared config file. Relevant fields:

```json
{
  "company_name": "ABC Plumbing",
  "owner_name": "Mike",
  "business_phone": "555-0100",
  "google_review_link": "https://g.page/r/CxxxxYYYYzzzz/review",
  "review_profiles": {
    "google": "https://g.page/abc-plumbing",
    "yelp": "https://yelp.com/biz/abc-plumbing-phoenix",
    "facebook": "https://facebook.com/abcplumbing",
    "bbb": ""
  },
  "review_settings": {
    "check_frequency": "2x_daily",
    "auto_draft_responses": true,
    "alert_threshold": 3,
    "weekly_report_day": "monday",
    "review_request_link": "https://g.page/r/CxxxxYYYYzzzz/review",
    "response_contact_phone": "555-0100"
  }
}
```

If `config.json` does not exist or is missing `review_settings`, use these defaults:
- `check_frequency`: `"2x_daily"`
- `auto_draft_responses`: `true`
- `alert_threshold`: `3` (alert on reviews at or below this rating)
- `weekly_report_day`: `"monday"`
- `response_contact_phone`: use `business_phone` from config

---

## Alert Priority System

### Priority Classification

| Rating | Priority | Response Window | Action |
|--------|----------|----------------|--------|
| 1-2 stars | **CRITICAL** | Alert owner IMMEDIATELY. Draft response within the hour. | Stop what you are doing and alert. This is a fire. |
| 3 stars | **HIGH** | Alert within 4 hours. Draft response same day. | Needs attention — mixed review could go either way publicly. |
| 4 stars | **NORMAL** | Mention at next interaction or in weekly briefing. Draft thank-you response. | Good review — still respond to show engagement. |
| 5 stars | **NORMAL** | Mention at next interaction or in weekly briefing. Draft thank-you response. | Great review — respond with specific gratitude. |

### Alert Format

**CRITICAL (1-2 stars):**
> "ALERT: New 1-star review on Google from [reviewer name]. They said: '[first 100 chars of review text]...' I've drafted a response — want to hear it? This needs a reply today."

**HIGH (3 stars):**
> "Heads up — new 3-star review on Yelp from [reviewer name]. Mixed feedback: '[brief summary]'. I've got a draft response ready when you want to look at it."

**NORMAL (4-5 stars):**
> "Good news — [reviewer name] left a 5-star review on Google. They mentioned [technician] by name. I drafted a thank-you response. Want to hear it or should I add it to your review queue?"

---

## Response Drafting Rules

### CRITICAL RULE: Owner Approval Required

**NEVER respond to a review without owner approval.** The workflow is:
1. Agent drafts the response
2. Agent reads the draft to the owner (or displays it)
3. Owner approves, edits, or rejects
4. Owner posts the response on the platform (agent cannot post directly)

The agent's role is DRAFTING, not posting. Make this clear every time.

### For Positive Reviews (4-5 Stars)

**Rules:**
- Thank the reviewer by first name
- Reference the specific service if identifiable from the review text
- Mention the technician by name if they were called out in the review
- Invite them back or mention a related service naturally
- Keep to 2-3 sentences — concise and genuine
- **VARY responses — NEVER use the same template twice in a row**

**Track variety:** The `response_templates_used` array in `reviews.json` stores the last 10 response opening phrases. Before drafting, check this list and ensure the new response starts differently.

**Example responses (vary every time):**

> "Thank you, John! We're glad Mike got that water heater taken care of same day. That's what we aim for every time — call us anytime!"

> "Really appreciate the kind words, Sarah! Carlos takes a lot of pride in his work and it shows. If your HVAC ever needs attention, we've got you covered."

> "Thanks for taking the time to share this, David! Glad the repipe went smoothly. That PEX system should serve you well for decades."

> "John, this made our day! We appreciate you trusting us with your plumbing. Don't hesitate to reach out if you need anything."

**Pattern to avoid:** Do NOT start every response with "Thank you" — vary openings: "Really appreciate...", "This made our day!", "Glad to hear...", "So happy...", "[Name], thanks for..."

### For Negative Reviews (1-2 Stars)

**Rules:**
- Acknowledge the concern sincerely — the reviewer felt strongly enough to write about it
- Apologize without making excuses or blaming the customer
- Offer to make it right — concrete action, not vague promises
- Provide the business phone number for direct contact
- Take the conversation offline — public back-and-forth never ends well
- **NEVER argue with the reviewer**
- **NEVER blame the customer or suggest they are wrong**
- **NEVER reveal private details** (job cost, specific work done that was not in the review, customer account info)
- **NEVER mention the dollar amount of the job**
- **NEVER say "per our records" or "according to our files"** — this sounds defensive and corporate
- Keep to 3-4 sentences

**Example responses:**

> "We're sorry to hear about your experience, Mark. This isn't the standard we hold ourselves to. We'd like the chance to make this right — please give us a call at 555-0100 so we can discuss this directly."

> "Lisa, we apologize for the frustration. Every customer deserves better than what you described. Please reach out to us at 555-0100 — we want to resolve this for you personally."

> "We take this feedback seriously, Tom. We're sorry we fell short. Please call us at 555-0100 so we can address your concerns directly and make things right."

**What NOT to write (EVER):**

- "We have no record of this service." (calling them a liar)
- "Actually, our technician reported that..." (arguing publicly)
- "We charged you $X which is fair for..." (revealing pricing, being defensive)
- "If you had called us first instead of posting..." (blaming them)
- "We're sorry you FEEL that way." (non-apology)
- "Per our policy..." (corporate deflection)

### For Mixed Reviews (3 Stars)

**Rules:**
- Thank them for the honest feedback — they took the time to be balanced
- Acknowledge what went well (they said something positive — highlight it)
- Address the concern directly without being defensive
- Offer to improve their experience or follow up
- Keep to 3-4 sentences

**Example responses:**

> "Thanks for the honest feedback, Karen. We're glad the repair itself went well! We hear you on the scheduling delay — that's something we're actively working to improve. Give us another shot and we'll make sure the timing is right."

> "Appreciate the review, James. We're happy the work quality met your expectations. Sorry about the communication gap — we're going to do better there. Call us anytime at 555-0100."

> "Thanks for sharing this, Maria. Glad Chris did solid work on the install. We understand the wait was longer than expected and we're addressing that. We'd love the chance to earn that 5th star next time."

---

## Trigger Phrase Handling

### "Check my reviews" / "Any new reviews?"

**Action:** Run a review scan across all configured platforms using serper-search.

**Steps:**
1. Read `workspace/business/reviews.json` to get `summary.last_checked` and existing review IDs
2. Search each platform for the company name + "reviews" via serper
3. Compare results against existing entries
4. Add any new reviews with `response_status: "pending"`
5. Update `summary.last_checked`
6. Recalculate `summary` totals (total_reviews, average_rating, rating_distribution, platform counts)
7. Report findings

**Response format:**
> "Checked all platforms. [N] new reviews since last check:
> - **5 stars** on Google from John Smith: 'Great service, on time and professional.'
> - **2 stars** on Yelp from Lisa Brown: 'Overcharged and messy cleanup.'
>
> That Yelp review needs attention — want me to draft a response?"

If no new reviews:
> "All clear — no new reviews since [last_checked date]. Your ratings are holding steady at [average] across [total] reviews."

### "How's our rating?" / "What's our Google rating?"

**Action:** Read `reviews.json` and deliver a rating summary.

**Response format:**
> "You're at 4.7 overall across 127 reviews. Google is your strongest at 4.8 with 85 reviews. Yelp is 4.5 with 32 reviews — a couple of 3-stars brought that down last month. Facebook is 4.9 but only 10 reviews. Your 5-star rate is 70%."

If a specific platform is mentioned ("Google rating"), focus on that platform but mention overall for context.

### "Show me negative reviews"

**Action:** Filter `reviews.json` for reviews with rating <= 2. If asking about "bad reviews" or "problem reviews", include 3-star reviews too.

**Response format:**
> "You've got 8 reviews at 3 stars or below:
> - 3 are 1-star, 5 are 2-star, 0 at 3 stars
> - [N] have been responded to, [N] are still pending
> - Most common complaints: [top 2-3 topics from negative reviews]
>
> Want me to go through the unresponded ones?"

### "Draft a response to [reviewer name]"

**Action:** Find the review by reviewer name. Generate a response following the rules for that rating level.

**Steps:**
1. Find the review in `reviews.json` by `reviewer_name` (fuzzy match — "John" matches "John Smith")
2. Read the review text and rating
3. Draft a response following the appropriate rules (positive/negative/mixed)
4. Check `response_templates_used` to avoid repetition
5. Read the draft to the owner

**Response format:**
> "Here's a draft response for John Smith's 5-star Google review:
>
> 'Thank you, John! We're glad Mike got that water heater taken care of same day. That's what we aim for — call us anytime!'
>
> Want me to adjust anything, or is that good to go?"

After approval:
- Set `response_status: "approved"`
- Set `response_text` to the final text
- Set `response_approved_by: "owner"`
- Add the opening phrase to `response_templates_used`

> "Marked as approved. Go ahead and post that on Google when you get a chance. The review link is: [google review profile URL]"

After owner confirms they posted it:
- Set `response_status: "responded"`
- Set `response_date` to today

### "Review report" / "Reputation update"

**Action:** Comprehensive spoken report. See Weekly Reputation Report section below.

### "Show reputation dashboard"

**Action:** Generate the `reputation-dashboard.html` canvas page. See Canvas Page section below.

---

## Heartbeat Behavior

### Review Check Schedule

Check for new reviews **2x per day** — once in the morning (around 9 AM) and once in the evening (around 5 PM). This aligns with when business owners are most likely to be available to approve responses.

### Heartbeat Check Logic

```
ON EACH HEARTBEAT CYCLE:

1. Read workspace/business/reviews.json
2. Read summary.last_checked timestamp
3. Determine if a check is due:
   - If last_checked is > 10 hours ago → run morning or evening check
   - If last_checked is today AND both checks already done → skip
4. If check is due:
   a. Run serper searches for company name across platforms
   b. Compare results against existing reviews
   c. For each NEW review found:
      - Assign next REV-NNN ID
      - Classify sentiment
      - Extract topics
      - Set response_status = "pending"
      - Add to reviews array
   d. Update summary statistics
   e. Update last_checked timestamp
   f. Write reviews.json
5. Alert based on priority:
   - 1-2 stars → IMMEDIATE alert (interrupt whatever else is happening)
   - 3 stars → mention in next interaction
   - 4-5 stars → queue for weekly report (or mention casually)
6. If auto_draft_responses is true in config:
   - Draft responses for all new reviews with response_status == "pending"
   - Set response_status to "draft_ready"
   - For CRITICAL reviews, present the draft immediately
```

### Negative Review Immediate Alert

1-2 star reviews BYPASS the normal heartbeat schedule. If a negative review is detected at ANY point during a review check, alert the owner immediately regardless of time of day or what else is being discussed.

**Alert format:**
> "STOP — we just got a [1/2]-star review on [platform] from [reviewer name]. [If text exists: 'They said: [first 80 characters]...'] I have a draft response ready. This should get a reply within the hour if possible. Want to hear the draft?"

### Tracking State

Track heartbeat state in `workspace/business/.review-check-state.json`:

```json
{
  "last_morning_check": "2026-03-05T09:15:00",
  "last_evening_check": "2026-03-04T17:22:00",
  "last_alert_review_id": "REV-127",
  "pending_alerts": []
}
```

Do not re-alert on reviews the owner has already been told about. Track `last_alert_review_id` to know where to start.

---

## Weekly Reputation Report

Deliver this report on the configured day (default: Monday) during the first interaction. Can also be triggered manually with "review report" or "reputation update".

### Report Structure (Spoken — 60-90 seconds)

#### Section 1 — This Week's Reviews (15 seconds)

> "[N] new reviews this week, averaging [X.X] stars. [Breakdown: N at 5-star, N at 4-star, etc.]. [If positive trend:] That's up from [last week's average]. [If negative trend:] That's down from [last week's X.X average]."

#### Section 2 — Rating Trends (15 seconds)

> "Your overall rating is [X.X] across [total] reviews. [Compared to last month:] [Up/down/flat] from [last month's average]. Google is at [X.X], Yelp at [X.X]. [Platform with biggest change:] [Platform] moved [up/down] [X.X] points this month."

#### Section 3 — Response Performance (15 seconds)

> "Response rate this week: [X]% — you responded to [N] of [N] reviews. Average response time: [X] days. [If any unresponded:] You still have [N] unresponded reviews — [N] negative, [N] positive. The negative ones should get a reply."

#### Section 4 — What Customers Are Saying (20 seconds)

> "Top themes in positive reviews: [top 3 topics]. Customers keep mentioning [specific theme]. Top complaints: [top 2 negative topics]. [If a specific issue appears multiple times:] '[Topic]' came up [N] times this month — might be worth addressing with the team."

#### Section 5 — Competitor Context (10 seconds, if data available)

> "For context, [competitor name] is at [X.X] stars with [N] reviews on Google. You're [ahead/behind] by [X.X] points. [If ahead:] Keep it up. [If behind:] Closing that gap should be a priority."

Only include competitor data if it has been previously gathered and stored. Do NOT run a serper search just for this section during the report.

#### Section 6 — Action Items (15 seconds)

> "Three things to do: First — respond to [reviewer name]'s [rating]-star review on [platform]. I've got a draft ready. Second — [if negative trend:] Talk to the team about [recurring complaint topic]. It's come up [N] times. Third — [if review volume is low:] We only got [N] reviews this week. Remind your techs to hand out the review card after every job."

### Report Calculations

| Metric | Formula |
|--------|---------|
| Week's average rating | Sum of ratings for reviews with `date` in current week / count |
| Rating trend | Current week average - previous week average |
| Response rate | Reviews with `response_status == "responded"` / total reviews in period |
| Average response time | Mean of (`response_date` - `date`) for responded reviews in period |
| Top topics (positive) | Frequency count of `topics` where `sentiment == "positive"`, top 3 |
| Top topics (negative) | Frequency count of `topics` where `sentiment == "negative"`, top 3 |
| Platform breakdown | Group by `source`, calculate count and average per platform |
| Unresponded count | Count where `response_status` is `"pending"` or `"draft_ready"` |

---

## Review Solicitation Guidance

When the owner asks "How do I get more reviews?" or "How do we ask for reviews?", provide this guidance. Also proactively mention it if review volume is low (fewer than 4 reviews per week for an active service company).

### Best Practices

1. **Timing is everything.** Ask after the customer has confirmed satisfaction — NEVER before. The customer-followup skill handles this at Stage 2 (review request) after Stage 1 (satisfaction check) passes.

2. **Make it easy.** Provide the direct Google review link. One tap, not three. The link should be in `config.json` at `google_review_link` or `review_settings.review_request_link`.

3. **Ask in person or by text.** The best conversion comes from the technician asking face-to-face: "Would you mind leaving us a quick Google review? It really helps us out." Second best is a text message with the direct link within 2 hours of service completion.

4. **Put the link everywhere:**
   - On every invoice and receipt
   - In the email signature
   - On the business card
   - On the "Thank You" page of the website
   - On the van wrap or leave-behind card
   - In the text message sent after service

5. **Ask for HONEST feedback, not positive reviews.** Say: "We'd love to hear how we did" — NOT "Please leave us a 5-star review." Asking specifically for positive reviews violates Google, Yelp, and Facebook terms of service and can get the business penalized.

6. **NEVER offer incentives for reviews.** No discounts, no gift cards, no contest entries, no "leave a review and get 10% off." This violates every major platform's ToS. Google will remove incentivized reviews and may flag the business profile. Yelp actively penalizes this. The FTC considers undisclosed incentivized reviews deceptive.

7. **Respond to every review.** Businesses that respond to reviews get 12% more reviews on average. It signals to potential reviewers that their voice will be heard. It also signals to Google that the business is active and engaged.

8. **Don't ask everyone at once.** A sudden spike of 20 reviews in one week looks fake. Google's algorithm filters suspicious patterns. Steady, organic growth (3-5 reviews per week) is the goal.

9. **Don't panic about negative reviews.** A business with ONLY 5-star reviews looks fake. A few 3-star or even 2-star reviews with thoughtful owner responses actually BUILD trust. Respond well and move on.

### Review Link Reminder

If the review request link is configured in `config.json`, periodically remind the owner:

> "Your Google review link is: [link]. Make sure it's on every invoice and receipt. Techs should be handing out the review card after every satisfied customer."

If the link is NOT configured:

> "You don't have a review request link set up yet. Go to your Google Business Profile, click 'Ask for reviews', and copy that link. I'll save it in your config so your team can use it."

---

## Sentiment Analysis

When processing a new review, classify the sentiment and extract topics.

### Sentiment Classification

| Sentiment | Criteria |
|-----------|----------|
| `positive` | Rating 4-5 AND text is primarily complimentary |
| `negative` | Rating 1-2 AND text describes problems or dissatisfaction |
| `mixed` | Rating 3 OR text contains both positive and negative elements |
| `neutral` | Rating-only review with no text, or text is purely factual with no emotional content |

### Topic Extraction

Scan the review text for these themes and tag accordingly:

| Topic | Keywords / Signals |
|-------|-------------------|
| `speed` | "fast", "quick", "same day", "on time", "prompt", "rapid", "didn't have to wait" |
| `professionalism` | "professional", "courteous", "respectful", "thorough", "knowledgeable" |
| `cleanliness` | "clean", "tidy", "no mess", "cleaned up", "spotless" |
| `price` | "expensive", "affordable", "fair price", "overcharged", "worth it", "reasonable", "rip off", "cost" |
| `quality` | "quality", "workmanship", "well done", "shoddy", "good job", "excellent work" |
| `communication` | "communicated", "kept me informed", "called ahead", "explained", "didn't return calls", "ghosted" |
| `punctuality` | "on time", "showed up late", "arrived early", "punctual", "no-show", "waited" |
| `knowledge` | "knowledgeable", "expert", "knew what they were doing", "experienced", "diagnosed quickly" |
| `friendliness` | "friendly", "nice", "personable", "rude", "attitude", "pleasant" |
| `follow-up` | "followed up", "checked back", "never heard back", "warranty", "came back to fix" |

A single review can have multiple topics. Include all that apply.

### Service and Technician Detection

Scan review text for:
- **Service type:** Match against services listed in `config.json` (e.g., "water heater" -> `water-heater-install`, "repipe" -> `whole-house-repipe`)
- **Technician name:** Match against known team member names from `config.json` or `customers.json` job history

If uncertain, leave the field null. Never guess.

---

## Canvas Page: reputation-dashboard.html

When the user asks to "show reputation dashboard" or "show me reviews visually", generate this canvas page with real data from `reviews.json`.

### Page Requirements

- Dark theme, all inline CSS, no external CDNs, no Tailwind, no external scripts
- PostMessage bridge for interactive buttons
- Mobile-friendly layout (flexbox/grid with min-width breakpoints)
- Real data populated from `reviews.json` — never placeholder values

### Dashboard Layout

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reputation Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #0a0a0a;
    color: #e2e8f0;
    padding: 20px;
    min-height: 100vh;
  }
  .header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #1e293b;
  }
  .header h1 { font-size: 1.8rem; color: #fff; margin-bottom: 5px; }
  .header .subtitle { color: #94a3b8; font-size: 0.9rem; }

  /* Overall Rating Badge */
  .rating-hero {
    text-align: center;
    margin-bottom: 30px;
    padding: 30px;
    background: #111111;
    border: 1px solid #1e293b;
    border-radius: 12px;
  }
  .rating-number {
    font-size: 4rem;
    font-weight: 800;
    color: #fbbf24;
    line-height: 1;
  }
  .rating-stars {
    font-size: 1.5rem;
    color: #fbbf24;
    margin: 8px 0;
    letter-spacing: 4px;
  }
  .rating-total {
    font-size: 0.9rem;
    color: #94a3b8;
  }

  /* Metrics Row */
  .metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }
  .metric-card {
    background: #111111;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }
  .metric-card .value {
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 4px;
  }
  .metric-card .label {
    color: #94a3b8;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .green { color: #22c55e; }
  .red { color: #ef4444; }
  .amber { color: #f59e0b; }
  .blue { color: #3b82f6; }

  /* Rating Distribution Bars */
  .distribution {
    background: #111111;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  }
  .distribution h2 {
    font-size: 1rem;
    margin-bottom: 16px;
    color: #fff;
  }
  .dist-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }
  .dist-label {
    width: 50px;
    font-size: 0.85rem;
    color: #94a3b8;
  }
  .dist-bar-bg {
    flex: 1;
    height: 20px;
    background: #1e293b;
    border-radius: 4px;
    overflow: hidden;
    margin: 0 10px;
  }
  .dist-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
  }
  .dist-bar-5 { background: #22c55e; }
  .dist-bar-4 { background: #84cc16; }
  .dist-bar-3 { background: #f59e0b; }
  .dist-bar-2 { background: #f97316; }
  .dist-bar-1 { background: #ef4444; }
  .dist-count {
    width: 30px;
    text-align: right;
    font-size: 0.85rem;
    color: #94a3b8;
  }

  /* Platform Breakdown */
  .platforms {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
  }
  .platform-card {
    background: #111111;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 16px;
  }
  .platform-name {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    margin-bottom: 8px;
  }
  .platform-rating {
    font-size: 1.5rem;
    font-weight: 700;
    color: #fbbf24;
  }
  .platform-count {
    font-size: 0.8rem;
    color: #64748b;
    margin-top: 4px;
  }

  /* Recent Reviews Section */
  .section {
    background: #111111;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  }
  .section h2 {
    font-size: 1rem;
    margin-bottom: 16px;
    color: #fff;
  }
  .review-card {
    background: #0a0a0a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 10px;
  }
  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  .review-name { font-weight: 600; font-size: 0.9rem; }
  .review-source {
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: #1e293b;
    color: #94a3b8;
    text-transform: uppercase;
  }
  .review-stars { color: #fbbf24; font-size: 0.85rem; margin-bottom: 6px; }
  .review-text { font-size: 0.85rem; color: #cbd5e1; line-height: 1.5; }
  .review-date { font-size: 0.75rem; color: #64748b; margin-top: 6px; }
  .review-status {
    display: inline-block;
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    margin-top: 6px;
    font-weight: 600;
  }
  .status-responded { background: rgba(34,197,94,0.15); color: #22c55e; }
  .status-pending { background: rgba(239,68,68,0.15); color: #ef4444; }
  .status-draft { background: rgba(59,130,246,0.15); color: #3b82f6; }

  /* Topics Word Cloud */
  .topics {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 8px;
  }
  .topic-tag {
    background: #1e293b;
    color: #94a3b8;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
  }
  .topic-tag.hot { background: rgba(34,197,94,0.15); color: #22c55e; }

  /* Action Button */
  .btn {
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.8rem;
    cursor: pointer;
    margin-top: 8px;
  }
  .btn-primary { background: #3b82f6; color: #fff; }
  .btn-primary:hover { background: #2563eb; }
  .btn-alert { background: #ef4444; color: #fff; }
  .btn-alert:hover { background: #dc2626; }
</style>
</head>
<body>

<div class="header">
  <h1>Reputation Dashboard</h1>
  <div class="subtitle">COMPANY_NAME &mdash; Last checked: LAST_CHECKED</div>
</div>

<!-- OVERALL RATING HERO -->
<div class="rating-hero">
  <div class="rating-number">OVERALL_RATING</div>
  <div class="rating-stars">STAR_SYMBOLS</div>
  <div class="rating-total">TOTAL_REVIEWS reviews across PLATFORM_COUNT platforms</div>
</div>

<!-- METRICS ROW -->
<div class="metrics-row">
  <div class="metric-card">
    <div class="value green">THIS_WEEK_COUNT</div>
    <div class="label">New This Week</div>
  </div>
  <div class="metric-card">
    <div class="value amber">THIS_WEEK_AVG</div>
    <div class="label">Week Avg</div>
  </div>
  <div class="metric-card">
    <div class="value blue">RESPONSE_RATE%</div>
    <div class="label">Response Rate</div>
  </div>
  <div class="metric-card">
    <div class="value red">UNRESPONDED_COUNT</div>
    <div class="label">Needs Reply</div>
  </div>
</div>

<!-- RATING DISTRIBUTION -->
<div class="distribution">
  <h2>Rating Distribution</h2>
  <div class="dist-row">
    <span class="dist-label">5 star</span>
    <div class="dist-bar-bg"><div class="dist-bar dist-bar-5" style="width: FIVE_STAR_PCT%;"></div></div>
    <span class="dist-count">FIVE_STAR_COUNT</span>
  </div>
  <div class="dist-row">
    <span class="dist-label">4 star</span>
    <div class="dist-bar-bg"><div class="dist-bar dist-bar-4" style="width: FOUR_STAR_PCT%;"></div></div>
    <span class="dist-count">FOUR_STAR_COUNT</span>
  </div>
  <div class="dist-row">
    <span class="dist-label">3 star</span>
    <div class="dist-bar-bg"><div class="dist-bar dist-bar-3" style="width: THREE_STAR_PCT%;"></div></div>
    <span class="dist-count">THREE_STAR_COUNT</span>
  </div>
  <div class="dist-row">
    <span class="dist-label">2 star</span>
    <div class="dist-bar-bg"><div class="dist-bar dist-bar-2" style="width: TWO_STAR_PCT%;"></div></div>
    <span class="dist-count">TWO_STAR_COUNT</span>
  </div>
  <div class="dist-row">
    <span class="dist-label">1 star</span>
    <div class="dist-bar-bg"><div class="dist-bar dist-bar-1" style="width: ONE_STAR_PCT%;"></div></div>
    <span class="dist-count">ONE_STAR_COUNT</span>
  </div>
</div>

<!-- PLATFORM BREAKDOWN -->
<div class="platforms">
  <!-- One platform-card per platform in summary.platforms -->
  <div class="platform-card">
    <div class="platform-name">Google</div>
    <div class="platform-rating">GOOGLE_AVG</div>
    <div class="platform-count">GOOGLE_COUNT reviews</div>
  </div>
  <div class="platform-card">
    <div class="platform-name">Yelp</div>
    <div class="platform-rating">YELP_AVG</div>
    <div class="platform-count">YELP_COUNT reviews</div>
  </div>
  <div class="platform-card">
    <div class="platform-name">Facebook</div>
    <div class="platform-rating">FB_AVG</div>
    <div class="platform-count">FB_COUNT reviews</div>
  </div>
  <!-- Add more platforms as data exists -->
</div>

<!-- UNRESPONDED REVIEWS (if any) -->
<div class="section">
  <h2 style="color: #ef4444;">Needs Response</h2>
  <!-- One review-card per unresponded review, negative first -->
  <div class="review-card" style="border-left: 3px solid #ef4444;">
    <div class="review-header">
      <span class="review-name">REVIEWER_NAME</span>
      <span class="review-source">PLATFORM</span>
    </div>
    <div class="review-stars">STAR_SYMBOLS</div>
    <div class="review-text">REVIEW_TEXT</div>
    <div class="review-date">REVIEW_DATE</div>
    <button class="btn btn-alert" onclick="window.parent.postMessage({type:'canvas-action',action:'speak',text:'Draft a response to REVIEWER_NAME'},'*')">Draft Response</button>
  </div>
  <!-- If none: <p style="color:#64748b;text-align:center;padding:20px;">All reviews responded to!</p> -->
</div>

<!-- RECENT REVIEWS -->
<div class="section">
  <h2>Recent Reviews</h2>
  <!-- Last 10 reviews, newest first -->
  <div class="review-card">
    <div class="review-header">
      <span class="review-name">REVIEWER_NAME</span>
      <span class="review-source">PLATFORM</span>
    </div>
    <div class="review-stars">STAR_SYMBOLS</div>
    <div class="review-text">REVIEW_TEXT_TRUNCATED</div>
    <div class="review-date">REVIEW_DATE</div>
    <span class="review-status status-responded">Responded</span>
  </div>
  <!-- More review-cards... -->
</div>

<!-- TOP MENTIONED TOPICS -->
<div class="section">
  <h2>What Customers Mention Most</h2>
  <div class="topics">
    <!-- Top 10 topics by frequency, most mentioned first -->
    <!-- Use .hot class for the top 3 -->
    <span class="topic-tag hot">TOPIC_NAME (COUNT)</span>
    <span class="topic-tag hot">TOPIC_NAME (COUNT)</span>
    <span class="topic-tag hot">TOPIC_NAME (COUNT)</span>
    <span class="topic-tag">TOPIC_NAME (COUNT)</span>
    <span class="topic-tag">TOPIC_NAME (COUNT)</span>
  </div>
</div>

<script>
  // No external scripts. PostMessage bridge only.
  // Draft Response buttons use canvas-action speak to trigger agent.
  // Refresh dashboard:
  function refreshDashboard() {
    window.parent.postMessage({type:'canvas-action', action:'speak', text:'Show reputation dashboard'}, '*');
  }
  // Close:
  function closeDashboard() {
    window.parent.postMessage({type:'canvas-action', action:'close'}, '*');
  }
</script>
</body>
</html>
```

**When generating this page:** Read `reviews.json`, compute all metrics, and replace ALL placeholder values with real data. Generate one `review-card` per review in the Recent Reviews section (last 10). Generate one `review-card` per unresponded review in the Needs Response section. Calculate bar widths as percentages of the highest count. Generate one `platform-card` per platform that has data. Generate topic tags from frequency counts across all reviews.

Star symbols: Use filled/empty stars based on rating:
- 5 stars: `★★★★★`
- 4 stars: `★★★★☆`
- 3 stars: `★★★☆☆`
- 2 stars: `★★☆☆☆`
- 1 star: `★☆☆☆☆`

For the rating hero, if the average is, say, 4.7 — show 4.5 rounded to nearest half: `★★★★★` (round up at .75+, show half at .25-.74... actually, just show all 5 filled for 4.5+ and adjust visually. Keep it simple — the number is the precision, the stars are the visual.)

---

## Competitor Tracking (Optional)

If the owner asks "How do we compare to [competitor]?" or mentions competitors:

1. Search for the competitor on Google/Yelp via serper-search
2. Record their rating and review count
3. Store in `workspace/business/competitors.json`:

```json
{
  "competitors": [
    {
      "name": "Smith Plumbing",
      "google_rating": 4.3,
      "google_reviews": 67,
      "yelp_rating": 3.9,
      "yelp_reviews": 28,
      "last_checked": "2026-03-05"
    }
  ]
}
```

Use this data in weekly reports for context. Check competitor ratings monthly (not on every heartbeat — save API credits).

**Never mention competitor data to customers in review responses.** This is internal intelligence only.

---

## Integration with Other Skills

### customer-followup
The customer-followup skill's Stage 2 (Review Request) is the primary mechanism for generating new reviews. The review-manager skill handles what happens AFTER a review is posted. Coordination:
- After customer-followup sends a review link, review-manager watches for the new review to appear
- If a customer from the followup pipeline leaves a review, link it via `customer_id`
- If a negative review comes in from a customer who recently had service, check if a followup satisfaction check caught the issue

### business-briefing
The business-briefing skill includes a reviews section. Review-manager provides the data. When business-briefing reads `reviews.json`, it gets the full picture. The briefing skill shows headline numbers; the review-manager skill goes deep on responses and trends.

### serper-search
Used for all review monitoring. The review-manager skill depends on serper-search for web lookups. Respect serper's credit limits — batch searches, cache results, and do not run searches more than 2x per day on heartbeat.

### estimate-tracker
No direct integration, but reviews that mention an estimate or quote should be flagged. A negative review mentioning "expensive" or "overpriced" may connect to a lost estimate in the pipeline.

### agentmail
If the owner prefers written review responses for approval, draft the response and email it to them via agentmail for review. The owner can reply with approval or edits.

---

## Setup Guide

When first activated for a new client:

1. **Check config:** Read `workspace/business/config.json` for company name, review links, and settings.

2. **Create reviews file:** If `workspace/business/reviews.json` does not exist, create it:
   ```json
   {
     "summary": {
       "total_reviews": 0,
       "average_rating": 0,
       "rating_distribution": { "5": 0, "4": 0, "3": 0, "2": 0, "1": 0 },
       "last_checked": "",
       "platforms": {}
     },
     "reviews": [],
     "response_templates_used": []
   }
   ```

3. **Initial scan:** Run a serper search across all platforms to populate the initial review inventory. This may take multiple searches. Start with Google (highest priority), then Yelp, then Facebook.

4. **Identify unresponded reviews:** After the initial scan, flag all reviews with no visible owner response as `response_status: "pending"`. Prioritize drafting responses for negative reviews first.

5. **Set review link:** If `google_review_link` is not in config, ask the owner for it. This is critical for the customer-followup integration and for reminding techs to ask for reviews.

6. **Confirm settings:** Tell the owner what is configured:
   > "Review manager is set up. I'll check for new reviews twice a day and alert you immediately on anything 3 stars or below. I'll draft responses for all new reviews — you approve before anything gets posted. Weekly report comes on [day]. Your Google review link is [link] — make sure it's on every invoice."

---

## Handling Edge Cases

### Rating-Only Reviews (No Text)

Some platforms allow ratings without text. Handle these:
- Add to `reviews.json` with `text: ""`
- Set `sentiment: "neutral"` and `topics: []`
- For 4-5 stars: `response_status: "no_response_needed"` (nothing to reference in a response)
- For 1-3 stars: `response_status: "pending"` — draft a short response anyway:
  > "We appreciate you taking the time to rate us. If there's anything we can do better, please give us a call at [phone] — we'd love to hear from you."

### Duplicate Reviews

If the same reviewer name + platform + date appears more than once, it is likely a duplicate from the search. Do NOT create a second entry. Match on `reviewer_name` + `source` + `date` to deduplicate.

### Suspected Fake Reviews

If a review appears suspicious (reviewer has no other reviews, mentions services the company does not offer, contains competitor names), flag it in the notes but do NOT accuse the reviewer publicly. Inform the owner:
> "This review from [name] looks unusual — [reason]. You may want to report it to [platform] for investigation. Do NOT respond publicly calling it fake — that backfires."

### Review Removed by Platform

If a previously tracked review disappears on a subsequent check, do NOT delete it from `reviews.json`. Add a note: `"removed_by_platform": true, "removed_date": "YYYY-MM-DD"`. Inform the owner if it was a negative review that was removed (good news).

### Owner Wants to Respond Themselves

If the owner says "I'll handle this one" or writes their own response:
- Record the response text they provide in `response_text`
- Set `response_status: "responded"`, `response_approved_by: "owner"`, `response_date: today`
- Do NOT critique their response unless they ask for feedback

### Multiple Businesses

If the owner has more than one business (e.g., ABC Plumbing and ABC HVAC), each business should have its own `reviews.json` or use a top-level business identifier. For now, this skill handles one business per workspace. If multi-business comes up, suggest separate workspace directories.

---

## Critical Rules — Non-Negotiable

1. **NEVER fabricate or guess at review content.** Only report what is actually found in search results or stored in `reviews.json`. If a search returned no results, say "no new reviews found" — do not invent them.

2. **NEVER respond to a review without owner approval.** Draft first, owner confirms. The agent does not have access to post on review platforms. The owner must copy and post the response themselves.

3. **NEVER reveal customer private information in a public response.** No job costs, no account details, no specific diagnosis or repair details that were not already in the review itself. If the reviewer says "they charged me $800 for nothing" — the response should NOT confirm or deny the amount.

4. **NEVER argue with a reviewer.** Not even if the review is unfair, inaccurate, or appears fake. The response must be measured, empathetic, and focused on resolution. Arguments in public review responses damage the business more than the original bad review.

5. **ALWAYS vary response language.** Cookie-cutter responses ("Thank you for your kind words! We appreciate your business!") repeated across 20 reviews look automated and lazy. Track openings in `response_templates_used` and rotate.

6. **NEVER offer incentives for reviews.** Not in responses, not in solicitation, not ever. This violates platform ToS and can result in review removal, profile penalties, or account suspension.

7. **Track the review link.** The `google_review_link` in config is the single most important URL for the business's reputation. Remind the owner to include it on invoices, receipts, email signatures, and leave-behind cards.

8. **Respond to negative reviews first.** When multiple reviews are pending, always draft negative review responses before positive ones. Speed matters — a negative review sitting without a response for a week does compounding damage.

9. **Keep response tone consistent with brand.** A plumber's responses should sound like a plumber, not a PR firm. Friendly, direct, human. No corporate jargon.

10. **Never mention competitors in responses.** Even if the reviewer compares the business to a competitor, the response should focus only on the reviewer's experience and the business's commitment to quality.

---

## File Operations Summary

| Operation | File | Action |
|-----------|------|--------|
| Read existing reviews | `workspace/business/reviews.json` | READ |
| Add new reviews | `workspace/business/reviews.json` | READ then WRITE |
| Update response status | `workspace/business/reviews.json` | READ then WRITE |
| Read business config | `workspace/business/config.json` | READ |
| Update review settings | `workspace/business/config.json` | READ then WRITE |
| Track check state | `workspace/business/.review-check-state.json` | READ then WRITE |
| Store competitor data | `workspace/business/competitors.json` | READ then WRITE |
| Generate dashboard | `workspace/reputation-dashboard.html` | WRITE (canvas page) |

**Always read before writing.** Never overwrite the entire file blindly — read, parse, modify the specific fields, write back. Preserve all existing review entries. Never remove a review from the array.
