---
name: client-promises
description: When you tell a client you will do something at a time — "I'll remind you at 1pm", "I'll text you Thursday", "send me a morning report" — register it here. Real host crons, verified delivery, tracked by the accountability officer. TRIGGER whenever you commit to a future action for a human. DO NOT use .claude/scheduled_tasks.json or openclaw cron for client commitments.
---

# Client promises — if you said you'd do it, this is how it actually happens

## The rule

**Telling a client you will do something later is a PROMISE. It must be registered here,
or you have not scheduled anything — you have written a note to yourself.**

Never use `.claude/scheduled_tasks.json`. Never use `openclaw cron`. Measured 2026-08-20 on
hrsf: a reminder written to `scheduled_tasks.json` fired at the wrong hour, **ignored an
edit made seven minutes before it fired**, left no receipt anywhere, and sent the client a
message whose text contradicted its own timing. `openclaw cron list` showed nothing the
whole time. There was no way to tell, from outside, that a client had been promised
anything at all.

By contrast the host-cron path has delivered every client message it was asked to: 51 daily
kickoffs across phatty/gksprayfoam/azrim, each with a carrier id in the drain log.

## One-off promise — "remind me at 1pm", "text me Thursday"

### If you are a TENANT agent (inside an openclaw container) — use the request lane

