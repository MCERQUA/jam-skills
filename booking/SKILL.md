---
name: booking
description: "Book, cancel, and manage appointments for the client's business via the Cal.diy-backed booking system. Use when the user mentions booking, appointment, schedule, availability, calendar, 'book me', 'cancel my appointment', 'am I free', or 'I'm busy <day>'. Goes through the OVU booking plugin — never call Cal.diy directly."
metadata: {"openclaw": {"requires": {"anyBins": ["curl"]}}}
---

# Booking — Cal.diy Appointment Scheduling

You can schedule, list, cancel, and block appointments for your client's business.
Bookings are backed by **Cal.diy** (a shared instance at `cal.jam-bot.com`) but you
**never talk to Cal.diy directly** — you call the **OpenVoiceUI booking plugin API**,
which holds the per-tenant API key server-side and signs/proxies every request.

## Critical Rules

1. **Confirmations are automatic — do NOT separately email or SMS the customer.**
   When a booking is created, changed, or cancelled, the Cal.diy webhook bridge sends
   the customer's confirmation and notifies the client automatically. You must not send
   a second confirmation through any other channel (task-system **Rule 1** — never
   double-send customer comms).
2. **Always go through the plugin** (`http://openvoiceui:5001/api/booking/*`). Never
   curl `cal.jam-bot.com` directly — you don't have the key and shouldn't.
3. **Never ask the customer for an API key or calendar credentials.** It's already
   configured server-side.
4. **Check `status` first if anything fails** — the booking service may not be
   configured or deployed yet (see Error Handling).

## Base URL

All calls use the internal OVU address over the Docker network:

```
http://openvoiceui:5001/api/booking
```

Use `curl -s` (silent). **Every call needs the internal agent auth header** — OVU's
global auth gate requires it even for same-Docker-network calls (verified 2026-07-23):

```
-H "X-Agent-Key: $AGENT_API_KEY"
```

`AGENT_API_KEY` is already set in your environment — just include the header, don't
hardcode the value.

---

## The 5 Tool Calls

### 1. check_availability — when does the client have open slots?

Trigger: "When can I come in?", "Are you free Thursday?", "What times are open?"

```bash
curl -s -H "X-Agent-Key: $AGENT_API_KEY" \
  "http://openvoiceui:5001/api/booking/slots?eventTypeId=30min&start=2026-06-10&end=2026-06-12&timeZone=America/Phoenix"
```

- `eventTypeId` (or `eventTypeSlug`) — the appointment type. Ask the client which
  service if there's more than one; otherwise omit and it uses the default account.
- `start` / `end` — ISO dates or datetimes for the window to search.
- `timeZone` — use the business's timezone.

Returns the available slot times. Read them back to the customer and let them pick one,
then call **create_booking**.

### 2. create_booking — book the chosen slot

Trigger: customer picks a time. "Book me Thursday at 2pm."

```bash
curl -s -X POST http://openvoiceui:5001/api/booking/bookings \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "start": "2026-06-12T14:00:00.000Z",
    "eventTypeId": 30,
    "attendee": {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "timeZone": "America/Phoenix"
    },
    "metadata": {"phone": "+16025551234", "notes": "Front door dripping"}
  }'
```

- `start` — the exact slot start time from `check_availability`.
- `attendee.name` + `attendee.email` — required by Cal.diy. Collect both before booking.
- After a 200/201, tell the customer it's booked. **Do not send a confirmation message**
  — the webhook bridge already did.

### 3. cancel_booking — cancel an existing appointment

Trigger: "Cancel my appointment", "I need to reschedule" (cancel, then re-book).

```bash
curl -s -X POST http://openvoiceui:5001/api/booking/bookings/<uid>/cancel \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"cancellationReason": "Customer requested cancellation"}'
```

- `<uid>` — the booking's uid. Get it from **list_bookings** if you don't have it.
- The customer is notified automatically — don't send a separate "you're cancelled" text.

### 4. block_time — "I'm busy Wednesday"

Trigger: the **client/owner** (not a customer) says "Block off Wednesday", "I'm out
Friday", "Don't let anyone book me tomorrow afternoon."

```bash
curl -s -X POST http://openvoiceui:5001/api/booking/block \
  -H "X-Agent-Key: $AGENT_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "start": "2026-06-10T00:00:00.000Z",
    "end":   "2026-06-10T23:59:59.000Z",
    "reason": "Out of office"
  }'
```

- `start` / `end` — the window to block. For a whole day, use 00:00:00 → 23:59:59 in
  the business timezone (expressed as UTC ISO).
- Reserving the day prevents customers from booking those slots. A `SLOT_RESERVED`
  webhook fires and the client gets a "Wednesday blocked" confirmation automatically.

### 5. list_bookings — what's on the calendar?

Trigger: "What appointments do I have?", "Who's coming in tomorrow?", and to find a
`uid` before cancelling.

```bash
curl -s -H "X-Agent-Key: $AGENT_API_KEY" "http://openvoiceui:5001/api/booking/bookings?status=upcoming"
```

- `status` — `upcoming` (default), `past`, or `cancelled`.
- Each booking includes its `uid` (needed for cancel), start time, and attendee.

---

## Error Handling

**Before reporting any booking failure to the user, check status:**

```bash
curl -s -H "X-Agent-Key: $AGENT_API_KEY" http://openvoiceui:5001/api/booking/status
```

| status response | What it means | What to tell the user |
|---|---|---|
| `"configured": false` | No Cal.diy API key set up yet | "Booking isn't set up yet — the owner needs to finish the Booking Setup." Do NOT invent a confirmation. |
| `"reachable": false` | Service not deployed / unreachable | "The booking system is offline right now. I've noted your request — try again shortly." |
| `"authenticated": false` | Key rejected (401/403) | Tell the owner the API key needs to be re-entered in Booking Setup. |
| `503` from any endpoint | Same as `configured:false` | Don't fabricate a booking. Surface the real state. |

**Never tell a customer they're booked unless the create call returned success.** If
booking is unconfigured, say so honestly — do not pretend an appointment was made.

## Notes

- All times you send should be ISO-8601 UTC (`...Z`). Convert from the business
  timezone before sending.
- For rescheduling, cancel the existing booking then create a new one at the new time.
- The plugin auto-logs every webhook event to a per-tenant JSONL on the server — you
  don't need to track bookings yourself; just query `list_bookings`.
