---
name: claim-then-reprobe
description: Use BEFORE acting on any automated health/disk/load alert — take the mesh claim on the alert key, re-probe the raw underlying counter for ~15 seconds, and log the verdict (unchanged / new band / moving) before deciding to act, ack, or suppress. Turns "the alert says X" into "I measured X is Y right now."
metadata:
  tags: [ops, alerts, disk, health, mesh]
---

# claim-then-reprobe — measure before you act on an alert

Automated alerts describe the PAST (they fired at scan time). Every lane that consumes
`jambot-notify.sh` alerts has at least once acted on a stale or self-inflicted reading.
This skill is the 3-step gate between "alert arrived" and "I did something":

## Step 1 — CLAIM (before anything else)

The alert text tells you the key. Take it with the explicit-rc pattern (never `|| exit 0`):

```bash
AGENT_URI=<you>@mesh /home/mike/MIKE-AI/scripts/mesh-claim.sh take "$CLAIM_KEY" 1800; rc=$?
case $rc in 0) ;; 2) exit 0 ;;   # 2 = another lane holds it -> STAND DOWN
  *) echo "mesh-claim rc=$rc is a TOOL FAILURE, not held" >&2; exit $rc ;; esac
```

`CLAIM_KEY` is in the alert body (`claim_key:` frontmatter), e.g. `ops:health:disk--mnt-clients`.
Only exit 2 means held. 3/70/64/75 are tool failures.

## Step 2 — REPROBE the raw counter (~15 seconds)

The alert reports a derived verdict ("90% CRITICAL"). Re-measure the RAW thing it came from,
and sample twice so you can tell level from motion:

```bash
# disk example — two reads, 15s apart, gives you a rate, not just a level:
df -h /mnt/clients | tail -1; sleep 15; df -h /mnt/clients | tail -1
```

For non-disk alerts the same shape applies: read the counter the alert derives from
(load: `/proc/loadavg` twice; memory: `/proc/meminfo` MemAvailable twice; container:
`docker stats --no-stream` twice). Compare against the LAST KNOWN reading
(docs/DISK-DELETE-LIST.md re-fire entries are the disk ledger of record).

## Step 3 — LOG the verdict, then act per verdict

Write the verdict where the next responder will find it (re-fire ledger row, ack note,
history file). Exactly one of:

| Verdict | Meaning | Action |
|---|---|---|
| UNCHANGED | same band as last known reading | refresh ack (TTL ~12h, computed slug), add ledger line, NO SMS |
| MOVING | level same but velocity up | same as UNCHANGED plus: name the growing path (bounded du, `nice/timeout`) |
| NEW BAND | crossed a threshold | diagnose root cause; reclaim if safe; DISK-DELETE-LIST row; SMS only if acute |

## Field-tested traps this encodes

- **An alert's own text can be a week old** — `mesh-claim.sh` prints the prior claim's note;
  read it, then `df` (or the relevant probe) anyway. Measured 2026-09-20 + 09-29: re-fires
  at identical readings for 8+ days were expired-ack mechanics, not disk change.
- **One sample is not a rate.** Two reads 15s apart separate "sitting at 90%" from
  "climbing through 90%" — different responses.
- **Build-first check (disk on /mnt/system):** `pgrep -af 'docker build|jambot-build-images'`
  (verify via /proc cmdline, pgrep -f self-matches). If a build is running, THAT is the cause;
  wait, don't walk.
- **Never walk the whole volume unbounded.** `timeout 120 nice -n 19 ionice -c3 du -x -d1 -BM <mount>`
  then drill into the top dir only. `docker system df -v` for anything docker-owned.
- **Ack mechanics cause most re-fires**: ack filename must be the script's computed slug
  (`ack-health-<key>` lowercased, dashes); line 2 = TTL seconds; an expired ack re-fires the
  alert with ZERO disk change. Verify by reading the ack file back.
- **Release the claim when done**: `mesh-claim.sh release "$CLAIM_KEY"`.
