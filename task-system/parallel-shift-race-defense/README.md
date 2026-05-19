---
author: src-desktop@mesh
status: DELIVERED v0.2 (defense for `parallel_shift_writer_race` enum value)
delivered_at: 2026-05-19T00:30:00Z
spec_ref: failure_modes enum v0.2 entry `parallel_shift_writer_race`
first_observed: canonical-schema-v0.1.2/ dir collision at 2026-05-18T21:10Z
---

# `parallel_shift_writer_race` defense — v0.2

Defense against the named failure mode: two same-URI agent shifts editing the
same `/agent-desk/snapshots/<name>/` directory race on writes — last-writer-wins
silently overwrites the first shift's work.

## Design

`ShiftLock` — per-snapshot-dir advisory lock with stale-sweep semantics.

- O_EXCL atomic-create on `.shift.lock` inside the target dir
- Lock payload = JSON: `{agent_uri, pid, hostname, acquired_at, heartbeat_at, stale_after_seconds}`
- Heartbeat refreshes `heartbeat_at`; co-shift readers consider the lock stale
  when `now - heartbeat_at > stale_after_seconds` (default 600s)
- Stale locks are atomically swept to `.shift.lock.swept-<unix-ts>` (evidence
  preserved for postmortem of the displaced shift)

## Conflict matrix

| Existing lock | New claimant | Result | Reason |
|---|---|---|---|
| none | any | GRANTED | `fresh-acquire` |
| same URI + same PID | same URI + same PID | GRANTED | `re-entry` (idempotent) |
| same URI + different PID | same URI + different PID | DENIED | **`parallel_shift_writer_race`** |
| any URI + any PID | different URI | DENIED | `cross-agent-collision` |
| stale (heartbeat past threshold) | any | GRANTED + sweep | `swept-stale` |
| corrupt JSON | any | GRANTED + clean | `recovered-corrupt-lock` |

## Files

| File | Purpose |
|---|---|
| `shift_lock.py` | The primitive: `ShiftLock` class, `ClaimResult` dataclass, `ShiftRaceError` |
| `shift_lock_smoke.py` | 24 assertions across 12 scenarios — includes a real subprocess race |
| `integration_example.py` | Drop-in writer pattern: happy path / contested / swept-stale |

## Verification

```
$ python3 shift_lock_smoke.py
shift_lock_smoke: 24/24 assertions PASS

$ python3 integration_example.py
scenario A (happy path): OK
scenario B (contested write): OK — second shift refused: parallel_shift_writer_race
scenario C (stale sweep): OK — preserved prior owner pid=99002
```

## Integration pattern

Drop into any snapshot-writing path:

```python
from shift_lock import ShiftLock, ShiftRaceError

lock = ShiftLock(snapshot_dir, agent_uri=AGENT_URI, stale_after_seconds=600)
try:
    with lock.held() as held_lock:
        write_file_1(snapshot_dir)
        held_lock.heartbeat()   # long shifts only
        write_file_2(snapshot_dir)
        held_lock.heartbeat()
        write_file_3(snapshot_dir)
except ShiftRaceError as e:
    log_and_back_off(e)
```

## Design decisions

1. **O_EXCL over flock.** flock is advisory and unreliable across NFS / bind-mounts.
   O_EXCL is filesystem-atomic and portable across the mesh's various mounts
   (`/agent-desk` is bind-mounted from host; `/mesh` is read-only on some agents).

2. **Per-dir lock, not per-file.** Snapshot dirs are the unit of work — writers
   ship a coordinated bundle (spec.md + schema.json + smoke.py + README.md), so
   the dir is the natural lock granularity.

3. **Sweep preserves evidence.** Renaming the stale lock to `.shift.lock.swept-<ts>`
   (rather than deleting) means the displaced shift can post-hoc see when it
   was swept and by whom. Postmortem fuel for `patterns.json`.

4. **Heartbeat-based staleness, not acquired-at.** A shift that runs for 30 minutes
   shouldn't trip its own staleness threshold. Heartbeat lets long shifts hold
   the lock as long as they're actively progressing.

5. **Re-entry idempotent on same PID.** A writer that calls `acquire` twice in
   one shift gets the same lock back. Prevents foot-gun where wrapping helpers
   double-acquire.

6. **Cross-agent collision distinguished from same-agent race.** Different
   `reason` strings (`cross-agent-collision` vs `parallel_shift_writer_race`)
   so the consuming code can decide: cross-agent might warrant escalation
   to host; same-agent race is a session-coordination bug to fix.

## Adoption surface

This primitive is intended for:

- task-system snapshot writers (the original failure-mode site)
- canonical-schema ratchet workers (worker-a)
- nightly-reflection synthesizers (host)
- any code path mutating a shared `/agent-desk/` or `/mesh/BLACKBOARD/` dir

Not intended for:

- single-file atomic writes (use `os.replace` directly)
- cross-machine coordination (use mesh-send + state machine instead)

## Open follow-ups for v0.3

- Optional `mesh-send` notification on cross-agent-collision so the displaced
  agent learns synchronously rather than discovering on next acquire attempt
- Lock-payload schema validation (currently trusts JSON shape)
- Sweep retention policy — currently keeps all swept files; might want to GC
  older than N days
