---
name: hermes-expert
description: Hermes Agent (Nous Research) expert. Full indexed mirror of hermes-agent.nousresearch.com/docs (156 source docs, ~2.3MB of upstream content) plus a JamBot-operational overlay (Z.AI subscription routing, v0.6↔v0.13 diff, mid-flight pipeline, container layout). Load by-need via `index.json` + `sections/<id>.json`; don't try to read everything at once.
---

# Hermes Expert

This skill has two layers:

1. **Upstream docs corpus** — 156 sections extracted from `https://hermes-agent.nousresearch.com/docs/`, indexed for keyword / env-var / CLI / config / slash-command lookup. Authoritative for "how does feature X work upstream."
2. **JamBot operational overlay** — the rest of this file. Authoritative for "how do we run Hermes inside JamBot tenants" (Z.AI subscription endpoint, container layout, the v0.6 → v0.13 upgrade path, mid-flight abort/steer/interject plugin). Filled in from active session context 2026-05-16; verify against live containers (`hermes --version`, `hermes config show`) before quoting in PRs.

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

### Categories (counts as of 2026-05-16)

| Category | Sections |
|---|---|
| user-guide/features | 42 |
| user-guide/messaging | 27 |
| guides | 27 |
| developer-guide | 25 |
| user-guide (top-level) | 13 |
| reference | 11 |
| getting-started | 6 |
| integrations | 2 |
| user-guide/skills | 2 |
| docs | 1 |
| **Total** | **156** |

### When the upstream corpus says one thing and JamBot says another

The JamBot overlay (rest of this file) wins for JamBot-tenant operations. Examples where they diverge intentionally:

- Provider routing → upstream documents `anthropic` provider against `api.anthropic.com`; JamBot must point `base_url` at `https://api.z.ai/api/anthropic` for the Z.AI Coding Plan subscription. See §2.
- Container layout → upstream Docker docs describe the official `nousresearch/hermes-agent` image; JamBot ships `jambot/hermes:latest` from `/mnt/system/base/hermes/`. See §10.
- Mid-flight abort/steer → upstream uses `POST /v1/runs/{run_id}/stop` (v0.13+); current JamBot runtime is still v0.6 and uses the connection-close hack in `plugins/hermes-agent/gateway.py`. See §6.

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

