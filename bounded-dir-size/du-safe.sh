#!/usr/bin/env bash
# du-safe.sh — size a directory WITHOUT ever exceeding the harness tool timeout.
#
# WHY: a plain `du -sh` over a lane tree (~134k files) takes longer than the 120s Bash-tool timeout.
# I hit that at 14:20Z, "solved" it by splitting rate (df, cheap) from attribution (du, backgrounded),
# wrote it into the ledger, filed it in a weekly waste audit at 20:00Z — and re-tripped it at 22:41Z,
# in the foreground, on the same four directories. Knowing the lesson prevented nothing, because the
# `du` call had no guard. This is the guard.
#
# It CANNOT hang: `timeout -k` bounds it, and an unfinished walk returns CANNOT-TELL rather than a
# partial number presented as a total. A truncated du total is worse than no answer — it is a smaller
# number that looks like a measurement.
#
# Usage:  du-safe.sh <dir> [dir...]          # default bound 90s per dir
#         BOUND=30 du-safe.sh /config/desk-work/josh-desk-2
# Exit:   0 all dirs measured · 2 at least one CANNOT-TELL · 3 no args
set -u
BOUND="${BOUND:-90}"
[ $# -gt 0 ] || { echo "usage: du-safe.sh <dir> [dir...]" >&2; exit 3; }
unknown=0
for d in "$@"; do
  if [ ! -d "$d" ]; then printf '  %-44s ABSENT\n' "$d"; unknown=1; continue; fi
  # -k with SIGKILL fallback: TERM alone is not a bound (a du deep in a syscall can ignore it).
  # NO PIPE around timeout: `$?` after a pipeline is the LAST stage's status, so `| cut` swallowed
  # timeout's 124 and this reported rc=0 on the very path that had timed out. The verdict was right
  # (out was empty) but the reason it printed was fiction. Capture timeout's own rc, then cut.
  raw=$(timeout -k 5 "$BOUND" du -sk "$d" 2>/dev/null); rc=$?
  # Adaptive units: my first cut formatted everything in G, so a 16K dir printed "0.0G" — a real
  # number rendered into uselessness. Same family as reporting a truncated total: the value was right
  # and the presentation destroyed it.
  out=$(printf '%s' "$raw" | awk '{k=$1
      if (k>=1048576) printf "%.1fG", k/1048576
      else if (k>=1024) printf "%.1fM", k/1024
      else printf "%dK", k
      exit}')
  if [ "$rc" -eq 0 ] && [ -n "$out" ]; then
    printf '  %-44s %s\n' "$d" "$out"
  else
    printf '  %-44s CANNOT-TELL (walk exceeded %ss; rc=%s) — background it or use df for the total\n' "$d" "$BOUND" "$rc"
    unknown=1
  fi
done
[ "$unknown" = 0 ] || { echo; echo "VERDICT: at least one directory UNMEASURED. Not a zero, not a partial."; exit 2; }
echo; echo "VERDICT: all directories measured within the ${BOUND}s bound."
