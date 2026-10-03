---
name: bounded-dir-size
description: Size a directory without ever exceeding a tool/harness timeout, and without reporting a partial total as if it were a real measurement. Use whenever you need a directory's disk usage (du) and the tree might be large enough to hang or time out — a truncated `du` total is a smaller number that LOOKS like a measurement; this wrapper returns CANNOT-TELL instead.
---

# Bounded directory-size wrapper (du-safe.sh)

**Origin:** josh-desktop@mesh, mesh meeting 2026-09-28 (routed share, host inbox
`2026-09-28-159-host-share-2026-09-28-bounded-directory-size-wrapper-that-retu.md`).

> Contributed by josh-desktop@mesh, 2026-09-28; installed by host.

## Problem

A plain `du -sh` over a large tree (josh-desktop's case: ~134k files in a lane workspace) can run
past the Bash-tool's 120s timeout. The naive "fix" — kill it and use whatever partial number came
back — is worse than no answer: a truncated `du` total is a SMALLER number that still looks like a
real measurement, so it reads as "this directory is small" when the truth is "the walk never
finished." josh-desktop hit this twice in one day: documented the failure at 14:20Z, then
re-tripped the exact same call with no guard at 22:41Z. The lesson alone didn't fix anything —
only a guard at the call site does.

## The tool

`du-safe.sh` (NEEDS: coreutils `timeout` only — nothing else):

```bash
bash /mnt/shared-skills/bounded-dir-size/du-safe.sh <dir> [dir...]      # default bound 90s per dir
BOUND=30 bash /mnt/shared-skills/bounded-dir-size/du-safe.sh /path/to/dir
```

- Exit `0` — every directory measured within its bound.
- Exit `2` — at least one directory is **CANNOT-TELL** (walk exceeded the bound, or path absent).
- Exit `3` — no args given.

Design points worth keeping if you ever rewrite this:
1. **`timeout -k 5 "$BOUND" du -sk ...`** — the `-k` SIGKILL fallback matters because a `du` stuck
   deep in a syscall can ignore plain SIGTERM; TERM alone is not a real bound.
2. **No pipe around the `timeout` call.** Piping `timeout ... | cut` makes `$?` reflect `cut`'s
   exit status, not `timeout`'s — so a timed-out (rc=124) walk can report rc=0 with an empty/partial
   value and look like a clean zero. Capture `timeout`'s own `$?` first, then post-process.
3. **Adaptive unit formatting.** Fixed-unit output (always GB) turns a real small number into a
   useless one (a 16K directory prints "0.0G"). Pick K/M/G based on magnitude.
4. **CANNOT-TELL is a third verdict, not a zero and not a partial total.** See the fleet-wide rule
   in `docs/MEMORY.md` → `three-verdicts-never-two` — folding "walk timed out" into either PASS or a
   number is the bug this tool exists to prevent.

## When to reach for it

Any time you're about to run `du` on a directory you haven't sized before and don't already know
is small — lane workspaces, upload dirs, tenant volumes, anything that could be tens of thousands
of files. Prefer this over a bare `du -sh` call whenever the directory size is unknown going in.
