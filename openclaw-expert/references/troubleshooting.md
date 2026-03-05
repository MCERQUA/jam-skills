# OpenClaw Troubleshooting Reference

---

## 1. FIRST STEP: `openclaw doctor`

Always run this first. Fixes stale config, migrates legacy keys, gives actionable repair steps.

```bash
openclaw doctor                    # interactive
openclaw doctor --repair           # apply fixes without prompting
openclaw doctor --repair --force   # aggressive (overwrites custom supervisor configs)
openclaw doctor --yes              # headless/automation: accept all defaults
openclaw doctor --non-interactive  # safe migrations only, skips restart/service actions
openclaw doctor --deep             # scan system for extra gateway installs
openclaw doctor --generate-gateway-token  # force token creation in automation
```

`--fix` = alias for `--repair`. Writes backup to `~/.openclaw/openclaw.json.bak`.

**Doctor checks:** config normalization, legacy key migrations, on-disk state migration, state dir integrity + permissions, model auth health (OAuth expiry), sandbox image repair, gateway service migrations, security warnings, systemd linger (Linux), skills status, gateway health + restart prompt, channel status warnings, supervisor config audit, gateway runtime best practices, port collision diagnostics.

**macOS: `launchctl` env overrides cause persistent "unauthorized" errors:**
```bash
launchctl getenv OPENCLAW_GATEWAY_TOKEN    # check
launchctl unsetenv OPENCLAW_GATEWAY_TOKEN  # clear
launchctl getenv OPENCLAW_GATEWAY_PASSWORD
launchctl unsetenv OPENCLAW_GATEWAY_PASSWORD
```

---

## 2. Triage Ladder (First 60 Seconds)

```bash
openclaw status
openclaw status --all
openclaw gateway probe
openclaw gateway status
openclaw doctor
openclaw channels status --probe
openclaw logs --follow
```

**Healthy signals:**
- `openclaw gateway status` → `Runtime: running` and `RPC probe: ok`
- `openclaw doctor` → no blocking errors
- `openclaw channels status --probe` → channels show `connected` or `ready`
- `openclaw logs --follow` → steady activity, no repeating fatal errors

---

## 3. Reading Logs

**Default log location:** `/tmp/openclaw/openclaw-YYYY-MM-DD.log` (rolling, host timezone)

**Override in `~/.openclaw/openclaw.json`:**
```json
{ "logging": { "file": "/path/to/openclaw.log" } }
```

```bash
openclaw logs --follow               # live tail via RPC (works remote)
openclaw logs --json                 # line-delimited JSON
openclaw logs --limit 500
openclaw logs --local-time
openclaw channels logs --channel whatsapp   # channel-specific filter
```

**Log config:**
```json
{
  "logging": {
    "level": "info",
    "consoleLevel": "info",
    "consoleStyle": "pretty",
    "redactSensitive": "tools",
    "redactPatterns": ["sk-.*"]
  }
}
```

| Field | Options |
|-------|---------|
| `level` | `trace`/`debug`/`info`/`warn`/`error` — file log verbosity |
| `consoleStyle` | `pretty` / `compact` / `json` |
| `redactSensitive` | `off` / `tools` (default: `tools`, console only) |

- `--verbose` affects console only; does NOT raise file log level
- Logs empty? Check Gateway is running and writing to `logging.file`
- Need more detail? Set `logging.level` to `debug` or `trace`

**Targeted debug flags (without raising global level):**
```json
{ "diagnostics": { "flags": ["telegram.http"] } }
```
Env override: `OPENCLAW_DIAGNOSTICS=telegram.http,telegram.payload`

**WS log verbosity:**
```bash
openclaw gateway --verbose --ws-log compact   # all WS traffic (paired)
openclaw gateway --verbose --ws-log full      # all WS traffic (full meta)
```

---

## 4. Health Checks

```bash
openclaw health               # fetch health from running Gateway
openclaw health --json        # machine-readable snapshot
openclaw health --verbose     # live probes + per-account timings
openclaw status               # local summary
openclaw status --all         # full local diagnosis (safe to paste for debugging)
openclaw status --deep        # also probes running Gateway per-channel
```

- `openclaw health` exits non-zero if Gateway unreachable or probe fails
- `--timeout <ms>` overrides 10s default
- Send `/status` in WhatsApp/WebChat for status reply without invoking agent

