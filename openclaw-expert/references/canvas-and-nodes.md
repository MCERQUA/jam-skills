# Canvas & Nodes Reference

---

## Canvas System (macOS)

- Files: `~/Library/Application Support/OpenClaw/canvas/<session>/...`
- URL scheme: `openclaw-canvas://<session>/<path>`
- No `index.html` → shows built-in scaffold
- Disable: Settings → **Allow Canvas** → returns `CANVAS_DISABLED`
- Panel: borderless, resizable, auto-reloads on file changes, one panel at a time

| URL Example | Resolves To |
|-------------|-------------|
| `openclaw-canvas://main/` | `<canvasRoot>/main/index.html` |
| `openclaw-canvas://main/assets/app.css` | `<canvasRoot>/main/assets/app.css` |

### Canvas CLI

```bash
openclaw nodes canvas present --node <id>
openclaw nodes canvas present --node <id> --target https://example.com  # optional --x/--y/--width/--height
openclaw nodes canvas hide --node <id>
openclaw nodes canvas navigate --node <id> --url "/"
openclaw nodes canvas eval --node <id> --js "document.title"
openclaw nodes canvas snapshot --node <id>
openclaw nodes canvas snapshot --node <id> --format jpg --max-width 1200 --quality 0.9
```

- `canvas.navigate` accepts: local paths, `http(s)://`, `file://`
- `canvas.snapshot` returns `{ format, base64 }`
- Low-level: `openclaw nodes invoke --node <id> --command canvas.eval --params '{"javaScript":"..."}'`

### Canvas → Agent Deep Links

```js
window.location.href = "openclaw://agent?message=Review%20this%20design";
```

---

## A2UI (Canvas)

- **v0.8**: ✅ supported — `beginRendering`, `surfaceUpdate`, `dataModelUpdate`, `deleteSurface`
- **v0.9** (`createSurface`): ❌ rejected
- A2UI host: `http://<gateway-host>:18793/__openclaw__/a2ui/`
- macOS auto-navigates to A2UI host on first open when Gateway advertises canvas host

```bash
openclaw nodes canvas a2ui push --node <id> --text "Hello from A2UI"
openclaw nodes canvas a2ui push --node <id> --jsonl ./payload.jsonl
openclaw nodes canvas a2ui reset --node <id>
```

### A2UI JSONL Smoke Test

```bash
cat > /tmp/a2ui-v0.8.jsonl <<'EOFA2'
{"surfaceUpdate":{"surfaceId":"main","components":[{"id":"root","component":{"Column":{"children":{"explicitList":["title","content"]}}}},{"id":"title","component":{"Text":{"text":{"literalString":"Canvas (A2UI v0.8)"},"usageHint":"h1"}}},{"id":"content","component":{"Text":{"text":{"literalString":"If you can read this, A2UI push works."},"usageHint":"body"}}}]}}
{"beginRendering":{"surfaceId":"main","root":"root"}}
EOFA2
openclaw nodes canvas a2ui push --jsonl /tmp/a2ui-v0.8.jsonl --node <id>
```

---

## Node Connection Protocol

- Node: companion device connecting to Gateway WS with `role: "node"`
- Exposes `canvas.*`, `camera.*`, `system.*` etc. via `node.invoke`
- **Not a gateway** — peripherals only

| Platform | Can Host Gateway | Capabilities |
|----------|-----------------|--------------|
| macOS | Yes | canvas, camera, screen, system.run, notify |
| iOS | No | canvas, camera, screen, location, talk, voicewake |
| Android | No | canvas, camera, screen, location, sms, talk, voicewake |
| Linux/headless | Yes | system.run, system.which |

### Pairing

```bash
openclaw gateway --port 18789          # start gateway
openclaw nodes pending                 # list pending requests
openclaw nodes approve <requestId>
openclaw nodes reject <requestId>
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw devices list
openclaw devices approve <requestId>
openclaw nodes rename --node <id|name|ip> --name "Build Node"
openclaw gateway call node.list --params "{}"
```

---

## Node Commands Reference

### Camera

| Command | Key Params | Returns |
|---------|-----------|---------|
| `camera.list` | — | `{devices:[{id,name,position,deviceType}]}` |
| `camera.snap` | `facing`, `maxWidth`, `quality`, `format`, `delayMs`, `deviceId` | `{format:"jpg", base64, width, height}` |
| `camera.clip` | `facing`, `durationMs`, `includeAudio`, `format`, `deviceId` | `{format:"mp4", base64, durationMs, hasAudio}` |

