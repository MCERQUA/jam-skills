---
name: comms-control
description: "Change the client's proactive-messaging rules of engagement — kickoff time, quiet hours/cutoff, texting frequency, scheduled recurring updates (weather, stocks, custom). TRIGGER whenever the client asks to change when/how often/what you text them: 'move my kickoff to 7am', 'don't text me past 8pm', 'add the weather to my morning', 'stop the morning rundown'. Changes are ENFORCED from machine JSON files — editing human notes alone does NOT take effect; this skill makes the change stick."
---

# comms-control — make the client's messaging preferences actually take effect

The host enforces your rules of engagement and fires the morning kickoff + recurring updates by reading **two machine JSON files in your workspace**, live, every run:

- `business/comms-rules.json` — the GATE: timezone, quiet-hours window, frequency cap, and the **morning kickoff time**. The host-side outbound drain reads this every minute and HOLDS any proactive message you send outside the window.
- `business/comms-schedule.json` — the SCHEDULE: whether the kickoff is on, and the list of recurring `jobs[]` (weather, stocks, custom text) with their cadence.

**You own both files (uid node).** When the client asks to change anything about *when/how often/what* you message them, you MUST edit the relevant JSON file. The change takes effect on the next scheduler run (within minutes) — no restart, no host action needed. Then confirm the new setting back to the client in plain language.

> ⚠️ The human-readable `business/comms-preferences.md` is just a note for yourself. Editing it does NOTHING to behaviour. ALWAYS edit the JSON file(s) below or the change is fake.

## Always edit JSON safely (don't corrupt it)

Use `jq` (preferred) so you never hand-break the JSON:

```bash
cd /home/node/.openclaw/workspace/business
# always work on a temp + validate before replacing
jq '<filter>' comms-rules.json > .tmp && mv .tmp comms-rules.json && echo OK || echo "BAD JSON - aborted"
```

If `jq` is unavailable, use `python3 -c` with `json.load`/`json.dump`. Never echo raw JSON over the file blind.

---

## Recipes

### 1. Change the morning kickoff time  ("move my kickoff to 7am")
The kickoff time is `morning_kickoff` in **comms-rules.json**. If the new time is EARLIER than `quiet_hours.send_window_start`, also lower the window start to match — otherwise the host will HOLD the kickoff until the window opens and it will fire late.

```bash
cd /home/node/.openclaw/workspace/business
NEW="07:00"   # 24h HH:MM in the client's timezone
jq --arg t "$NEW" '
  .morning_kickoff = $t
  | .quiet_hours.send_window_start = (if ($t < .quiet_hours.send_window_start) then $t else .quiet_hours.send_window_start end)
' comms-rules.json > .tmp && mv .tmp comms-rules.json && echo OK
```
Confirm: *"Done — your morning kickoff is now 7:00 AM CST. You can change it again anytime, just tell me."*

### 2. Change the evening cutoff / quiet hours  ("nothing past 8pm")
`quiet_hours.send_window_end` in **comms-rules.json** (proactive messages only — you ALWAYS reply when they text you, any hour).
```bash
jq '.quiet_hours.send_window_end = "20:00"' comms-rules.json > .tmp && mv .tmp comms-rules.json && echo OK
```

### 3. Change how often you may text  ("only once a day" / "a few times a day")
`frequency_cap_per_day` in **comms-rules.json** — integer, or `null` for unlimited. once=1, a few=3, "only when I ask"=0.
```bash
jq '.frequency_cap_per_day = 1' comms-rules.json > .tmp && mv .tmp comms-rules.json && echo OK
```

### 4. Add a recurring update  ("send me AAPL & TSLA every hour", "add weather to my morning")
Append a job to `jobs[]` in **comms-schedule.json**.
- `kind`: `weather` | `stocks` | `custom_text` | `reflections_overview`
- `cadence`: `daily HH:MM` | `weekdays HH:MM` | `hourly` | `every Nh`
- `args`: kind-specific (`{"symbols":["AAPL","TSLA"]}` for stocks; `{"lat":38.98,"lon":-94.67}` or `{"location":"Overland Park, KS"}` for weather; `{"text":"..."}` for custom_text)

```bash
cd /home/node/.openclaw/workspace/business
jq '.jobs += [{"id":"stocks-hourly","kind":"stocks","cadence":"hourly","args":{"symbols":["AAPL","TSLA"]},"enabled":true,"last_fired":null}]' \
  comms-schedule.json > .tmp && mv .tmp comms-schedule.json && echo OK
```
For "add weather to my *morning*" (not a separate job) add `"weather"` to `morning_kickoff.include`:
```bash
jq '.morning_kickoff.include += ["weather"] | .morning_kickoff.include |= unique' comms-schedule.json > .tmp && mv .tmp comms-schedule.json && echo OK
```

### 5. Turn the kickoff on/off  ("stop the morning rundown")
`morning_kickoff.enabled` in **comms-schedule.json**.
```bash
jq '.morning_kickoff.enabled = false' comms-schedule.json > .tmp && mv .tmp comms-schedule.json && echo OK
```

### 6. Pause / remove a recurring job  ("stop the hourly stocks")
```bash
jq '(.jobs[] | select(.id=="stocks-hourly") | .enabled) = false' comms-schedule.json > .tmp && mv .tmp comms-schedule.json && echo OK
```

---

## After every change
1. Re-read the file to confirm it's valid JSON and the value is what the client asked for.
2. Text the client a short plain-language confirmation of the new setting.
3. (Optional) mirror the change into `business/comms-preferences.md` for your own readable record — but the JSON is the source of truth.

## Why this matters
The whole point of the SMS channel is to **collect info/knowledge from the client and nudge them to use you more**. Honoring "text me at 7, not 8" and "send my stocks hourly" instantly and correctly is how the client learns the channel actually works and keeps engaging. A change that silently doesn't happen breaks that trust — so always edit the JSON, never just promise.

A host-side validator (`scripts/comms-scheduler/validate-comms-files.py`) repairs malformed JSON as a safety net, but don't rely on it — edit cleanly with `jq`.