---

## 5. Issue Categories

### 5.1 Gateway Won't Start / Service Not Running

```bash
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw gateway status --deep
```

| Error signature | Fix |
|----------------|-----|
| `Gateway start blocked: set gateway.mode=local` | Set `gateway.mode=local` in config |
| `refusing to bind gateway ... without auth` | Non-loopback bind requires `gateway.auth.token` or password |
| `another gateway instance is already listening` | Stop other instance |
| `EADDRINUSE` | Port `18789` busy → `openclaw gateway --force` or free the port |

**Service reinstall after config drift:**
```bash
openclaw gateway install --force
openclaw gateway restart
```

### 5.2 No Replies

```bash
openclaw channels status --probe
openclaw pairing list <channel>
openclaw config get channels
openclaw logs --follow
```

| Log signature | Meaning |
|---------------|---------|
| `drop guild message (mention required` | Group message ignored until bot mentioned |
| `pairing request` | Sender needs DM pairing approval |
| `blocked` / `allowlist` | Sender/channel filtered by policy |

### 5.3 Channel Connected But Messages Don't Flow

```bash
openclaw channels status --probe
openclaw pairing list <channel>
openclaw status --deep
openclaw logs --follow
```

| Log signature | Meaning |
|---------------|---------|
| `mention required` | Group mention gating blocked processing |
| `pairing` / pending | Sender not approved |
| `missing_scope` / `not_in_channel` | Missing channel API permissions |
| `Forbidden` / `401` / `403` | Channel credential issue |

### 5.4 Auth / Model Auth Issues

```bash
openclaw models status
openclaw doctor
```

**"No credentials found":**
```bash
claude setup-token                                         # run on gateway host
openclaw models auth setup-token --provider anthropic
# Or paste manually:
openclaw models auth paste-token --provider anthropic
```

**If you see:**
```
This credential is only authorized for use with Claude Code and cannot be used for other API requests.
```
→ Use an Anthropic API key instead.

**API key setup:**
```bash
cat >> ~/.openclaw/.env <<'EOF'
ANTHROPIC_API_KEY=...
EOF
openclaw models status
openclaw doctor
```

**Automation-friendly expiry check (exit 1=expired, 2=expiring):**
```bash
openclaw models status --check
```

### 5.5 Dashboard / Control UI Won't Connect

```bash
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw gateway status --json
```

| Log signature | Meaning |
|---------------|---------|
| `device identity required` | Non-secure context or missing device auth |
| `unauthorized` / reconnect loop | Token/password mismatch |
| `gateway connect failed:` | Wrong host/port/URL target |

### 5.6 Post-Upgrade Breakage

```bash
openclaw config get gateway.mode
openclaw config get gateway.remote.url
openclaw config get gateway.auth.mode
openclaw config get gateway.bind
openclaw config get gateway.auth.token
openclaw devices list
openclaw pairing list <channel>
openclaw doctor
```

- `gateway.mode=remote` → CLI targets remote, local service may be fine
- Explicit `--url` calls do NOT fall back to stored credentials
- `gateway.token` (old key) does NOT replace `gateway.auth.token`
- Non-loopback binds (`lan`, `tailnet`, `custom`) need auth configured

| Signature | Fix |
|-----------|-----|
| `refusing to bind gateway ... without auth` | Set `gateway.auth.token` |
| `RPC probe: failed` while runtime running | Auth/URL mismatch |
| `device identity required` | Device auth not satisfied |
| `gateway connect failed:` | Wrong URL target |

**After config/state disagreement:**
```bash
openclaw gateway install --force
openclaw gateway restart
```

---

## 6. Per-Channel Quick Reference

### WhatsApp
| Symptom | Check | Fix |
|---------|-------|-----|
| Connected, no DM replies | `openclaw pairing list whatsapp` | Approve sender or switch DM policy/allowlist |
| Group messages ignored | `requireMention` + mention patterns | Mention bot or relax mention policy |
| Disconnect/relogin loops | `openclaw channels status --probe` + logs | Re-login, verify credentials dir |

**Relink (status 409–515 or `loggedOut` in logs):**
```bash
openclaw channels logout && openclaw channels login --verbose
```