**Upstream latest:** `nousresearch/hermes-agent:v2026.5.7` (v0.13.0, "Tenacity Release", 2026-05-07).
**Docker Hub:** date-based tags only. `v0.X.Y` semver tags do NOT exist on Hub (open question #1 in upgrade doc: confirmed 404 on `:v0.6.0`).

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
# .env
ANTHROPIC_API_KEY=<your-zai-key>           # NOT a sk-ant-api03-... key — the Z.AI key goes here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
API_TIMEOUT_MS=3000000
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

- `glm-5-turbo` — primary Coding Plan model, 200K context, 128K output. Function-calling, thinking modes, streaming, MCP, structured output.
- `glm-5.1`, `glm-4.7`, `glm-4.5-air` also covered per docs.

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

### Two session headers (NOT one)

| Header | When added | Scope | Source |
|---|---|---|---|
| `X-Hermes-Session-Id` | v0.7 | per-conversation | OVU `conversation_id` |
| `X-Hermes-Session-Key` | v0.13 | per-tenant long-term memory | OVU `user_id` or tenant name |

Send BOTH on every POST. Our gateway.py at the time of writing this skill sends neither — Phase 3 patch required.

### Schema migration is clean

`hermes config check` against a v0.6-era config.yaml reports `Config version: 23 ✓` with no rewrites or warnings. Our MiniMax-primary / Z.AI-fallback ordering survives the version jump. Schema migrations are non-destructive.

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
sg docker -c "docker exec hermes-test-dev /usr/local/bin/hermes config show"
# Or v0.13:
sg docker -c "docker exec <container> /opt/hermes/.venv/bin/hermes config show"
```

### Validate config

```bash
sg docker -c "docker exec <container> /opt/hermes/.venv/bin/hermes config check"
# Reports schema version + which env vars are set/missing
```

### Change provider on the fly

```bash
# v0.13 — proper API
sg docker -c "docker exec hermes-test-dev /usr/local/bin/hermes config set model.provider anthropic"
sg docker -c "docker exec hermes-test-dev /usr/local/bin/hermes config set model.base_url 'https://api.z.ai/api/anthropic'"
# Then restart to pick up env changes (env-file is read at start, not hot-reloaded):
sg docker -c "docker restart hermes-test-dev"
```

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

## 11. The active session's high-impact findings (2026-05-16)

These should become memory entries or land in the upgrade-doc; capturing here so they survive context reset:

1. **`api.z.ai/api/anthropic` is the subscription endpoint, not `api.z.ai/api/paas/v4`.** Hermes's `anthropic` provider with `base_url` override routes there correctly. Z.AI key goes in `ANTHROPIC_API_KEY` env. Verified end-to-end on test-dev 2026-05-16 — first successful 200 with `prompt_tokens: 11199` against the subscription quota.

2. **The "no balance" 429 was misleading.** Pay-per-use balance was $0 (subscription doesn't fund PAYG), so calls to `/api/paas/v4` 429'd even though subscription credits were 96% available.

3. **`jambot/hermes:latest` is bricked at the LLM layer on prod** unless config.yaml is patched to point at subscription endpoint. test-dev fixed in this session; any other tenant who later installs hermes-agent would hit the same wall until their config is patched. Phase 3 should bake the subscription routing into the entrypoint/template.

4. **Phase 1 of the upgrade plan completed in this session.** PR #4 against `MCERQUA/openvoiceui-plugins` syncs the mid-flight pipeline code from runtime to distribution. plugin-catalog/ on host also synced. test-dev runtime unchanged (it already has it).

5. **v0.13.0 sandbox image built (`jambot/hermes:0.13.0-test`, 8.91 GB)** and preserved for Phase 3. SSE wire format pulled from source: `event: hermes.tool.progress` with `{tool,emoji,label,toolCallId,status:running|completed}`. Our parser is blind to it; patch design in upgrade doc §10.

6. **GLM-5-Turbo is the right subscription model.** 200K context, 128K output, function-calling, thinking modes. Already correctly named in config — just needed the right endpoint.

---

## 12. Skill TODOs (refine after context reset)

- [ ] Add a "decision tree" for "Hermes is not responding" — branches: 429 → subscription endpoint check; 401 → API_SERVER_KEY check; empty stream → check fallback provider chain; container won't start → check `API_SERVER_KEY` + `GATEWAY_ALLOW_ALL_USERS`.
- [ ] Add a script catalog under `/mnt/system/base/skills/hermes-expert/scripts/` mirroring `openclaw-expert/scripts/`.
- [ ] Audit-anchors for the parts most likely to drift: provider list, env var names, endpoint paths, binary path, config schema version.
- [ ] Reference index of upstream PRs we patched against: #7455 (API_SERVER_KEY), #7500 (tool-progress events), #16588 (toolCallId/status), #15842 (run-stop), #17277 (Curator).
- [ ] Cross-link to `hermes-upgrade-2026.4.30.md` from each section that mentions Phase N work.
- [ ] Add a "rollback" section: how to revert `jambot/hermes:latest` to a known-good tag if a bump goes bad.
- [ ] Document the `hermes auth` interactive wizard with sample dialog.
- [ ] Document `hermes config migrate` behavior (haven't tested yet — schema 23 readers don't seem to need it, but check what `migrate` actually does).
- [ ] Cover the v0.13 platform allowlists: `TELEGRAM_ALLOWED_USERS`, `DISCORD_ALLOWED_ROLES`, `WHATSAPP_*` rejects strangers by default (CVSS 8.1 fix).
- [ ] Document the `[[as_document]]` skill directive (v0.13 media routing).
