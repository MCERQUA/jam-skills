---
name: service-scheduler
description: "Appointment booking, technician scheduling, and job dispatch for local service companies. Handles intake, triage, scheduling, confirmations, and day-of dispatch."
metadata: {"openclaw": {"emoji": "📅"}}
---

# Service Scheduler Skill

## Overview

Complete appointment booking, technician scheduling, and job dispatch system for local service companies. Handles the full lifecycle: customer intake, urgency triage, technician matching, slot scheduling, confirmation, reminders, rescheduling, cancellations, and day-of dispatch coordination.

This is the operational backbone. Every inbound call asking for service flows through this skill. Every technician's day starts with the schedule this skill produces.

### What This Skill Does

- Captures customer intake information via natural voice conversation
- Classifies urgency and routes accordingly (emergency dispatch vs. scheduled appointment)
- Matches the right technician based on skills, availability, location, and load balance
- Books appointments into time windows and prevents double-booking
- Confirms appointments back to the customer with full details
- Manages rescheduling and cancellations
- Generates a visual schedule board as a canvas page
- Provides day-of dispatch briefings for technicians
- Tracks all jobs from scheduled through completed

### Data Files

| File | Purpose | Access |
|------|---------|--------|
| `workspace/business/config.json` | Tech roster, business hours, service areas, company info | READ |
| `workspace/business/jobs.json` | All scheduled, in-progress, and completed jobs | READ/WRITE |

---

## Business Configuration

**File:** `workspace/business/config.json`

This file MUST exist before the scheduler can operate. If it does not exist, walk the owner through setup (see Setup Guide at the end).

The scheduler uses the following sections from `config.json`:

```json
{
  "business_name": "ABC Plumbing",
  "business_phone": "555-0100",
  "owner_name": "Mike",
  "timezone": "America/Phoenix",
  "business_hours": {
    "start": "08:00",
    "end": "17:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
  },
  "service_area_zip_codes": [
    "85001", "85002", "85003", "85004", "85005", "85006", "85007", "85008",
    "85009", "85010", "85012", "85013", "85014", "85015", "85016", "85017",
    "85018", "85019", "85020", "85021", "85022", "85023", "85024", "85028",
    "85029", "85031", "85032", "85033", "85034", "85035", "85040", "85041",
    "85042", "85043", "85044", "85045", "85048", "85050", "85051", "85053",
    "85054", "85083", "85085", "85086", "85087"
  ],
  "technicians": [
    {
      "name": "Mike",
      "phone": "555-0101",
      "skills": ["plumbing-general", "water-heater", "repipe", "gas-line", "sewer", "emergency"],
      "on_call": true,
      "max_jobs_per_day": 5,
      "home_zip": "85003"
    },
    {
      "name": "Dave",
      "phone": "555-0102",
      "skills": ["plumbing-general", "drain-cleaning", "faucet", "toilet", "garbage-disposal"],
      "on_call": false,
      "max_jobs_per_day": 6,
      "home_zip": "85016"
    },
    {
      "name": "Carlos",
      "phone": "555-0103",
      "skills": ["plumbing-general", "water-heater", "drain-cleaning", "faucet", "toilet", "sewer"],
      "on_call": false,
      "max_jobs_per_day": 5,
      "home_zip": "85022"
    }
  ],
  "services": {
    "faucet-replacement": {"display_name": "Faucet Replacement", "avg_duration_hours": 1.5, "skill_required": "faucet"},
    "water-heater-install": {"display_name": "Water Heater Install", "avg_duration_hours": 3, "skill_required": "water-heater"},
    "drain-cleaning": {"display_name": "Drain Cleaning", "avg_duration_hours": 1.5, "skill_required": "drain-cleaning"},
    "toilet-repair": {"display_name": "Toilet Repair", "avg_duration_hours": 1, "skill_required": "toilet"},
    "garbage-disposal": {"display_name": "Garbage Disposal Install/Repair", "avg_duration_hours": 1.5, "skill_required": "garbage-disposal"},
    "sewer-line": {"display_name": "Sewer Line Repair", "avg_duration_hours": 4, "skill_required": "sewer"},
    "repipe": {"display_name": "Whole-House Repipe", "avg_duration_hours": 8, "skill_required": "repipe"},
    "gas-line": {"display_name": "Gas Line Work", "avg_duration_hours": 3, "skill_required": "gas-line"},
    "general-plumbing": {"display_name": "General Plumbing", "avg_duration_hours": 2, "skill_required": "plumbing-general"},
    "emergency": {"display_name": "Emergency Service", "avg_duration_hours": 2, "skill_required": "emergency"}
  },
  "scheduling": {
    "default_window_hours": 4,
    "buffer_minutes_between_jobs": 30,
    "max_advance_booking_days": 30
  }
}
```

The agent MUST read `config.json` before performing any scheduling operation. If the config file is missing required sections (technicians, services, business_hours, service_area_zip_codes), inform the owner and offer to set it up.

---

## Job Data Schema

**File:** `workspace/business/jobs.json`

