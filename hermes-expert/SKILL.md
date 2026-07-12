---
name: hermes-expert
description: "Hermes Agent (Nous Research) expert — indexed mirror of hermes-agent.nousresearch.com/docs plus the JamBot operational overlay (Z.AI subscription routing, production version state, mid-flight pipeline, container layout) and r/hermesagent community patterns. For health/optimization work START at overlay §0 — the Hermes × OpenVoiceUI optimization playbook (8-touchpoint integration map, ordered audit pass incl. scripts/session-health.sh + audit-anchors.sh, unshipped-upgrade backlog). Load docs by-need via index.json + sections/<id>.json — never read everything at once. TRIGGER when working on hermes-* containers, Hermes config/upgrades, optimizing/debugging the OVU hermes voice path, or Hermes docs questions."
---

# Hermes Expert

This skill has two layers:

1. **Upstream docs corpus** — 156 sections extracted from `https://hermes-agent.nousresearch.com/docs/`, indexed for keyword / env-var / CLI / config / slash-command lookup. Authoritative for "how does feature X work upstream."
2. **JamBot operational overlay** — the rest of this file. Authoritative for "how do we run Hermes inside JamBot tenants" (Z.AI subscription endpoint, container layout, the v0.6 → v0.13 upgrade path, mid-flight abort/steer/interject plugin). Filled in from active session context 2026-05-16; verify against live containers (`hermes --version`, `hermes config show`) before quoting in PRs. **2026-05-23 update:** added §1.1 noting upstream v0.14 (PyPI install, broken `uv pip install`, free Brave/DDGS search) — production still on v0.13, no swap yet.
3. **Community pattern sections** (`sections/community-*.json`) — 13 patterns sourced from r/hermesagent threads: Obsidian three-tier memory, empirical model tier list (May 2026), budget provider routing matrix, Anthropic June 15 clawback rationale for Z.AI routing, local-model proven hardware stacks, multi-Hermes ACP orchestration, skill bundles, Camoufox stealth browser, /debug log-leak warning, TokenTelemetry observability, v0.14 install gotchas, Claude-Code-bundled skill + 2-pod pattern, upstream-watch cron. Each section has a Reddit post URL in the `url` field for traceability.

## How to use this skill

**Don't read the whole skill.** It's structured for selective loading.

### File layout
```
hermes-expert/
├── SKILL.md            ← this file (JamBot ops overlay + index pointer)
├── SCHEMA.md           ← per-section JSON schema (for re-indexing)
├── index.json          ← master index + reverse lookups (~330 KB)
├── sections/<id>.json  ← 156 per-doc JSON files (~2.5 MB total)
├── raw/llms-full.txt   ← source bundle (2.3 MB; only read if a section is missing detail)
├── raw/llms.txt        ← upstream's short index (18 KB)
└── scripts/
    ├── lookup.sh       ← jq-backed CLI lookup
    └── build-index.py  ← rebuild index.json from sections/
```

### Lookup recipes

```bash
ROOT=/mnt/system/base/skills/hermes-expert

# Find which section covers an env var, CLI command, config key, or slash command
bash $ROOT/scripts/lookup.sh --env API_SERVER_KEY
bash $ROOT/scripts/lookup.sh --cli "hermes config show"
bash $ROOT/scripts/lookup.sh --config model.provider
bash $ROOT/scripts/lookup.sh --slash /sessions

# Fuzzy search across titles, summaries, keywords, env vars, CLI, config, slash
bash $ROOT/scripts/lookup.sh "credential pool"
bash $ROOT/scripts/lookup.sh "voice mode"

# Dump one full section JSON (id from the lookups above)
bash $ROOT/scripts/lookup.sh --section credential-pools
# or just: cat $ROOT/sections/credential-pools.json | jq .

# List categories with counts
bash $ROOT/scripts/lookup.sh --list-categories
```

### Programmatic reads (preferred from Claude)

When you need a single section, `Read` the file directly — each section JSON has `summary`, `key_concepts`, `env_vars[]`, `cli_commands[]`, `config_keys[]`, `slash_commands[]`, `code_examples[]`, `gotchas[]`, `cross_refs[]`, `keywords[]`, and `full_text` (verbatim upstream markdown).

```
Read /mnt/system/base/skills/hermes-expert/sections/configuration.json
```

For reverse lookups (e.g. "which docs touch `ANTHROPIC_BASE_URL`?"):

```bash
jq -r '.by_env_var.ANTHROPIC_BASE_URL[]?' $ROOT/index.json
```

### Categories (counts as of 2026-05-23)

| Category | Sections |
|---|---|
| user-guide/features | 42 |
| user-guide/messaging | 27 |
| guides | 27 |
| developer-guide | 25 |
| user-guide (top-level) | 13 |
| **community** *(added 2026-05-23)* | **13** |
| reference | 11 |
| getting-started | 6 |
| integrations | 2 |
| user-guide/skills | 2 |
| docs | 1 |
| **Total** | **169** |

### Community sections (added 2026-05-23 — r/hermesagent deep-read)

Sourced from real Reddit threads, NOT upstream docs. Each has a Reddit post URL in `url` for traceability:

| Section id | Topic | Source post |
|---|---|---|
| `community-obsidian-three-tier-memory` | Vault-as-memory pattern (highest-voted r/hermesagent thread) | 1stz6gd |
| `community-model-tier-list-2026-05` | Empirical 6B-token model ranking | 1tjeitj + 1sj8hyw |
| `community-budget-routing` | Sub-$20 provider matrix + gotchas | 1tewdky |
| `community-anthropic-clawback-2026-06` | Why JamBot routes through Z.AI (June 15 unbundle) | 1tdb404 |
| `community-local-model-stacks` | Five proven hardware+model combos | 1tegogu |
| `community-v0.14-install` | PyPI install + `uv pip install` broken (#8744) | 1teu9u4 |
| `community-claude-code-bundled` | `autonomous-ai-agents/claude-code` + 2-pod pattern | 1tjarlz |
| `community-multi-hermes-orchestration` | Persistent multi-profile via named ACP sessions | 1ss20t0 |
| `community-skill-bundles` | YAML bundles → grouped skills behind one slash command | 1tixe6k |
| `community-camoufox` | Stealth browser backend (v0.7.0) | 1sd1wji |
| `community-tokentelemetry` | Third-party local observability dashboard | 1tixe6k |
| `community-v0.9-debug-leak` | `/debug` slash command log-leak warning | 1skl8le |
| `community-upstream-watch-cron` | Daily upstream-drift detection cron | 1t9gz2f |

Additionally, the following existing sections were patched with Reddit-sourced gotchas + code examples: `provider-routing`, `credential-pools`, `kanban`, `skills`, `curator`, `acp`, `browser`, `web-search`, `tts`, `messaging-telegram`, `installation`, `updating`, `memory`, `docker`, `subscription-proxy`, `ref-slash-commands`, `voice-mode`, `sessions`.

### When the upstream corpus says one thing and JamBot says another

The JamBot overlay (rest of this file) wins for JamBot-tenant operations. Examples where they diverge intentionally:

- Provider routing → upstream documents `anthropic` provider against `api.anthropic.com`; JamBot must point `base_url` at `https://api.z.ai/api/anthropic` for the Z.AI Coding Plan subscription. See §2.
- Container layout → upstream Docker docs describe the official `nousresearch/hermes-agent` image; JamBot ships `jambot/hermes:latest` from `/mnt/system/base/hermes/`. See §10.
- Mid-flight abort/steer → upstream uses `POST /v1/runs/{run_id}/stop` (v0.13+); the JamBot fleet is now **v0.18.0** (all 4 tenants, rolled 2026-07-03 — see §1 for the authoritative version state) so `/v1/runs/{run_id}/stop` is available, but the plugin still uses the connection-close hack in `plugins/hermes-agent/gateway.py` because the swap to the clean-cancel endpoint was never done. See §6 — clean cancel via `/v1/runs/{run_id}/stop` should replace the connection-close trick.

If you're unsure, look it up in the upstream corpus first (it's the source of truth for *how Hermes works*), then check this file for *how we wire it into JamBot*.

### Rebuilding the index

If `sections/*.json` is edited or a new doc is added:

```bash
python3 /mnt/system/base/skills/hermes-expert/scripts/build-index.py
```

That regenerates `index.json` from the section files. Schema for new sections is in `SCHEMA.md`.

**Companion docs (JamBot-side):**
- `/home/mike/MIKE-AI/docs/jambot/hermes-upgrade-2026.4.30.md` — v0.6 → v0.13 upgrade plan v2 with empirical findings
- `/home/mike/MIKE-AI/docs/jambot/hermes-agent-integration/` — original integration plan + research
- `/home/mike/MIKE-AI/docs/jambot/hermes-setup-issues.md` — historical SSE-format patches
- Memory: `hermes-agent.md`, `hermes-midflight-pipeline.md`, `vault-v2.md`, `phase1.5-vault-writes.md`

---

# JamBot Operational Overlay
*Below this line is the JamBot-specific operational reference dumped from active session 2026-05-16. Verify against live containers before quoting in PRs.*

---

## 0. Hermes × OpenVoiceUI optimization playbook (START HERE — added 2026-07-12)

**Purpose:** wherever this skill is loaded, this is the ordered pass that gets Hermes fully healthy AND fully optimized *in the context of the whole OVU stack* — not just "is the container up." Run it when asked to "optimize hermes," when onboarding a new hermes tenant, after any image roll, or on periodic review. Each row/step points to the deeper section.

### The full OVU integration surface (know all 8 touchpoints before changing any one)

| # | Touchpoint | Where | What breaks if wrong |
|---|---|---|---|
| 1 | LLM routing | `/mnt/clients/<t>/hermes/config.yaml` + `.env` (`ANTHROPIC_BASE_URL=api.z.ai/api/anthropic`) | 429 "insufficient balance" (§2) |
| 2 | OVU plugin | `/mnt/clients/<t>/openvoiceui/plugins/hermes-agent/gateway.py` (SSE parse, session headers, empty-turn guard, v1.2.1 inline poison auto-heal, `_refresh_hermes_api_key` self-heal) | silent/empty voice turns (§1A, §8) |
| 3 | Mid-flight routes | plugin `routes/hermes.py` + frontend `convPath()` in app.js (`gateway_id` in localStorage) | abort/steer hits openclaw instead (§6) |
| 4 | Session store | Hermes' OWN SQLite `/opt/data/state.db` — OVU-side POST guards CANNOT protect it | session poison → 30–60s empty turns (§1A) |
| 5 | Networking | tenant bridge `jambot-<t>` ONLY — hermes must NOT join `jambot-shared` (`--hostname hermes` registers DNS on every attached net → cross-tenant round-robin 401s) | intermittent 401 ~1-in-N (§1A second root cause) |
| 6 | Auth | `API_SERVER_KEY` lives ONLY in `/opt/data/.env` (not process env); OVU's `HERMES_API_KEY` env can be stale (plugin self-heals in-process) | false-negative 401 diagnoses (§1A gotchas) |
| 7 | Workspace + canvas | `/workspace` RW + `HERMES_WRITE_SAFE_ROOT=/workspace:/openvoiceui` (canvas dirs are symlinks into `/openvoiceui`); brain read-symlinks in `/opt/data`; bare-name writes = landmine | canvas writes denied / brain symlinks severed (§1C) |
| 8 | Context injection | OVU `routes/conversation.py` prepends the master prompt → every voice turn is ~18KB user content, ~20K prompt tokens cold | cost, latency, and poison-spiral amplification (§1A) |
| 9 | Transcripts → reflections | OVU `routes/transcripts.py save_conversation_turn` is gateway-AGNOSTIC — hermes voice turns land in `openvoiceui/transcripts/<date>/` and flow into the nightly-reflection conversation extract automatically. `gateway` field added to the schema 2026-07-12 (OVU branch `feat/transcript-gateway-attribution`, `cdb4c85`; hotfixed test-dev) so reflections can attribute turns per gateway. | reflections blind to which gateway handled a turn |
| 10 | Fallback pool | `zai-account-B` in every tenant's `anthropic` credential pool (§7) — rotates on 429/402/401 | single-account quota/auth failures take the tenant down |