### Telegram
| Symptom | Check | Fix |
|---------|-------|-----|
| `/start` but no reply flow | `openclaw pairing list telegram` | Approve pairing or change DM policy |
| Group stays silent | Verify mention req + bot privacy mode | Disable privacy mode or mention bot |
| Network send failures | Logs for API call failures | Fix DNS/IPv6/proxy to `api.telegram.org` |

### Discord
| Symptom | Check | Fix |
|---------|-------|-----|
| Bot online, no guild replies | `openclaw channels status --probe` | Allow guild/channel, verify message content intent |
| Group messages ignored | Logs for mention gating drops | Mention bot or set `requireMention: false` |
| DM replies missing | `openclaw pairing list discord` | Approve DM pairing |

### Slack
| Symptom | Check | Fix |
|---------|-------|-----|
| Socket mode connected, no responses | `openclaw channels status --probe` | Verify app token + bot token + scopes |
| DMs blocked | `openclaw pairing list slack` | Approve pairing or relax DM policy |
| Channel message ignored | `groupPolicy` + channel allowlist | Allow channel or switch policy to `open` |

### iMessage / BlueBubbles / Signal / Matrix
| Channel | Symptom | Fix |
|---------|---------|-----|
| iMessage | No inbound events | Fix webhook URL or BlueBubbles server state |
| iMessage | Can send, no receive (macOS) | Re-grant TCC permissions, restart channel process |
| Signal | Daemon reachable, bot silent | Verify `signal-cli` daemon URL/account + receive mode |
| Matrix | Ignores room messages | Check `groupPolicy` + room allowlist |
| Matrix | Encrypted rooms fail | Enable encryption support, rejoin/sync room |

DM sender blocked on any channel: `openclaw pairing list <channel>` → approve or update allowlist.

---

## 7. Config Validation / Legacy Key Migrations

When config has deprecated keys, **other commands refuse to run** and prompt for `openclaw doctor`. Doctor explains, shows migration, rewrites `~/.openclaw/openclaw.json`.

**Check config before doctor rewrites:** `cat ~/.openclaw/openclaw.json`

**Current migrations (old → new):**

| Old key | New key |
|---------|---------|
| `routing.allowFrom` | `channels.whatsapp.allowFrom` |
| `routing.groupChat.requireMention` | `channels.<channel>.groups."*".requireMention` |
| `routing.groupChat.historyLimit` | `messages.groupChat.historyLimit` |
| `routing.groupChat.mentionPatterns` | `messages.groupChat.mentionPatterns` |
| `routing.queue` | `messages.queue` |
| `routing.bindings` | top-level `bindings` |
| `routing.agents` / `routing.defaultAgentId` | `agents.list` + `agents.list[].default` |
| `routing.agentToAgent` | `tools.agentToAgent` |
| `routing.transcribeAudio` | `tools.media.audio.models` |
| `bindings[].match.accountID` | `bindings[].match.accountId` |
| `identity` | `agents.list[].identity` |
| `agent.*` | `agents.defaults` + `tools.*` |
| `agent.model` / `allowedModels` / `modelAliases` / `modelFallbacks` | `agents.defaults.model.primary/fallbacks` |

---

## 8. Node Tool Failures

```bash
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>
openclaw logs --follow
```

| Error code | Meaning | Fix |
|-----------|---------|-----|
| `NODE_BACKGROUND_UNAVAILABLE` | App backgrounded (iOS/Android) | Bring node app to foreground |
| `CAMERA_DISABLED` | Camera toggle off | Enable in node settings |
| `*_PERMISSION_REQUIRED` | OS permission missing/denied | Re-grant OS permission |
| `LOCATION_DISABLED` | Location mode off | Enable in node settings |
| `LOCATION_PERMISSION_REQUIRED` | Location mode not granted | Grant location permission |
| `LOCATION_BACKGROUND_UNAVAILABLE` | Backgrounded, only "While Using" perm | Foreground or upgrade permission |
| `SYSTEM_RUN_DENIED: approval required` | Exec request needs approval | Check `openclaw approvals get --node <id>` |
| `SYSTEM_RUN_DENIED: allowlist miss` | Command not on exec allowlist | `openclaw approvals allowlist add --node <id> "/usr/bin/cmd"` |