```json
{
  "jobs": [
    {
      "id": "JOB-2026-0305-003",
      "customer_id": "CUST-NEW",
      "customer_name": "Jane Doe",
      "customer_phone": "555-0200",
      "service": "faucet-replacement",
      "description": "Kitchen faucet leaking at base",
      "status": "scheduled",
      "urgency": "standard",
      "scheduled_date": "2026-03-07",
      "scheduled_window": "08:00-12:00",
      "technician": "Mike",
      "address": "789 Pine St, Phoenix, AZ 85003",
      "zip_code": "85003",
      "special_notes": "Gate code 4521, park on street",
      "amount_quoted": null,
      "amount_billed": null,
      "created_at": "2026-03-05T10:30:00",
      "completed_at": null,
      "follow_up_status": "not_started"
    }
  ]
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique ID. Format: `JOB-YYYY-MMDD-XXX` (XXX is sequential per day, zero-padded) |
| `customer_id` | string | no | Links to customer record if CRM exists. Use `CUST-NEW` for first-time callers |
| `customer_name` | string | yes | Full name as provided by customer |
| `customer_phone` | string | yes | Callback phone number — ALWAYS capture this |
| `service` | string | yes | Service type slug (must match a key in `config.json` services) |
| `description` | string | yes | Customer's description of the problem in their own words |
| `status` | string | yes | One of: `scheduled`, `dispatched`, `in_progress`, `completed`, `cancelled`, `no_show` |
| `urgency` | string | yes | One of: `emergency`, `urgent`, `standard`, `flexible` |
| `scheduled_date` | string | yes | ISO date: YYYY-MM-DD |
| `scheduled_window` | string | yes | Time window: `HH:MM-HH:MM` (e.g., `08:00-12:00`, `12:00-17:00`, `ASAP`) |
| `technician` | string | yes | Technician name from config roster |
| `address` | string | yes | Full service address including city, state, zip |
| `zip_code` | string | yes | Extracted from address for service area validation and routing |
| `special_notes` | string | no | Gate codes, parking instructions, pet warnings, access details |
| `amount_quoted` | number | no | Dollar amount quoted (filled after tech visit or estimate) |
| `amount_billed` | number | no | Dollar amount billed (filled on completion) |
| `created_at` | string | yes | ISO datetime when the job was created |
| `completed_at` | string | no | ISO datetime when the job was completed |
| `follow_up_status` | string | yes | One of: `not_started`, `in_progress`, `completed`. Links to customer-followup skill |

### Job ID Generation

Format: `JOB-YYYY-MMDD-XXX` where XXX is a zero-padded sequential number for that calendar day.

```
To generate a new ID for today (2026-03-05):
1. Read all existing jobs from jobs.json
2. Filter to jobs where id starts with "JOB-2026-0305-"
3. Find the highest XXX value (or 0 if none exist)
4. New ID = "JOB-2026-0305-" + (highest + 1), zero-padded to 3 digits

Examples:
  First job of the day:  JOB-2026-0305-001
  Second job:            JOB-2026-0305-002
  Tenth job:             JOB-2026-0305-010
```

### Status Transitions

```
scheduled → dispatched → in_progress → completed
    |                                      |
    +→ cancelled                           +→ follow_up_status transitions
    +→ no_show
```

- `scheduled`: Job is on the books, waiting for the day
- `dispatched`: Day-of, tech has been notified and is en route or will be soon
- `in_progress`: Tech is on site working
- `completed`: Work is done, customer signed off
- `cancelled`: Customer cancelled (capture reason in special_notes)
- `no_show`: Customer was not home / not accessible (capture details)

---

## Intake Workflow

This is the primary flow for inbound customer calls and chats. Every service request starts here.

### Step 1: CAPTURE

Collect information conversationally. Do NOT fire off a list of questions — weave them into natural dialogue. The customer is usually calling because something is broken and they want help, not an interrogation.

**Required information:**
1. **Customer name** — First and last
2. **Phone number** — Callback number (may already have from caller ID)
3. **Address** — Full street address with zip code
4. **Service needed** — What is the problem? Let them describe it, then classify
5. **Urgency indicators** — Listen for keywords that signal emergency or urgency

**Voice script — opening:**
> "Thanks for calling [business_name], this is [agent name]. How can I help you today?"

Let the customer describe their problem. Listen. Do not interrupt. Then confirm what you heard:
> "Okay, so you've got a [restate problem]. Let me get you taken care of. Can I get your name?"

After name:
> "And [name], what's the best number to reach you at?"

After phone:
> "What's the address where you need the work done?"

After address:
> "Got it. And just to make sure I have the full picture — [clarifying question about the issue if needed]?"

**Clarifying questions by service type:**
- **Leak:** "Is it actively dripping right now, or is it a slow leak? Where exactly — under the sink, at the wall, coming through the ceiling?"
- **Drain:** "Is it one drain that's slow, or are multiple drains backing up? Any sewage smell?"
- **Water heater:** "Is it not heating at all, or just not getting hot enough? Gas or electric? How old is the unit?"
- **Toilet:** "Is it running constantly, not flushing, or leaking at the base?"
- **General:** "Can you describe what's happening? When did you first notice it?"

### Step 2: CLASSIFY Urgency

Based on the customer's description, classify the urgency level. This determines scheduling priority and response time.

| Urgency | Criteria | Response |
|---------|----------|----------|
| **EMERGENCY** | Active water leak flooding the home, no heat in winter (below 40F), gas smell, sewage backup into the home, burst pipe, no water to the house | Dispatch IMMEDIATELY. Call on-call tech. No scheduling window — "as fast as possible." |
| **URGENT** | No hot water, AC down in summer (above 100F), main drain clogged (only one drain works), water heater leaking but contained, slab leak suspected | Same-day service. First available slot today. |
| **STANDARD** | Faucet replacement, garbage disposal, running toilet, slow drain (one fixture), minor leak (bucket catches it), outdoor faucet repair | This week. Schedule into a normal window. |
| **FLEXIBLE** | Estimate request, preventive maintenance, cosmetic upgrade, "when you get a chance" language, remodel planning | Best available slot. Can be next week or later. |

**Emergency detection keywords:** "flooding," "water everywhere," "can't stop the water," "smell gas," "sewage," "no heat," "pipe burst," "water pouring," "emergency"

**Urgent detection keywords:** "no hot water," "AC is out," "it's 110 degrees," "totally clogged," "nothing drains," "water heater leaking"

**Flexible detection keywords:** "whenever," "no rush," "estimate," "thinking about," "planning," "just looking," "when you get a chance"

If urgency is ambiguous, ASK:
> "Is this something that needs attention today, or can it wait a few days? I want to make sure we prioritize you correctly."

### Step 3: SERVICE AREA CHECK

Before scheduling, validate the customer's zip code against `config.json` service_area_zip_codes.

```
Extract zip_code from the customer's address.
Look up zip_code in config.service_area_zip_codes.

