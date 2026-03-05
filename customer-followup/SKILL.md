---
name: customer-followup
description: "Post-service customer follow-up pipeline — satisfaction checks, review requests, referral offers, maintenance plan pitches. Automated lifecycle for local service companies."
metadata: {"openclaw": {"emoji": "🔄"}}
---

# Customer Follow-Up Pipeline

Automated post-service follow-up system for local service companies. Runs a 4-stage quality-gated pipeline after every completed job: satisfaction check, review request, referral offer, and maintenance plan pitch.

## When to Use

Use this skill when:
- A new completed job appears in `workspace/business/jobs.json`
- The user asks about follow-ups, reviews, or referrals
- On heartbeat — check for due follow-up actions
- The user says "any follow-ups due?" or "follow up with [name]"
- The user wants to see the follow-up pipeline status

## Overview

Every completed job triggers a 4-stage pipeline. Each stage has a quality gate — the pipeline only advances when the previous stage succeeds. If a customer is dissatisfied at Stage 1, the pipeline STOPS and the business owner gets alerted. No customer who reported a problem ever receives a review request or sales pitch.

```
JOB COMPLETED
    |
    v
[Stage 1] Satisfaction Check (Day 1)
    |
    +-- NOT satisfied --> STOP. Alert owner. Create remediation task.
    |
    +-- Satisfied -->
    v
[Stage 2] Review Request (Day 2-3)
    |
    v
[Stage 3] Referral Offer (Day 7)
    |
    v
[Stage 4] Maintenance Plan Pitch (Day 14-30)
    |
    v
PIPELINE COMPLETE
```

---

## Data Files

### Input Files (Read)

**`workspace/business/jobs.json`** — Completed jobs trigger the pipeline.
```json
{
  "jobs": [
    {
      "id": "JOB-2026-0301",
      "customer_id": "CUST-001",
      "service_type": "water-heater-replacement",
      "description": "50-gallon gas water heater replacement",
      "status": "completed",
      "completed_date": "2026-03-01",
      "technician": "Mike",
      "total": 2450.00,
      "notes": "Old unit was leaking. Installed Rheem Performance Plus."
    }
  ]
}
```

**`workspace/business/customers.json`** — Customer contact info and preferences.
```json
{
  "customers": [
    {
      "id": "CUST-001",
      "name": "John Smith",
      "phone": "555-0150",
      "email": "john.smith@email.com",
      "address": "1234 Oak St, Phoenix AZ 85001",
      "preferred_contact": "phone",
      "opted_out_followup": false,
      "has_maintenance_plan": false,
      "lifetime_value": 4900.00,
      "jobs_completed": 2,
      "notes": "Referred by neighbor. Prefers morning calls."
    }
  ]
}
```

**`workspace/business/config.json`** — Business settings, timing, incentives.
```json
{
  "company": {
    "name": "Desert Cool HVAC",
    "phone": "555-0100",
    "google_review_link": "https://g.page/r/CxxxxYYYYzzzz/review",
    "service_types": ["hvac-repair", "hvac-install", "water-heater-replacement", "duct-cleaning", "maintenance"]
  },
  "followup": {
    "timing": {
      "satisfaction_check_days": 1,
      "review_request_days": 3,
      "referral_offer_days": 7,
      "maintenance_pitch_days": 21
    },
    "max_attempts": {
      "satisfaction_check": 3,
      "review_request": 2,
      "referral_offer": 1,
      "maintenance_pitch": 1
    },
    "quiet_hours": {
      "start": "19:00",
      "end": "09:00"
    },
    "min_attempt_spacing_hours": 24,
    "referral_incentive": "$50 off their next service",
    "maintenance_plan": {
      "price": "29.99/month",
      "benefits": [
        "Two tune-ups per year",
        "Priority scheduling",
        "15% off all repairs",
        "No overtime charges"
      ]
    }
  }
}
```

### Output File (Read/Write)

**`workspace/business/followups.json`** — Pipeline state for every customer follow-up.

