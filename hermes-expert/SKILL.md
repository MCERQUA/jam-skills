---
name: hermes-expert
description: Hermes Agent (Nous Research) expert. Full indexed mirror of hermes-agent.nousresearch.com/docs (169 source + community sections, ~2.5MB of content) plus a JamBot-operational overlay (Z.AI subscription routing, v0.6↔v0.13 production state with v0.14 upstream awareness, mid-flight pipeline, container layout). Includes 13 community-pattern sections from r/hermesagent (Obsidian three-tier memory, model tier list, budget routing, June 2026 Anthropic clawback, local-model stacks, etc. — prefix `community-`). Load by-need via `index.json` + `sections/<id>.json`; don't try to read everything at once.
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
- Mid-flight abort/steer → upstream uses `POST /v1/runs/{run_id}/stop` (v0.13+); JamBot runtime is now v0.13.0 on test-dev (since 2026-05-16) but the plugin still uses the connection-close hack in `plugins/hermes-agent/gateway.py` because the upgrade swap wasn't done. See §6 — clean cancel via `/v1/runs/{run_id}/stop` is now available and should replace the connection-close trick.

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

## 1. Versions running today

| Where | Image | Hermes version | Notes |
|---|---|---|---|
| `hermes-test-dev` (production) | `jambot/hermes:latest` (= `:0.13.1-rc1`, built 2026-05-16) | **v0.13.0** (`2026.5.7`, "Tenacity") | Only live Hermes tenant. Binary at `/opt/hermes/.venv/bin/hermes` (no PATH symlink — use absolute path in `docker exec`). |
| `jambot/hermes:0.6.0-rollback` (preserved) | original v0.6 build | **v0.6.0** (`2026.3.30`) | Insurance — retag to `:latest` + recreate hermes-test-dev for emergency revert. Binary at `/usr/local/bin/hermes` in this image. |

