# OpenClaw Skills System — Condensed Reference

## SKILL.md Format

Minimum required frontmatter:
```markdown
---
name: my-skill-name
description: One-line description shown in prompt and UI
---

# Skill Instructions

Markdown instructions for the agent. Use `{baseDir}` to reference the skill folder path.
```

### All Frontmatter Keys

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `name` | string | required | Skill identifier (used as config key) |
| `description` | string | required | Shown in agent prompt + macOS UI |
| `metadata` | JSON (single-line) | optional | Gating, install, emoji — see below |
| `homepage` | URL | optional | "Website" link in macOS Skills UI |
| `user-invocable` | bool | `true` | Expose as user slash command |
| `disable-model-invocation` | bool | `false` | Exclude from model prompt (user-only) |
| `command-dispatch` | `tool` | optional | Bypass model; dispatch slash command directly to a tool |
| `command-tool` | string | optional | Tool name for `command-dispatch: tool` |
| `command-arg-mode` | `raw` | `raw` | Forwards raw args string to tool |

When `command-dispatch: tool`, tool receives:
```json
{ "command": "<raw args>", "commandName": "<slash command>", "skillName": "<skill name>" }
```

**Parser constraint:** `metadata` must be a **single-line** JSON object (embedded agent parser limitation).

---

## Three Locations + Precedence

```
<workspace>/skills  (HIGHEST — per-agent)
~/.openclaw/skills  (managed/local — shared across all agents)
bundled skills      (shipped with install — lowest)
skills.load.extraDirs  (config-added dirs — lowest of all)
```

- **Workspace skills** override managed, which override bundled — by name conflict.
- **extraDirs** (via config) are lowest precedence; useful for shared skill packs.
- **Plugin skills**: listed in `openclaw.plugin.json` → load when plugin enabled → follow normal precedence.
- **Per-agent** isolation: each agent's `<workspace>/skills` is private. `~/.openclaw/skills` is shared.

---

## Gating (`metadata.openclaw`)

Skills are **filtered at load time**. If no `metadata.openclaw` block, skill is always eligible.

```markdown
---
name: nano-banana-pro
description: Generate or edit images via Gemini 3 Pro Image
metadata: {"openclaw": {"requires": {"bins": ["uv"], "env": ["GEMINI_API_KEY"], "config": ["browser.enabled"]}, "primaryEnv": "GEMINI_API_KEY"}}
---
```

### Gating Fields

| Field | Type | Behavior |
|-------|------|----------|
| `always: true` | bool | Skip all gates — always include |
| `os` | array | `["darwin","linux","win32"]` — OS allowlist |
| `requires.bins` | array | ALL must exist on `PATH` |
| `requires.anyBins` | array | At LEAST ONE must exist on `PATH` |
| `requires.env` | array | Each must exist in env OR be provided via config |
| `requires.config` | array | Each `openclaw.json` path must be truthy |
| `primaryEnv` | string | Env var associated with `skills.entries.<name>.apiKey` |
| `emoji` | string | macOS Skills UI display |
| `homepage` | URL | macOS Skills UI "Website" link |
| `skillKey` | string | Alternate key to use under `skills.entries` |
| `install` | array | Installer specs for macOS Skills UI |

### Sandboxing + `requires.bins`
- `requires.bins` checked on **host** at load time.
- If agent is sandboxed (Docker), binary must also exist **inside the container**.
- Install in container via `agents.defaults.sandbox.docker.setupCommand` (runs once after create).

---

## Installer Specs (`metadata.openclaw.install`)

```markdown
metadata: {"openclaw": {"emoji": "♊️", "requires": {"bins": ["gemini"]}, "install": [{"id": "brew", "kind": "brew", "formula": "gemini-cli", "bins": ["gemini"], "label": "Install Gemini CLI (brew)"}]}}
```

### Installer Kinds

| Kind | Notes |
|------|-------|
| `brew` | Uses `formula` field; macOS only (use `"os": ["darwin"]`) |
| `node` | Honors `skills.install.nodeManager` (npm/pnpm/yarn/bun) |
| `go` | If `go` missing + brew available → installs Go via brew first |
| `uv` | Python uv-based install |
| `download` | Requires `url`; optional `archive`, `extract`, `stripComponents`, `targetDir` (default: `~/.openclaw/tools/<skillKey>`) |

- Multiple installers listed → gateway picks **single** preferred (brew first, else node).
- All `download` → lists all entries in UI.
- `os` field on each installer to filter by platform.

---

## Config Overrides (`~/.openclaw/openclaw.json`)