**You cannot run `promise.py`. It is not in your container and neither is `crontab`.**
Until 2026-08-28 this skill told you to run it anyway, which is why a real appointment
(foamology lead #2023, inspection booked for Mon Aug 31) had to be escalated over the mesh
and only got armed because a host session happened to be awake to do it by hand.

Drop a JSON file into a directory you already have rw on. A host cron picks it up within
2 minutes, arms the real one-shot cron, and writes you back a result.

```bash
cat > /mnt/agent-mesh/mesh/PROMISES/requests/$(date -u +%Y%m%dT%H%M%SZ)-lead2023.json <<'JSON'
{
  "request_id": "foamology-lead2023-followup",
  "tenant": "foamology",
  "to": "+19073103000",
  "at_local": "2026-09-01T09:00",
  "body": "Morning — how did the Driskell inspection go yesterday?",
  "promised_by": "foamology@mesh",
  "source": "ledger/sms/2026-08-28/..."
}
JSON
```

**`at_local` is the CLIENT'S WALL CLOCK — do not convert it yourself.** The zone comes from
your own `USER.md` Timezone field, and the conversion (including both DST edge cases) is done
by the tool. If that field is empty the request is REFUSED rather than guessed at — fill it,
or ask the host to. Use `"at"` with an explicit `...Z` only when you genuinely mean UTC.

**Then READ YOUR RESULT.** Every request gets one, accepted or not:

```bash
cat /mnt/agent-mesh/mesh/PROMISES/results/foamology-lead2023-followup.json
```

`"outcome": "ACCEPTED"` carries the `promise_id` — that is your proof it will fire.
`"outcome": "REJECTED"` carries the exact reason; fix it and submit again with a NEW
`request_id`. **Submitting and not reading the result is the same as not scheduling
anything** — that is the entire defect this system exists to end.

The lane refuses, by design: a recipient not registered to YOUR tenant, another tenant's
owner, the admin line, a time in the past, a body over 900 chars, and a repeated
`request_id` (so a retry can never double-text your client).

### If you are the HOST (or anything with a shell on the box)

```bash
python3 /home/mike/MIKE-AI/scripts/promises/promise.py add \
  --tenant hrsf --to +19797165542 \
  --at-local 2026-08-20T13:00 \
  --body "Hi Edith — 1pm as you asked. Ready to pick the quoting back up?" \
  --promised-by hrsf-voice@mesh \
  --source ledger/sms/2026-08-20/00-31-15-in-local-1787185875.md
```

`--at-local` resolves the zone from the tenant's `USER.md` and REFUSES on an empty field,
on a non-IANA value, on a DST spring-forward gap (the time does not exist) and on a
fall-back overlap (it happens twice). `--at` still accepts explicit UTC. `--tz` overrides.

This installs a **real one-shot crontab line**, visible in `crontab -l | grep JAMBOT-PROMISE-ONESHOT`,
which removes itself after firing. At fire time the message goes into the same outbound SMS
spool every agent send uses, and a receipt is written.

### When the plan changes

| what happened | what to run |
|---|---|
| moved to a different time | `promise.py add` the new one, then `promise.py supersede --id <old> --by <new> --reason "..."` |
| client cancelled outright | `promise.py cancel --id <id> --reason "..."` (reason is mandatory) |
| audit says NOT ARMED | `promise.py rearm --id <id>` — the sweeper also does this automatically every 10 min |

**Never hand-edit the crontab, and never `promise.py add` a replacement without superseding
the original** — the old line is still armed and your client gets the same text twice.

## Recurring report — ONLY when the client asks for one

Morning reports are **opt-in and client-specified**. Do not subscribe anyone by default.
The old always-on daily kickoff was switched off precisely because it fired whether or not
there was anything worth saying.

```bash
python3 /home/mike/MIKE-AI/scripts/promises/report.py subscribe \
  --tenant hrsf --to +19797165542 --at 13:00 \
  --sections leads,owed \
  --quote "text me my leads from the day before every morning"
```

`--quote` is what the client **actually said**, verbatim. It is the record of what they
agreed to.

**If a client asks for a section that has no provider, the subscribe is REFUSED.** That is
deliberate: silently dropping "the weather" would mean promising something we never send.
Build the provider, then subscribe them.

## An SMS must be worth the client's attention

**Mike's bar: "if we send an SMS it better have value — not wasted messages annoying clients
with nothing valuable."**

Three gates enforce it, in order:

**1. At subscribe time — can this client EVER have something to report?**
Every section is probed before the subscription is created. If none can produce content, the
subscribe is **REFUSED**. Measured 2026-08-20: `mrglass` was configured for a 06:00 daily
kickoff with **0 leads, 0 websites, 0 SMS conversation** — it would have gone SILENT-KEPT
every day forever, which from outside is indistinguishable from being broken. `phatty` had
**0 leads and still received 28 kickoffs**; that is where the content-free filler came from.
Connect the data source first, or `--force` if content is genuinely expected before the
first send.

**2. In the provider — `content` means the client would ACT on it.**
"Nothing happened today" is `empty`, not `content`. "0 new leads" is `empty`. A provider that
dresses up nothing as something is the bug.

**3. The value floor — a backstop for when a provider gets that wrong.**
A body with no specifics at all — no counts, no names, no dates — is greeting-shaped filler.
It is suppressed and recorded as SILENT-KEPT with the suppressed text kept in the receipt, so
you can see what was almost sent. "Good morning! Hope you have a great day." does not go out.

**4. A perpetually silent subscription is a FINDING, not a success.**
Seven consecutive SILENT-KEPT runs raises `SUBSCRIBED-TO-NOTHING`: this client has never had
anything to report, so either connect the source or unsubscribe them. Silence is a valid day;
silence forever means the promise was never real.

## What happens when there's nothing to say

**SILENT-KEPT.** If every section comes back empty, no message is sent and the quiet day is
recorded. Staying silent when there is no news is honouring the contract, not failing it.

**But `empty` and `error` are different things, and a provider must never confuse them:**

| provider returns | meaning | result |
|---|---|---|
| `("content", text)` | there is something to say | **SENT** |
| `("empty", why)` | genuinely nothing today | contributes to **SILENT-KEPT** |
| `("error", why)` | **could not look** | **DEGRADED** — nothing sent, alert raised |

If a broken leads feed returned `empty`, the run would go SILENT-KEPT, the client would
receive nothing, and every dashboard would read green. A section that errors makes the whole
run DEGRADED — even if other sections had content — because a partial report that hides a
broken section is worse than no report.

## Nothing is forgotten — the accountability sweep

`promise-audit-cron.sh` runs `10,40 * * * *` and does a three-way check on both lanes:

    registry  <->  crontab line  <->  delivery receipt

States you will see: `ARMED · QUEUED · KEPT · SILENT-KEPT · DEGRADED · UNVERIFIED · BREACH`.

**`UNVERIFIED` is not `BREACH`.** "The send failed" and "I cannot tell whether it sent" are
different facts and are never merged.

A registered promise with no crontab line reports **BREACH — NOT ARMED** immediately, which
is exactly the failure that left Edith's reminder as a file nobody ran. The sweep also alerts
when the auditor itself cannot run, so a crashed auditor never reads as "no findings".

## Checking your own work

```bash
python3 .../promise.py list --tenant hrsf     # every promise and its state
python3 .../promise.py audit                  # exit 1 if anything is off track
python3 .../report.py  audit                  # same for subscriptions
crontab -l | grep -E 'JAMBOT-PROMISE-ONESHOT|JAMBOT-REPORT'
```

**Registering is not keeping.** The only evidence a promise was kept is a delivery receipt.
Do not tell a client, or Mike, that something is scheduled on the strength of having written
it down.
