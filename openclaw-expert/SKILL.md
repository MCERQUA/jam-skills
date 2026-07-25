---
name: openclaw-expert
description: "OpenClaw expertise for JamBot — catalog-indexed router into 761 upstream doc pages plus JamBot-specific overrides and 29 version-anchor corrections (gateway fail-closed on non-loopback bind, pairing/trusted-proxy hardening, database-first SQLite migration, doctor rework, CVE-2026-25253, ClawHavoc supply chain, GLM-5.2/Z.AI thinking ladder, upstream's own `openclaw fleet` multi-tenant model). TRIGGER: teach, debug, configure, or build on OpenClaw."
metadata: {"openclaw": {"emoji": "🧠"}}
---

# OpenClaw Expert

| | |
|---|---|
| **JamBot runs** | `2026.5.7` — verified in `openclaw-test-dev` + the three pinned installer paths, 2026-07-25 |
| **Upstream `latest`** | `2026.7.1-2` (npm, 2026-07-18); a `2026.6.33` maintenance line also exists |
| **Catalog** | 761 pages · rebuilt 2026-07-25 · see `catalog.json` `fetchedAt` |
| **Anchors** | 29 · waves 1–15 (changelog ≤5.2), 16–21 (community), 22–29 (the 5.7→7.1 delta) |

> ⚠️ **We are ~2 months of releases behind the pin, and that gap is not benign.** Anchors #22–#29 cover it. Four of them describe changes that break JamBot's specific deployment shape — **`#22` means every tenant gateway refuses to start on ≥2026.5.17 unless the auth mode is made explicit first.** Read `playbooks/upgrade-5.7-to-7.x.md` before touching `bump-openclaw-version.sh`.

This skill is a **router**, not a textbook. Upstream docs at `docs.openclaw.ai` are authoritative — we index them, layer JamBot deltas, and surface version-specific corrections found in production.

---

## How to use this skill

### 1. Find the right page

```bash
bash {baseDir}/scripts/lookup.sh compaction        # keyword (also searches upstream one-line summaries)
bash {baseDir}/scripts/lookup.sh section:Plugins   # by section
bash {baseDir}/scripts/lookup.sh relevance:high    # 241 JamBot-relevant pages
bash {baseDir}/scripts/lookup.sh anchor:22         # by audit-anchor number (1–29)
bash {baseDir}/scripts/lookup.sh annotated         # pages we've annotated (38)
bash {baseDir}/scripts/lookup.sh stale 60          # annotations not re-verified in 60 days
```

### 2. Read the right layer first

Order matters when answering a question:

1. **`audit-anchors/`** — version-specific corrections. If a page carries an anchor, upstream prose is known to be misleading and the anchor says what to say instead. **Check the anchor's version scope** — several are pin-relative (see the table in `audit-anchors/README.md`).
2. **`overrides/`** — what JamBot does *differently*. The override wins.
3. **`annotations/<page>.md`** — page-specific JamBot notes, burns, related files.
4. **`cache/<page>.md`** — frozen upstream snapshot (lazy, 24h TTL).
5. **Live upstream** — when current truth beats speed: `WebFetch` the URL.

```bash
bash {baseDir}/scripts/fetch-page.sh concepts__compaction        # fetch + cache + print
bash {baseDir}/scripts/fetch-page.sh --path-only plugins__voice-call
bash {baseDir}/scripts/fetch-page.sh --no-cache providers__zai   # force refetch
```

### 3. Refresh when OpenClaw releases

```bash
bash {baseDir}/scripts/refresh-catalog.sh      # fetch llms.txt, diff, regenerate (guarded)
python3 {baseDir}/scripts/sync-annotations.py  # relink annotation files -> pages
python3 {baseDir}/scripts/link-anchors.py      # rebuild anchor <-> page edges
```

Run them **in that order** — `link-anchors.py` rebuilds the anchor edges from scratch each time.

| Exit | Meaning |
|---|---|
| 0 | no page-set change |
| 1 | fetch failed |
| 2 | pages added/removed/renamed — review the diff, annotate new high-relevance pages |
| 3 | **REFUSED** — the diff claimed >20% of pages removed. That is a parser break, not an upstream deletion. Catalog left untouched; fix `LINK_RE` in `build-catalog.py`. |

---

## Audit anchors (29)

When answering ANY question touching these topics, the anchor wins over upstream prose. Full index with version scope + upgrade reading order: **`audit-anchors/README.md`**. Each anchor has a file with sources (changelog lines / PR numbers / Reddit post ids), exact config keys, and affected skill files.

