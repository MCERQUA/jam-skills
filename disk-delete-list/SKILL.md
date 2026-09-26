---
name: disk-delete-list
description: Standard close-out for ANY disk-pressure incident — verify reclaim candidates individually, write evidence-backed rows to DISK-DELETE-LIST.md, total the pending GB, and hand ONE owner decision to Mike. Never delete, never prune live data, never offer a volume grow.
---

# Disk Delete List — the standard close-out for disk incidents

**The pattern (proven 2026-09-24, /mnt/system 92→93% incident):** an agent answering a disk
alert does NOT delete anything and does NOT improvise prunes. It measures the cause, finds
what is genuinely reclaimable, verifies each candidate INDIVIDUALLY, and writes rows to the
fleet's single delete list. Mike does the deleting — one owner decision, one place.

## When to use

Any disk alert, watchdog refire, or "volume is filling" finding on any volume
(`/mnt/system`, `/mnt/clients`, `/`, the graveyard volume). Pair with the detection side:
`docs/jambot/disk-hygiene-audit-rubric.md` (ghost chains, build cache, rw layers).

## The close-out steps

1. **Name the cause first.** What grew, since when, how fast. A close-out without a cause
   named is not a close-out. Compare with the last audit's numbers — delta and slope.
2. **Suppression discipline:** same-day, same-verdict refires of the same alert get NO new
   SMS and NO new rows. Re-send only on a new band, new velocity, or a changed verdict.
3. **Verify each candidate individually** before listing it. Check the disqualifying traps:
   - pnpm stores: files hard-linked from live `node_modules` → frees 0 B.
   - Docker: an image with 0 containers may be the designated rollback tag for `:latest`
     (check `docs/jambot/docker-images-registry.md`). NEVER `docker system prune` /
     `volume prune` on this box.
   - A "backup" is deletable only when a verified identical copy exists elsewhere (sha256
     both sides). Check `st_nlink` before assuming a copy is free.
4. **Write one row per candidate** to `/home/mike/MIKE-AI/docs/DISK-DELETE-LIST.md`:
   what · size · EVIDENCE it is safe (measured, with date) · exact command. A row without
   evidence does not belong on the list.
5. **Total the pending GB** at the top or in your report so Mike sees what one decision
   frees.
6. **Hand Mike ONE decision**, not a menu. Never write "grow", "resize", or "add a volume"
   as an option — the standing ruling is we are NOT buying more space
   (`jamfact disk.never_buy_space`). Safe reclaim you can do yourself (e.g. `docker builder
   prune -af` when cache is the confirmed pig) is fine; everything else waits for Mike.

## Who does what

- **Any agent** answering a disk incident: steps 1–6, on the volume in question.
- **host@mesh** keeps and grows DISK-DELETE-LIST.md.
- **Mike** does the deleting, by hand, and ticks the row + records `df` after.

## Related

- Artifact: `/home/mike/MIKE-AI/docs/DISK-DELETE-LIST.md`
- Detection rubric: `docs/jambot/disk-hygiene-audit-rubric.md`
- Budget/instruments: `docs/jambot/server-resource-handbook.md` + `/server-efficiency`
- Graveyard (never-delete release valve): `/mnt/HC_Volume_105431542/graveyard/`
