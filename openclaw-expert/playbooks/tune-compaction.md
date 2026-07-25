# Playbook — Tune compaction, context pruning, and transcript rotation

**When to run this:** sessions going quiet mid-turn, "prep" latency climbing, GLM-5 Turbo timeouts, context filling faster than expected, or after any `contextTokens` / model change.

**Anchors that govern this page:** #6 (compaction trigger ≈68% + the 4.26/4.27 keys), #15 (`rotateBytes` removed), #2 (memory-core runs before every reply), #5 (bootstrap caps).
**Read first:** `overrides/openclaw-json-deltas.md`, and the `/jambot-performance` skill (it owns the operational runbook; this page owns the *why* and the key map).

---

## 0. The rule that comes before any tuning

**Never edit `openclaw.json` directly.** Use `openclaw config set` from inside the container, or edit the template and re-provision. See `overrides/config-edit-policy.md` and anchors #19/#25. A hand-edited config that fails validation takes the tenant's gateway down; on ≤6.x a `doctor --fix` afterwards can compound it.

```bash
sg docker -c "docker exec openclaw-<tenant> openclaw config set agents.defaults.compaction.reserveTokens 80000"
sg docker -c "docker restart openclaw-<tenant>"
```

Template changes require a container restart to take effect — a template edit alone changes nothing for a running tenant.

---

## 1. The live JamBot values (from `/mnt/system/base/templates/openclaw.json`)

Verify against the template before quoting these — the template is the source of truth, this table is orientation.

| Key | JamBot value | Why |
|---|---|---|
| `agents.defaults.contextTokens` | `204000` | GLM-5 Turbo window |
| `compaction.mode` | `"default"` | **NEVER `"safeguard"`** — it delays compaction until 90%+ full and GLM-5 Turbo times out |
| `compaction.reserveTokens` | `80000` | headroom kept free for the reply |
| `compaction.reserveTokensFloor` | `80000` | floor so the reserve can't be squeezed away |
| `compaction.keepRecentTokens` | `16000` | recent turns carried verbatim through a compaction |
| `compaction.memoryFlush.enabled` | `true` | writes durable context to `memory/` before it is summarized away |
| `compaction.memoryFlush.softThresholdTokens` | `6000` | when the flush prompt fires |
| `contextPruning.mode` | `"cache-ttl"` | prune by prompt-cache TTL, not by raw size |
| `contextPruning.ttl` | `"30m"` | matches provider cache behavior |
| `contextPruning.keepLastAssistants` | `3` | |
| `contextPruning.softTrimRatio` / `hardClearRatio` | `0.3` / `0.5` | |
| `bootstrapMaxChars` / `bootstrapTotalMaxChars` | `24000` / `55000` | per-file and total bootstrap caps — anchor #5 |
| `timeoutSeconds` | `360` | **DO NOT revert to 300** — must exceed the longest in-agent skill (online-brand-report ≈322s) plus the exec cap |
| `memorySearch.enabled` | `false` | disabled 2026-07-01: semantic search needed an embeddings provider we don't run on-policy; it was 401-ing fleet-wide every 5 min. Memory *storage* is unaffected. Re-enable only after wiring an on-policy embeddings provider. |

---

## 2. Diagnose before you tune

Work in this order — most "compaction problems" are not compaction.

1. **Is the box under memory pressure?** `free -h` + `vmstat 1 5`. When several unrelated things look slow at once, check the common substrate first (2026-07-25 OOM incident).
2. **Is the cost per-turn rather than per-compaction?** The session-resource-loader runs 5–8s on **every turn** — that is not compaction and trimming client context will not fix it. Measure before attributing.
3. **Is memory-core running before every reply?** Anchor #2: bundled `memory-core` + the active-memory sub-agent run ahead of every reply unless `plugins.slots.memory: "none"`. That is real latency that looks like slow compaction.
4. **Only then** look at compaction: does the transcript actually reach the trigger? Anchor #6 puts it around 68% prompt usage.

```bash
sg docker -c "docker exec openclaw-<tenant> openclaw status"
sg docker -c "docker exec openclaw-<tenant> openclaw sessions"
sg docker -c "docker logs --tail 300 openclaw-<tenant>" | grep -iE "compact|prune|reserve|timeout"
```

---

## 3. Key map for the 4.26 / 4.27 additions (anchor #6)

| Key | Introduced | What it does |
|---|---|---|
| `compaction.midTurnPrecheck` | v4.27 | checks headroom mid-turn instead of only at turn start |
| `session.maxActiveTranscriptBytes` | v4.26 | caps the active transcript by bytes |
| `compaction.memoryFlush.model` | v4.27 | dedicated (cheaper) model for the flush summary |
| pluggable compaction provider | v4.7 | compaction can be routed to a different provider |
| `session.writeLock.acquireTimeoutMs` | v4.27 | **replaces** `session.maintenance.rotateBytes` (removed — anchor #15); default 60s |

If you find `session.maintenance.rotateBytes` in any config or doc, it is stale — it was removed in 4.27.

---

## 4. Changing `contextTokens` or the primary model

Both invalidate the tuning above. When the model changes:

1. Set `contextTokens` to the **new model's** window, not the old one.
2. Re-check `reserveTokens` — it should stay a meaningful fraction of the window, not a number carried over from a differently-sized model.
3. Re-check `timeoutSeconds` against the slowest in-agent skill.
4. Restart the container; verify one real turn end-to-end before rolling to other tenants.

**On ≥2026.6.10** the Z.AI thinking control is no longer binary (anchor #27) — `off/low/high/max` map to Z.AI reasoning effort. `"off"` stays the JamBot default (visible-text failure is a real production burn), but `low` becomes testable on a single tenant.

---

## 5. Do not

- Do NOT set `compaction.mode: "safeguard"`. It is the single change most likely to reintroduce GLM-5 Turbo timeouts.
- Do NOT "fix" slowness by trimming a tenant's bootstrap/context files. Anchor #5 caps already truncate with a marker, and the measured per-turn cost is elsewhere.
- Do NOT tune compaction on the fleet. One tenant, one real conversation, then roll.