```json5
{
  skills: {
    allowBundled: ["gemini", "peekaboo"],   // optional allowlist for bundled skills only
    load: {
      extraDirs: ["~/Projects/agent-scripts/skills", "~/Projects/oss/some-skill-pack/skills"],
      watch: true,          // auto-refresh on SKILL.md changes (default: true)
      watchDebounceMs: 250, // debounce ms (default: 250)
    },
    install: {
      preferBrew: true,       // prefer brew installers (default: true)
      nodeManager: "npm",     // npm | pnpm | yarn | bun (default: npm)
    },
    entries: {
      "nano-banana-pro": {
        enabled: true,
        apiKey: "GEMINI_KEY_HERE",          // shortcut for primaryEnv var
        env: {
          GEMINI_API_KEY: "GEMINI_KEY_HERE",  // injected only if not already set
        },
        config: {
          endpoint: "https://example.invalid",  // custom per-skill fields
          model: "nano-pro",
        },
      },
      peekaboo: { enabled: true },
      sag: { enabled: false },
    },
  },
}
```

### Config Rules

| Setting | Behavior |
|---------|----------|
| `allowBundled` | Only bundled skills in list are eligible; managed/workspace unaffected |
| `enabled: false` | Disables skill even if bundled/installed |
| `env` | Injected **only if** var not already in process env |
| `apiKey` | Convenience for `primaryEnv` declared var |
| `config` | Optional bag for custom per-skill fields |

- Keys under `entries` = skill `name` by default. Use `skillKey` if skill defines `metadata.openclaw.skillKey`.
- Hyphenated skill names: quote the key (`"nano-banana-pro": {...}`).
- `allowBundled` only affects bundled; managed/workspace always load if eligible.

---

## `{baseDir}` Placeholder

Use `{baseDir}` anywhere in the skill's markdown instructions to reference the **absolute path to the skill folder**. Useful for pointing the agent to scripts or config files bundled with the skill.

```markdown
Run the helper script at `{baseDir}/scripts/run.sh`.
```

---

## User-Invocable vs Model-Invocable

| Behavior | Config |
|----------|--------|
| Slash command for user + included in model prompt (default) | `user-invocable: true` (default) |
| Excluded from model prompt, available as slash command only | `disable-model-invocation: true` |
| Not exposed as slash command | `user-invocable: false` |
| Slash command bypasses model entirely → routes to tool | `command-dispatch: tool` + `command-tool: <name>` |

**Progressive disclosure pattern:** Use `disable-model-invocation: true` for skills that are noisy in the prompt but still needed on-demand. The user can invoke via slash command; the model won't see them unless called.

---

## Environment Injection (Per Agent Run)

1. Agent run starts
2. OpenClaw reads skill metadata
3. Applies `skills.entries.<key>.env` and `skills.entries.<key>.apiKey` to `process.env`
4. Builds system prompt with eligible skills
5. **Restores original env after run ends** — scoped, not global

**Sandbox note:** Sandboxed skills run in Docker and do **not** inherit host `process.env`. Use `agents.defaults.sandbox.docker.env` or bake into custom image instead.

---

## Session Snapshot + Hot Reload

- Skills snapshot taken **when session starts** → reused for all turns in that session.
- Changes take effect on **next new session**.
- Skills watcher (`load.watch: true`) auto-bumps snapshot mid-session when `SKILL.md` changes → picked up on next agent turn (hot reload).
- Remote macOS nodes: if Linux gateway + macOS node connected with `system.run` allowed → macOS-only skills become eligible (agent uses `nodes` tool to invoke).

---

## Token Impact

```
total_chars = 195 + Σ (97 + len(name_escaped) + len(description_escaped) + len(location_escaped))
rough_tokens ≈ total_chars / 4
```

- Base overhead (when ≥1 skill): **195 chars**
- Per skill: **97 chars + field lengths**
- ~97 chars ≈ 24 tokens per skill (plus name/description length)
- XML escaping expands `& < > " '` → adds chars

---

## Creating a Custom Skill (Step-by-Step)

```bash
# Step 1: Create directory
mkdir -p ~/.openclaw/workspace/skills/hello-world

# Step 2: Create SKILL.md
cat > ~/.openclaw/workspace/skills/hello-world/SKILL.md << 'EOF'
---
name: hello_world
description: A simple skill that says hello.
---

# Hello World Skill

When the user asks for a greeting, use the `echo` tool to say "Hello from your custom skill!".
EOF

# Step 3: Refresh
# Ask agent to "refresh skills" OR restart the gateway

# Step 4: Test
openclaw agent --message "use my hello_world skill"
```