```json
{
  "followups": [
    {
      "id": "FU-2026-0301-CUST001",
      "job_id": "JOB-2026-0301",
      "customer_id": "CUST-001",
      "customer_name": "John Smith",
      "customer_phone": "555-0150",
      "service_type": "water-heater-replacement",
      "service_description": "50-gallon gas water heater replacement",
      "job_completed_date": "2026-03-01",
      "pipeline_status": "active",
      "current_stage": "review_request",
      "stages": {
        "satisfaction_check": {
          "status": "completed",
          "attempts": 1,
          "last_attempt_date": "2026-03-02",
          "outcome": "satisfied",
          "notes": "Customer said everything is working great, water heats up fast.",
          "completed_date": "2026-03-02"
        },
        "review_request": {
          "status": "pending",
          "attempts": 0,
          "due_date": "2026-03-04",
          "outcome": null,
          "notes": null
        },
        "referral_offer": {
          "status": "not_started",
          "due_date": "2026-03-08",
          "attempts": 0,
          "outcome": null,
          "notes": null
        },
        "maintenance_pitch": {
          "status": "not_started",
          "due_date": "2026-03-22",
          "attempts": 0,
          "outcome": null,
          "notes": null
        }
      },
      "created_date": "2026-03-01",
      "completed_date": null
    }
  ]
}
```

**Pipeline status values:** `active`, `completed`, `stopped`, `opted_out`
**Stage status values:** `not_started`, `pending`, `in_progress`, `completed`, `failed`, `skipped`
**Stage outcome values (satisfaction):** `satisfied`, `unsatisfied`, `no_answer`, `voicemail`
**Stage outcome values (review):** `review_left`, `link_sent`, `declined`, `no_answer`
**Stage outcome values (referral):** `interested`, `not_interested`, `no_answer`
**Stage outcome values (maintenance):** `signed_up`, `interested`, `declined`, `already_has_plan`, `no_answer`

---

## Quality Gates and Safety Rules

These are NON-NEGOTIABLE. Never bypass them.

### 1. Quiet Hours
```
BEFORE any customer contact:
  current_time = now()
  quiet_start = config.followup.quiet_hours.start  (default: 19:00)
  quiet_end = config.followup.quiet_hours.end      (default: 09:00)

  IF current_time >= quiet_start OR current_time < quiet_end:
      DO NOT CONTACT. Say: "It's outside calling hours. I'll follow up with [name] tomorrow morning after 9am."
      STOP.
```

### 2. Opt-Out Check
```
BEFORE any customer contact:
  customer = lookup customer_id in customers.json

  IF customer.opted_out_followup == true:
      Mark pipeline_status = "opted_out"
      Say: "[Name] has opted out of follow-ups. Skipping."
      STOP. Do not contact. Do not advance any stages.
```

### 3. Satisfaction Gate
```
IF stages.satisfaction_check.outcome == "unsatisfied":
    pipeline_status = "stopped"
    DO NOT advance to Stage 2, 3, or 4. EVER.
    Alert the owner immediately.
    Create a remediation note in the followup entry.
```

### 4. Attempt Limits
```
Each stage has a max attempt count from config.followup.max_attempts.
Default: satisfaction=3, review=2, referral=1, maintenance=1

IF attempts >= max_attempts AND outcome is still null or "no_answer":
    Mark stage status = "failed"
    Advance to next stage (EXCEPT if satisfaction failed — pipeline stops)
    Say: "I've tried reaching [name] [X] times for [stage]. Moving on."
```

### 5. Attempt Spacing
```
IF last_attempt_date exists:
    hours_since = now() - last_attempt_date
    IF hours_since < config.followup.min_attempt_spacing_hours (default: 24):
        DO NOT CONTACT. Say: "Too soon to retry [name]. Last attempt was [X] hours ago."
        STOP.
```

### 6. Maintenance Plan Check
```
BEFORE Stage 4:
  customer = lookup customer_id in customers.json

  IF customer.has_maintenance_plan == true:
      Mark maintenance_pitch status = "skipped", outcome = "already_has_plan"
      Say: "[Name] already has a maintenance plan. Skipping the pitch."
      Mark pipeline as completed.
```

---

## The Pipeline — Stage by Stage

### STAGE 1: Satisfaction Check

**When:** Day after service completion (config: `satisfaction_check_days`)
**Goal:** Confirm the customer is happy. Catch problems early.
**Max attempts:** 3 (default)

#### Voice Scripts