```bash
openclaw nodes camera list --node <id>
openclaw nodes camera snap --node <id>                  # both front+back → 2 MEDIA lines
openclaw nodes camera snap --node <id> --facing front
openclaw nodes camera snap --node <id> --max-width 1280 --delay-ms 2000
openclaw nodes camera clip --node <id> --duration 10s
openclaw nodes camera clip --node <id> --duration 3000 --no-audio
```

- `maxWidth` default: 1600; clips clamped to ≤60s; photos recompressed to <5 MB base64
- macOS default delay: 2000ms; macOS camera default: **off** (Settings → Allow Camera)
- iOS/Android camera default: **on**

### Screen Recording

```bash
openclaw nodes screen record --node <id> --duration 10s --fps 10
openclaw nodes screen record --node <id> --duration 10s --fps 10 --no-audio
openclaw nodes screen record --node <id> --screen <index>   # multi-display
```

- Clamped ≤60s; Android shows system prompt first

### System / Exec (macOS + headless)

```bash
openclaw nodes run --node <id> -- echo "Hello"
openclaw nodes notify --node <id> --title "Ping" --body "Ready" --priority active --delivery overlay
```

- `system.run` flags: `--cwd`, `--env KEY=VAL`, `--command-timeout`, `--needs-screen-recording`

### Location

```bash
openclaw nodes location get --node <id>
openclaw nodes location get --node <id> --accuracy precise --max-age 15000 --location-timeout 10000
```

- Off by default. Returns: `{lat, lon, accuracy (meters), timestamp}`

### SMS (Android only)

```bash
openclaw nodes invoke --node <id> --command sms.send \
  --params '{"to":"+15555550123","message":"Hello from OpenClaw"}'
```

---

## Foreground Requirements

- `canvas.*`, `camera.*`, `screen.*` → **foreground only** on iOS/Android
- Background returns: `NODE_BACKGROUND_UNAVAILABLE`

## Permissions Matrix

| Capability | iOS | Android | macOS | Failure |
|-----------|-----|---------|-------|---------|
| `camera.snap/clip` | Camera (+ mic) | Camera (+ mic) | Camera (+ mic) | `*_PERMISSION_REQUIRED` |
| `screen.record` | Screen Recording | Screen capture prompt | Screen Recording | `*_PERMISSION_REQUIRED` |
| `location.get` | While Using/Always | Foreground/Background | Location | `LOCATION_PERMISSION_REQUIRED` |
| `system.run` | n/a | n/a | Exec approvals | `SYSTEM_RUN_DENIED` |

---

## Exec Approvals

```bash
openclaw approvals get --node <id>
openclaw approvals allowlist add --node <id> "/usr/bin/uname"
```

Approvals file: `~/.openclaw/exec-approvals.json`

```bash
openclaw config set tools.exec.host node
openclaw config set tools.exec.security allowlist
openclaw config set tools.exec.node "<id-or-name>"
openclaw config set agents.list[0].tools.exec.node "node-id-or-name"
openclaw config unset tools.exec.node
# Per-session: /exec host=node security=allowlist node=<id-or-name>
```

---

## Headless Node Host

```bash
# Foreground
openclaw node run --host <gateway-host> --port 18789 --display-name "Build Node"

# Service
openclaw node install --host <gateway-host> --port 18789 --display-name "Build Node"
openclaw node restart

# SSH tunnel (when gateway binds loopback)
ssh -N -L 18790:127.0.0.1:18789 user@gateway-host
export OPENCLAW_GATEWAY_TOKEN="<token>"
openclaw node run --host 127.0.0.1 --port 18790 --display-name "Build Node"
```

- Token: `gateway.auth.token` in `~/.openclaw/openclaw.json` on gateway host
- TLS: add `--tls` / `--tls-fingerprint`
- macOS fallback env: `OPENCLAW_NODE_EXEC_HOST=app`, `OPENCLAW_NODE_EXEC_FALLBACK=0`

---

## macOS App

### Menu Bar States

| State | Icon | When |
|-------|------|------|
| `idle` | normal | All sessions idle |
| `workingMain` | glyph + full tint + animation | Main session active |
| `workingOther` | glyph + muted tint | Non-main session active |

Glyphs: exec→💻 read→📄 write→✍️ edit→📝 attach→📎 default→🛠️

Status row: `<Session role> · <activity label>` (e.g. `Main · exec: pnpm test`)

Debug override: Settings ▸ Debug ▸ "Icon override" → `System (auto)` | `Working: main` | `Working: other` | `Idle`

### Voice Wake

| Parameter | Value |
|-----------|-------|
| Silence window (speech flowing) | 2.0s |
| Silence window (trigger only) | 5.0s |
| Hard stop | 120s |
| Debounce | 350ms |
| PTT key | Right Option (`keyCode 61` + `.option`) |
| Trigger gap | ~0.55s between wake word and command |