**Upstream latest:** `nousresearch/hermes-agent:v2026.5.16` (**v0.14.0**, "Foundation Release", 2026-05-16). JamBot test-dev is one release behind — see §1.1.
**Docker Hub:** date-based tags only. `v0.X.Y` semver tags do NOT exist on Hub (open question #1 in upgrade doc: confirmed 404 on `:v0.6.0`).

---

## 1.1 Upstream v0.14 awareness (added 2026-05-23)

Production on test-dev is on v0.13.0. v0.14.0 shipped 2026-05-16 (808 commits / 633 PRs / 545 closed issues since v0.13). Not yet swapped into JamBot — captured here so the option is well-scoped.

**What v0.14 brings:**
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

### Status: Hermes path on test-dev is slow/broken — UNRESOLVED since 2026-05-21

Hermes-only voice path on `test-dev` returns empty responses or times out 30–250s on every voice turn. **OpenClaw path is unaffected — still working.** Mike sees "Hey, give me just a moment — I'm getting started" placeholder when the hermes profile is active.

**Symptoms observed during 2026-05-21 session:**
- Hermes logs show `Invalid API response (response.content invalid (not a non-empty list))` retried 3× and giving up
- Direct hermes API calls (`urllib` and OVU's `python-requests`) succeed with real text content
- OVU-side hermes-agent plugin (`gateway.py`) calls hermes but the chain breaks somewhere
- The 2026-05-16 doc (`hermes-plugin-update-resume.md`) said "Voice working" on the same `:latest` image — either something has drifted in the 5 days since OR the working state was a narrow pre-compression window

**Likely causes (not yet confirmed; do not commit to one without re-testing):**
1. z.ai returning thinking-only content blocks despite `thinkingDefault: "off"`
2. Session compression firing every turn (token threshold tripping)
3. Something OVU-side dropping the streamed response

**Important:** all 2026-05-21 hermes config/code experiments were **rolled back to the 2026-05-16 baseline** at session end. The current state IS the post-revert state. Don't reintroduce reverted fixes blind.

**Full reports (READ BOTH BEFORE any hermes fix attempt):**
- [`docs/jambot/hermes-debugging-session-2026-05-21.md`](/home/mike/MIKE-AI/docs/jambot/hermes-debugging-session-2026-05-21.md) — original symptom + dead ends.
- [`docs/jambot/hermes-debugging-session-2026-05-24.md`](/home/mike/MIKE-AI/docs/jambot/hermes-debugging-session-2026-05-24.md) — **CURRENT HANDOFF.** Confirms `reasoning_effort: none` IS working (`thinking=None` in kwargs, verified via live debug patch). Narrowed bug to content-specific trigger in OVU's 57-msg history. Synthetic 57-msg+27-tool+17K-system payloads return text 6/6 — so trigger isn't request shape. Debug patch v2 LIVE on test-dev waiting to dump first/last 5 messages on next voice turn.

**Related memory:** `[[hermes-debugging-session-2026-05-24]]` · `[[hermes-debugging-session-2026-05-21]]` · `[[took-longer-than-expected-fix-2026-05-21]]` · `[[hermes-plugin-update-resume-2026-05-16]]`

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
# → hermes-test-dev   Up <N> hours (healthy)
```

Only one Hermes container exists. No fleet roll planned until slow/broken state resolved.

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

## 7. Credential pools (v0.13 capability — Phase 5 opportunity)

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
- Image: `jambot/hermes:latest` (currently v0.13.0 / `nousresearch/hermes-agent:v2026.5.7`; `:0.6.0-rollback` preserved for emergency revert)
- Hostname: `hermes` (sibling-resolvable via Docker DNS)
- Port: 18790 internal (NOT exposed to host)
- Memory: 2 GB limit, 1.0 CPU
- Restart: `unless-stopped`
- Network: `jambot-<tenant>` bridge (per-tenant isolated)

### Sibling resolution

OVU container reaches Hermes via `ws://openclaw:18790`... wait, that's openclaw. For Hermes: `http://hermes:18790/v1/chat/completions`. Both containers join the per-tenant bridge network.

---

## 10A. Rollback procedure — `:0.6.0-rollback` retag + recreate

**When to use:** any v0.13 regression that can't be fixed forward within 30 min. The rollback image is preserved in the local Docker registry and contains the entire v0.6.0 build.

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
- [ ] **§13A `[[as_document]]` skill directive** — research from upstream skills section corpus + document the v0.13 media routing pattern.
- [ ] Script catalog under `scripts/` parity with openclaw-expert (currently 2/9 — see §13B catalog below).
- [ ] Audit-anchors for parts most likely to drift — see §13B "Audit anchors" section + `scripts/audit-anchors.sh`.
- [ ] Cross-link to `hermes-upgrade-2026.4.30.md` from each section mentioning Phase N work (partially done in §1A; complete in §3 + §6).
- [ ] **Resolve §1A**: hermes path on test-dev still broken. When fix lands, add §1B documenting the resolution + close the loop with `[[hermes-debugging-session-2026-05-21]]` memory.

## 13A. `[[as_document]]` skill directive (v0.13 media routing)

Upstream introduced `[[as_document]]` as a v0.13 skill directive for routing rich media (PDFs, images, structured documents) through skill responses. Not currently used in JamBot — research stub for the next session that needs it. See indexed corpus: `bash scripts/lookup.sh as_document` returns no direct section yet (likely under `user-guide/skills/` — re-run after next upstream sync).

When implemented, document here: directive syntax, where it's parsed (probably `agent/skills/`), what media types are supported, and how the OVU canvas would receive an `[[as_document]]`-tagged response.

## 13B. Audit anchors + drift detection

The fields most likely to silently drift from this skill's documentation:

| Anchor | Current value (verify against runtime) | How to re-check |
|---|---|---|
| Hermes version on test-dev | v0.13.0 (`2026.5.7`, "Tenacity") | `docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes --version` |
| OpenClaw version on test-dev | 2026.5.7 (eeef486) | `docker exec openclaw-test-dev openclaw --version` |
| LLM primary | `zai/glm-5-turbo` | `docker exec openclaw-test-dev openclaw config get agents.defaults.model.primary` |
| LLM fallback | `zai_fb/glm-5-turbo` | `docker exec openclaw-test-dev openclaw config get agents.defaults.model.fallbacks` |
| Hermes binary path | `/opt/hermes/.venv/bin/hermes` (v0.13) or `/usr/local/bin/hermes` (v0.6 rollback only) | `docker exec hermes-test-dev which hermes \|\| ls /opt/hermes/.venv/bin/hermes` |
| Z.AI subscription endpoint | `https://api.z.ai/api/anthropic` | `docker exec hermes-test-dev sh -c 'echo $ANTHROPIC_BASE_URL'` (host .env path is permission-restricted; check container env instead) |
| Config schema version | 23 | `docker exec hermes-test-dev /opt/hermes/.venv/bin/hermes config check` |
| Lane timeout (openclaw) | 45000ms (NOT exposed via `openclaw config set`) | Source-only; check `grep -r "45000" openclaw npm package` |
| Provider chain identity | Z.AI A + Z.AI B (MiniMax dropped) | `docs/jambot/llm-provider-registry.md` |
| Live tenant inventory | 1: hermes-test-dev | `docker ps --filter name=hermes --format '{{.Names}}'` |
| Rollback image | `jambot/hermes:0.6.0-rollback` present (7.4 GB) | `docker images jambot/hermes \| grep rollback` |

**Drift check script:** `bash /mnt/system/base/skills/hermes-expert/scripts/audit-anchors.sh` — runs all of the above and diffs against the documented values, prints a one-line PASS/FAIL per anchor. Run after any hermes/openclaw bump, any LLM-chain change, or any per-tenant Hermes deploy.

## 13C. Script catalog (parity target: openclaw-expert)

| Script | Status | Purpose |
|---|---|---|
| `lookup.sh` | ✅ exists | jq-backed CLI lookup against `index.json` |
| `build-index.py` | ✅ exists | Rebuild `index.json` from `sections/*.json` |
| `audit-anchors.sh` | ✅ NEW 2026-05-23 | Runtime drift detection (see §13B) |
| `refresh-catalog.sh` | ❌ TODO | Re-fetch upstream docs corpus (mirror of `openclaw-expert/refresh-catalog.sh`) |
| `cleanup.sh` | ❌ TODO | Remove stale section files when upstream removes docs |
| `link-anchors.py` | ❌ TODO | Auto-cross-link `[[name]]` references between sections |
| `sync-annotations.py` | ❌ TODO | Sync JamBot-overlay annotations from SKILL.md into per-section JSONs |
| `watchdog.sh` | ❌ TODO | Periodic drift sentinel (cron-driven; alert host if anchors drift) |
| `fetch-page.sh` | ❌ TODO | Re-fetch a single section from upstream when it changes |
| `build-skill.sh` | ❌ TODO | One-shot full skill rebuild from scratch (mirror of `openclaw-expert/build-skill.sh`) |

Open-question note: the openclaw-expert scripts assume the upstream is web-accessible Markdown. Hermes upstream is also web-accessible at `hermes-agent.nousresearch.com/docs/`. Adapting the openclaw-expert scripts should be largely a search-and-replace of the base URL + path pattern.