**Opening — first attempt:**
> "Hey [name], it's [agent name] from [company]. Just checking in on that [service description] we did yesterday. Everything working good for you?"

**Opening — second attempt:**
> "Hi [name], it's [company] again. I tried reaching you yesterday about the [service type] work. Just wanted to make sure everything's running smoothly. Got a quick minute?"

**Opening — third attempt:**
> "Hey [name], [company] here — last time I'll bug you, promise. Just wanted to confirm that [service description] is working well. If you have any issues at all, give us a call at [company phone]."

**If customer says YES / satisfied:**
> "Awesome, glad to hear it! [Technician] does great work. If anything comes up down the road, don't hesitate to call us. We've got you covered."

Record: `outcome: "satisfied"`, advance `current_stage` to `review_request`, calculate `review_request.due_date` based on config timing.

**If customer says NO / has a problem:**
> "I'm really sorry to hear that. Can you tell me what's going on? I want to make sure we get this taken care of for you right away."

Listen to their issue. Record it in the stage notes. Then:
> "I'm going to have [owner/manager name] reach out to you personally to get this resolved. We don't consider a job done until you're completely satisfied."

Record: `outcome: "unsatisfied"`, `pipeline_status: "stopped"`. Include detailed notes about what the customer reported.

**IMMEDIATELY report to the owner:**
> "ALERT: [customer name] reported a problem with their [service type] job (ID: [job_id]). Issue: [brief description]. Pipeline stopped — no further marketing contact. They need a callback to resolve this."

**If no answer / voicemail:**
> Leave a brief voicemail: "Hey [name], it's [company]. Just checking in on the work we did for you. Hope everything's great. If you have any questions, give us a ring at [company phone]. I'll try you again tomorrow."

Record: `outcome: "voicemail"` or `"no_answer"`, increment attempts, set `last_attempt_date`.

---

### STAGE 2: Review Request

**When:** 2-3 days after service (config: `review_request_days`)
**Prerequisite:** Stage 1 outcome must be `"satisfied"`
**Goal:** Get a Google review while the positive experience is fresh.
**Max attempts:** 2 (default)

#### Voice Scripts

**First attempt — natural transition from satisfaction:**
> "By the way [name], since things went well — we'd really appreciate it if you could leave us a quick Google review. It makes a huge difference for a small business like ours. I can text you the direct link so it takes like 30 seconds."

**First attempt — standalone call:**
> "Hey [name], it's [agent name] from [company]. Glad your [service type] is working well! I was hoping I could ask a small favor — would you be willing to leave us a quick Google review? A couple sentences goes a long way for us."

**If customer agrees:**
> "You're the best, thank you! I'm sending you the link right now. It'll take you straight to the review page — super easy."

Provide the review link from `config.json`. Record: `outcome: "link_sent"`.

**If customer declines:**
> "No worries at all, I totally understand. Just glad you're happy with the work. Remember, we're always here if you need anything."

Record: `outcome: "declined"`, advance to next stage.

**Second attempt (if first was no answer):**
> "Hi [name], [company] here. I sent you a message the other day — just wondering if you'd have a sec to leave us a Google review. Totally understand if you're busy, but it really does help us out."

**After review is confirmed left:**
Record: `outcome: "review_left"`. This is the best outcome. Note it for the owner's reporting.

---

### STAGE 3: Referral Offer

**When:** About 1 week after service (config: `referral_offer_days`)
**Goal:** Turn satisfied customers into a referral source.
**Max attempts:** 1 (default)

#### Voice Scripts

> "Hey [name], [agent name] from [company]. Quick thing — if you know anyone who needs [service type generalized, e.g., 'plumbing work' or 'HVAC service'], we're offering [referral incentive from config] when they mention your name. No pressure at all, just wanted to let you know it's there."

**If customer says they know someone:**
> "That's great! Just have them call us at [company phone] and mention your name. We'll make sure you get your [incentive]. And we'll take great care of them just like we did for you."

Record: `outcome: "interested"`, add any names/details to notes.

**If not interested:**
> "No problem! Just thought I'd mention it. Thanks again for choosing us, [name]."

Record: `outcome: "not_interested"`.

---

### STAGE 4: Maintenance Plan Pitch