### Ordered optimization pass

```bash
ROOT=/mnt/system/base/skills/hermes-expert
# [0] Drift + baseline — one command, PASS/FAIL per anchor
bash $ROOT/scripts/audit-anchors.sh

# [1] Session health across the whole fleet (poison = the #1 recurring degrader)
bash $ROOT/scripts/session-health.sh          # read-only; flags empty turns + trailing user-turn spirals
# FLAG on `main` → recovery is `hermes sessions delete main --yes` (§1A). The plugin's v1.2.1
#   auto-heal + health-monitor Check 7.5 should catch spirals now — a manual FLAG that persists
#   means those layers missed it; investigate why before deleting.

# [2] DNS isolation — exactly ONE IP per tenant or the cross-tenant leak is back
for t in test-dev adrian danielle src; do
  sg docker -c "docker exec openvoiceui-$t python3 -c 'import socket; print(\"$t\", sorted(set(r[4][0] for r in socket.getaddrinfo(\"hermes\",0))))'"
done

# [3] Live-turn latency probe (healthy: ~4s warm, ~17s cold; sustained >30s → back to [1])
#     use the §9 "Probe from inside OVU container" recipe with the bearer key from /opt/data/.env

# [4] Config levers per tenant (hermes config show + /opt/data/.env):
#     curator.enabled=false · redaction per canvas needs · auxiliary.compression sane ·
#     HERMES_WRITE_SAFE_ROOT=/workspace:/openvoiceui · GATEWAY_ALLOW_ALL_USERS=true
```

### Known-unshipped upgrades (the standing optimization backlog)

Documented, verified-possible improvements nobody has shipped yet. When asked to "improve/optimize hermes," these are the shovel-ready items:

1. **Clean cancel** — swap `abort_active_run`'s connection-close hack for `POST /v1/runs/{run_id}/stop` (available since v0.13; fleet is v0.18). §4, §6.
2. **Tool-progress SSE events** — `gateway.py:_iter_sse_content` still ignores `event: hermes.tool.progress` lines, so the OVU UI shows nothing while Hermes runs tools. Parse them and surface tool activity (emoji ships in the payload). §5.
3. **Non-Z.AI resilience** — credential pool (`anthropic` pool: Z.AI A + B + direct-Anthropic haiku) to survive the recurring Z.AI tail-latency windows. Needs Mike's call on token spend. §1A, §7.
4. **Context-injection diet** — the ~18KB-per-turn OVU master-prompt injection is the multiplier behind cost, cold-start latency, AND poison-spiral growth (each failed turn stores another 18KB user row). Any reduction in `routes/conversation.py` context assembly pays off three ways. §1A.
5. **Session headers** — verify the plugin sends BOTH `X-Hermes-Session-Id` and `X-Hermes-Session-Key` (§3); Session-Key enables per-tenant long-term memory.
6. **Rebuild a rollback image** — both rollback tags were pruned 2026-07-12 (see §10A); until one is rebuilt or the next version bump preserves a `pre-roll` tag, revert = rebuild-from-source (slow path).

*(Shipped from this list 2026-07-12: session-poison auto-heal — plugin v1.2.1 inline heal + health-monitor Check 7.5.)*

**Before shipping any plugin change:** sync live ↔ catalog ↔ distribution (§8) — a reinstall from a stale catalog regresses hotfixes. After shipping: re-run `audit-anchors.sh` and update §13B anchor values in the same commit.

**Before any container recreate (roll/rollback):** in-container hotfixes (files patched via `docker exec` into `/opt/hermes/...`) live in the container's writable layer and are WIPED by recreate. Proven 2026-07-12: the 644 new-file-mode patch was applied live to all 4 containers by one session, then wiped hours later by the v0.18.2 roll from a parallel session — and its cont-init copy had been appended AFTER `exit 0` (dead code), so nothing re-applied it. Rules: (a) every in-container patch MUST also land in the build's `cont-init-jambot.sh` **above the final `exit 0`**, idempotently; (b) before recreating, `grep` the live container for known patch markers (`else chmod 644` in `tools/file_operations.py` is the current one) and re-verify them after.

---

## 1. Versions running today (updated 2026-07-12 — v0.18.2 roll-forward)

| Where | Image | Hermes version | Notes |
|---|---|---|---|
| `hermes-test-dev` + `hermes-adrian` + `hermes-danielle` + `hermes-src` (production — **4 tenants**) | **`jambot/hermes:v0.18.2`** (built 2026-07-12 from `/mnt/system/base/hermes-v0182-build/`, base `nousresearch/hermes-agent:v2026.7.7.2`) | **v0.18.2** (`2026.7.7.2`, upstream `9de9c25f` — 2026-07-07 infra patch + WhatsApp dep fix) | **ROLLED 2026-07-12** at Mike's direction (sandbox-verified: health, Z.AI subscription completion, SSE format unchanged, schema 32→**33** clean auto-migrate, uid-1000 gateway, multi-root safe-root honored; then per-tenant with session-active guard — `scripts/hermes-upgrade-v0182-roll.sh`, which also DROPS the stale `jambot-shared` attach the old roll script still had). Per-tenant OVU-sibling probes verified real replies + single-IP DNS. Same s6 structure: uid 1000 BAKED at build, seeding via `cont-init.d/05-jambot-seed`, binary `/opt/hermes/.venv/bin/hermes`. §1C behavior still applies. Pre-roll backups: `/mnt/clients/<t>/hermes-backup-20260712-*-pre-v0.18.2`. |
| `jambot/hermes:pre-roll-20260712` | = the v0.18.0 image, tagged before the roll | **v0.18.0** | **Instant-rollback tag** (the new pre-roll rule in action). Keep until v0.18.2 has soaked. |
| `jambot/hermes:v0.18.0` | 1.14GB†, built 2026-07-03 from `hermes-v018-build/` | v0.18.0 | Previous production image (same bits as pre-roll tag). †docker reports 4.84GB uncompressed. |
| `jambot/hermes:v0.15.2` | ~~v0.15.2 build (5.53GB)~~ | **v0.15.2** | ⚠️ **REMOVED 2026-07-06** (Mike-approved early drop, 3 days into stable v0.18.0 — see `docs/jambot/docker-images-registry.md`). Rebuild path: `/mnt/system/base/hermes-v015-build/`. |
| `jambot/hermes:0.6.0-rollback` | ~~original v0.6 build~~ | **v0.6.0** (`2026.3.30`) | ⚠️ **PRUNED** (same reclaim). Binary was at `/usr/local/bin/hermes` in that image. |

**⚠️ 2026-07-12: `docker images jambot/hermes` shows ONLY `v0.18.0` — there is NO instant-revert image anymore.** Rollback = rebuild from the preserved build dirs (`hermes-v015-build/`, `hermes-v018-build/`; upstream bases pullable from Docker Hub by date tag) — see §10A. Before the NEXT version roll, keep the outgoing image tagged (`pre-roll-<date>`) so instant revert is restored.

**Upstream latest (verified 2026-07-03):** **v0.18.0** (`2026.7.1`) — we are CURRENT. v0.16 "desktop app" (2026-06-05), v0.17 "channels/iMessage + image slimming" (2026-06-19), v0.18 "Judgment — verification contracts, /learn, MoA presets, background fan-out" (2026-07-01). None broke our stack: s6/uid-bake/API-server/SSE all held; `HERMES_WRITE_SAFE_ROOT` now accepts multiple dirs (our single `/workspace` still valid); `/resume`+`/sessions` scoped to caller origin (IDOR fix — no impact, OVU uses headers); curator consolidation became opt-in (we disable curator anyway); `compression.summary_*` auto-migrated to `auxiliary.compression`.
**Docker Hub:** date-based tags only (`v2026.7.1` = v0.18.0). `v0.X.Y` semver tags do NOT exist on Hub.

---

## 1.1 Upstream awareness — CURRENT as of 2026-07-03 (historical: the v0.13→v0.15 gap analysis below)