- Wake runtime restart never blocked by overlay visibility
- PTT pauses wake runtime; auto-restarts after release
- Requires: Microphone + Speech + Accessibility/Input Monitoring

**Debug sticky overlay:**
```bash
sudo log stream --predicate 'subsystem == "bot.molt" AND category CONTAINS "voicewake"' --level info --style compact
```

### Talk Mode

Continuous loop: Listen → Think → Speak via ElevenLabs

**Config (`~/.openclaw/openclaw.json`):**

```json5
{
  talk: {
    voiceId: "elevenlabs_voice_id",
    modelId: "eleven_v3",
    outputFormat: "mp3_44100_128",
    apiKey: "elevenlabs_api_key",
    interruptOnSpeech: true,
  },
}
```

- `outputFormat` default: `pcm_44100` (macOS/iOS), `pcm_24000` (Android)
- `stability` for `eleven_v3`: only `0.0`, `0.5`, or `1.0`
- Uses `chat.send` against session key `main`

**Voice directive in reply** (stripped before TTS):
```json
{ "voice": "<voice-id>", "once": true }
```

Keys: `voice/voice_id/voiceId`, `model/model_id/modelId`, `speed`, `rate`, `stability`, `similarity`, `style`, `speakerBoost`, `seed`, `normalize`, `lang`, `output_format`, `latency_tier`, `once`

---

## Linux Gateway — systemd

### Quick VPS

```bash
npm i -g openclaw@latest
openclaw onboard --install-daemon
ssh -N -L 18789:127.0.0.1:18789 <user>@<host>
# Open http://127.0.0.1:18789/ and paste token
```

### Service Install

```bash
openclaw onboard --install-daemon
# or: openclaw gateway install
# or: openclaw configure  → select Gateway service
openclaw doctor   # repair/migrate
```

### Systemd User Unit

```ini
[Unit]
Description=OpenClaw Gateway (profile: <profile>, v<version>)
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/local/bin/openclaw gateway --port 18789
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

File: `~/.config/systemd/user/openclaw-gateway[-<profile>].service`

```bash
systemctl --user enable --now openclaw-gateway[-<profile>].service
```

- Bun not recommended (WhatsApp/Telegram bugs)
- No native Linux companion app yet (contributions welcome)

---

## Voice Wake — Global Wake Words

- Single global list owned by Gateway; no per-node custom words
- Each device has its own enabled/disabled toggle

File: `~/.openclaw/settings/voicewake.json`
```json
{ "triggers": ["openclaw", "claude", "computer"], "updatedAtMs": 1730000000000 }
```

| Method | Params | Returns |
|--------|--------|---------|
| `voicewake.get` | — | `{ triggers: string[] }` |
| `voicewake.set` | `{ triggers: string[] }` | `{ triggers: string[] }` |

- Event `voicewake.changed` → broadcast to all WS clients + nodes on change + node connect

---

## Node Troubleshooting

### Diagnostic Commands

```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw nodes status
openclaw nodes describe --node <idOrNameOrIp>
openclaw approvals get --node <idOrNameOrIp>
```

### Error Codes

| Code | Cause | Fix |
|------|-------|-----|
| `NODE_BACKGROUND_UNAVAILABLE` | App backgrounded | Foreground the app |
| `CAMERA_DISABLED` | Camera toggle off | Enable in node settings |
| `*_PERMISSION_REQUIRED` | OS permission denied | Grant OS permission |
| `LOCATION_DISABLED` | Location mode off | Enable in node settings |
| `LOCATION_PERMISSION_REQUIRED` | Mode not granted | Grant location permission |
| `LOCATION_BACKGROUND_UNAVAILABLE` | Backgrounded + only While Using | Foreground or upgrade to Always |
| `SYSTEM_RUN_DENIED: approval required` | Exec needs approval | Approve exec request |
| `SYSTEM_RUN_DENIED: allowlist miss` | Command blocked | Add to allowlist |
| `CANVAS_DISABLED` | Canvas disabled | Settings → Allow Canvas |
| `A2UI_HOST_NOT_CONFIGURED` | Gateway not advertising canvas host | Check `canvasHost` in gateway config |

### Pairing vs Approvals

Two separate gates:
1. **Device pairing** — can this node connect to the gateway?
2. **Exec approvals** — can this node run a specific shell command?

```bash
openclaw devices list                                           # check pairing
openclaw approvals allowlist add --node <id> "/usr/bin/uname"  # fix exec
```

### Recovery Steps (verbatim)

1. Re-approve device pairing: `openclaw devices approve <requestId>`
2. Re-open node app (bring to foreground)
3. Re-grant OS permissions
4. Recreate/adjust exec approval policy