**When:** 2-4 weeks after service (config: `maintenance_pitch_days`)
**Prerequisite:** Customer does NOT already have a maintenance plan (check `customers.json`)
**Goal:** Offer ongoing value and lock in recurring revenue.
**Max attempts:** 1 (default)

#### Voice Scripts

> "Hey [name], [agent name] from [company]. I wanted to let you know about something that might save you some money down the road. We offer a maintenance plan for [price from config] a month. It includes [read benefits from config — e.g., 'two tune-ups a year, priority scheduling, 15% off repairs, and no overtime charges']. Helps keep your [system type] running efficiently and catches small problems before they turn into big ones. Sound like something you'd be interested in?"

**If interested:**
> "Great! I can get you signed up right now or have someone walk you through the details — whatever works best for you. Which do you prefer?"

Record: `outcome: "interested"` or `"signed_up"`. If they sign up, update `customers.json` to set `has_maintenance_plan: true`.

**If declined:**
> "Totally understand. The offer's always there if you change your mind. Thanks for being a great customer, [name]. Call us anytime."

Record: `outcome: "declined"`.

**After Stage 4 completes (any outcome):**
Set `pipeline_status: "completed"`, `completed_date: today`.

---

## Automatic Pipeline Creation

On every heartbeat or when checking jobs, scan `workspace/business/jobs.json` for completed jobs that do NOT have a corresponding entry in `followups.json`.

```
FOR each job in jobs.json WHERE status == "completed":
    followup_exists = any entry in followups.json with job_id == job.id

    IF NOT followup_exists:
        customer = lookup job.customer_id in customers.json

        IF customer.opted_out_followup == true:
            SKIP. Log: "Skipping follow-up for [name] — opted out."
            CONTINUE.

        Create new followup entry:
            id: "FU-{job.completed_date formatted YYYY-MMDD}-{customer.id}"
            job_id: job.id
            customer_id: job.customer_id
            customer_name: customer.name
            customer_phone: customer.phone
            service_type: job.service_type
            service_description: job.description
            job_completed_date: job.completed_date
            pipeline_status: "active"
            current_stage: "satisfaction_check"
            stages:
                satisfaction_check:
                    status: "pending"
                    attempts: 0
                    due_date: job.completed_date + config.followup.timing.satisfaction_check_days
                review_request:
                    status: "not_started"
                    due_date: job.completed_date + config.followup.timing.review_request_days
                referral_offer:
                    status: "not_started"
                    due_date: job.completed_date + config.followup.timing.referral_offer_days
                maintenance_pitch:
                    status: "not_started"
                    due_date: job.completed_date + config.followup.timing.maintenance_pitch_days
            created_date: today

        Report: "New follow-up created for [name] after their [service description] job. Satisfaction check due [due_date]."

        Write updated followups.json.
```

---

## Heartbeat Integration

On each heartbeat cycle, run this check:

```
1. Load followups.json
2. Filter to pipeline_status == "active"
3. For each active followup:
    a. Get current_stage
    b. Check if that stage's due_date <= today
    c. Check quiet hours (do NOT execute outside 9am-7pm)
    d. Check attempt spacing (24hr minimum)
    e. Check attempt limits
    f. If all gates pass → execute the stage action
    g. Update followups.json with results

4. Also scan jobs.json for new completed jobs without followup entries (see above)

5. Report summary:
   "Follow-up check: [N] actions due today. Contacted [name] for satisfaction check — they're happy. [Name2]'s review request is due tomorrow."
```

**Heartbeat reporting should be concise.** Do not read out every field. Summarize:
- How many follow-ups are active
- What actions were taken
- What's coming up next
- Any alerts (unsatisfied customers, failed contacts)

---

## Manual Triggers

### "Any follow-ups due?"
Read `followups.json`. List all entries where `pipeline_status == "active"` and any stage has `due_date <= today` and `status` is `pending` or `not_started`.

Format the response conversationally:
> "You've got 3 follow-ups due today:
> 1. **John Smith** — review request (water heater job from March 1st)
> 2. **Sarah Johnson** — satisfaction check (AC repair from yesterday)
> 3. **Mike Davis** — referral offer (duct cleaning from last week)
>
> Want me to start working through them?"