**2026-07-03: fleet rolled to v0.18.0 — see §1.** The section below is the historical v0.13-era gap analysis, kept for the still-valid v0.14+ facts (PyPI install canonical, `uv pip install` broken #8744, Brave/DDGS search).

Historical (2026-05-31): production was v0.13.0 (`2026.5.7`); upstream had shipped:

| Version | Date | Codename | Highlights |
|---|---|---|---|
| **v0.15.2** | 2026-05-29 | (patch) | Packaging fix — bundled `plugin.yaml` manifests in wheel/sdist. **Current latest.** |
| **v0.15.1** | 2026-05-29 | "The Patch" | 28 commits/21 PRs — dashboard reload-loop fix, Docker security, MCP compat. |
| **v0.15.0** | 2026-05-28 | "Velocity" | **MAJOR** — 1,302 commits, core agent code cut **76%**, multi-agent Kanban orchestration, **session search improvements**, security hardening. |
| **v0.14.0** | 2026-05-16 | "Foundation" | PyPI install, xAI Grok OAuth, OpenAI-compatible local proxy, debloat. |

**Relevance to the 2026-05-31 session-poison fix (§1A):** v0.15.0 "session search improvements" + the 76% core-code rewrite may have changed session-store handling — worth checking whether the empty-turn accumulation that poisoned our session is already mitigated upstream before/while planning the swap.

**v0.14 details (still apply to the swap):**
- **Canonical install is now PyPI**: `pip install hermes-agent && hermes`. No more clone-and-shell-installer. JamBot's container bake can simplify.
- **`uv pip install` is BROKEN** at v0.14 — incorrect dep specs trip uv's stricter resolver (Hermes issue #8744). If we adopt v0.14, the bake MUST use vanilla `pip` in a venv, not uv.
- **Brave Search + DuckDuckGo (DDGS)** as native free web-search providers (PR #21337). Could replace Tavily where we use it.
- **Teams plugin** closes the Microsoft Graph stack.
- **xAI SuperGrok + Premium+ Grok access** as a runtime backend.
- **Codex as runtime backend for OpenAI models** — relevant to subscription-proxy patterns.
- **LSP support.**
- **Windows native beta** + Linux Computer Use (works per u/septicdank's debian+x11 result, but not bundled).

**Known v0.13 regressions worth noting in the upgrade decision:**
- `hermes dashboard --tui` shows `[session ended]` after v0.13 update — TUI build fails via PTY WebSocket handler (issue #21801).
- "The new version Hermes Agent v0.13.0 (2026.5.7) seems fairly unstable" (issue #22315).

**Recommendation for the v0.13 → v0.14 swap:**
- Pin to **vanilla `pip install hermes-agent`** in venv, NOT `uv pip install`.
- Drop `curl … | sh` from bake.
- Verify Brave/DDGS web_search providers work with the JamBot session-key + API-server-key wiring before retiring Tavily config (see §3).
- Cross-ref: `community-v0.14-install`, `community-anthropic-clawback-2026-06`.

---

## 1A. Current operational state (overlay — 2026-05-23)

**This section overrides anything below that conflicts.** Verify against live container before quoting in PRs:
```bash
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes --version"
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config show"
```

### Status: Hermes voice path on test-dev — ✅ RESOLVED 2026-05-31

The long-running "empty responses / 30–250s timeouts on every voice turn" bug is **FIXED**. Verified end-to-end through the browser UI: `tools=5`, 864-char response, `[CANVAS:...]` action tags firing, 2–4s replies, no fallback. Hermes now does tool use and drives canvas/music/desktop just like OpenClaw.

**ROOT CAUSE (it was none of the 2026-05-21 hypotheses):** a **poisoned SQLite session** in `/opt/data/state.db` (tables `sessions`+`messages`), keyed by `X-Hermes-Session-Id`. The OVU voice path uses session-id `main`/`hermes-main`, which had accumulated 77 messages incl. **14 empty-content turns** — because the OVU `gateway.py` stored every assistant reply *including empty ones*. Loading that poisoned history made GLM-5-turbo return `response.content invalid (not a non-empty list)` → 3 retries → ~30s → empty → OVU fell back to its **toolless** `zai-direct-slow-empty` path (hence "no tool use / nothing opens / slow").

**Decisive test:** same message, `X-Hermes-Session-Id: main` → 30s empty; any fresh session-id → 2.6s real reply + action tags. The JSON `session_main.json` is just a serialization — deleting it is futile, `state.db` rebuilds it. `hermes sessions list` is the SQLite store (the JSON file mirrors it).

**THE FIX (10-second recovery if it ever recurs):**
```bash
sg docker -c "docker exec -u hermes -e HOME=/opt/data hermes-test-dev /opt/hermes/.venv/bin/hermes sessions delete main --yes"
sg docker -c "docker exec -u hermes -e HOME=/opt/data hermes-test-dev /opt/hermes/.venv/bin/hermes sessions delete hermes-main --yes"
```
**Recurrence prevention shipped:** `plugins/hermes-agent/gateway.py` (live bind-mount copy + source repo) patched to (a) never store empty assistant turns — roll back the user turn on empty, (b) strip empty-content turns before every POST. So `main` can't slowly re-poison. **⚠️ 2026-07-12: this guard turned out INCOMPLETE — see "RECURRED" block below.**

### ⚠️ RECURRED 2026-07-12 — the OVU-side guard does NOT protect Hermes' own store

`main` on test-dev re-poisoned (81 messages, 344KB) and the agent went back to ~60s/turn (`response.content invalid (not a non-empty list)` → 3 retries with backoff). Two poison vectors, **both inside Hermes' `/opt/data/state.db`, which the OVU gateway.py guard never touches** (OVU only POSTs the new message; Hermes rebuilds history from its own SQLite):

1. **Empty assistant tool-call turns** — assistant rows with `content=''` but `tool_calls` set (14 of them, from a 2026-06-05 tool session). Legit in OpenAI wire form, but GLM rejects the replayed history.
2. **Compounding consecutive user turns** — when a turn fails all 3 retries, Hermes has already stored the ~18KB user message (OVU context injection makes every voice turn that big) but never stores an assistant reply. The next attempt appends another 18KB user turn. `main` ended with 6+ back-to-back user turns and no assistant between — each failure makes the next one likelier. This is a death spiral, not a slow drift.

**Recovery (re-verified 2026-07-12):** `hermes sessions delete main --yes` (the `hermes-main` id from the old fix no longer exists — only `main`). Immediately after: first turn 17s (cold, ~20K prompt tokens = system prompt + skills, normal), warm turns 4s.

**Diagnosis gotchas learned while verifying (saves 3 dead-ends next time):**
- `API_SERVER_KEY` is **NOT in the container's process env** — it lives only in `/opt/data/.env`. `docker exec … env | grep API_SERVER_KEY` finds nothing; read the file.
- The OVU container's `HERMES_API_KEY` env var can be stale and 401 — the **live plugin self-heals in-process** (`_refresh_hermes_api_key()` docker-execs the sibling and patches `os.environ`), so a fresh `docker exec openvoiceui-… python3` test process inheriting the stale env will 401 even while the real voice path works. Test with the `/opt/data/.env` key, not the OVU env var.
- Healthy latency baseline: ~4s warm, ~17s on a cold session (20K-token prompt). Sustained >30s + the `not a non-empty list` log line = check `main` for poison first.

**Poison check one-liner** (run when hermes feels slow, before anything else):
```bash
sg docker -c "docker exec hermes-<tenant> python3 -c \"
import sqlite3; db=sqlite3.connect('/opt/data/state.db'); c=db.cursor()
c.execute('SELECT COUNT(*), SUM(CASE WHEN trim(coalesce(content,\\\"\\\"))=\\\"\\\" THEN 1 ELSE 0 END) FROM messages WHERE session_id=\\\"main\\\"')
print('total, empty:', c.fetchone())\""
# empty > 0 or a tail of consecutive user rows → delete session main
```

**Defense layers as of 2026-07-12 (all live):**
1. **Replay sanitize (ROOT FIX, input-side)** — `agent/turn_context.py` patched (marker `JamBot replay sanitize`, applied via cont-init in both build dirs + live fleet): replayed history is normalized before every provider call — empty assistant turns WITH tool_calls get placeholder content `"(tool call)"` (preserves tool-result pairing), empty ones without are dropped. **Proven:** the worst poisoned session (8 empty turns) went from 3-retry/60s-empty to a 3.1s real reply, with correct history recall. This neutralizes existing latent poison WITHOUT purging (no memory loss).
2. **Inline auto-heal (plugin v1.2.1)** — 2 consecutive empty responses → plugin purges the hermes-side session.
3. **Cron backstop** — `jambot-health-monitor.sh` Check 7.5 detects the signature every 5 min.
4. **Write-side guard (still owed, host v1.3)** — stop persisting empty turns into state.db at all; with layer 1 live this is belt-and-suspenders.

### ⚠️ SECOND 2026-07-12 root cause — cross-tenant `hermes` DNS round-robin over jambot-shared (FIXED)

Same session, separate fault: after the session purge, the browser showed "Connected to Hermes gateway — waiting for agent… Reconnecting…" and OVU logs showed `401 Invalid API key` **even after the plugin's self-heal refresh**. Cause: all 4 hermes containers were attached to `jambot-shared`, and **`--hostname hermes` registers a DNS record on every attached network** (aliases are irrelevant — removing them does NOT stop it). So from any OVU on the shared net, `hermes` resolved to ALL four hermes containers and requests round-robined across tenants; a foreign tenant's `API_SERVER_KEY` rejects the bearer → intermittent 401 (worked ~1-in-4). adrian/danielle never showed it only because their OVUs aren't on jambot-shared.

**Fix (2026-07-12):** hermes containers must NOT be on `jambot-shared` at all — nothing consumes hermes over it (OVU uses the per-tenant bridge; monitors use `docker exec`). Detached all 4 live; fixed the three re-attach sources in the same change: `jambot-health-monitor.sh ensure_hermes_alias` (now DETACHES from shared as the heal; still enforces the alias on `jambot-<tenant>`), `jambot-provision-service.py` (dropped the `network connect jambot-shared` step; service bounced), `hermes-recreate-uid1000-test-dev.sh`.

**Diagnostic:** `docker exec openvoiceui-<t> python3 -c 'import socket; print(sorted(set(r[4][0] for r in socket.getaddrinfo("hermes",0))))'` — MUST return exactly ONE IP (the tenant-bridge hermes). Multiple IPs = the leak is back.

**§10 correction:** the per-tenant container spec listing "connect to jambot-shared" for hermes is superseded — tenant bridge ONLY.

**PROVEN FACTS — stop re-litigating these:** Hermes uses the SAME `glm-5-turbo` via Z.AI as OpenClaw; the OVU master prompt IS injected (prepended to the message in `routes/conversation.py`); the openclaw workspace IS mounted RW at `/workspace` in the hermes container; Hermes emits `[CANVAS:...]`/`[MUSIC_PLAY:...]` action tags that OVU parses. Tool use is master-prompt-driven and framework-agnostic — any "hermes can't do X" is a session/setup issue, not a capability gap.

**Watch — plugin drift (§8):** synced as of 2026-07-12 (v1.2.1, md5 `6fae1aad` across catalog + all 5 tenant runtimes + distribution). The standing risk remains: hotfixes land on tenant bind-mounts first, so ANY future hotfix re-opens the gap — a plugin **reinstall from a stale catalog/distribution regresses** fixes. Verify md5 parity (§13B anchor) before any reinstall, and sync live→catalog→distribution after any hotfix.

**Full writeup:** `docs/jambot/hermes-setup-issues.md §9`. Historical dead-ends (for context only, superseded): `hermes-debugging-session-2026-05-21.md`, `hermes-debugging-session-2026-05-24.md`.

**Related memory:** `[[hermes-session-poison-empty-response]]` · `[[hermes-zai-key-staleness-on-rotation]]` · `[[hermes-debugging-session-2026-05-24]]`

### Companion OpenClaw bump — 2026.5.2 → 2026.5.7 SHIPPED on test-dev (2026-05-21)

test-dev's OpenClaw is now 2026.5.7 (was 2026.5.2). Source-repo pin changes uncommitted at session end (tech debt — 5 pinned files at 2026.5.7 on working tree).

- `openclaw --version` → `OpenClaw 2026.5.7 (eeef486)`
- `pdf-tool` stage timing: 5,000ms → **0ms** (deferAutoModelResolution fix)
- `ovui-desktop` plugin had to be **compiled TS→JS via esbuild** — 2026.5.7 rejects TypeScript-only plugins. Loader needs `dist/index.js` or `index.js`, won't load `index.ts` source.
- 14 other tenants still on 2026.5.2 — fleet roll deferred awaiting 24h soak.

Relevance to Hermes: ovui-desktop is shared infra. If you build a new tenant with Hermes after the fleet roll, the plugin must be compiled.

### Slow-empty Z.AI fallback patch — SHIPPED (hotfixed, not rebuilt)

Branch `fix/slow-empty-zai-fallback` on `MCERQUA/OpenVoiceUI`, commit `5d10a1d`. Modifies `routes/conversation.py:2225-2238` (17 → 76 lines): when `llm_inference_ms ≥ 30000` AND response empty AND not already retried → try Z.AI direct call to `api.z.ai/api/anthropic/v1/messages` with `glm-5-turbo` (20s timeout, full agent prompt + context) BEFORE falling through to the "took a bit longer" apology.

**State:** hotfixed via `docker cp` into all 15 live OVU containers + rolling restart. **NOT yet PR'd → dev → main + image rebuilt.** Containers recreated since may have lost the hotfix (test-dev did, verified mid-session). When the source-repo gets the openclaw 5.7 pin commit, bundle this into the same PR.

### LLM provider chain — current truth as of 2026-05-23

§2 + §3 below describe Z.AI subscription routing correctly on the **how**. Current chain identity (overrides any other doc):

- **Primary:** `zai/glm-5-turbo` via `https://api.z.ai/api/anthropic` (account A — env `GLM_API_KEY` = `ZAI_API_KEY`, same value, alias)
- **Fallback:** `zai_fb/glm-5-turbo` via same endpoint (account B — env `ZAI_FALLBACK_API_KEY`)
- **No non-Z.AI fallback exists.** When Z.AI tail-latency >45s (the openclaw lane timeout — see "Known recurring failure mode" below), both A + B fail together.
- **MiniMax is DROPPED indefinitely** (2026-05-19). Account closed. DO NOT propose re-adding — Mike has corrected this multiple times.

Single source of truth: [`docs/jambot/llm-provider-registry.md`](/home/mike/MIKE-AI/docs/jambot/llm-provider-registry.md). Memory pointer: `[[llm-provider-current]]`. Key inventory (fingerprint-only, committable): `docs/jambot/api-key-ledger.json`.

### Known recurring failure mode — Z.AI tail latency × 45s lane timeout

When Z.AI's tail latency exceeds the openclaw 45s lane timeout (happens roughly every couple days for ~5min windows), both primary and fallback fail together since both ARE Z.AI. Symptom in logs:
```
FallbackSummaryError: All models failed (2):
  zai/glm-5-turbo: Command lane "main" task timed out after 45000ms
  zai_fb/glm-5-turbo: Command lane "main" task timed out after 45000ms
```

User sees "Hey getting started" placeholder forever. Recovers in 1-5 min unaided. Durable fix options (Mike's call, not yet picked):
1. Add Anthropic API direct as a third fallback (`claude-haiku-4-5`). Independent of Z.AI, token-pay only when Z.AI fails. **Hermes credential pools (§7) could implement this cleanly via the `anthropic` pool with Z.AI + direct-Anthropic + OpenRouter rotation.**
2. Add another non-Z.AI provider speaking Anthropic protocol.
3. Accept the brief outages.

### Live tenant inventory

```bash
sg docker -c "docker ps --filter name=hermes --format '{{.Names}}\t{{.Status}}'"
# → hermes-test-dev / hermes-adrian / hermes-danielle / hermes-src   Up (healthy)
```

**FOUR Hermes containers as of 2026-07-03** (test-dev, adrian, danielle, src — all `jambot/hermes:v0.18.0`). Every OVU tenant also loads the hermes-agent plugin (GatewayManager: openclaw + hermes; browser `gateway_id` selects per session). The plugin-catalog/distribution drift (§8) was CLOSED 2026-07-03: catalog synced to the fleet's gateway.py (md5 c14c4fa2) and `MCERQUA/openvoiceui-plugins` pushed (637b7a5). foambot's formerly-stale plugin copy was synced to v1.2.0/0.18.0 same day (no hermes container — its OVU correctly skips hermes gateway registration until one is provisioned). The 2026-05-31 session-poison fix (§1A) remains in the fleet gateway.py.

### When debugging next, do this in order

1. Read `docs/jambot/hermes-debugging-session-2026-05-21.md` end-to-end.
2. Verify current state with `docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config show` + try a fresh voice turn to confirm symptom still reproduces.
3. Test the three hypotheses ONE AT A TIME (the 2026-05-21 session jumped between them — that's why nothing stuck).
4. Use §1B for resolution notes when fix lands. Do NOT edit §1A — it captures the un-resolved baseline.

---

## 1B. MiniMax — currently dropped, recoverable

MiniMax was the primary LLM provider from JamBot inception until **2026-04-20** (operational swap to GLM-primary) and was fully dropped on **2026-05-19** when the account closed. Per Mike: "we are not using minimax right now but we might get it back later." This section preserves the known-good MiniMax wiring so reactivation is a config change, not archaeology.

**Status:** DROPPED. Do NOT propose adding back without Mike's explicit approval. Account closed; key value purged from `.openclaw-keys.env` 2026-05-23 (only the guard comment remains).

**Recovery checklist** (when/if MiniMax billing resumes):

1. New MiniMax account → grab API key from `https://www.minimaxi.com/user-center/basic-information/interface-key`.
2. Add to `/mnt/system/base/.openclaw-keys.env`:
   ```bash
   # ── MiniMax-M2.7-highspeed — RESTORED <date> ────────────────────────────
   # Used by: openclaw fallback chain on all tenants
   # Provider: api.minimaxi.chat/v1/text/chatcompletion_v2 (anthropic-messages via mx provider)
   # Status:   active (restored after <date>)
   # Rule:     Provider name in openclaw.json is `mx` NOT `minimax`.
   # Health:   curl -m 10 -H "Authorization: Bearer $MINIMAX_API_KEY" \
   #            -d '{"model":"MiniMax-M2.7-highspeed","max_tokens":5,"messages":[{"role":"user","content":"hi"}]}' \
   #            -H "Content-Type: application/json" \
   #            https://api.minimaxi.chat/v1/text/chatcompletion_v2
   MINIMAX_API_KEY=<value>
   ```
3. Update the dropped→active status in `docs/jambot/api-key-ledger.json` (the `dropped` entry has the prior `previous_value_fingerprint` for verification).
4. Bump the fallback chain — `agents.defaults.model.fallbacks` adds `mx/MiniMax-M2.7-highspeed` AFTER both Z.AI accounts (so Z.AI stays primary). Edit via `openclaw config set` from inside each tenant container per CLAUDE.md rule, not host JSON edits.
5. Hermes-side: if Hermes is rolled to multiple tenants by then and you want it in their pool, `hermes auth add mx --type api-key --api-key <key>` from inside the container (see §7A). Hermes provider config in `config.yaml`:
   ```yaml
   model:
     fallback:
       - provider: mx
         model: MiniMax-M2.7-highspeed
         base_url: https://api.minimaxi.chat
   ```
6. Update `[[llm-provider-current]]` memory + the `MiniMax DROPPED` line in `docs/jambot/llm-provider-registry.md` → "MiniMax RESTORED <date>" + add to active chain section.
7. Update `feedback_env_file_is_a_system_tool` memory if any new operational rule emerged from the restoration.

**Historical context:** MiniMax-M2.7-highspeed was on a coding-plan billing model that lapsed 2026-04-20 ("your current token plan not support model (2061)" error). The pre-purge key fingerprint is recorded in `api-key-ledger.json` `dropped` entries for verification.

The original integration used `Authorization: Bearer` header (not `x-api-key`). The Ollama-Cloud MiniMax beta variant was also dropped at the same time — not recommended for restoration since the direct API works fine.

Related memory: `[[llm-provider-current]]` · `[[feedback_env_file_is_a_system_tool]]` (annotation discipline applies when re-adding the key).

---

## 1C. v0.15 FILE-TOOL PATH RESOLUTION — bare names resolve to HERMES_HOME, NOT cwd (NEW 2026-06-03)

**Discovered during the v0.15.2 test-dev cutover. This is a behavior change from v0.13 that breaks the shared-workspace bare-name access the OpenClaw-replacement model relied on.**

- **v0.13:** the entrypoint ran the gateway with `cd /workspace`, and the file tool resolved relative/bare paths against the process cwd → "read IDENTITY.md" hit `/workspace/IDENTITY.md`. Worked.
- **v0.15:** `/opt/hermes/agent/skill_utils.py:307` — *"Resolve relative paths against HERMES_HOME, not cwd."* The file tool now roots bare/relative names at **HERMES_HOME (`/opt/data`)**, NOT `terminal.cwd` and NOT the process cwd. `main-wrapper.sh` cd's to `/opt/data`; the gateway process cwd ends up `/opt/hermes`. So "read IDENTITY.md" hits `/opt/data/IDENTITY.md` → **"doesn't exist"** → the agent (whose SOUL.md tells it to read brain files by bare name) flounders with no tool result. Symptom looks identical to the session-poison empty-response, but it's a PATH problem.
- **There is NO config to point just the file tool at /workspace.** Only `terminal.cwd` exists (controls the TERMINAL/exec tool's cwd, verified via the corpus — no `file.root`/`workspace_dir` key). `HERMES_HOME=/workspace` is NOT viable: it collides on `skills/` (both Hermes and OpenClaw have one) and dumps Hermes state (state.db/.env/auth.json/config.yaml/sessions/cache) into the shared workspace.

### What actually works (verified on test-dev v0.15.2, 2026-06-03)
- **`/workspace` IS fully read+write** — raw uid-1000 writes succeed (mount is RW, not `:ro`), and file_safety does NOT block it (see below). Agent wrote `/workspace/hermes-rw-proof.md` via full path and it landed; full-path reads work too.
- **Full `/workspace/<path>` and the terminal tool give complete RW** to every workspace file incl. new ones. **This is the reliable access method** — instruct the agent to use `/workspace/` paths, not bare names.
- **Bare-name READS** work ONLY via symlinks from `/opt/data` → `/workspace` (the cont-init hook in `hermes-v015-build/` symlinks `*.md` + `memory/` + `business/`). Convenience for SOUL.md's "read IDENTITY.md" instinct.
- **Bare-name WRITES are a LANDMINE:** the write tool does NOT follow symlinks — it REPLACES `/opt/data/<name>` (the symlink) with a real file, so the write lands in `/opt/data`, NOT `/workspace`, and severs the symlink. Never rely on bare-name writes to workspace files.

### file_safety write guardrail (`/opt/hermes/agent/file_safety.py`)
- `get_safe_write_root()` reads env **`HERMES_WRITE_SAFE_ROOT`**. If SET, file-tool writes are blocked outside it. If UNSET (our default), no safe-root restriction — writes allowed anywhere except the denylist.
- **Write denylist (always blocked):** `auth.json`, `config.yaml`, `webhook_subscriptions.json` (under HERMES_HOME and root), `<root>/.env`, `~/.ssh/config`, `mcp-tokens/`. So the agent CANNOT clobber Hermes' own credential/config plane even with full workspace RW.
- Implication: to fence the agent's writes to ONLY /workspace, set `HERMES_WRITE_SAFE_ROOT=/workspace` (file-tool writes then must resolve under /workspace; gateway-internal writes to /opt/data are NOT via the file tool, so unaffected). Bare-name writes to symlinked brain files would then be allowed (realpath under /workspace) while new bare-name `/opt/data` writes get blocked rather than silently mislocated.

### The fix — APPLIED + VERIFIED on test-dev 2026-06-03
The agent has full RW via `/workspace/` paths + terminal tool. Two pieces shipped in the cont-init hook (`/mnt/system/base/hermes-v015-build/cont-init-jambot.sh`):
1. **Brain read-symlinks** — `*.md` + `memory/` + `business/` from `/workspace` linked into `/opt/data`, so SOUL.md's bare-name READS ("read IDENTITY.md") resolve. Verified: agent reads IDENTITY.md and knows its operator is Mike.
2. **`HERMES_WRITE_SAFE_ROOT=/workspace`** (seeded in `.env`, plumbed to CENV) — fences file-tool WRITES to /workspace. **Verified live:** full `/workspace/x` write succeeds + lands; a BARE-name write is **denied** ("blocked by the guard") instead of clobbering a symlink into /opt/data. Hermes' own `/opt/data` state (state.db/sessions/cache) is written by the gateway internals, NOT the file tool, so it's unaffected; `auth.json`/`config.yaml`/`.env` stay denylisted.

Net: the agent reads its brain by bare name, reads+writes the whole workspace by `/workspace/` path, and bare-name writes fail loudly (agent retries with a path) instead of silently mislocating. Do NOT set `HERMES_HOME=/workspace` (skills/ collision + state clutter).

### 2026-07-12 addendum — safe-root must be `/workspace:/openvoiceui` (canvas writes were denied)

`workspace/canvas-pages|uploads|music|generated_music` are SYMLINKS to `/openvoiceui/*`, and the guard realpath-resolves — so `HERMES_WRITE_SAFE_ROOT=/workspace` alone denied every canvas-page write with the misleading error `"…is a protected system/credential file"` (it's just the outside-safe-root denial). v0.15.2+ supports multiple `:`-separated roots. Fixed to `/workspace:/openvoiceui` in all 4 tenants' `.env` + the `hermes-v018-build/cont-init-jambot.sh` seed default (needs an image rebuild to reach future tenants; existing `.env`s already carry it).

**Agent-side self-model poison (fixed same day):** the tenant skill `skills/software-development/systematic-debugging/references/hermes-container-filesystem.md` (and its SKILL.md pointer) still described the pre-2026-06-03 `:ro` workspace and taught `os.unlink()`-the-symlink-and-rewrite as the workaround — i.e. it instructed the agent to sever its own brain symlinks. Rewritten with the current mount truth on test-dev. If an agent claims "/workspace is read-only" while the mount says `RW=true`, check (a) the gateway's effective `HERMES_WRITE_SAFE_ROOT` (in `/run/s6/container_environment/`, NOT `docker exec env` — exec shows the baked image env, not the with-contenv service env), and (b) stale skill/memory files feeding the belief.

---

## 2. Provider routing — the most important thing to get right

### Z.AI Coding Plan SUBSCRIPTION — the right way

**Subscription endpoint:** `https://api.z.ai/api/anthropic` (Anthropic-messages protocol, NOT OpenAI-wire)
**Documented at:** https://docs.z.ai/scenario-example/develop-tools/claude.md

```yaml
# config.yaml
model:
  provider: anthropic
  default: glm-5-turbo
  base_url: https://api.z.ai/api/anthropic
```

```bash
# .env (current naming as of 2026-05-23 — see docs/jambot/llm-provider-registry.md)
ANTHROPIC_API_KEY=<your-zai-key>           # NOT a sk-ant-api03-... key — the Z.AI key goes here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
API_TIMEOUT_MS=3000000

# In .openclaw-keys.env the SAME value is also exported as:
#   ZAI_API_KEY=<value>      # alias kept for legacy openclaw.json refs
#   GLM_API_KEY=<value>      # the canonical name used by entrypoints
# All three names point at the same Z.AI account A key. See
# docs/jambot/api-key-ledger.json for fingerprint.
```

**Why this works:** Hermes's `anthropic` provider talks Anthropic-messages protocol. Z.AI's `/api/anthropic` facade accepts that protocol, authenticates with the Coding Plan key, and bills against subscription quota (not PAYG balance).

### Z.AI PAY-PER-USE — the wrong way for subscription holders

`https://api.z.ai/api/paas/v4` is the OpenAI-wire endpoint. Subscription keys hit here get **`HTTP 429: Insufficient balance or no resource package`** because the PAYG balance is $0 even though subscription credits are plentiful. The error message is misleading — it's reporting PAYG balance, not subscription state.

**Standing rule (memory `feedback_zai_subscription_not_api`):** ALWAYS use `api.z.ai/api/anthropic` for the JamBot Z.AI subscription. NEVER `open.bigmodel.cn`.

### How to verify which path Hermes is using

Watch container logs after a request. The endpoint will be printed on errors:
```
🌐 Endpoint: https://api.z.ai/api/paas/v4   ← wrong (PAYG)
🌐 Endpoint: https://api.z.ai/api/anthropic ← right (subscription)
```

Or check the Coding Plan dashboard at z.ai — usage % rises on subscription hits, stays flat on PAYG hits.

### Models known to work behind the subscription facade

- `glm-5-turbo` — primary Coding Plan model, 200K context, 128K output. Function-calling, thinking modes, streaming, MCP, structured output. **Currently used by all openclaw tenants.**
- `glm-5.1`, `glm-4.7`, `glm-4.5-air` — covered per upstream docs but **not used in production**. Untested in JamBot. If switching, verify behavior matches `glm-5-turbo` first.

---

## 3. v0.13 vs v0.6 — what changed that BITES

### Refuse-to-start: `API_SERVER_KEY` is mandatory on non-loopback bind

```
ERROR gateway.platforms.api_server: [Api_Server] Refusing to start:
  binding to 0.0.0.0 requires API_SERVER_KEY. Set API_SERVER_KEY or
  use the default 127.0.0.1.
```

**Fix:** mint a key BEFORE the gateway starts, persist to .env. Entrypoint pattern:
```bash
if ! grep -q '^API_SERVER_KEY=' "$HERMES_HOME/.env"; then
  echo "API_SERVER_KEY=$(openssl rand -hex 32)" >> "$HERMES_HOME/.env"
fi
```

**Auth surface:**
- `/health` is UNGUARDED (200 with or without key). Useful for healthchecks.
- `/v1/*` requires `Authorization: Bearer <API_SERVER_KEY>`. Missing → `HTTP 401 {"error":{"message":"Invalid API key","code":"invalid_api_key"}}`.

### Refuse-to-serve: `GATEWAY_ALLOW_ALL_USERS=true` new in v0.13

```
WARNING gateway.run: No user allowlists configured. All unauthorized
  users will be denied. Set GATEWAY_ALLOW_ALL_USERS=true in ~/.hermes/.env
  to allow open access, or configure platform allowlists.
```

We don't gate users at Hermes — nginx + Clerk do that one layer up. So set `GATEWAY_ALLOW_ALL_USERS=true` in the .env.

### Platform allowlists (v0.13 CVSS 8.1 hardening — default is now DENY)

v0.13 rejects strangers by default across messaging platforms. Resolution order (checked top-down, first match wins):

1. Per-platform allow-all flag — e.g. `DISCORD_ALLOW_ALL_USERS=true`
2. DM pairing approved list (interactive pairing flow)
3. Platform-specific allowlists — e.g. `TELEGRAM_ALLOWED_USERS=12345,67890`
4. Global allowlist — `GATEWAY_ALLOWED_USERS=12345`
5. Global allow-all — `GATEWAY_ALLOW_ALL_USERS=true`
6. Default: **DENY**

Per-platform env vars:
- `TELEGRAM_ALLOWED_USERS` — comma-separated Telegram user IDs
- `DISCORD_ALLOWED_ROLES` — comma-separated Discord role IDs (role-based, not user-based)
- `DISCORD_ALLOW_ALL_USERS` — open access on Discord
- `WHATSAPP_ALLOWED_USERS` — comma-separated WhatsApp numbers (E.164)
- `WHATSAPP_ALLOW_ALL_USERS` — open access on WhatsApp

**JamBot status:** we don't run Hermes against Telegram/Discord/WhatsApp today — only OVU voice. The `GATEWAY_ALLOW_ALL_USERS=true` flag is sufficient for the OVU path. If a messaging-platform deploy happens later, add the per-platform allowlist FIRST and verify rejection before enabling allow-all.

### Two session headers (NOT one)

| Header | When added | Scope | Source |
|---|---|---|---|
| `X-Hermes-Session-Id` | v0.7 | per-conversation | OVU `conversation_id` |
| `X-Hermes-Session-Key` | v0.13 | per-tenant long-term memory | OVU `user_id` or tenant name |

Send BOTH on every POST. Our gateway.py at the time of writing this skill sends neither — Phase 3 patch required.

### Schema migration is clean

`hermes config check` against a v0.6-era config.yaml reports `Config version: 23 ✓` with no rewrites or warnings. Schema migrations are non-destructive.

> Historical note: at the time of original write-up the chain was MiniMax-primary / Z.AI-fallback. That's **dropped** as of 2026-05-19 — current chain is Z.AI A primary + Z.AI B fallback. See §1A for current truth.

### Curator (v0.12+) — background skill maintenance, ON by default

```yaml
# config.yaml — disable for first rollout
curator:
  enabled: false
```

Default = `True`, 7-day interval. Lives in `/opt/hermes/agent/curator.py:`. Wakes on cron ticker (`maybe_run_curator()` gated by `config.interval_hours`). Mutates per-tenant skill files under `$HERMES_HOME/skills/` — bundled/hub skills are protected.

### Redaction default flipped BACK to ON in v0.13

(reversed from v0.12 OFF). Opt out via `redaction.enabled: false` if you want raw tool outputs (e.g. for canvas rendering).

### Binary path moved

- v0.6: `/usr/local/bin/hermes` + `/opt/hermes/hermes`
- v0.13: `/opt/hermes/.venv/bin/hermes` (no PATH symlink — `which hermes` returns nothing)

Use absolute path in `docker exec` calls.

---

## 4. API server endpoints (full surface as of v0.13)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/health` | GET | none | Liveness — 200 returns `{"status":"ok","platform":"hermes-agent"}` |
| `/health/detailed` | GET | bearer | Richer status (cross-container probing) |
| `/v1/capabilities` | GET | bearer | Feature-flag manifest. Use to detect v0.13 vs v0.6 at runtime. Returns `{capabilities: {run_events_sse, run_stop, tool_progress_events, session_continuity_header, session_key_header, ...}, endpoints: {...}}` |
| `/v1/models` | GET | bearer | Returns only `{"id":"hermes-agent","owned_by":"hermes"}` — does NOT enumerate underlying providers |
| `/v1/chat/completions` | POST | bearer | OpenAI-compatible. Stream or non-stream. Model field used for profile routing. |
| `/v1/responses` | POST | bearer | Responses API style. Inline image inputs supported. |
| `/v1/runs` | POST | bearer | Start a run async; returns `run_id` (202) |
| `/v1/runs/{run_id}` | GET | bearer | Run status |
| `/v1/runs/{run_id}/events` | GET (SSE) | bearer | Lifecycle events — SEPARATE channel from chat-completions SSE |
| `/v1/runs/{run_id}/stop` | POST | bearer | Clean cancel — **use this** instead of "close HTTP connection to interrupt" hack (replaces `abort_active_run`'s connection-close trick) |

### Capability detection at startup

```python
caps = requests.get(f"{HERMES_BASE_URL}/v1/capabilities",
                    headers={"Authorization": f"Bearer {API_KEY}"}).json()
if caps.get("capabilities", {}).get("run_stop"):
    # v0.13+ — use clean cancel endpoint
else:
    # v0.6 — fall back to HTTP connection close
```

---

## 5. SSE wire format — chat-completions stream

### v0.6 + v0.13 common (content deltas — UNCHANGED across versions)

```
data: {"id":"...","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"...","choices":[{"index":0,"delta":{"content":"Hey there!"},"finish_reason":null}]}

data: {"id":"...","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{...}}

data: [DONE]
```

### v0.10+ NEW: tool-progress events (custom SSE events, interleaved)

```
event: hermes.tool.progress
data: {"tool":"shell","emoji":"💻","label":"echo hello","toolCallId":"call_abc","status":"running"}

event: hermes.tool.progress
data: {"tool":"shell","toolCallId":"call_abc","status":"completed"}
```

**Source:** `/opt/hermes/gateway/platforms/api_server.py:1283-1287` (the only place `event:` lines are written).

**Status values:** `running` | `completed`. Filter: tool names starting with `_` (internal tools like `_thinking`) are NOT emitted.

**Our existing parser (`gateway.py:_iter_sse_content`) is BLIND to these.** It only reads `data:` lines, ignores `event:` SSE headers. Tool-progress events silently dropped today. Phase 3 patch design lives in `hermes-upgrade-2026.4.30.md` §10 Q12.

**Tool emojis come from `tools.registry.get_emoji(tool_name)`** — per-tool `emoji` field. Default fallback `⚡`. **No hardcoded `EMOJI_TOOL_MAP` needed once we adopt tool-progress events** — Hermes ships the emoji in the payload.

---

## 6. Mid-flight pipeline — abort / steer / interject

Built 2026-04-18 after runaway-cascade incident (MiniMax emitted ~300 identical `read_file` calls). Memory: `hermes-midflight-pipeline.md`.

**Rule:** Hermes pipeline is TOTALLY separate from openclaw's. Do NOT modify `services/gateway_manager.py` or core `routes/conversation.py` interject/steer/abort routes — they default to openclaw and return False for hermes sessions. Build hermes-owned parallel primitives in the plugin.

### Plugin-side primitives (in `gateway.py`)

```python
class HermesGateway(GatewayBase):
    def __init__(self):
        self._active_runs: dict = {}  # session_key → {response, event_queue, captured_actions, aborted_by_steer}
        self._active_runs_lock = threading.Lock()

    def abort_active_run(self, session_key) -> bool:
        # close the in-flight requests.Response → Hermes detects SSE disconnect → agent.interrupt()

    def send_steer(self, message, session_key) -> bool:
        # mark aborted_by_steer=True, close connection, spawn new thread with SAME event_queue + captured_actions
        # browser SSE keeps flowing without a visible seam

    def reset_session(self, session_key):
        # calls abort_active_run first so no zombie thread writes to orphan queue
```

### Plugin-side routes (in `routes/hermes.py`)

| Route | Behavior |
|---|---|
| `POST /api/hermes/abort` | direct `HermesGateway.abort_active_run()` |
| `POST /api/hermes/steer` | direct `HermesGateway.send_steer()` + logs user turn |
| `POST /api/hermes/interject` | classifier-routed: `context`/`steer` → `send_steer`; `fast_lane` → parallel `stream_to_queue` on separate `hermes-fast-lane` session_key, 15s timeout, returns inline |

All routes fetch via `gateway_manager.get("hermes")` (NOT via `send_steer` which defaults to openclaw). Returns 503 if hermes gateway not configured.

### Frontend wiring (in OVU app.js)

```js
function convPath(action) {
    const gid = localStorage.getItem('gateway_id') || 'openclaw';
    return gid === 'hermes'
        ? `/api/hermes/${action}`
        : `/api/conversation/${action}`;
}
```

6 hardcoded call sites replaced with `${convPath('abort')}` / `${convPath('interject')}` per the mid-flight memory. Default behavior (openclaw) unchanged.

### v0.13 upgrade opportunity

Replace the "close HTTP connection" trick in `abort_active_run` with `POST /v1/runs/{run_id}/stop`. Cleaner, no connection-leak risk, deterministic.

---

## 7. Credential pools (WIRED 2026-07-12 — Z.AI account B live on all 4 tenants)

**Status:** `zai-account-B` (env `ZAI_FALLBACK_API_KEY` from `.openclaw-keys.env`) is in every tenant's `anthropic` pool with `base_url: https://api.z.ai/api/anthropic`. Rotation fires on 429/402/401 (NOT plain latency — both accounts are Z.AI, so tail-latency windows still hit both; a non-Z.AI third entry remains the §0 backlog item).

**Gotchas learned wiring it (2026-07-12):**
- `hermes auth add` while the gateway is restarting gets silently wiped — add AFTER healthy, then verify in `/opt/data/auth.json`. A settled manual entry DOES survive restarts (tested).
- `hermes auth add anthropic` defaults the entry's `base_url` to `https://api.anthropic.com` — a Z.AI key there 401s on rotation. There is no `--base-url` flag; fix the entry's `base_url` in `/opt/data/auth.json` directly (atomic tmp+rename, keep mode 600).
- `hermes auth list` may show only env-sourced entries; `/opt/data/auth.json` `credential_pool.anthropic` is the truth.
- Env-sourced entries show `token_len=0` in the file — normal (env is read live).
- Anchor: `audit-anchors.sh` checks the pool entry exists with the Z.AI base_url.

v0.13 supports multi-key-per-provider rotation. Different from fallback providers (cross-provider failover) — credential pools rotate within the same provider.

```bash
hermes auth add anthropic --type api-key --api-key sk-ant-api03-second-key
hermes auth list
hermes auth                # interactive wizard
```

Rotation strategies: `fill_first` (default), `round_robin`, `least_used`, `random`. Configured in `config.yaml`:
```yaml
credential_pool_strategies:
  anthropic: least_used
```

Errors trigger rotation:
- 429 → retry once, second 429 rotates (1hr cooldown)
- 402 billing → immediate rotation (24hr cooldown)
- 401 auth → try OAuth refresh, then rotate

Auto-discovery: env vars (`OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`), OAuth tokens (`~/.hermes/auth.json`), Claude Code credentials (`~/.claude/.credentials.json`), custom endpoint config (`model.api_key` in config.yaml).

**JamBot use cases:**
- Multiple Z.AI subscription keys for capacity
- Mix Z.AI subscription + direct Anthropic + OpenRouter under `anthropic` pool for resilience
- Per-tenant key isolation (not yet wired)

Storage: `~/.hermes/auth.json` under `credential_pool` key.

### `hermes auth` CLI — adding + managing credentials

The interactive wizard discovers providers, prompts for key type (api-key | oauth | claude-code | endpoint), and writes to `~/.hermes/auth.json`. Three usage modes:

**1. Wizard (interactive, easiest for first-time setup):**
```bash
sg docker -c "docker exec -it hermes-test-dev /opt/hermes/.venv/bin/hermes auth"
# Dialog:
#   Which provider? [anthropic / openrouter / openai / mx / custom]
#   Authentication type? [api-key / oauth / claude-code / endpoint]
#   API key (or path to credentials file):
#   Label this credential? (optional, e.g. "account-A")
#   Rotation priority? [fill_first / round_robin / least_used / random]
```

**2. Non-interactive add** (scriptable, what we'd use in entrypoints):
```bash
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes auth add anthropic \
  --type api-key --api-key \"$ZAI_API_KEY\" --label zai-account-A"

sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes auth add anthropic \
  --type api-key --api-key \"$ZAI_FALLBACK_API_KEY\" --label zai-account-B"
```

**3. List + remove:**
```bash
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes auth list"
# Shows: provider, type, label, last_used, status (healthy|cooldown|disabled)

sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes auth remove anthropic --label zai-account-B"
```

**OAuth providers** (when applicable):
```bash
sg docker -c "docker exec -it hermes-test-dev /opt/hermes/.venv/bin/hermes auth add anthropic --type oauth"
# Opens browser/SSH-over-tunnel flow. See guide-oauth-over-ssh.json section
# in this skill's corpus for the SSH tunnel pattern when running over remote shell.
```

**Recovery from cooldown:** if a key hits 429 cooldown (1hr) or 402 billing cooldown (24hr), check via `hermes auth list`. Cooldown is automatic; manual reset via `hermes auth reset <provider> --label <label>`.

**Persistence:** all entries in `~/.hermes/auth.json` (mode 0600). Survive container restart. Survive image rebuild ONLY if the volume mount preserves `$HERMES_HOME` (it does in our setup — `/opt/data` bind mount).

---

## 8. Architecture — where plugin files live

### Three trees, two are authoritative

| Path | Role | Source of truth? |
|---|---|---|
| `/mnt/system/base/OpenVoiceUI/plugins/hermes-agent/` | OVU app repo (stub) | NO — `.gitignore:95-117` deliberately stubs community plugins. Only `plugin.json` + `README.md` tracked. |
| `https://github.com/MCERQUA/openvoiceui-plugins` (distribution) | Full plugin payload published here. OVU loader fetches via `services/plugins.py:165 _download_remote_plugin`. | YES (public-facing) |
| `/mnt/system/base/plugin-catalog/hermes-agent/` (host disk) | Bind-mounted into running OVU containers as install source. Not a git repo. | YES (local install source for existing tenants) |
| `/mnt/clients/<tenant>/openvoiceui/plugins/hermes-agent/` | Per-tenant runtime copy (bind-mount from client volume → container `/app/plugins`) | This is what the running OVU loads |

### Plugin install flow

```
admin UI "Install hermes-agent"
  → services/plugins.py:install_plugin()
  → if /mnt/system/base/plugin-catalog/hermes-agent/ exists:
       shutil.copytree() → PLUGIN_DIR / hermes-agent  (= /app/plugins/hermes-agent inside container)
    else:
       _download_remote_plugin() → fetch from GitHub openvoiceui-plugins repo
  → manifest.lifecycle.post_install.requires_container == True
       → POST http://provision-service:5200/provision/hermes/<username>
       → host runs jambot-provision-service.py:provision_hermes()
           → creates /mnt/clients/<user>/hermes/ dir
           → writes config.yaml + .env
           → docker run hermes-<user> with jambot/hermes:latest
  → returns container_id, status
```

### Drift between trees as of 2026-05-16

- test-dev's runtime copy is **newest** (713 lines gateway.py, Apr 18 — has mid-flight pipeline)
- plugin-catalog was stale (557 lines, Apr 10) — **fixed in this session**
- GitHub openvoiceui-plugins distribution was stale (557 lines) — **fixed by PR #4 (https://github.com/MCERQUA/openvoiceui-plugins/pull/4) in this session**

### Plugin pin — UPDATED 2026-07-12 (v1.2.1 inline auto-heal)

- **plugin v1.2.1 / gateway.py md5 `6fae1aad`** across catalog + all 5 tenant runtime copies (test-dev/adrian/danielle/src/foambot) + distribution (`MCERQUA/openvoiceui-plugins` `d921835`, pushed). New in 1.2.1: **inline session-poison auto-heal** — 2 consecutive empty responses on a hermes session → plugin docker-execs the sibling and deletes that session (timeouts/conn-errors not counted). Loaded LIVE on test-dev; other tenants pick it up on their next OVU restart (health-monitor Check 7.5 covers them meanwhile).
- **Upstream versions since our v0.18.0 image pin (checked 2026-07-12):** v0.18.1 + v0.18.2 (both 2026-07-07; ~667-commit infra patch + WhatsApp dep fix; curated notes deferred to v0.19). NOT rolled — no identified fix for our poison-replay issue; evaluate in sandbox before any image bump.

### Plugin pin — 2026-07-03 (v0.18.0 fleet roll, superseded by v1.2.1 note above)

- **manifest:** plugin v1.2.0 / `hermes_version 0.18.0` / `container.image nousresearch/hermes-agent:v2026.7.1` across ALL copies (plugin-catalog, 4 tenant runtimes, OVU-repo seed, distribution). gateway.py = the fleet's self-heal version (38681B, md5 **c14c4fa2**) — catalog was 4.6KB BEHIND the fleet (a fresh install would have REGRESSED tenants); synced catalog ← test-dev runtime (backup `gateway.py.bak-20260703-pre-v018sync`).
- **distribution:** `MCERQUA/openvoiceui-plugins` rebased onto origin/main + PUSHED (`637b7a5`) — the §8 drift is CLOSED.
- **provisioner:** `jambot-provision-service.py` pins `jambot/hermes:v0.18.0`; service bounced (Restart=always) so the pin is live.
- **foambot (updated same day on Mike's ask):** its stale orphan plugin copy (v1.0.0/hermes 0.6.0) was synced to v1.2.0/0.18.0 too. It has NO hermes container, and the v1.2.0 gateway_manager correctly SKIPS registering the hermes gateway when `HERMES_HOST` is unset — so foambot's OVU shows 1 gateway (openclaw) until a hermes container is provisioned. GOTCHA: a backup DIR inside `plugins/` gets probed by BOTH loaders (gateway_manager + services.plugins — the latter even without plugin.json, erroring on a duplicate blueprint); park plugin backups as a DOT-dir (`.hermes-agent.bak-*`), which the loaders skip.

### Plugin pinned to Hermes v0.15.2 — 2026-06-03 (historical)

- **manifest:** `plugin.json` → `version 1.1.0`, `hermes_version 0.15.2` across ALL copies (plugin-catalog, per-tenant runtime, distribution clone, OVU-repo seed). gateway.py is current (34015B, empty-turn fix, md5 245ce97c) across catalog/runtime/distribution — **NO gateway.py code change needed for v0.15** (protocol backward-compatible; voice verified). The stale OVU-repo disk gateway.py (gitignored) was synced to match.
- **image tag** is pinned in `jambot-provision-service.py` → `jambot/hermes:v0.15.2` (and `-e HERMES_UID` DROPPED — see §1C / §10 note). plugin.json `hermes_version` is informational metadata; the provisioner is the actual image source.
- **git:** distribution committed local main `137b1fd` (NOT pushed); OVU-repo pin on isolated local branch `chore/hermes-v0.15.2-plugin-pin` (NOT pushed, feature branch left pristine). Both pending Mike's push/PR — metadata-only, the catalog+provisioner install path already yields correct v0.15.2 tenants without them.
- Full record: `docs/jambot/hermes-v0.15-cutover-checklist.md`.

---

## 9. Common operations

### View what Hermes is using

```bash
# v0.13 (current — test-dev): binary at /opt/hermes/.venv/bin/hermes (no PATH symlink)
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config show"

# v0.6 (rollback image only): binary at /usr/local/bin/hermes
# Use this path ONLY if you've retagged :0.6.0-rollback to :latest for emergency revert.
```

### Validate config

```bash
sg docker -c "docker exec <container> /opt/hermes/.venv/bin/hermes config check"
# Reports schema version + which env vars are set/missing
```

### Change provider on the fly

```bash
# v0.13 — use the v0.13 binary path
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config set model.provider anthropic"
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config set model.base_url 'https://api.z.ai/api/anthropic'"
# Then restart to pick up env changes (env-file is read at start, not hot-reloaded):
sg docker -c "docker restart hermes-test-dev"
```

> Container restart MUST happen in the 04-09 Toronto window (08-13 UTC) per
> `feedback_container_restart_window_toronto_4am_9am`. Use `at` to schedule
> if you're outside the window. Exception: production-blocking emergencies.

### Build a sandbox image (without disturbing prod `:latest`)

```bash
# Pin Dockerfile to dated tag, build to test tag:
sg docker -c "docker build --pull \
  -f /mnt/system/base/hermes/Dockerfile.0.13-sandbox \
  -t jambot/hermes:0.13.0-test /mnt/system/base/hermes/"
```

### Run a sandbox container (no impact on test-dev)

```bash
API_KEY=$(openssl rand -hex 32)
sg docker -c "docker run -d --name hermes-013-sandbox \
  --hostname hermes-013-sandbox \
  -p 127.0.0.1:18791:18790 \
  --env-file /mnt/clients/test-dev/hermes/.env \
  -e API_SERVER_KEY=$API_KEY \
  -e GATEWAY_ALLOW_ALL_USERS=true \
  -e ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic \
  -e API_TIMEOUT_MS=3000000 \
  -v /tmp/hermes-013-sandbox/data-prod-copy:/opt/data \
  --memory 2g --cpus 1.0 \
  jambot/hermes:0.13.0-test"
```

### Probe from inside OVU container (no published port)

```bash
sg docker -c "docker exec openvoiceui-test-dev python3 -c \"
import urllib.request, json
req = urllib.request.Request('http://hermes:18790/v1/chat/completions',
    data=json.dumps({'model':'hermes-agent','messages':[{'role':'user','content':'hi'}]}).encode(),
    headers={'Content-Type':'application/json'})
print(urllib.request.urlopen(req).read().decode())
\""
```

### Snapshot config before edits

```bash
TS=$(date +%Y%m%d-%H%M%S)
sg docker -c "cp /mnt/clients/test-dev/hermes/config.yaml /mnt/clients/test-dev/hermes/config.yaml.bak-${TS}-pre-X"
```

### `hermes config migrate` — when do you need it?

The current schema version is **23** (as of v0.13.0). `hermes config check` reports `Config version: 23 ✓` without rewriting on v0.6-era configs in our tests — schema migrations through v0.13 have been backward-compatible reads.

**When `hermes config migrate` matters:**
- When upgrading to a future major version that introduces a NEW schema key that requires a non-default value to be set (rare; v0.13 added keys but all defaulted to safe values).
- When the upstream changelog says "breaking: schema X" — read the upstream release notes BEFORE the next bump.

**Safe operating procedure:**
```bash
# Snapshot first (always)
TS=$(date +%Y%m%d-%H%M%S)
sg docker -c "cp /mnt/clients/test-dev/hermes/config.yaml /mnt/clients/test-dev/hermes/config.yaml.bak-${TS}-pre-migrate"

# Dry-run check (reports what would change)
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config check"

# Apply migration only if check reports needed
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config migrate"

# Diff the result against snapshot
diff /mnt/clients/test-dev/hermes/config.yaml.bak-${TS}-pre-migrate /mnt/clients/test-dev/hermes/config.yaml
```

**If a migrate goes bad:** restore from `.bak-*` snapshot, restart container.

---

## 10. JamBot-specific Hermes container layout

### Per-tenant directory

```
/mnt/clients/<tenant>/hermes/
  config.yaml            ← model, agent, personalities, compression
  config.yaml.bak-*      ← timestamped snapshots
  .env                   ← API keys + endpoint vars
  auth.json              ← OAuth tokens + credential pool state (v0.13)
  auth.lock              ← file lock
  channel_directory.json ← messaging platform configs
  cron/                  ← scheduled jobs
  hooks/                 ← shell hooks (v0.12+ replacement for BOOT.md)
  logs/                  ← gateway logs, curator reports
  sessions/              ← multi-turn conversation state
  sessions-poisoned-backup-* ← quarantined sessions from runaway-cascade incidents
  skills/                ← per-tenant skill files (auto-curated by Curator if enabled)
  bin/, cache/           ← runtime
```

Mounted into container as `/opt/data` (the `HERMES_HOME`).

### Per-tenant container

- Name: `hermes-<tenant>`
- Image: `jambot/hermes:latest` (currently v0.13.0 / `nousresearch/hermes-agent:v2026.5.7`; `:0.6.0-rollback` preserved for emergency revert; `:pre-uid1000-20260531` = pre-RW-replacement backup)
- Hostname: `hermes` + `--network-alias hermes` (OVU reaches it via `HERMES_HOST=hermes`; alias self-heals via `jambot-health-monitor.sh`)
- **User: uid/gid 1000 (== OpenClaw `node`)** — set via `HERMES_UID`/`HERMES_GID` (Dockerfile ENV + provisioner `-e`). Makes Hermes a true drop-in OpenClaw replacement. NOTE: `docker exec` without `-u` is ROOT; the gateway is gosu-dropped to 1000.
- **Workspace: `/mnt/clients/<t>/openclaw/workspace → /workspace` READ-WRITE** (was `:ro`). Bidirectional RW with OpenClaw. Shared identity wired in the entrypoint: SOUL.md symlink + `cd /workspace` + `terminal.cwd: /workspace` → Hermes loads/updates OpenClaw's SOUL/AGENTS/IDENTITY/TOOLS/MEMORY/memory.
- Port: 18790 internal (NOT exposed to host)
- Memory: 2 GB limit, 1.0 CPU
- Restart: `unless-stopped`
- Network: `jambot-<tenant>` bridge (per-tenant isolated)
- **Full architecture:** `docs/jambot/hermes-setup-issues.md §10`. Recreate: `scripts/hermes-recreate-uid1000-test-dev.sh`.

### Sibling resolution

OVU container reaches Hermes via `ws://openclaw:18790`... wait, that's openclaw. For Hermes: `http://hermes:18790/v1/chat/completions`. Both containers join the per-tenant bridge network.

---

## 10A. Rollback procedure — `:0.6.0-rollback` retag + recreate

> **⚠️ 2026-07-12 STATUS: BOTH rollback images (`v0.15.2` + `0.6.0-rollback`) were PRUNED** during the /mnt/system disk reclaim — the retag procedure below cannot run as written. Current rollback path: **rebuild from source dirs** — `docker build /mnt/system/base/hermes-v015-build/` (v0.15.2) or `hermes-v018-build/` with an older base tag; upstream base images remain pullable from Docker Hub by date tag (`nousresearch/hermes-agent:v2026.X.Y`). Config auto-migrated to schema 32 at the v0.18 roll — restore per-tenant `config.yaml.bak-*` / `hermes-backup-20260703-*` when reverting below v0.18. The steps below remain valid once you've rebuilt-and-tagged a rollback image. Rule going forward: tag the outgoing image `pre-roll-<date>` before every version bump.

**When to use:** any regression that can't be fixed forward within 30 min.

**Verify the rollback image is still present BEFORE you start:**
```bash
sg docker -c "docker images jambot/hermes --format '{{.Repository}}:{{.Tag}}\t{{.CreatedAt}}'" | grep rollback
# Expect: jambot/hermes:0.6.0-rollback   2026-04-01 ...
# If missing → DO NOT proceed. The rollback safety net is gone; investigate before risking the recreate.
```

**Steps (run in 04-09 Toronto window unless production emergency):**

```bash
# 1. Snapshot the current :latest tag so it's recoverable
sg docker -c "docker tag jambot/hermes:latest jambot/hermes:pre-rollback-$(date -u +%Y%m%d-%H%M%S)"

# 2. Retag the rollback image to :latest
sg docker -c "docker tag jambot/hermes:0.6.0-rollback jambot/hermes:latest"

# 3. Snapshot the test-dev hermes config (v0.13 config may have keys v0.6 rejects)
TS=$(date -u +%Y%m%d-%H%M%S)
cp /mnt/clients/test-dev/hermes/config.yaml /mnt/clients/test-dev/hermes/config.yaml.bak-${TS}-pre-rollback
cp /mnt/clients/test-dev/hermes/.env       /mnt/clients/test-dev/hermes/.env.bak-${TS}-pre-rollback

# 4. Stop + remove the v0.13 container
sg docker -c "docker stop hermes-test-dev && docker rm hermes-test-dev"

# 5. Recreate using the existing compose (which now pulls :latest = v0.6.0)
sg docker -c "docker compose -f /mnt/clients/test-dev/compose/docker-compose.yml \
  --env-file /mnt/clients/test-dev/compose/.env up -d hermes"

# 6. Verify version
sg docker -c "docker exec hermes-test-dev /usr/local/bin/hermes --version"
# Expect: v0.6.0 (binary path is /usr/local/bin/hermes on rollback, NOT /opt/hermes/.venv/bin/)

# 7. Verify health
sg docker -c "docker exec hermes-test-dev curl -s http://localhost:18790/health"
```

**Config compatibility risks during rollback:**
- v0.13 config keys that v0.6 doesn't recognize → check `docker logs hermes-test-dev` after step 5 for "unknown key" warnings.
- `API_SERVER_KEY` is v0.13-only — v0.6 ignores it (no harm), but the OVU side may still be sending it as bearer.
- `GATEWAY_ALLOW_ALL_USERS` is v0.13-only — v0.6 has no equivalent gate (or no gate at all).
- Two session headers `X-Hermes-Session-Id` (v0.7+) and `X-Hermes-Session-Key` (v0.13) — v0.6 will ignore the Session-Key header; conversation may lose long-term memory.

**Forward path after rollback:**
- Document why the rollback was needed in `[[hermes-debugging-session-<date>]]` memory + append to `docs/jambot/hermes-debugging-session-2026-05-21.md` (or a new dated report).
- Retain the `pre-rollback-*` tag until the v0.13 path is fixed forward.
- Do not delete the `:0.6.0-rollback` tag (insurance for the next regression).

---

## 11. The active session's high-impact findings (2026-05-16)

These should become memory entries or land in the upgrade-doc; capturing here so they survive context reset:

1. **`api.z.ai/api/anthropic` is the subscription endpoint, not `api.z.ai/api/paas/v4`.** Hermes's `anthropic` provider with `base_url` override routes there correctly. Z.AI key goes in `ANTHROPIC_API_KEY` env. Verified end-to-end on test-dev 2026-05-16 — first successful 200 with `prompt_tokens: 11199` against the subscription quota.

2. **The "no balance" 429 was misleading.** Pay-per-use balance was $0 (subscription doesn't fund PAYG), so calls to `/api/paas/v4` 429'd even though subscription credits were 96% available.

3. **`jambot/hermes:latest` is bricked at the LLM layer on prod** unless config.yaml is patched to point at subscription endpoint. test-dev fixed in this session; any other tenant who later installs hermes-agent would hit the same wall until their config is patched. Phase 3 should bake the subscription routing into the entrypoint/template.

4. **Phase 1 of the upgrade plan completed in this session.** PR #4 against `MCERQUA/openvoiceui-plugins` syncs the mid-flight pipeline code from runtime to distribution. plugin-catalog/ on host also synced. test-dev runtime unchanged (it already has it).

5. **v0.13.0 sandbox image built (`jambot/hermes:0.13.0-test`, 8.91 GB)** and preserved for Phase 3. SSE wire format pulled from source: `event: hermes.tool.progress` with `{tool,emoji,label,toolCallId,status:running|completed}`. Our parser is blind to it; patch design in upgrade doc §10.

6. **GLM-5-Turbo is the right subscription model.** 200K context, 128K output, function-calling, thinking modes. Already correctly named in config — just needed the right endpoint.

---

## 11A. "Hermes is not responding" — decision tree

Use this when a tenant reports the voice agent stuck on "Hey, give me just a moment — I'm getting started" or otherwise silent on the hermes profile.

```
START
 │
 ▼
[1] Is the container even running?
    sg docker -c "docker ps --filter name=hermes-<tenant>"
    │
    ├─ NOT RUNNING → check `docker logs hermes-<tenant>` for crash cause
    │                 common: missing API_SERVER_KEY (v0.13 refuses to start on non-loopback)
    │                 or GATEWAY_ALLOW_ALL_USERS=true missing (refuses to serve)
    │                 → see §3. Restart in 04-09 Toronto window unless emergency.
    │
    └─ RUNNING → continue
 ▼
[2] Is the API server up?
    sg docker -c "docker exec hermes-<tenant> curl -s http://localhost:18790/health"
    Expect: {"status":"ok","platform":"hermes-agent"}
    │
    ├─ NO RESPONSE / connection refused → API_SERVER bind failed.
    │                                     check API_SERVER_KEY env, restart container.
    │
    └─ YES → continue
 ▼
[3] Direct hermes call from inside the OVU sibling — does Hermes return content?
    sg docker -c "docker exec openvoiceui-<tenant> python3 -c \"
    import urllib.request, json
    req = urllib.request.Request('http://hermes:18790/v1/chat/completions',
        data=json.dumps({'model':'hermes-agent','messages':[{'role':'user','content':'hi'}]}).encode(),
        headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ['API_SERVER_KEY']})
    print(urllib.request.urlopen(req, timeout=30).read().decode())
    \""
    │
    ├─ 200 + real text → Hermes itself is fine. The OVU plugin is dropping the response.
    │                    → check `plugins/hermes-agent/gateway.py` SSE parser, session header forwarding,
    │                      stream-to-queue thread. This is the 2026-05-21 likely culprit (see §1A).
    │
    ├─ 200 + empty content / `not a non-empty list` → Z.AI returning thinking-only blocks OR
    │                                                  session compression firing every turn.
    │                                                  → check `thinkingDefault: "off"` in hermes config.yaml
    │                                                  → check compression threshold + session state size
    │                                                  → restart container with fresh session ($HERMES_HOME/sessions/ rotated)
    │
    ├─ 401 "Invalid API key" → bearer token wiring broken between OVU and Hermes.
    │                          → check API_SERVER_KEY is the same in hermes container and in OVU's hermes-agent plugin env
    │
    ├─ 429 "Insufficient balance" → wrong Z.AI endpoint!
    │                                → check ANTHROPIC_BASE_URL = api.z.ai/api/anthropic (subscription)
    │                                  NOT api.z.ai/api/paas/v4 (PAYG, $0 balance even with subscription).
    │                                  See §2. Fix in config.yaml + restart.
    │
    ├─ timeout >30s → Z.AI tail-latency event. Check `docker logs hermes-<tenant>` for endpoint.
    │                  If Z.AI is just slow, recovers in 1-5min unaided. See §1A "Known recurring failure mode."
    │                  Durable fix: credential pool with non-Z.AI fallback (§7).
    │
    └─ connection refused → Hermes is up but not bound to expected port. Check config.api_server.port.
 ▼
[4] If Hermes returns content but OVU UI still silent:
    → check OVU `routes/conversation.py` slow-empty Z.AI fallback patch is in place (see §1A).
      It hotfix-shipped 2026-05-21 but containers recreated since may have lost it.
    → check `services/gateways/compat.py` to confirm OVU is routing to hermes (gateway_id),
      not falling back to openclaw.
    → check browser-side localStorage `gateway_id` value — if empty, defaults to openclaw.
```

**Don't skip steps.** The 2026-05-21 debugging session jumped between hypotheses 3 (multi-cause) and that's why nothing stuck. Walk the tree top-to-bottom, observe before fixing.

---

## 12. Upstream PR cross-reference index

These are the upstream Hermes PRs that our patches / capability use depends on. Use when reading a section that says "after PR #XXXX" and you need to confirm the feature is in the running version.

| PR | Title (paraphrased) | Hermes version landed | Where in this skill it matters |
|---|---|---|---|
| **#7455** | `API_SERVER_KEY` mandatory on non-loopback bind | v0.13.0 | §3 "Refuse-to-start" — our entrypoint mints this key |
| **#7500** | tool-progress SSE custom events (`event: hermes.tool.progress`) | v0.10.0 | §5 — our parser is BLIND to these; Phase 3 patch needed |
| **#15842** | `POST /v1/runs/{run_id}/stop` clean cancel | v0.13.0 | §4, §6 — replaces connection-close hack |
| **#16588** | `toolCallId` + `status` fields on tool-progress payload | v0.10.0+ | §5 — payload schema |
| **#17277** | Curator (background skill maintenance, ON by default) | v0.12.0 | §3 "Curator" — we set `curator.enabled: false` for first rollout |
| **#18233** | `[[as_document]]` skill directive (v0.13 media routing) | v0.13.0 | §3, §13A below |

**To verify a PR is in the running version:**
```bash
sg docker -c "docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes --version"
# Then cross-reference upstream changelog at:
#   https://github.com/NousResearch/hermes-agent/releases
```

Capability detection at runtime: `GET /v1/capabilities` (bearer-authed) returns a feature-flag manifest. If you need to programmatically check, parse the JSON for the capability name (e.g. `run_stop`, `tool_progress_events`).

## 13. Skill TODOs

- [x] **DONE 2026-05-23:** decision tree for "Hermes is not responding" — see §11A.
- [x] **DONE 2026-05-23:** §1A current-operational-state overlay (broken status, OpenClaw 5.7 bump, slow-empty fallback patch, current LLM chain, dropped MiniMax, recurring 45s lane-timeout failure mode).
- [x] **DONE 2026-05-23:** §1B MiniMax dropped-but-recoverable section (Mike's "we might get it back later" note).
- [x] **DONE 2026-05-23:** §3 platform allowlists (`TELEGRAM_ALLOWED_USERS`, `DISCORD_ALLOWED_ROLES`, `WHATSAPP_*`, deny-default).
- [x] **DONE 2026-05-23:** §7 `hermes auth` wizard + non-interactive add walkthrough.
- [x] **DONE 2026-05-23:** §9 `hermes config migrate` safe operating procedure.
- [x] **DONE 2026-05-23:** §10A runnable rollback procedure (`:0.6.0-rollback` retag + recreate).
- [x] **DONE 2026-05-23:** §12 upstream PR cross-reference index (5 PRs we depend on).
- [x] **DONE 2026-07-12:** §0 Hermes × OVU optimization playbook (integration-surface map, ordered audit pass, unshipped-upgrade backlog) + `scripts/session-health.sh` fleet poison scanner + audit-anchors updates (rollback images pruned → rebuild-dirs anchor; gateway.py fleet-parity check).
- [ ] **Rebuild a rollback image** — both `:v0.15.2` and `:0.6.0-rollback` pruned 2026-07-12; tag outgoing image `pre-roll-<date>` at the next version bump (§10A).
- [ ] **§13A `[[as_document]]` skill directive** — research from upstream skills section corpus + document the v0.13 media routing pattern.
- [ ] Script catalog under `scripts/` parity with openclaw-expert (currently 2/9 — see §13B catalog below).
- [ ] Audit-anchors for parts most likely to drift — see §13B "Audit anchors" section + `scripts/audit-anchors.sh`.
- [ ] Cross-link to `hermes-upgrade-2026.4.30.md` from each section mentioning Phase N work (partially done in §1A; complete in §3 + §6).
- [x] **DONE 2026-05-31 — Resolve §1A**: hermes path on test-dev FIXED. Root cause = poisoned SQLite session (`state.db`, session-id `main`, 14 empty turns). Fix = `hermes sessions delete main` + gateway empty-turn guard. Documented in §1A + `docs/jambot/hermes-setup-issues.md §9` + memory `[[hermes-session-poison-empty-response]]`.

## 13A. `[[as_document]]` skill directive (v0.13 media routing)

Upstream introduced `[[as_document]]` as a v0.13 skill directive for routing rich media (PDFs, images, structured documents) through skill responses. Not currently used in JamBot — research stub for the next session that needs it. See indexed corpus: `bash scripts/lookup.sh as_document` returns no direct section yet (likely under `user-guide/skills/` — re-run after next upstream sync).

When implemented, document here: directive syntax, where it's parsed (probably `agent/skills/`), what media types are supported, and how the OVU canvas would receive an `[[as_document]]`-tagged response.

## 13B. Audit anchors + drift detection

The fields most likely to silently drift from this skill's documentation:

| Anchor | Current value (verify against runtime) | How to re-check |
|---|---|---|
| Hermes version (fleet, 2026-07-12) | v0.18.2 (`2026.7.7.2`, upstream `9de9c25f`) on all 4 tenants | `docker exec hermes-<t> /opt/hermes/.venv/bin/hermes --version` |
| OpenClaw version on test-dev | 2026.5.7 (eeef486) | `docker exec openclaw-test-dev openclaw --version` |
| LLM primary | `zai/glm-5-turbo` | `docker exec openclaw-test-dev openclaw config get agents.defaults.model.primary` |
| LLM fallback | `zai_fb/glm-5-turbo` | `docker exec openclaw-test-dev openclaw config get agents.defaults.model.fallbacks` |
| Hermes binary path | `/opt/hermes/.venv/bin/hermes` (v0.13+) or `/usr/local/bin/hermes` (v0.6 rollback only) | `docker exec hermes-test-dev which hermes \|\| ls /opt/hermes/.venv/bin/hermes` |
| Z.AI subscription endpoint | `https://api.z.ai/api/anthropic` | `docker exec hermes-test-dev sh -c 'echo $ANTHROPIC_BASE_URL'` (host .env path is permission-restricted; check container env instead) |
| Config schema version | 33 (auto-migrated at v0.18.2 first boot; was 32 at v0.18.0) | `docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config check` |
| Lane timeout (openclaw) | 45000ms (NOT exposed via `openclaw config set`) | Source-only; check `grep -r "45000" openclaw npm package` |
| Provider chain identity | Z.AI A + Z.AI B (MiniMax dropped) | `docs/jambot/llm-provider-registry.md` |
| Live tenant inventory | 4: hermes-{test-dev,adrian,danielle,src} | `docker ps --filter name=hermes --format '{{.Names}}'` |
| Rollback images | `jambot/hermes:pre-roll-20260712` (= v0.18.0, tagged before the 07-12 roll-forward) + `v0.18.0` tag; older rollbacks (v0.15.2, 0.6.0) remain pruned — rebuild dirs `hermes-v015-build/` / `hermes-v018-build/` / `hermes-v0182-build/` | `docker images jambot/hermes` |
| Provisioner image pin | `jambot/hermes:v0.18.2` (service bounced 2026-07-12) | `grep 'jambot/hermes:' /home/mike/MIKE-AI/scripts/jambot-provision-service.py` |
| Plugin pin (catalog + fleet + distribution) | plugin v1.2.1 / hermes_version 0.18.2 / gateway.py md5 **6fae1aad** (41875B, inline poison auto-heal — synced 2026-07-12) | `md5sum /mnt/system/base/plugin-catalog/hermes-agent/gateway.py` + same md5 on all tenant runtime copies |
| Session health (poison) | 0 empty turns + no trailing user-turn run in `main` on all tenants | `bash scripts/session-health.sh` (this skill) |
| JamFlow lane | n101 plat:hermes — poll_hermes glow (agent.log POST markers) + live per-tenant plugin table in desc | `curl -s 127.0.0.1:8777/api/watch/graph` |

**Drift check script:** `bash /mnt/system/base/skills/hermes-expert/scripts/audit-anchors.sh` — runs all of the above and diffs against the documented values, prints a one-line PASS/FAIL per anchor. Run after any hermes/openclaw bump, any LLM-chain change, or any per-tenant Hermes deploy.

## 13C. Script catalog (parity target: openclaw-expert)

| Script | Status | Purpose |
|---|---|---|
| `lookup.sh` | ✅ exists | jq-backed CLI lookup against `index.json` |
| `build-index.py` | ✅ exists | Rebuild `index.json` from `sections/*.json` |
| `audit-anchors.sh` | ✅ 2026-05-23 (updated 2026-07-12: rollback-rebuild-dirs anchor + gateway.py fleet-parity check) | Runtime drift detection (see §13B) |
| `session-health.sh` | ✅ NEW 2026-07-12 | Read-only session-poison scanner, whole fleet — empty turns + trailing user-turn spirals (§0 step 1, §1A) |
| `refresh-catalog.sh` | ❌ TODO | Re-fetch upstream docs corpus (mirror of `openclaw-expert/refresh-catalog.sh`) |
| `cleanup.sh` | ❌ TODO | Remove stale section files when upstream removes docs |
| `link-anchors.py` | ❌ TODO | Auto-cross-link `[[name]]` references between sections |
| `sync-annotations.py` | ❌ TODO | Sync JamBot-overlay annotations from SKILL.md into per-section JSONs |
| `watchdog.sh` | ❌ TODO | Periodic drift sentinel (cron-driven; alert host if anchors drift) |
| `fetch-page.sh` | ❌ TODO | Re-fetch a single section from upstream when it changes |
| `build-skill.sh` | ❌ TODO | One-shot full skill rebuild from scratch (mirror of `openclaw-expert/build-skill.sh`) |

Open-question note: the openclaw-expert scripts assume the upstream is web-accessible Markdown. Hermes upstream is also web-accessible at `hermes-agent.nousresearch.com/docs/`. Adapting the openclaw-expert scripts should be largely a search-and-replace of the base URL + path pattern.