IF zip_code is IN the list:
    Proceed to scheduling.

IF zip_code is NOT in the list:
    Politely inform the customer.
```

**Out-of-area script:**
> "I'm sorry, we don't currently service that area. The closest area we cover is [find nearest zip from the list]. Would you like me to check if we can make an exception for your situation, or can I suggest another company?"

If the customer wants to check for an exception, note it for the owner:
> "I've got a request from [name] at [address] — that's outside our normal service area. They need [service]. Want me to add them to the schedule anyway?"

Do NOT auto-book out-of-area jobs. Flag them for the owner.

### Step 4: SCHEDULE

Find the best available slot. The matching algorithm considers multiple factors in priority order.

#### Technician Matching Algorithm

```
1. FILTER by skill match:
   - Get the service's skill_required from config.services
   - Filter technicians to those whose skills array includes that skill
   - If no tech has the required skill, alert: "None of our techs are certified for [service]. Let me have [owner] call you back."

2. FILTER by availability:
   - For the target date, check jobs.json for existing jobs assigned to each tech
   - A tech is unavailable if:
     a. They already have max_jobs_per_day scheduled for that date
     b. Their existing job windows overlap with the proposed window
   - Account for buffer_minutes_between_jobs between appointments

3. RANK by location proximity:
   - Compare customer's zip_code with tech's home_zip and their other jobs that day
   - Same zip code = best match
   - Adjacent zip codes = good match
   - Distant zip codes = acceptable but not preferred
   - Goal: minimize drive time, cluster jobs geographically

4. RANK by load balance:
   - Count each tech's jobs for the target date
   - Prefer the tech with fewer jobs (distribute work evenly)
   - Tie-breaker: tech with fewer jobs this week

5. SELECT the top-ranked tech.
```

#### Emergency Dispatch (Bypasses Normal Scheduling)

```
IF urgency == "emergency":
    1. Check if current time is within business_hours
    2. IF within business hours:
        - Find the tech with the fewest remaining jobs today who has "emergency" skill
        - If a tech is between jobs or finishing soon, dispatch them next
        - Bump non-emergency jobs if necessary (notify affected customers)
    3. IF outside business hours:
        - Find the on_call tech (technician where on_call == true)
        - If no on_call tech defined, alert the owner immediately
    4. Set scheduled_window to "ASAP"
    5. Create the job entry immediately
    6. Say: "I'm dispatching [tech] to you right now. They'll be there as fast as they can. Keep your phone nearby — [tech] may call you on the way."