### "Follow up with [customer name]"
Find the active followup for that customer. Execute the next pending stage regardless of due date (but still respect quiet hours, opt-out, and satisfaction gates).

> "Following up with John Smith now. He's on Stage 2 — review request. His satisfaction check went well on Monday."
> [Execute Stage 2 script]

### "Skip [stage] for [customer]"
Mark the specified stage as `status: "skipped"`, advance `current_stage` to the next stage. If skipping satisfaction check, ask for confirmation because it means bypassing the quality gate:

> "Are you sure you want to skip the satisfaction check for John Smith? That means we'd move straight to requesting a review without confirming he's happy. Should I go ahead?"

### "Show follow-up pipeline" / "Show follow-up dashboard"
Generate a canvas page — see Canvas Page section below.

### "Follow-up report" / "How are follow-ups going?"
Provide aggregate stats:

> "Follow-up pipeline report:
> - **Active:** 8 customers in the pipeline
> - **Completed:** 23 follow-up sequences finished
> - **Satisfaction rate:** 95% (22 of 23 were satisfied)
> - **Reviews collected:** 14 out of 22 asked (64% conversion)
> - **Referrals generated:** 5 active referrals
> - **Maintenance plans sold:** 3 new sign-ups
>
> Next up: 2 satisfaction checks due tomorrow, 1 review request due Thursday."

---

## Canvas Page: Follow-Up Pipeline Dashboard

When the user asks to see the pipeline, generate `follow-up-pipeline.html` as a canvas page.

**Requirements:**
- Dark theme, inline CSS only (NO external stylesheets, NO CDN scripts)
- All JavaScript inline
- postMessage navigation for interactive elements
- Mobile-friendly layout

**The page must show:**

1. **Pipeline Funnel** — Visual funnel showing counts at each stage
2. **Due Today** — Cards for each follow-up action due today with customer name, service type, stage, and an "Execute" button
3. **Active Pipelines** — List of all active follow-ups with current stage indicator
4. **Success Metrics** — Satisfaction rate, review conversion rate, referral count, maintenance plan conversions
5. **Recently Completed** — Last 5 completed pipelines with outcomes