### Wave 1 — changelog audit, v2026.4.20 → v2026.5.2 (applies at our pin)

| # | Topic | One-liner |
|---|-------|-----------|
| 1 | Plugin SDK breaking | `registerEmbeddedExtensionFactory` removed v4.24 → use `registerAgentToolResultMiddleware` |
| 2 | memory-core auto-activates | Bundled `memory-core` + active-memory sub-agent run before every reply unless `plugins.slots.memory: "none"` |
| 3 | Strict tool-allowlist | v5.2 hard-errors: "No callable tools remain after resolving explicit tool allowlist" |
| 4 | Embedded run timeout = 15s | NOT `agents.defaults.timeoutSeconds` — the embedded path has its own low default |
| 5 | Per-file bootstrap caps | TOOLS.md ≈24K chars, MEMORY.md ≈10.5K (auto-truncated with marker). 7.1 made caps per-agent (#84424) |
| 6 | Compaction trigger ≈68% | Plus `midTurnPrecheck` (4.27), `maxActiveTranscriptBytes` (4.26), `memoryFlush.model` (4.27) |
| 7 | `meta.lastTouchedVersion` migration | Auto-runs on first 5.2 start; auto-adds zai to `plugins.allow` when referenced |
| 8 | Bonjour disabled by default | Bundled Compose gateways on bridge networking — `OPENCLAW_DISABLE_BONJOUR=0` opts back in |
| 9 | GLM-5 consecutive-turn fix | v5.2 preserves prior context for z.ai/openrouter/in-house GLM gateways |
| 10 | Anthropic-messages scoping | v4.20 — custom providers MUST set `api: "anthropic-messages"` |
| 11 | plugins.entries vs skills.entries | `plugins.slots.memory: "none"` is the only single-knob memory-core disable |
| 12 | External plugin migration | v5.2 moved ~26 channels/tools out of the bundle. **BlueBubbles fully removed in 5.12** |
| 13 | tools.exec defaults → YOLO | v4.5 — gateway/node host now `security: "full", ask: "off"` |
| 14 | messages.queue.mode default flipped | v4.29 — now `steer` with 500ms followup-fallback debounce |
| 15 | rotateBytes deprecated | v4.27 — use `session.writeLock.acquireTimeoutMs` (default 60s) |

### Wave 2 — r/openclaw community deep-read, 2026-05-23 (applies at our pin)

| # | Topic | One-liner |
|---|-------|-----------|
| 16 | Anthropic subscription cutover | Pro/Max OAuth extraction killed 2026-04-04; use `providers.anthropic.type: "claude-cli"` + `mode: "oauth"`; 5h cap kills cron-on-sub |
| 17 | CVE-2026-25253 + gateway-bind exposure | ~500k instances exposed on `0.0.0.0`; CVE patched, config default still needs `gateway.bind: loopback` |
| 18 | ClawHavoc supply chain | 1,467 malicious ClawHub skills; flagship `capability-evolver` (35k installs) exfiltrating — **mandatory vetting + allowlist** |
| 19 | `openclaw doctor` is destructive | `--fix` can overwrite custom config. **Version-scoped by #25** — reworked in 7.1 |
| 20 | QMD memory default shift | Default markdown+keyword memory under-performs; community uses QMD or memory-lancedb via `plugins.slots.memory` |
| 21 | GLM-5 reliability divergence | Triage rule budget → anti-loop → version migration BEFORE panic-switching the primary |

### Wave 3 — the v2026.5.7 → v2026.7.1 delta, audited 2026-07-25 (does NOT apply at our pin — these describe what breaks when it moves)

| # | Topic | Version | One-liner |
|---|-------|---------|-----------|
| 22 | **Gateway fails closed on non-loopback bind** | 5.17 | 🔴 No shared-secret or trusted-proxy auth → gateway won't start. Image default command no longer bypasses config validation. **The upgrade blocker.** |
| 23 | Pairing + trusted-proxy hardening | 5.12 | 🔴 Setup-code/browser/Control-UI pairing now require approval; trusted-proxy source validation hardened; partial relax in 5.19 |
| 24 | Database-first SQLite migration | 6.5–6.9 | 🟠 State moves into SQLite — agent-repo snapshots + backups silently under-capture. `openclaw backup sqlite` is the new path |
| 25 | `openclaw doctor` reworked | 7.1 | 🟢 Refuses to replace an unreadable `openclaw.json`; shows rather than applies sensitive changes; adds `--lint --only <check>` |
| 26 | Agent cron scoping + WS protocol v4 | 7.1 / 5.19 | 🟠 Agent cron scoped to own jobs, mixed-version fails closed; gateway requires v4 clients (OVU-side check) |
| 27 | GLM-5.2 + Z.AI thinking ladder | 6.8–7.1 | 🟡 `off/low/high/max` replaces binary thinking; 429s distinguish overload from rate-limit → retune the breaker |
| 28 | `openclaw fleet` multi-tenant model | experimental | ℹ️ Upstream now documents per-tenant "cells" — our overrides can no longer claim the docs are silent. **Do not migrate onto it.** |
| 29 | Release-notes ops behavior changes | 6.11 / 7.1 | 🔴 **Crash-loop repair pauses auto-restart — it fights our Layer 1A/2 restart reflex.** Plus: OOM survival (systemd only), readiness-drain signal, cron stuck-call recovery, ClawHub pre-download blocking, durable audit history |

---

## JamBot-specific overrides

`overrides/` holds what JamBot does that docs don't describe. **The override wins.**

| File | Covers |
|---|---|
| `openclaw-json-deltas.md` | the 4 critical fields (`thinkingDefault`, `trustedProxies`, `allowInsecureAuth`, `dangerouslyDisableDeviceAuth`) + compaction tuning |
| `config-edit-policy.md` | NON-NEGOTIABLE `openclaw.json` mutation rule — `openclaw config set` or template, never a direct edit |
| `docker-deployment.md` | `name: jambot-<user>`, `jambot-shared`, no `external: true` in compose |
| `multi-tenant-isolation.md` | per-tenant container pair/network/data tree, the deliberate `jambot-shared` hole, gaps vs upstream's hardened baseline |
| `voice-flow-quirks.md` | single-instance SpeechRecognition rule, wake-word abort loop |
| `skill-allowlist.md` | ClawHub allowlist/blocklist; mandatory vetting before anything enters `/mnt/system/base/skills/` |
| `glm5-turbo-pin.md` | primary-model version policy + fallback chain; community-divergence triage |

## Playbooks (task-shaped recipes)

| File | Covers |
|---|---|
| `upgrade-5.7-to-7.x.md` | **the pending upgrade** — phased plan, gates, rollback. Status: NOT STARTED |
| `provision-new-tenant.md` | openclaw-layer provisioning, verification, version-dependent traps |
| `tune-compaction.md` | live JamBot values, diagnose-before-tune order, the 4.26/4.27 key map |
| `add-new-channel.md` | channel plugin install, vetting, the allowlist hard-error trap |
| `debug-empty-final.md` | the 13-fix MiniMax empty-response recovery cascade |
| `safe-config-edit.md` | atomic, validated, git-tracked `openclaw.json` editing (anchor #19) |
| `skill-install-vetting.md` | pre-install vetting workflow with Skill Vetter (anchor #18) |
| `migrate-to-claude-cli-provider.md` | wiring `providers.anthropic.type: "claude-cli"` post-cutover (anchor #16) |
| `cron-as-sub-agent.md` | heartbeats dispatch sub-agents, never run work directly (anchor #16's 5h cap) |

---

## Files

| Path | Purpose |
|---|---|
| `catalog.json` | 761 pages × {url, section, title, summary, relevance, annotation, audit_anchors, lastVerified, tags} |
| `catalog.json.bak` | previous catalog, written by `refresh-catalog.sh` before every regen |
| `audit-anchors/anchor-NN-*.md` + `README.md` | 29 anchors with version scope + upgrade reading order |
| `annotations/<page-id>.md` | JamBot notes per upstream page (id = url path, `/` → `__`) |
| `cache/<page-id>.md` (+ `.meta.json`) | lazy Markdown snapshot, 24h TTL |
| `overrides/*.md` · `playbooks/*.md` | see tables above |
| `reference/openclaw-2026.3.24-deep-reference.md` | frozen deep reference for the 3.24 era — historical, do not extend |
| `scripts/{build-skill,watchdog,cleanup}.sh` | ⚠️ **ORPHANED, do not run** — March-2026 build scaffolding, referenced by nothing. `cleanup.sh` removes cron entries. Kept per the never-delete rule; banner-marked in-file |
| `references/` | **DEPRECATED** — pre-redesign prose. Do not extend. New work → annotations or playbooks |
| `SKILL.md.pre-2026-05-04` | frozen pre-redesign skill for archaeology |

## Quick reference

**Default ports:** Gateway WS `127.0.0.1:18789`, Clawdbot `18791`, Canvas host `18793`
**Config:** `~/.openclaw/openclaw.json` (JSON5) · **Workspace:** `~/.openclaw/workspace/` · **Logs:** `~/.openclaw/logs/`
**Sessions:** `~/.openclaw/agents/<agent>/sessions/` · **Cron runs:** `~/.openclaw/cron/runs/<jobId>.jsonl`
⚠️ On ≥2026.6.9 a growing share of this is SQLite, not files (anchor #24).

**JamBot paths:**
- Tenant config: `/mnt/clients/<user>/openclaw/openclaw.json`
- Tenant workspace: `/mnt/clients/<user>/openclaw/workspace/`
- Shared skills (mounted into every container): `/mnt/system/base/skills/`
- **Canonical config template:** `/mnt/system/base/templates/openclaw.json`

## Diagnostic commands

```bash
openclaw status
openclaw gateway status
openclaw doctor                               # since v5.2 also runs meta.lastTouchedVersion migration
openclaw doctor --help                        # RE-VERIFY flags after any version bump (anchor #25)
openclaw gateway restart --force --wait 60s
openclaw logs --follow
openclaw channels status --probe              # probes the provider; plain status only reports local belief
openclaw plugins registry --refresh           # v4.25+
openclaw plugins deps                         # v4.27+
openclaw migrate plan --dry-run               # v4.26+
openclaw sandbox explain                      # sandbox / tool-policy / elevated layering
openclaw doctor --lint --all --json           # v7.1+ ONLY — non-mutating structured checks (anchor #25)
openclaw backup sqlite create|list|verify     # v7.x — sanctioned state snapshot (anchor #24)
```

In JamBot, prefix with `sg docker -c "docker exec openclaw-<tenant> ..."`.

## Maintenance discipline

- **After any OpenClaw upgrade:** `refresh-catalog.sh` → `sync-annotations.py` → `link-anchors.py`, in that order. Exit 2 → review the diff and annotate new high-relevance pages. Exit 3 → the parser broke; fix it, don't force it.
- **After a production gotcha:** write an annotation, bump its `last-verified`, re-run `sync-annotations.py`.
- **Annotations older than 60 days:** `bash scripts/lookup.sh stale 60`. If still correct, bump `last-verified` only.
- **Never re-prose upstream docs here.** Cache them. Annotate the deltas.
- **State staleness honestly.** This skill's job is to be trusted about versions; a confident answer from a stale anchor is worse than "the anchor covers ≤6.x, let me check 7.x."

### Known coverage gaps (as of 2026-07-25)

- **The catalog indexes 761 pages; ~50 have actually been read.** Indexed ≠ reviewed. Every page has an upstream title + one-line summary (searchable via `lookup.sh`), which is enough to route — not enough to answer from.
- The 5.7→7.1 audit ran in two passes: a **keyword grep** of the raw 7,500-line changelog (anchors #22–#28, covering config/auth/storage/cron/protocol/provider), then a **read of the curated release notes** for `2026.6.11` and `2026.7.1` at highlight + targeted-section level (anchor #29, which caught operational changes the grep structurally could not — they are described in prose, not key names).
- **Still open:** the **Control UI** overhaul in 7.1 vs our per-tenant Control UI exposure; the **Codex harness**; **macOS/iOS** (we don't use them). Releases `5.20 → 6.10` and `6.33` have **no curated release-notes page** in the catalog and were covered only by the keyword grep.
- **Annotations: 0 stale.** All 33 pre-existing annotations were re-verified 2026-07-25 and 4 new ones added (38 pages carry an annotation; some files are linked from two pages). Each carries a `<!-- verification-stamp -->` block stating exactly what was checked — **config keys against the live `2026.5.7` binary schema, not prose against 7.x docs.** Read the stamp before trusting a page's currency for 7.x.
- 297 pages were added in the 2026-07-25 rebuild. Annotated so far: `gateway/security/exposure-runbook`, `tools/permission-modes`, `concepts/multi-user`, `tools/swarm`. **Still unannotated:** the ClawHub section, `gateway/multi-tenant-hosting` (covered by anchor #28 instead), `tools/code-mode`, `tools/workboard`, and all of `plugins/reference/*`.
- There is **no cron** running `refresh-catalog.sh`. Drift is found only when someone runs it by hand — which is how the parser break went unnoticed from ~2026-06 to 2026-07-25.
- **`openclaw security audit` is not wired into monitoring** despite existing at our pin. It currently reports 1 critical + 2 warn on every tenant — all knowingly accepted; see `annotations/gateway__security__exposure-runbook.md`.