```

#### Scheduling Windows

| Window | Time Range | Used For |
|--------|------------|----------|
| Morning | 08:00-12:00 | Standard/flexible bookings, customer preference |
| Afternoon | 12:00-17:00 | Standard/flexible bookings, customer preference |
| Specific | Customer-requested time | Accommodate if slot is open |
| ASAP | No window — first available | Emergency dispatch only |

**Offering a slot to the customer:**
> "I've got [tech name] available on [day, date] in the [morning/afternoon]. That would be between [start time] and [end time]. Does that work for you?"

**If the customer wants a specific time:**
> "Let me check... [tech name] can be there around [time]. I'll put you down for a [time]-[time+1hr] window. Just keep in mind arrival can vary a bit depending on the job before yours."

**If no same-day slot exists for an URGENT job:**
> "Our schedule is full for today, but I can get someone out first thing tomorrow morning at 8am. Will that work, or do we need to squeeze this in as an emergency today?"

**If no slots are available for the requested day:**
> "We're booked up on [day]. The next opening I have is [next available day and window]. Would that work, or would you like me to check a different day?"

### Step 5: CONFIRM

After the slot is selected and the technician is assigned, confirm everything back to the customer. Read back every detail.

**Confirmation script:**
> "Alright [name], I've got you scheduled for [day, date] in the [morning/afternoon]. [Tech name] will be there between [start time] and [end time]. You'll get a reminder the day before. Is there anything else I should note for the technician — like a gate code or parking instructions?"

If the customer provides special notes, capture them:
> "Got it, I'll make sure [tech name] knows about [note]. You're all set. We'll see you on [day]!"

**After confirmation, CREATE the job entry in jobs.json IMMEDIATELY.** Do not wait. The schedule must be updated the moment the appointment is confirmed so that subsequent scheduling checks see the slot as taken.

---

## Rescheduling

When a customer asks to reschedule:

**Step 1:** Find their existing job in `jobs.json` by name, phone, or job ID.

**Step 2:** Confirm which appointment:
> "I see your [service] appointment on [date] with [tech]. Is that the one you want to reschedule?"

**Step 3:** Find a new slot using the same scheduling algorithm.

**Step 4:** Update the EXISTING job entry — do NOT create a new one. Change:
- `scheduled_date` to the new date
- `scheduled_window` to the new window
- `technician` to the new tech (if different)
- Add a note to `special_notes`: "Rescheduled from [old date] [old window]"

**Step 5:** Confirm the new time:
> "Done — I've moved you to [new day, date] in the [morning/afternoon] with [tech name]. Same address at [address]. Anything else?"

---

## Cancellation

When a customer asks to cancel:

**Step 1:** Find their job. Confirm:
> "I see your [service] appointment on [date]. Are you sure you'd like to cancel?"

**Step 2:** If they confirm:
- Set `status: "cancelled"`
- Add cancellation reason to `special_notes` if they give one
- Do NOT delete the job entry — keep it for records

**Step 3:**
> "I've cancelled your appointment for [date]. If you change your mind or need service later, just give us a call. We're always here."

**Step 4:** Offer to rebook:
> "Would you like me to schedule this for a later date instead?"

---

## Day-of Dispatch

### Morning Briefing

At the start of each business day (or when the owner asks "what's on the schedule today"), provide a dispatch briefing for each technician.

**Briefing format per tech:**
> "[Tech name] has [N] jobs today:
> 1. **8:00-12:00** — [Customer name], [service display name] at [address]. [Special notes if any]. Phone: [phone].
> 2. **12:00-17:00** — [Customer name], [service display name] at [address]. Phone: [phone].
>
> Route note: Jobs are [clustered in the same area / spread across town — suggest starting with X]."

### Job Status Updates

When the owner or tech reports a status change:

**"[Tech] is heading to [customer]":**
- Update job status to `dispatched`

**"[Tech] is on site at [customer]":**
- Update job status to `in_progress`

**"[Tech] finished at [customer]":**
- Update job status to `completed`
- Set `completed_at` to current datetime
- Ask: "How much was the final bill?" → set `amount_billed`

**"[Customer] wasn't home":**
- Update job status to `no_show`
- Add note to `special_notes`
- Offer: "Want me to call [customer] and reschedule?"

---

## Reminders

### Day-Before Reminder

For every job with `status == "scheduled"` and `scheduled_date == tomorrow`:

**Customer reminder:**
> "Reminder: [tech name] from [business_name] is coming to [address] tomorrow between [scheduled_window] for [service display name]. If you need to reschedule, just give us a call at [business_phone]."

### Morning-of Tech Notification

For every job with `status == "scheduled"` and `scheduled_date == today`:

**Tech briefing per job:**
> "[Tech name], your [Nth] job today: [customer_name] at [address] between [scheduled_window] for [service display name]. Phone: [customer_phone]. [Special notes]. [If returning customer and jobs.json has history: 'Returning customer — last service was [previous service] on [date].']"

### Heartbeat Integration

On each heartbeat cycle:
1. Check for jobs with `scheduled_date == tomorrow` and `status == "scheduled"` — trigger day-before reminders
2. Check for jobs with `scheduled_date == today` and `status == "scheduled"` — trigger morning dispatch briefing
3. Check for overdue jobs — `scheduled_date < today` and `status == "scheduled"` (missed/forgotten) — alert the owner

**Heartbeat alert (overdue):**
> "ALERT: [customer_name]'s [service] job (ID: [id]) was scheduled for [scheduled_date] but was never marked dispatched or completed. Did this happen? Should I reschedule?"

Only alert when there is something actionable. If the day's schedule is running smoothly, say nothing.

---

## Trigger Phrases

The agent should recognize these natural language triggers and respond accordingly.

### "I need a plumber" / "I need help with..."
**Action:** Start the intake workflow (Step 1 through Step 5). Capture all information, classify urgency, find a slot, confirm.

### "What's on the schedule today?"
**Action:** Pull all jobs from `jobs.json` where `scheduled_date == today` and `status` is `scheduled`, `dispatched`, or `in_progress`. Group by technician and present as a dispatch briefing.

**Response:**
> "Today's schedule: [N] jobs across [M] techs.
> [Tech 1]: [count] jobs — [brief list]
> [Tech 2]: [count] jobs — [brief list]
> [Any gaps or light days noted.]"

### "Is [tech] available [day]?"
**Action:** Check `jobs.json` for all jobs assigned to that tech on the specified day. Compare against their `max_jobs_per_day`. Report back with available windows.

**Response:**
> "[Tech] has [N] jobs on [day]. They're booked in the [morning/afternoon] but have [window] open. Want me to slot someone in?"

Or:
> "[Tech] is wide open on [day] — no jobs scheduled yet."

Or:
> "[Tech] is maxed out on [day] with [N] jobs. [Other tech] has availability though — want me to check?"

### "Schedule [customer] for [service] on [day]"
**Action:** Direct booking. Skip the full intake flow — the owner is providing the details. Validate the date, find the best tech, create the job entry. Confirm back.

**Response:**
> "Got it — booked [customer] for [service display name] on [day] with [tech] in the [window]. Job ID: [id]."

### "Show the schedule"
**Action:** Generate and display the `schedule-board.html` canvas page.

### "Reschedule [customer name]"
**Action:** Start the rescheduling flow. Find their job, offer new slots, update the existing entry.

### "Who's on call?"
**Action:** Look up `config.json` technicians where `on_call == true`.

**Response:**
> "[Tech name] is on call. Their number is [phone]. Want me to dispatch them for an emergency?"

Or if no on-call tech:
> "Nobody is currently set as on-call in the system. Want me to flag this for [owner name]?"

### "Cancel [customer name]'s appointment"
**Action:** Find the job, confirm cancellation, update status.

### "Mark [customer] as completed" / "[Tech] finished at [customer]"
**Action:** Update job status to `completed`, capture billing amount if provided.

### "What's [tech]'s week look like?"
**Action:** Show all jobs for the tech across the current week (Mon-Fri). Summarize daily load.

**Response:**
> "[Tech]'s week:
> Monday: 4 jobs (morning heavy)
> Tuesday: 2 jobs (light day)
> Wednesday: 5 jobs (full)
> Thursday: 3 jobs
> Friday: 1 job so far
> Total: 15 jobs this week."

---

## Double-Booking Prevention

This is the single most important integrity rule. NEVER double-book a technician.

### Conflict Detection Algorithm

```
BEFORE assigning tech T to a new job on date D in window W:

1. Load all jobs from jobs.json where:
   - technician == T
   - scheduled_date == D
   - status is NOT "cancelled" and NOT "completed" and NOT "no_show"

2. Check job count:
   IF count >= T.max_jobs_per_day:
       REJECT. "[T] already has [count] jobs on [D] — that's their max."

3. Check window overlap:
   FOR each existing job J on date D for tech T:
       Parse J.scheduled_window into start_J and end_J
       Parse W into start_W and end_W

       Add buffer = config.scheduling.buffer_minutes_between_jobs (default: 30min)

       IF start_W < (end_J + buffer) AND (end_W + buffer) > start_J:
           OVERLAP DETECTED.
           REJECT. "[T] already has a [J.service] job at [J.scheduled_window] on [D]."

4. IF no conflicts: ALLOW the booking.
```

**If the preferred tech has a conflict:**
> "[Tech] is already booked for [existing service] during that time. I can schedule you with [alt tech] instead, or we can try a different time with [tech]. Which do you prefer?"

---

## Canvas Page: schedule-board.html

When the owner says "show the schedule" or "show the schedule board," generate and display this canvas page.

### Page Requirements

- **Default view:** Today's schedule (daily calendar)
- **Toggle:** Daily / Weekly view button
- **Layout:** Rows = technicians, columns = time slots (hourly from 8am-5pm)
- **Job cards:** Positioned in the correct time slot, spanning the estimated duration
- **Card content:** Customer name, service type, address (abbreviated), status
- **Color coding by status:**
  - Scheduled: blue (#3b82f6)
  - Dispatched: orange (#f59e0b)
  - In-progress: yellow (#eab308)
  - Completed: green (#22c55e)
  - Emergency: red (#ef4444)
  - Cancelled: gray with strikethrough (#6b7280)
- **Urgency indicator:** Emergency jobs get a pulsing red border
- **Tap a job card:** Sends postMessage to speak action with job details
- **"Book New" button** at top right: Sends postMessage to trigger intake flow
- **Dark theme:** Background #0a0a0a, card background #1a1a2e, text #e2e8f0
- **ALL inline CSS — no external CDNs, no Tailwind, no external scripts**
- **PostMessage bridge for all interactive elements**

### Canvas Page Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Schedule Board</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #0a0a0a; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 16px; }

    .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #222; }
    .header h1 { font-size: 1.4rem; color: #fff; }
    .header .date-label { color: #94a3b8; font-size: 0.9rem; }
    .header-actions { display: flex; gap: 8px; }

    .btn { padding: 8px 16px; border-radius: 6px; border: 1px solid #333; background: #1a1a2e; color: #e2e8f0; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: background 0.15s; }
    .btn:hover { background: #252547; }
    .btn-primary { background: #3b82f6; border-color: #3b82f6; color: #fff; }
    .btn-primary:hover { background: #2563eb; }
    .btn-active { background: #3b82f6; border-color: #3b82f6; color: #fff; }

    .summary-bar { display: flex; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
    .summary-stat { background: #111; border-radius: 8px; padding: 12px 18px; }
    .summary-stat .value { font-size: 1.5rem; font-weight: 700; color: #fff; }
    .summary-stat .label { font-size: 0.75rem; color: #94a3b8; margin-top: 2px; }

    .schedule-grid { display: grid; grid-template-columns: 100px repeat(HOUR_COLS, 1fr); gap: 1px; background: #111; border-radius: 8px; overflow: hidden; }
    .time-header { background: #0d0d14; padding: 10px 4px; text-align: center; font-size: 0.7rem; color: #64748b; font-weight: 600; border-bottom: 1px solid #222; }
    .tech-label { background: #0d0d14; padding: 12px 8px; font-size: 0.8rem; font-weight: 600; color: #fff; display: flex; align-items: center; border-right: 1px solid #222; }
    .time-slot { background: #0a0a12; padding: 4px; min-height: 60px; position: relative; border-right: 1px solid #1a1a2e; border-bottom: 1px solid #1a1a2e; }

    .job-card { border-radius: 4px; padding: 6px 8px; margin-bottom: 2px; cursor: pointer; font-size: 0.75rem; line-height: 1.3; transition: transform 0.1s, box-shadow 0.1s; }
    .job-card:hover { transform: scale(1.02); box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
    .job-card .card-customer { font-weight: 600; color: #fff; margin-bottom: 2px; }
    .job-card .card-service { color: #94a3b8; font-size: 0.7rem; }
    .job-card .card-address { color: #64748b; font-size: 0.65rem; margin-top: 2px; }
    .job-card .card-status { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.6rem; font-weight: 600; text-transform: uppercase; margin-top: 3px; }

    .job-scheduled { background: rgba(59,130,246,0.15); border-left: 3px solid #3b82f6; }
    .job-scheduled .card-status { background: rgba(59,130,246,0.2); color: #3b82f6; }
    .job-dispatched { background: rgba(245,158,11,0.15); border-left: 3px solid #f59e0b; }
    .job-dispatched .card-status { background: rgba(245,158,11,0.2); color: #f59e0b; }
    .job-in_progress { background: rgba(234,179,8,0.15); border-left: 3px solid #eab308; }
    .job-in_progress .card-status { background: rgba(234,179,8,0.2); color: #eab308; }
    .job-completed { background: rgba(34,197,94,0.15); border-left: 3px solid #22c55e; }
    .job-completed .card-status { background: rgba(34,197,94,0.2); color: #22c55e; }
    .job-emergency { background: rgba(239,68,68,0.15); border-left: 3px solid #ef4444; animation: emergency-pulse 2s infinite; }
    .job-emergency .card-status { background: rgba(239,68,68,0.2); color: #ef4444; }
    .job-cancelled { background: rgba(107,114,128,0.1); border-left: 3px solid #6b7280; opacity: 0.5; }
    .job-cancelled .card-customer { text-decoration: line-through; }
    .job-cancelled .card-status { background: rgba(107,114,128,0.2); color: #6b7280; }

    @keyframes emergency-pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); } 50% { box-shadow: 0 0 0 4px rgba(239,68,68,0); } }

    .empty-day { text-align: center; color: #555; padding: 40px 20px; font-size: 0.9rem; grid-column: 1 / -1; }

    .legend { display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap; justify-content: center; }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.7rem; color: #94a3b8; }
    .legend-dot { width: 10px; height: 10px; border-radius: 2px; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>Schedule Board</h1>
      <div class="date-label">DATE_LABEL</div>
    </div>
    <div class="header-actions">
      <button class="btn btn-active" onclick="window.parent.postMessage({type:'canvas-action',action:'speak',text:'Show today schedule'},'*')">Today</button>
      <button class="btn" onclick="window.parent.postMessage({type:'canvas-action',action:'speak',text:'Show this week schedule'},'*')">Week</button>
      <button class="btn btn-primary" onclick="window.parent.postMessage({type:'canvas-action',action:'speak',text:'I need to schedule a new appointment'},'*')">+ Book New</button>
    </div>
  </div>

  <div class="summary-bar">
    <div class="summary-stat">
      <div class="value">TOTAL_JOBS</div>
      <div class="label">Total Jobs</div>
    </div>
    <div class="summary-stat">
      <div class="value">SCHEDULED_COUNT</div>
      <div class="label">Scheduled</div>
    </div>
    <div class="summary-stat">
      <div class="value">IN_PROGRESS_COUNT</div>
      <div class="label">In Progress</div>
    </div>
    <div class="summary-stat">
      <div class="value">COMPLETED_COUNT</div>
      <div class="label">Completed</div>
    </div>
    <div class="summary-stat">
      <div class="value" style="color:#ef4444;">EMERGENCY_COUNT</div>
      <div class="label">Emergency</div>
    </div>
  </div>

  <!-- Schedule grid: one row per technician, columns = hourly time slots (8am-5pm) -->
  <div class="schedule-grid">
    <!-- Time headers -->
    <div class="time-header"></div>
    <!-- One column header per hour: 8AM, 9AM, 10AM, ... 4PM -->

    <!-- Per-tech rows -->
    <!-- TECH_NAME label cell, then job cards placed in appropriate time slot cells -->
  </div>

  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#3b82f6;"></div> Scheduled</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f59e0b;"></div> Dispatched</div>
    <div class="legend-item"><div class="legend-dot" style="background:#eab308;"></div> In Progress</div>
    <div class="legend-item"><div class="legend-dot" style="background:#22c55e;"></div> Completed</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div> Emergency</div>
    <div class="legend-item"><div class="legend-dot" style="background:#6b7280;"></div> Cancelled</div>
  </div>

  <script>
    /* Job card click — drill into job details via voice */
    document.querySelectorAll('.job-card').forEach(function(card) {
      card.addEventListener('click', function() {
        var jobId = this.getAttribute('data-id');
        window.parent.postMessage({
          type: 'canvas-action',
          action: 'speak',
          text: 'Tell me about job ' + jobId
        }, '*');
      });
    });
  </script>
</body>
</html>
```