**Best practices:**
- Be concise — instruct on *what* to do, not how to be an AI
- Safety first — if using `bash`, prevent arbitrary command injection from untrusted input
- Test locally before publishing

---

## CLI Commands

```bash
# Inspect skills
openclaw skills list               # all skills (bundled + workspace + managed)
openclaw skills list --eligible    # only currently eligible skills
openclaw skills info <name>        # details for one skill
openclaw skills check              # debug missing bins/env/config requirements
```

---

## ClawHub (Public Registry)

**Site:** https://clawhub.ai

### Install CLI
```bash
npm i -g clawhub
# or
pnpm add -g clawhub
```

### Auth
```bash
clawhub login                      # browser OAuth flow
clawhub login --token <token>      # paste API token
clawhub login --no-browser --token <token>  # non-interactive
clawhub logout
clawhub whoami
```

### Search & Install
```bash
clawhub search "postgres backups"
clawhub search "calendar" --limit 10
clawhub install <slug>
clawhub install <slug> --version 1.2.0
clawhub install <slug> --force     # overwrite existing folder
```

### Update
```bash
clawhub update <slug>
clawhub update <slug> --version 2.0.0
clawhub update --all
clawhub update --all --force       # overwrite even if local differs from any published version
```

### List Installed
```bash
clawhub list                       # reads .clawhub/lock.json
```

### Publish
```bash
clawhub publish ./my-skill --slug my-skill --name "My Skill" --version 1.0.0 --changelog "Initial release" --tags latest
```

### Sync (scan + publish many)
```bash
clawhub sync                       # interactive: scan workdir, prompt for each
clawhub sync --all                 # upload everything without prompts
clawhub sync --dry-run             # show what would be uploaded
clawhub sync --bump patch          # auto-bump version (patch|minor|major)
clawhub sync --all --changelog "Batch update" --tags latest
clawhub sync --root ~/extra/skills --concurrency 8
```

### Delete/Undelete (owner/admin only)
```bash
clawhub delete <slug> --yes
clawhub undelete <slug> --yes
```

### Global Options (all commands)
| Option | Description |
|--------|-------------|
| `--workdir <dir>` | Working dir (default: cwd, fallback: OpenClaw workspace) |
| `--dir <dir>` | Skills dir relative to workdir (default: `skills`) |
| `--site <url>` | Override site URL |
| `--registry <url>` | Override registry API URL |
| `--no-input` | Disable prompts (non-interactive/CI) |
| `-V` | Print CLI version |

### ClawHub Environment Variables
| Var | Purpose |
|-----|---------|
| `CLAWHUB_SITE` | Override site URL |
| `CLAWHUB_REGISTRY` | Override registry API URL |
| `CLAWHUB_CONFIG_PATH` | Override CLI token/config storage location |
| `CLAWHUB_WORKDIR` | Override default workdir |
| `CLAWHUB_DISABLE_TELEMETRY=1` | Disable install-count telemetry on `sync` |

### Where Skills Are Installed
- Default: `./skills` under current working directory
- Fallback: configured OpenClaw workspace `<workspace>/skills`
- Override: `--workdir` flag or `CLAWHUB_WORKDIR` env var
- Lockfile: `.clawhub/lock.json` in workdir

### Moderation / Security
- GitHub account must be **≥1 week old** to publish
- Any signed-in user can report a skill (up to 20 active reports per user)
- Skills with **3+ unique reports** → auto-hidden
- Moderators can: view hidden, unhide, delete, ban users

---

## Full SKILL.md Example with Gating + Installer

```markdown
---
name: nano-banana-pro
description: Generate or edit images via Gemini 3 Pro Image
metadata: {"openclaw": {"emoji": "🍌", "homepage": "https://clawhub.ai/skills/nano-banana-pro", "requires": {"bins": ["uv"], "env": ["GEMINI_API_KEY"]}, "primaryEnv": "GEMINI_API_KEY", "install": [{"id": "brew", "kind": "brew", "formula": "uv", "bins": ["uv"], "label": "Install uv (brew)", "os": ["darwin"]}, {"id": "node", "kind": "node", "formula": "uv", "bins": ["uv"], "label": "Install uv (npm)"}]}}
homepage: https://clawhub.ai/skills/nano-banana-pro
user-invocable: true
---

# Nano Banana Pro

Use the Gemini 3 Pro Image API to generate images. The API key is in `GEMINI_API_KEY`.

Scripts are at `{baseDir}/scripts/`. Run them with `uv run {baseDir}/scripts/generate.py`.
```