`canvas.*`, `camera.*`, `screen.*` are **foreground-only** on iOS/Android.

**Two different gates:**
1. **Device pairing** (can node connect?) → `openclaw devices list`
2. **Exec approvals** (can node run command?) → `openclaw approvals get --node <id>`

---

## 9. Automation (Cron / Heartbeat)

```bash
openclaw cron status
openclaw cron list
openclaw cron runs --id <jobId> --limit 20
openclaw system heartbeat last
openclaw logs --follow
```

| Signature | Meaning |
|-----------|---------|
| `cron: scheduler disabled; jobs will not run automatically` | Cron disabled in config/env |
| `cron: timer tick failed` | Scheduler tick crashed — check surrounding log context |
| `reason: not-due` | Manual run without `--force`, job not due yet |
| `heartbeat skipped` + `reason=quiet-hours` | Outside `activeHours` window |
| `requests-in-flight` | Main lane busy; heartbeat deferred |
| `empty-heartbeat-file` | `HEARTBEAT.md` exists but has no actionable content |
| `alerts-disabled` | Visibility settings suppress outbound heartbeat |
| `heartbeat: unknown accountId` | Invalid account id for delivery target |

**Timezone gotchas:**
- `Config path not found: agents.defaults.userTimezone` → falls back to host timezone
- Cron without `--tz` uses gateway host timezone
- ISO timestamps without timezone → treated as UTC for `at` schedules
- Heartbeat always skipped during daytime? Check `activeHours.timezone` is correct

---

## 10. Browser Tool Failures

```bash
openclaw browser status
openclaw browser start --browser-profile openclaw
openclaw browser profiles
openclaw logs --follow
openclaw doctor
```

| Error | Fix |
|-------|-----|
| `Failed to start Chrome CDP on port` | Browser process failed to launch — check executable path |
| `browser.executablePath not found` | Configured path is invalid |
| `Chrome extension relay is running, but no tab is connected` | Extension relay not attached to any tab |
| `Browser attachOnly is enabled ... not reachable` | Attach-only profile has no reachable CDP target |

---

## 11. State / Permissions / Service

```bash
ls -la ~/.openclaw/openclaw.json   # should be chmod 600
chmod 600 ~/.openclaw/openclaw.json
```

**Legacy state migrations (doctor handles these):**
- Sessions: `~/.openclaw/sessions/` → `~/.openclaw/agents/<agentId>/sessions/`
- Agent dir: `~/.openclaw/agent/` → `~/.openclaw/agents/<agentId>/agent/`
- WhatsApp auth: `~/.openclaw/credentials/*.json` → `~/.openclaw/credentials/whatsapp/<accountId>/`
  - ⚠️ WhatsApp auth only migrated via `openclaw doctor` (not auto on startup)

**systemd linger (Linux — gateway must survive logout):**
```bash
loginctl enable-linger $USER   # doctor offers this automatically
```

**Gateway runtime:** WhatsApp + Telegram require Node (not Bun). Version-manager paths (`nvm`/`fnm`/`volta`/`asdf`) can break after upgrades — service doesn't load shell init. Doctor offers migration to system Node.

**If `gateway.mode=remote`:** Run `openclaw doctor` on the **remote host** (state lives there).

---

## 12. Quick Reference — All Diagnostic Commands

```bash
# Gateway
openclaw status && openclaw status --all && openclaw status --deep
openclaw gateway status && openclaw gateway status --deep && openclaw gateway status --json
openclaw gateway probe
openclaw doctor && openclaw doctor --repair

# Logs
openclaw logs --follow
openclaw logs --json
openclaw channels logs --channel <name>

# Health
openclaw health && openclaw health --json && openclaw health --verbose

# Channels
openclaw channels status --probe
openclaw pairing list <channel>
openclaw config get channels

# Models/Auth
openclaw models status && openclaw models status --check
openclaw models auth order get --provider <name>

# Cron/Automation
openclaw cron status && openclaw cron list
openclaw cron runs --id <jobId> --limit 20
openclaw system heartbeat last

# Nodes
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>
openclaw devices list

# Browser
openclaw browser status && openclaw browser profiles

# Config
openclaw config get gateway.mode
openclaw config get gateway.bind
openclaw config get gateway.auth.token
cat ~/.openclaw/openclaw.json
```