**When generating the page:** Read live job data from `jobs.json` and technician list from `config.json`. Populate the grid with real data. Every job card MUST include `data-id="JOB-YYYY-MMDD-XXX"` for the click handler. Replace ALL placeholder values (DATE_LABEL, TOTAL_JOBS, etc.) with computed values. Place job cards in the correct time slot column based on `scheduled_window` start time. Cards for emergency jobs should use the `job-emergency` class regardless of their status.

---

## Analytics and Reporting

### "How busy are we this week?"

Calculate and report:
- Total jobs per day (Mon-Fri)
- Jobs per technician
- Percentage of capacity used (jobs / (techs * max_jobs_per_day))
- Emergency count
- Revenue (sum of `amount_billed` for completed jobs)

**Response:**
> "This week: [total] jobs across [days]. Running at [X]% capacity.
> [Tech 1]: [N] jobs ([%] of max)
> [Tech 2]: [N] jobs ([%] of max)
> Busiest day: [day] with [N] jobs. Lightest: [day] with [N].
> [If any:] [N] emergency calls this week.
> Revenue so far: $[amount] from [completed count] completed jobs."

### "Show me [tech]'s completed jobs"

List all jobs for the specified tech where `status == "completed"`, sorted by `completed_at` descending. Include customer name, service, date, and amount billed.

### Job History Search

