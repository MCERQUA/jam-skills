# Migrate to `claude-cli` provider (post-Apr-4-2026)

Anthropic cut OAuth token extraction on Apr 4 2026. The sanctioned replacement is OpenClaw's `claude-cli` provider type, which shells out to a locally-installed `claude` CLI with `-p`. This playbook walks through wiring a tenant onto that lane.

**Read first:** `audit-anchors/anchor-16-anthropic-subscription-cutover.md`.

## When to use this lane

Only for **interactive planning** on tenants with their own Pro/Max sub. Do NOT use for:
- Heartbeat / cron / scheduled work (5h cap will kill it)
- Voice gateway primary (latency + cap)
- Multi-tenant fan-out (each tenant needs their own Anthropic sub)

JamBot's standard primary remains `zai/glm-5-turbo` — `claude-cli` is escalation only.

## Prerequisites

- Tenant has an Anthropic Pro ($20/mo) or Max ($100+) subscription
- Tenant container can install the `claude` CLI (custom Dockerfile layer)
- Backup of current `openclaw.json` (git-committed — see `playbooks/safe-config-edit.md`)

## Step 1 — verify current config

```bash
docker exec jambot-<tenant> openclaw config get providers
docker exec jambot-<tenant> openclaw config get agents.defaults.model
```

Note the current Anthropic-related fields. Capture in a comment in the openclaw.json git history.

## Step 2 — install `claude` CLI inside the tenant container

The official OpenClaw image does NOT ship the CLI. Either bake it in:

```dockerfile
# In jambot-<tenant>/Dockerfile
FROM openclaw/openclaw:2026.5.2
RUN curl -fsSL https://claude.ai/install.sh | sh
```

Or install at runtime (less ideal — lost on container recreate):

```bash
docker exec jambot-<tenant> sh -c 'curl -fsSL https://claude.ai/install.sh | sh'
docker exec jambot-<tenant> claude --version
```

## Step 3 — wire OAuth (one-time, requires interactive shell)

```bash
docker exec -it jambot-<tenant> claude login
# Opens a browser auth flow (or device-code if no browser available)
# Persists auth to ~/.claude/credentials.json inside the container
```

**Critical:** if the tenant container is recreated without persisting `~/.claude/`, the auth is lost. Mount it as a volume:

```yaml
# docker-compose.yml for the tenant
services:
  openclaw:
    volumes:
      - ./claude-auth:/root/.claude
```

## Step 4 — set the provider

```bash
# Atomic, validated config edit (see playbooks/safe-config-edit.md)
docker exec jambot-<tenant> openclaw config set providers.anthropic.type claude-cli
docker exec jambot-<tenant> openclaw config set providers.anthropic.mode oauth
```

## Step 5 — smoke test (single prompt)

```bash
docker exec jambot-<tenant> openclaw chat send "Hello — confirm you are running through claude-cli OAuth and identify the model."
```

Expected: response mentions claude-3.5-sonnet (or whatever the tenant's sub-tier default is) and that the route is via local CLI.

## Step 6 — set fallback chain explicitly

```bash
docker exec jambot-<tenant> openclaw config set agents.defaults.model.fallbacks "[zai/glm-5-turbo, openrouter/claude-haiku-4-5]"
```

If `claude-cli` hits the 5h cap or any error, fallback to GLM-5-turbo (primary) then OpenRouter haiku as final safety net.

## Step 7 — git-commit the new config

```bash
docker exec jambot-<tenant> sh -c 'cd ~/.openclaw && git add openclaw.json && git commit -m "wire claude-cli provider for interactive planning lane"'
```

## Step 8 — validate the 5h cap is NOT hit by automation

```bash
# Confirm cron entries route around claude-cli
docker exec jambot-<tenant> openclaw cron list
# Each entry should specify model via agent-level override, not inherit the default
# If any cron uses default-Anthropic, change it BEFORE going live
```

## Rollback

If anything breaks:

```bash
docker exec jambot-<tenant> sh -c 'cd ~/.openclaw && git checkout HEAD~1 openclaw.json'
docker exec jambot-<tenant> openclaw gateway restart --force --wait 60s
```

## Caveats from production

- u/FFFrank +8 (r/openclaw 1svmq20): production sites have gone bare-Debian-VPS rather than wedging the CLI into the official Docker image. If the Dockerfile layer install causes issues, consider a per-tenant Debian VM instead of a container.
- Headless OAuth flow on a no-browser server: use `claude login --device-code` and complete the flow on a laptop browser.
- Heavy tool-use bias: Codex/Anthropic CLI runs burn cap fast (per r/hermesagent 1tewdky on the analogous Codex case). Restrict to specific tools per session if cap exhaustion happens early.