**Canvas page template:**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Follow-Up Pipeline</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0a0a0f;
    color: #e0e0e0;
    padding: 20px;
    min-height: 100vh;
  }
  .header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #1a1a2e;
  }
  .header h1 { font-size: 1.8rem; color: #fff; margin-bottom: 5px; }
  .header .subtitle { color: #888; font-size: 0.9rem; }
  .metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
  }
  .metric-card {
    background: #12121a;
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
  }
  .metric-card .value {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 4px;
  }
  .metric-card .label { color: #888; font-size: 0.8rem; text-transform: uppercase; }
  .metric-card.green .value { color: #4ade80; }
  .metric-card.blue .value { color: #60a5fa; }
  .metric-card.yellow .value { color: #facc15; }
  .metric-card.purple .value { color: #c084fc; }
  .funnel {
    background: #12121a;
    border: 1px solid #1a1a2e;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 30px;
  }
  .funnel h2 { font-size: 1.1rem; margin-bottom: 20px; color: #fff; }
  .funnel-stage {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
  }
  .funnel-bar {
    height: 36px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    padding: 0 14px;
    font-weight: 600;
    font-size: 0.85rem;
    min-width: 60px;
    transition: width 0.5s ease;
  }
  .funnel-label {
    min-width: 160px;
    font-size: 0.85rem;
    color: #aaa;
    margin-right: 12px;
  }
  .funnel-count {
    margin-left: 10px;
    color: #aaa;
    font-size: 0.85rem;
  }
  .stage-satisfaction .funnel-bar { background: #4ade80; color: #0a0a0f; }
  .stage-review .funnel-bar { background: #60a5fa; color: #0a0a0f; }
  .stage-referral .funnel-bar { background: #facc15; color: #0a0a0f; }
  .stage-maintenance .funnel-bar { background: #c084fc; color: #0a0a0f; }
  .section {
    background: #12121a;
    border: 1px solid #1a1a2e;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
  }
  .section h2 {
    font-size: 1.1rem;
    margin-bottom: 16px;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .due-card {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .due-card .info h3 { font-size: 1rem; color: #fff; margin-bottom: 4px; }
  .due-card .info p { font-size: 0.8rem; color: #888; }
  .due-card .stage-badge {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  .badge-satisfaction { background: rgba(74,222,128,0.15); color: #4ade80; }
  .badge-review { background: rgba(96,165,250,0.15); color: #60a5fa; }
  .badge-referral { background: rgba(250,204,21,0.15); color: #facc15; }
  .badge-maintenance { background: rgba(192,132,252,0.15); color: #c084fc; }
  .btn-execute {
    background: #4ade80;
    color: #0a0a0f;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.8rem;
    cursor: pointer;
  }
  .btn-execute:hover { background: #22c55e; }
  .pipeline-item {
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #1a1a2e;
  }
  .pipeline-item:last-child { border-bottom: none; }
  .pipeline-stages {
    display: flex;
    gap: 4px;
    margin-left: auto;
  }
  .pipeline-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #333;
  }
  .pipeline-dot.done { background: #4ade80; }
  .pipeline-dot.active { background: #60a5fa; animation: pulse 1.5s infinite; }
  .pipeline-dot.upcoming { background: #333; }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
  .empty-state { text-align: center; color: #555; padding: 30px; font-size: 0.9rem; }
</style>
</head>
<body>

<div class="header">
  <h1>Follow-Up Pipeline</h1>
  <div class="subtitle">Post-service customer lifecycle &mdash; COMPANY_NAME</div>
</div>

<!-- METRICS ROW -->
<div class="metrics-row">
  <div class="metric-card green">
    <div class="value">ACTIVE_COUNT</div>
    <div class="label">Active</div>
  </div>
  <div class="metric-card blue">
    <div class="value">SATISFACTION_RATE%</div>
    <div class="label">Satisfaction</div>
  </div>
  <div class="metric-card yellow">
    <div class="value">REVIEW_RATE%</div>
    <div class="label">Review Rate</div>
  </div>
  <div class="metric-card purple">
    <div class="value">PLANS_SOLD</div>
    <div class="label">Plans Sold</div>
  </div>
</div>

<!-- FUNNEL -->
<div class="funnel">
  <h2>Pipeline Funnel</h2>
  <div class="funnel-stage stage-satisfaction">
    <span class="funnel-label">Satisfaction Check</span>
    <div class="funnel-bar" style="width: SATISFACTION_WIDTH%;">SATISFACTION_COUNT</div>
  </div>
  <div class="funnel-stage stage-review">
    <span class="funnel-label">Review Request</span>
    <div class="funnel-bar" style="width: REVIEW_WIDTH%;">REVIEW_COUNT</div>
  </div>
  <div class="funnel-stage stage-referral">
    <span class="funnel-label">Referral Offer</span>
    <div class="funnel-bar" style="width: REFERRAL_WIDTH%;">REFERRAL_COUNT</div>
  </div>
  <div class="funnel-stage stage-maintenance">
    <span class="funnel-label">Maintenance Pitch</span>
    <div class="funnel-bar" style="width: MAINTENANCE_WIDTH%;">MAINTENANCE_COUNT</div>
  </div>
</div>

<!-- DUE TODAY -->
<div class="section">
  <h2>Due Today</h2>
  <!-- Populate with due-card elements for each follow-up due today -->
  <!-- Example: -->
  <div class="due-card">
    <div class="info">
      <h3>CUSTOMER_NAME</h3>
      <p>SERVICE_DESCRIPTION &mdash; completed JOB_DATE</p>
    </div>
    <span class="stage-badge badge-STAGE_CLASS">STAGE_LABEL</span>
    <button class="btn-execute" onclick="window.parent.postMessage({type:'canvas-action',action:'speak',text:'Follow up with CUSTOMER_NAME'},'*')">Execute</button>
  </div>
  <!-- If nothing due: -->
  <!-- <div class="empty-state">No follow-ups due today. Next action: NEXT_DUE_DESCRIPTION</div> -->
</div>

<!-- ACTIVE PIPELINES -->
<div class="section">
  <h2>Active Pipelines</h2>
  <!-- Populate with pipeline-item elements -->
  <!-- Example: -->
  <div class="pipeline-item">
    <div>
      <strong>CUSTOMER_NAME</strong>
      <span style="color:#888;font-size:0.8rem;margin-left:8px;">SERVICE_TYPE</span>
    </div>
    <div class="pipeline-stages">
      <div class="pipeline-dot done" title="Satisfaction: completed"></div>
      <div class="pipeline-dot active" title="Review: pending"></div>
      <div class="pipeline-dot upcoming" title="Referral: not started"></div>
      <div class="pipeline-dot upcoming" title="Maintenance: not started"></div>
    </div>
  </div>
</div>

<!-- RECENTLY COMPLETED -->
<div class="section">
  <h2>Recently Completed</h2>
  <!-- Populate with last 5 completed pipelines showing final outcomes -->
</div>

<script>
  // Navigation: close dashboard
  function closeDashboard() {
    window.parent.postMessage({type:'canvas-action', action:'close'}, '*');
  }
  // Refresh: tell agent to regenerate this page with fresh data
  function refreshDashboard() {
    window.parent.postMessage({type:'canvas-action', action:'speak', text:'Show follow-up pipeline'}, '*');
  }
</script>
</body>
</html>
```

**When generating this page, replace ALL placeholder values** (COMPANY_NAME, ACTIVE_COUNT, etc.) with real data from `followups.json` and `config.json`. Calculate percentages dynamically. Generate one `due-card` per due item, one `pipeline-item` per active pipeline. The template above is a structural guide — the actual output must contain real data.

---

## Creating a Follow-Up Entry (Step by Step)

When you detect a new completed job without a follow-up:

1. Read `workspace/business/jobs.json` — find the completed job
2. Read `workspace/business/customers.json` — find the customer record
3. Check `opted_out_followup` — if true, skip
4. Read `workspace/business/config.json` — get timing settings
5. Read `workspace/business/followups.json` — confirm no existing entry for this job
6. Calculate due dates:
   - `satisfaction_check.due_date` = `job.completed_date` + `timing.satisfaction_check_days`
   - `review_request.due_date` = `job.completed_date` + `timing.review_request_days`
   - `referral_offer.due_date` = `job.completed_date` + `timing.referral_offer_days`
   - `maintenance_pitch.due_date` = `job.completed_date` + `timing.maintenance_pitch_days`
7. Build the followup object (see schema above)
8. Append to `followups.followups` array
9. Write updated `followups.json`
10. Report to the owner

---

## Executing a Follow-Up Stage (Step by Step)

1. Read `followups.json` — find the active entry
2. Identify `current_stage`
3. Run quality gate checks IN ORDER:
   a. Quiet hours check
   b. Opt-out check
   c. Satisfaction gate (if past Stage 1)
   d. Attempt limit check
   e. Attempt spacing check
4. If all gates pass:
   a. Use the appropriate voice script for the stage and attempt number
   b. Conduct the conversation naturally — listen to the customer's response
   c. Determine the outcome based on what they say
   d. Update the stage: `status`, `attempts`, `last_attempt_date`, `outcome`, `notes`
   e. If stage completed successfully, advance `current_stage` to next stage
   f. If all stages complete, set `pipeline_status: "completed"`, `completed_date: today`
5. Write updated `followups.json`
6. Report results to the owner

---

## Conversation Style Guide

**DO:**
- Use the customer's first name
- Reference the specific work done ("that water heater we put in" not "your recent service")
- Sound like a friendly human, not a script reader
- Keep it brief — respect their time
- Match their energy — if they're chatty, be chatty; if they're short, be efficient
- Use contractions (it's, we'd, you're, don't)
- Pause and listen — let them talk

**DO NOT:**
- Use job IDs, customer IDs, or internal codes when speaking to customers
- Say "Dear Mr./Mrs." — use first names
- Read a script word-for-word if the conversation goes a different direction — adapt
- Push if they seem uninterested — gracefully move on
- Contact about multiple stages in one call (one purpose per contact)
- Use corporate jargon ("we value your business", "your satisfaction is our priority")
- Lie about why you're calling

**Tone calibration by stage:**
| Stage | Tone | Energy |
|-------|------|--------|
| Satisfaction Check | Warm, caring, concerned | Medium — genuine check-in |
| Review Request | Grateful, slightly asking a favor | Light — no pressure |
| Referral Offer | Casual, informational | Low-key — just letting them know |
| Maintenance Pitch | Helpful, advisory | Consultative — saving them money |

---

## Edge Cases

### Customer calls back before their follow-up is due
If a customer proactively contacts the company and mentions the recent service:
- Treat the conversation as an opportunity to complete the current pending stage
- If they express satisfaction, mark Stage 1 complete and proceed normally
- Update the followup entry with what happened

### Multiple jobs for the same customer
Each job gets its own follow-up pipeline. However:
- Do NOT run two follow-ups simultaneously for the same customer
- If a new job completes while an old pipeline is still active, queue the new one (set `pipeline_status: "queued"`) and start it when the current one finishes
- Never contact a customer about two different jobs in the same day

### Customer requests to stop follow-ups
If at any point a customer says "stop calling" or "don't contact me again":
- Immediately set `pipeline_status: "opted_out"` on the current followup
- Set `opted_out_followup: true` in `customers.json`
- Confirm: "Absolutely, I've made a note. You won't hear from us unless you reach out. Thanks, [name]."
- Report to owner: "[Name] opted out of follow-up calls. Updated their record."

### Config file missing or incomplete
If `config.json` doesn't exist or is missing fields, use these defaults:
- `satisfaction_check_days`: 1
- `review_request_days`: 3
- `referral_offer_days`: 7
- `maintenance_pitch_days`: 21
- `quiet_hours.start`: "19:00"
- `quiet_hours.end`: "09:00"
- `min_attempt_spacing_hours`: 24
- `max_attempts`: satisfaction=3, review=2, referral=1, maintenance=1
- `referral_incentive`: "$25 off their next service"
- `maintenance_plan.price`: "29.99/month"
- `maintenance_plan.benefits`: ["Annual tune-up", "Priority scheduling", "10% off repairs"]

### Data files don't exist yet
If `followups.json` doesn't exist, create it with `{"followups": []}`.
If `jobs.json` or `customers.json` doesn't exist, inform the owner:
> "I need job and customer data to run follow-ups. Please set up workspace/business/jobs.json and workspace/business/customers.json. I can create templates for you if you'd like."

---

## Reporting to the Owner

At the end of each day (or on demand), provide a follow-up summary:

> "Today's follow-up report:
> - Called John Smith (satisfaction check) — he's happy with the water heater. Review request going out Thursday.
> - Left voicemail for Sarah Johnson (satisfaction check, attempt 2 of 3). I'll try again tomorrow.
> - Sent Mike Davis the Google review link. He said he'd do it tonight.
> - ALERT: Tom Wilson reported his AC is making a noise after our repair. Pipeline stopped. He needs a callback.
>
> Pipeline stats: 12 active, 4 due tomorrow, 87% satisfaction rate this month."

---

## File Operations Summary

| Operation | File | Action |
|-----------|------|--------|
| Check for new jobs | `workspace/business/jobs.json` | READ |
| Look up customer | `workspace/business/customers.json` | READ |
| Get config/timing | `workspace/business/config.json` | READ |
| Read pipeline state | `workspace/business/followups.json` | READ |
| Create follow-up entry | `workspace/business/followups.json` | READ then WRITE |
| Update stage results | `workspace/business/followups.json` | READ then WRITE |
| Mark opted out | `workspace/business/customers.json` | READ then WRITE |
| Mark plan signed | `workspace/business/customers.json` | READ then WRITE |
| Generate dashboard | `workspace/follow-up-pipeline.html` | WRITE (canvas page) |

**Always read before writing.** Never overwrite the entire file — read, parse, modify, write back.

---

## Integration with Other Skills

- **AgentMail:** If the customer's `preferred_contact` is `"email"`, use the agentmail skill to send follow-up emails instead of voice calls. Adapt the voice scripts to email format — keep the same tone but written.
- **Suno Music:** For a creative touch, the referral offer could include a personalized jingle or thank-you song. Optional and only if the company's brand supports it.
- **Canvas Design:** The pipeline dashboard can be enhanced with the canvas-design skill for a more polished look.
- **Serper Search:** If you need to verify a customer left a Google review, use serper to search for the business and check recent reviews.