When the owner asks about a specific customer ("Have we been to [address] before?" or "What did we do for [customer name]?"):
- Search `jobs.json` by `customer_name` (partial match, case-insensitive) or `address`
- Return all matching jobs with date, service, tech, and status
- Useful for tech dispatch briefings — "returning customer" context

---

## Critical Rules

These are non-negotiable. Violating any of these causes real-world problems — missed appointments, angry customers, wasted tech time.

### 1. NEVER Double-Book a Technician
Run the conflict detection algorithm EVERY time before creating or modifying a job. No exceptions. No "I'll make it work." If there is a conflict, find an alternative.

### 2. ALWAYS Verify the Service Area
Check the zip code against `config.json` BEFORE scheduling. Out-of-area jobs waste drive time and create unhappy customers who expected faster service.

### 3. Emergency Dispatch Overrides Everything
When a customer has an active water leak, gas smell, or sewage backup — NOTHING else matters. Drop the current scheduling flow, find an available tech (on-call if after hours), and dispatch immediately. Then deal with the rest.

### 4. ALWAYS Capture a Callback Phone Number
If the customer does not provide a phone number, ask again. If they refuse, note it — but every job MUST have a `customer_phone` value. Techs need to call when they are en route.

### 5. Confirm Every Appointment Back to the Customer
Never end an intake call without reading back: date, time window, technician name, and address. The customer must hear the confirmation and agree. Misunderstood appointments waste everyone's time.

### 6. Create the Job Entry IMMEDIATELY After Confirmation
The moment the customer confirms, write to `jobs.json`. Do not batch, do not defer. The next call might try to book the same slot.

### 7. Rescheduling Updates the Existing Entry
When rescheduling, modify the existing job in `jobs.json`. Do NOT create a new job and leave the old one as "scheduled." That creates phantom appointments.

### 8. Respect Business Hours for Standard Bookings
Only offer time slots within `business_hours.start` and `business_hours.end` on `business_hours.days`. The only exception is emergency dispatch to the on-call tech.

### 9. Include Drive Time Context
When scheduling the second or later job for a tech on the same day, consider the previous job's location. Same zip code = tight scheduling is okay. Opposite ends of the service area = leave extra buffer. Use zip code proximity as a rough guide.

### 10. Track Everything in jobs.json
Every status change, every note, every rescheduling — it all goes in the job record. The job file is the single source of truth for what was promised and what happened.

---

## Data Integrity Rules

- **Never delete job entries** — even cancelled and no-show jobs remain in the file for historical record
- **Never overwrite jobs.json without reading first** — always read, parse, modify, write back
- **Job IDs are immutable** — once assigned, a job ID never changes
- **created_at is immutable** — reflects when the job was first booked, even after rescheduling
- **completed_at is set once** — when a job is marked completed, the timestamp is permanent
- **Keep jobs.json sorted by scheduled_date ascending** — makes the daily view easier to scan
- **Sequential IDs per day** — if a job is cancelled and a new one is created the same day, the new job gets the next number (do not reuse cancelled IDs)

---

## Setup Guide

When this skill is activated for a new client and `config.json` is missing the required scheduling sections, walk through setup:

### 1. Business Hours
> "What are your business hours? Like 8am to 5pm Monday through Friday?"

Capture start time, end time, and working days.

### 2. Technician Roster
> "Let's set up your team. Who are your technicians?"

For each tech, capture:
- Name
- Phone number
- Skills / what types of jobs they handle
- Maximum jobs per day (suggest 5-6 as default)
- Are they on-call for after-hours emergencies?
- Home zip code (for routing optimization)

### 3. Service Types
> "What services do you offer? I'll need the name, rough duration, and what skill level is required."

Capture each service with display name, average duration in hours, and the skill tag that maps to technician skills.

### 4. Service Area
> "What zip codes do you service?"

Capture the list. If they say a city or region name, look up the zip codes.

### 5. Initialize Jobs File
Create `workspace/business/jobs.json` with `{"jobs": []}`.

### 6. Existing Appointments
> "Do you have any existing appointments on the books that I should add?"

If yes, voice-capture each one.

### 7. Confirmation
> "Schedule system is set up. I've got [N] techs, [N] service types, and [N] zip codes in the service area. Say 'show the schedule' anytime to see the board, or just tell me when someone calls needing service."

---

## Integration Points

### With Other Skills

- **Estimate Tracker:** When an estimate converts to a booked job, the estimate-tracker skill should call this scheduler to create the job entry. The job's `customer_name`, `service`, and `address` come from the estimate. Link them with `booked_job_id` on the estimate.
- **Customer Follow-Up:** When a job is marked `completed`, the customer-followup skill picks it up on its next heartbeat. The `follow_up_status` field on the job tracks whether follow-up has started.
- **Canvas Design:** The schedule board can be enhanced with the canvas-design skill for richer visualizations if requested.
- **Review Manager:** Completed jobs feed the review pipeline. The reviewer skill uses job completion data to know who to ask for reviews.

### With External Systems

- `customer_id` enables linking to a CRM or customer database if one is connected later
- `amount_quoted` and `amount_billed` enable invoicing integration
- The job file format is JSON — easy to export, sync, or connect to external scheduling tools
- `follow_up_status` bridges to the post-service follow-up pipeline

---

## Example Sessions

### Inbound Service Call

