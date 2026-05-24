---
anchor: 20
slug: qmd-memory-default-shift
status: partially-confirmed
introduced: community shift ~2026-05
changelog_line: null
upstream_pages:
  - https://docs.openclaw.ai/concepts/memory.md
  - https://docs.openclaw.ai/concepts/active-memory.md
  - https://docs.openclaw.ai/plugins/architecture.md
old_behavior: "Default OpenClaw memory layer is markdown files + keyword search. Synonyms and rephrasings miss; agent re-asks for context it already has."
new_behavior: "Community has converged on hybrid retrieval — QMD plugin (~2-week-old standard per r/openclaw u/desexmachina, 1rkxr9g) for keyword+vector+local-rerank, or memory-lancedb plugin via `plugins.slots.memory: \"memory-lancedb\"`. JamBot tenants on default memory will retrieve worse than tenants on hybrid."
skill_files_affected:
  - annotations/concepts__memory.md (extend with hybrid retrieval recommendation)
  - annotations/concepts__active-memory.md (cross-ref)
  - playbooks/hybrid-memory-sqlite-lance.md (new — full architecture)
sources:
  - https://reddit.com/comments/1rkxr9g (341/78 — "Stop using out-of-box, 3 fixes" — QMD as default-memory replacement)
  - https://reddit.com/comments/1riudg5 (495/95 — "fix memory before it breaks" / QMD as #1 quality-of-life)
  - https://reddit.com/comments/1r49r9m (421/151 — "give your OpenClaw permanent memory" / SQLite-FTS5 + LanceDB hybrid)
  - https://reddit.com/comments/1qzyibu (301/91 — `memory.lancedb` shipped natively)
---

# Anchor #20 — Default memory under-performs; community-standard is hybrid retrieval

## What changed

The OpenClaw default memory layer is markdown files searched by keyword. Synonyms ("schedule" vs "calendar") and rephrasings ("the issue with X" vs "the bug from X") miss. Agents end up re-asking for context they already have.

Two community-standard upgrades:
1. **QMD plugin** — hybrid keyword + vector + local rerank. Per u/desexmachina (1rkxr9g), QMD has been the de-facto standard for "~2 weeks now" as of post date. Likely the path of least resistance.
2. **memory-lancedb plugin** — `plugins.slots.memory: "memory-lancedb"` swaps the default slot. Native to OpenClaw install (per r/openclaw 1qzyibu — LanceDB ships with the binary).

Heavier-weight alternative documented in r/openclaw 1r49r9m: hand-rolled SQLite-FTS5 + LanceDB hybrid with TTL decay tiers and decision-extraction. See `playbooks/hybrid-memory-sqlite-lance.md`.

## Why it matters for JamBot

JamBot tenants currently run the bundled `memory-core` (see anchor-02). For tenants whose conversations span days/weeks, the default keyword-only retrieval is a latent quality issue — they're losing context they actually have on disk.

**Recommendation:** evaluate QMD on one JamBot tenant for two weeks; measure "re-ask" rate (agent asking for info it already wrote to MEMORY.md). If improved, roll to all tenants via `plugins.slots.memory: "qmd"` (or keep as fallback against `memory-core`).

**Note:** QMD vs memory-lancedb relationship is unclear from Reddit alone — QMD may be a wrapper on top of LanceDB. Verify against upstream docs before standardizing across tenants.

## Config snippet (memory slot swap)

```json5
{
  plugins: {
    slots: {
      memory: "memory-lancedb"   // or "qmd" if confirmed available
    }
  }
}
```

## References

- Reddit thread 1rkxr9g — QMD as the post-default fix
- Reddit thread 1riudg5 — QMD as #1 first-72-hours upgrade
- Reddit thread 1r49r9m — hand-rolled hybrid architecture (full playbook)
- Reddit thread 1qzyibu — `memory.lancedb` shipped natively