**Customer:** "Hey, I need someone to come look at my kitchen faucet. It's leaking all over the place."
**Agent:** "I can definitely help with that. Let me get some info so we can get someone out to you. Can I get your name?"
**Customer:** "Jane Doe."
**Agent:** "And Jane, what's the best number to reach you at?"
**Customer:** "555-0200."
**Agent:** "What's the address?"
**Customer:** "789 Pine Street, Phoenix, 85003."
**Agent:** "Got it. So the kitchen faucet is leaking — is it dripping from the handle area, or is it leaking at the base where it meets the counter?"
**Customer:** "At the base. There's water pooling around it."
**Agent:** "Okay, sounds like the faucet seal. Let me check the schedule... I've got Mike available Friday morning. He'd be there between 8 and noon. Does that work?"
**Customer:** "Friday works."
**Agent:** "Alright Jane, I've got you scheduled for Friday, March 7th in the morning. Mike will be there between 8 and noon at 789 Pine Street. You'll get a reminder the day before. Is there anything Mike should know — like a gate code or where to park?"
**Customer:** "Yeah, gate code is 4521 and tell him to park on the street."
**Agent:** "Got it, I'll make sure Mike knows. You're all set — we'll see you Friday!"

---

### Emergency Dispatch

**Customer:** "Oh my god, there's water spraying everywhere! A pipe burst in the wall!"
**Agent:** "Okay, first thing — do you know where your main water shut-off valve is? It's usually near the water meter or where the main line enters the house. Turn it off if you can. What's your name?"
**Customer:** "Sarah, it's at 456 Elm Street, 85007."
**Agent:** "Sarah, I'm dispatching someone to you right now. Mike is our emergency tech and he'll be heading your way as fast as he can. Keep your phone nearby — he may call you on the way. Your number is 555-0199?"
**Customer:** "Yes."
**Agent:** "Hang tight, Sarah. Mike is on his way. Try to shut off that main valve if you can find it."

---

### Schedule Check

**Owner:** "What's on the schedule for tomorrow?"
**Agent:** "Tomorrow, Thursday March 6th, you've got 4 jobs:

Mike has 2:
1. Morning — John Smith, water heater install at 123 Oak Ave (85001). He's a returning customer.
2. Afternoon — Lisa Park, gas line inspection at 567 Maple Dr (85003).

Dave has 2:
1. Morning — Bob Wilson, drain cleaning at 890 Cedar Ln (85016). Note: he has two dogs, ring doorbell not knock.
2. Afternoon — Maria Santos, toilet repair at 234 Birch St (85014).

Carlos is open — no jobs scheduled yet. Want me to fill his day?"

---

### Rescheduling

**Customer:** "I need to reschedule my appointment."
**Agent:** "Sure thing. Can I get your name?"
**Customer:** "Jane Doe."
**Agent:** "I see your faucet replacement on Friday March 7th with Mike. Is that the one?"
**Customer:** "Yes, I can't do Friday anymore. Can I do next week?"
**Agent:** "Let me check... I've got Mike available Monday the 10th in the morning, or Dave could come Tuesday afternoon. What works better?"
**Customer:** "Monday morning with Mike."
**Agent:** "Done — I've moved you to Monday, March 10th, morning window between 8 and noon with Mike. Same address, 789 Pine Street. Anything else?"

---

## Scheduling Edge Cases

### Customer Wants a Specific Tech
If a customer requests a specific technician by name:
- Check that tech's availability first
- If available, book them even if another tech would be a "better" match by the algorithm
- If unavailable: "Mike is booked on that day, but Dave is excellent with faucets too. Would you like me to schedule Dave, or would you prefer to wait for Mike?"

### Multiple Jobs at Same Address
If two different services are needed at the same address (e.g., faucet replacement AND toilet repair):
- If the same tech can do both, book them back-to-back as a single extended visit
- Create two job entries but note in `special_notes` that they are a combined visit
- This saves the customer a second appointment window and saves drive time

### Last-Minute Cancellation Frees a Slot
When a job is cancelled on the same day:
- Check if any URGENT jobs are waiting for a same-day slot
- If yes, offer to move the urgent job into the freed slot
- Notify the owner: "[Customer] cancelled their [time] appointment. [Urgent customer] is waiting for a same-day slot — want me to move them in?"

### Weekend / After-Hours Calls
If a customer calls outside business hours with a non-emergency:
> "Our office hours are [start] to [end], [days]. I can schedule you for our next available slot on [next business day]. Would [morning/afternoon] work?"

If it is an emergency, dispatch the on-call tech regardless of day/time.

### Tech Calls in Sick
When a tech is unavailable for the day:
1. Pull all their jobs for today from `jobs.json`
2. For each job, find an alternative tech using the matching algorithm
3. If a suitable replacement exists, reassign and notify the customer
4. If no replacement is available, call the customer to reschedule
5. Update all affected job entries with the new tech or new date

> "[Tech] is out today. They had [N] jobs. I've reassigned [customer 1] to [alt tech] and [customer 2] to [alt tech]. [Customer 3]'s repipe needs to be rescheduled — no one else has that skill today. Want me to call them?"

---

## File Operations Summary

| Operation | File | Action |
|-----------|------|--------|
| Read tech roster, hours, service area | `workspace/business/config.json` | READ |
| Check tech availability | `workspace/business/jobs.json` | READ |
| Create new appointment | `workspace/business/jobs.json` | READ then WRITE |
| Update job status | `workspace/business/jobs.json` | READ then WRITE |
| Reschedule appointment | `workspace/business/jobs.json` | READ then WRITE |
| Cancel appointment | `workspace/business/jobs.json` | READ then WRITE |
| Generate schedule board | `workspace/schedule-board.html` | WRITE (canvas page) |

**Always read before writing.** Never overwrite the entire file — read, parse, modify the specific entry, write back.
