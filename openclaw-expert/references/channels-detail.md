# OpenClaw Channels — Per-Channel Quick Reference

> **Universal DM policies:** `pairing` (default) | `allowlist` | `open` (requires `"*"` in allowFrom) | `disabled`
> **Pairing:** 8-char codes, expire 1h, max 3 pending per channel.
> `openclaw pairing list <ch>` / `openclaw pairing approve <ch> <CODE>`
> **Diagnostics:** `openclaw doctor` / `openclaw channels status [--probe]` / `openclaw logs --follow`

---

## WhatsApp
**Status:** Production-ready via Baileys. **Node only (not Bun).**
```bash
openclaw channels login --channel whatsapp [--account work]
openclaw gateway
openclaw pairing approve whatsapp <CODE>
```
| Field | Default | Notes |
|-------|---------|-------|
| `dmPolicy` | `pairing` | |
| `allowFrom` | — | E.164 numbers |
| `groupPolicy` | `open`* | *if no config block; else `allowlist` |
| `groupAllowFrom` | falls back to `allowFrom` | |
| `groups` | — | JID allowlist |
| `textChunkLimit` | 4000 | `chunkMode: length\|newline` |
| `mediaMaxMb` | 50in/5out | |
| `sendReadReceipts` | `true` | skipped for self-chat |
| `ackReaction.emoji/direct/group` | — | `group: always\|mentions\|never` |
| `historyLimit` | 50 | group pending msgs as context; `0` disables |
| `selfChatMode` | — | personal-number setups |
| `session.dmScope` | `main` | |

**Gotchas:**
- `@status`/`@broadcast` always ignored
- Outbound fails if no active gateway listener
- Personal number in `allowFrom` activates self-chat protections
- Audio: `audio/ogg` rewritten to `codecs=opus` for voice-note
- Group `/activation always|mention` is session-only (owner-gated)
- Credentials: `~/.openclaw/credentials/whatsapp/<accountId>/creds.json`

---

## Telegram
**Status:** Production-ready. Long polling (default) or webhook. Uses grammY.
```bash
# @BotFather → /newbot → copy token
openclaw gateway && openclaw pairing approve telegram <CODE>
# Find user ID: openclaw logs --follow (read from.id)
```
| Field | Default | Notes |
|-------|---------|-------|
| `botToken` | — | or `TELEGRAM_BOT_TOKEN` env |
| `dmPolicy` | `pairing` | |
| `allowFrom` | — | numeric IDs or usernames |
| `groupPolicy` | `allowlist` | |
| `groups."<chatId>".requireMention` | `true` | |
| `groups."<chatId>".topics."<threadId>"` | — | forum topic config |
| `streamMode` | `partial` | `off\|partial\|block` (DM only) |
| `textChunkLimit` | 4000 | `chunkMode: length\|newline` |
| `mediaMaxMb` | 5 | |
| `replyToMode` | `first` | `off\|first\|all` |
| `reactionNotifications` | `own` | `off\|own\|all` |
| `webhookUrl`/`webhookSecret` | — | enables webhook mode |
| `customCommands` | — | `[{command, description}]` |

**Gotchas:**
- Privacy Mode: disable via `/setprivacy` in BotFather → **remove+re-add** bot to group
- Forum general topic (threadId=1): `sendMessage` omits `message_thread_id` (Telegram rejects it)
- Draft streaming: DMs only; requires `message_thread_id` + topics enabled
- `setMyCommands failed` = DNS/HTTPS to `api.telegram.org` blocked
- Animated TGS and video WEBM stickers are skipped (only static WEBP processed)
- Sticker cache: `~/.openclaw/telegram/sticker-cache.json`

---

## Discord
**Status:** Ready for DMs and guild channels.
```bash
# Developer Portal: New App → Bot → enable Message Content Intent + Server Members Intent
# OAuth scopes: bot + applications.commands → invite
openclaw gateway && openclaw pairing approve discord <CODE>
```
| Field | Default | Notes |
|-------|---------|-------|
| `token` | — | or `DISCORD_BOT_TOKEN` env |
| `dm.policy` | `pairing` | |
| `dm.groupEnabled` | `false` | group DMs |
| `groupPolicy` | `allowlist` | `open`/`disabled` |
| `guilds."<id>".requireMention` | `true` | |
| `guilds."<id>".users` | — | sender allowlist |
| `guilds."<id>".channels."<name>"` | — | per-channel config |
| `historyLimit` | 20 | |
| `replyToMode` | `off` | `off\|first\|all` |
| `pluralkit.enabled` | — | PluralKit proxy resolution |
| `execApprovals.enabled` | — | button-based in DMs |
| `allowBots` | `false` | bot→bot (risk: loops) |

**Action defaults:** reactions/messages/threads/pins/polls/search/memberInfo/roleInfo/channelInfo/channels/voiceStatus enabled; **roles/moderation/presence disabled.**

**Gotchas:**
- Env-only setup (no config block): `groupPolicy="open"` with warning
- Bare numeric IDs ambiguous for DM targets — use `user:<id>` or `<@id>`
- `channels status --probe` can't verify permissions for slug keys

---

## Slack
**Status:** Production-ready. Socket Mode (default) or HTTP Events API.
```bash
# Slack app: enable Socket Mode, App Token (xapp-...) with connections:write, Bot Token (xoxb-...)
# Subscribe events: app_mention, message.channels/groups/im/mpim, reaction_added/removed
# Enable App Home Messages Tab
```
```json5
{ channels: { slack: { mode: "socket", appToken: "xapp-...", botToken: "xoxb-..." } } }
// HTTP mode: mode: "http", botToken, signingSecret, webhookPath: "/slack/events"
```
| Field | Default | Notes |
|-------|---------|-------|
| `mode` | `socket` | `socket\|http` |
| `botToken`/`appToken` | — | envs: `SLACK_BOT_TOKEN`/`SLACK_APP_TOKEN` |
| `signingSecret` | — | HTTP mode |
| `dm.policy` | `pairing` | |
| `dm.groupEnabled` | `false` | MPIMs |
| `groupPolicy` | `allowlist` | |
| `channels."<id>".requireMention` | `true` | |
| `replyToMode` | `off` | `off\|first\|all` |
| `textChunkLimit` | 4000 | |
| `mediaMaxMb` | 20 | |
| `commands.native` | off | must explicitly enable (NOT auto) |
| `slashCommand.enabled` | `false` | single slash command mode |
| `userToken` | — | xoxp-...; no env fallback; `userTokenReadOnly: true` |

**Gotchas:**
- `commands.native: "auto"` does **NOT** enable Slack native commands
- HTTP mode: each account needs unique `webhookPath`
- Env-only setup: `groupPolicy="open"` with warning

---

## Signal
**Status:** External CLI integration (signal-cli). Java required.
```bash
signal-cli link -n "OpenClaw"  # scan QR in Signal
openclaw gateway && openclaw pairing approve signal <CODE>
```
```json5
{ channels: { signal: { enabled: true, account: "+15551234567", cliPath: "signal-cli", dmPolicy: "pairing" } } }
// External daemon: httpUrl: "http://127.0.0.1:8080", autoStart: false
```
| Field | Default | Notes |
|-------|---------|-------|
| `account` | — | E.164 bot number |
| `cliPath` | `signal-cli` | |
| `httpUrl` | — | external daemon |
| `autoStart` | `true` | if httpUrl unset |
| `startupTimeoutMs` | — | cap 120000 |
| `allowFrom` | — | E.164 or `uuid:<id>` |
| `groupPolicy` | `allowlist` | |
| `sendReadReceipts` | — | DMs only |
| `textChunkLimit` | 4000 | `chunkMode: length\|newline` |
| `mediaMaxMb` | 8 | |
| `historyLimit` | 50 | |

**Gotchas:**
- **Separate bot number strongly recommended** — personal number causes loop protection
- No native mentions — use regex mention patterns
- Group reactions require `targetAuthor`/`targetAuthorUuid`
- UUID-only senders stored as `uuid:<id>` in allowFrom

---

## iMessage (legacy: imsg)
> ⚠️ **DEPRECATED** — Use BlueBubbles for new setups. May be removed in future.

**Status:** Legacy macOS CLI via `imsg` (stdio JSON-RPC).
```bash
brew install steipete/tap/imsg
openclaw gateway && openclaw pairing approve imessage <CODE>
```
Config: `cliPath`, `dbPath`, `remoteHost` (for SSH+SCP remote Mac), `includeAttachments`, `dmPolicy`, `textChunkLimit` (4000), `mediaMaxMb` (16).

**Gotchas:** Full Disk Access + Automation must be granted in same process context. Run `imsg chats --limit 1` interactively to trigger prompts. Multi-participant threads may arrive `is_group=false` — list under `groups` explicitly.

---

## BlueBubbles
**Status:** ✅ Recommended for iMessage. REST API + webhooks.
```bash
# Install BlueBubbles server on Mac, enable web API, set password
# Point webhooks to: https://your-gateway/bluebubbles-webhook?password=<pw>
openclaw onboard  # or: openclaw channels add bluebubbles --http-url http://192.168.1.100:1234 --password <pw>
openclaw pairing approve bluebubbles <CODE>
```
| Field | Default | Notes |
|-------|---------|-------|
| `serverUrl` | — | BlueBubbles REST base URL |
| `password` | — | API password |
| `webhookPath` | `/bluebubbles-webhook` | |
| `dmPolicy` | `pairing` | |
| `groupPolicy` | `allowlist` | |
| `sendReadReceipts` | `true` | |
| `blockStreaming` | `false` | |
| `textChunkLimit` | 4000 | |
| `mediaMaxMb` | 8 | |
| `actions.reactions` | `true` | tapbacks (requires private API) |
| `actions.edit` | — | macOS 13+; **broken on macOS 26 Tahoe** |
| `actions.unsend` | — | macOS 13+ |
| `actions.setGroupIcon` | — | **flaky on macOS 26 Tahoe** |
| `actions.sendAttachment` | — | `asVoice: true` for voice memo (MP3→CAF) |

**Gotchas:**
- macOS 26 Tahoe: `edit` broken, `setGroupIcon` flaky
- Short IDs (`MessageSid`) expire on restart — use `MessageSidFull` for durable automations
- New DM to unknown handle: requires BlueBubbles Private API
- Same-host reverse proxy bypasses password — configure `gateway.trustedProxies`
- VM/headless: Messages.app goes idle — use AppleScript poke-messages LaunchAgent (every 300s)
- Preferred target format: `chat_guid:iMessage;-;<handle>`

---

## Google Chat
**Status:** Ready. HTTP webhooks only. Requires GCP service account.
```bash
# GCP: enable Chat API → Service Account → JSON key
# Chat app config: HTTP endpoint → <gateway>/googlechat → status: Live
export GOOGLE_CHAT_SERVICE_ACCOUNT_FILE=/path/to/sa.json
openclaw gateway && openclaw pairing approve googlechat <CODE>
```
```json5
{ channels: { googlechat: { serviceAccountFile: "/path/to/sa.json", audienceType: "app-url",
    audience: "https://gateway.example.com/googlechat", webhookPath: "/googlechat",
    botUser: "users/1234567890", dm: { policy: "pairing" }, groupPolicy: "allowlist" } } }
```
| Field | Notes |
|-------|-------|
| `audienceType` | `app-url` or `project-number` |
| `audience` | HTTPS webhook URL or project number |
| `botUser` | optional; helps mention detection |
| `typingIndicator` | `none\|message\|reaction` (reaction needs user OAuth) |
| `dm.allowFrom` | `users/<id>` or email |
| `groups."spaces/XXXX"` | `{allow, requireMention, users, systemPrompt}` |
| `mediaMaxMb` | 20 |

**Gotchas:** 405 = missing config or plugin disabled (`openclaw plugins list | grep googlechat`). Bot doesn't appear in Marketplace — search by name. Only expose `/googlechat` path publicly.

---

## Microsoft Teams
> "Abandon all hope, ye who enter here."

**Status:** Plugin required (moved out of core 2026-01-15). Text + DM attachments OK. Channel file sends need SharePoint + Graph.
```bash
openclaw plugins install @openclaw/msteams
# Azure: Create Azure Bot (Single Tenant) → appId, appPassword, tenantId
# Teams: manifest.zip (botId + icons + RSC permissions) → sideload
```
```json5
{ channels: { msteams: { appId: "<ID>", appPassword: "<PW>", tenantId: "<TID>",
    webhook: { port: 3978, path: "/api/messages" } } } }
// Env: MSTEAMS_APP_ID, MSTEAMS_APP_PASSWORD, MSTEAMS_TENANT_ID
```
| Field | Default | Notes |
|-------|---------|-------|
| `dmPolicy` | `pairing` | |
| `allowFrom` | — | AAD object IDs, UPNs, or display names |
| `groupPolicy` | `allowlist` | |
| `requireMention` | `true` | |
| `replyStyle` | `thread` | `thread\|top-level` (per-team/channel override) |
| `teams."<teamId>"` | — | per-team config |
| `teams."<id>".channels."<convId>"` | — | per-channel config |
| `sharePointSiteId` | — | required for file sends in groups/channels |
| `historyLimit` | 50 | |

**RSC manifest permissions:** `ChannelMessage.Read.Group`, `ChannelMessage.Send.Group`, `ChatMessage.Read.Chat`

**Gotchas:**
- **New multi-tenant bots deprecated after 2025-07-31** — use Single Tenant
- `groupId` URL param ≠ team ID — extract from URL path after `/team/` (URL-decoded)
- Manifest update: increment `version` + re-zip + re-upload + reinstall + **fully quit/relaunch Teams**
- Channel attachments = HTML stub only in webhook — Graph API required to download
- `replyStyle`: Teams doesn't expose channel UI style — configure per-channel manually
- Proactive messages only after user has first interacted
- Graph permissions for channel files: `Sites.ReadWrite.All` + `sharePointSiteId` config

---

## Matrix
**Status:** Plugin required. DMs, rooms, threads, media, E2EE, reactions, polls.
```bash
openclaw plugins install @openclaw/matrix
# Get access token via login API or set userId + password
```
```json5
{ channels: { matrix: { homeserver: "https://matrix.example.org", accessToken: "syt_***",
    encryption: true, dm: { policy: "pairing" } } } }
// Envs: MATRIX_HOMESERVER, MATRIX_ACCESS_TOKEN, MATRIX_USER_ID, MATRIX_PASSWORD
```
| Field | Default | Notes |
|-------|---------|-------|
| `accessToken` | — | user ID auto-fetched via `/whoami` |
| `encryption` | `false` | Rust crypto SDK; requires device verification |
| `dm.policy` | `pairing` | |
| `dm.allowFrom` | — | full Matrix IDs `@user:server` |
| `groupPolicy` | `allowlist` | |
| `groups."<roomId>"` | — | `{allow, requireMention, users}` |
| `threadReplies` | `inbound` | `off\|inbound\|always` |
| `autoJoin` | `always` | `always\|allowlist\|off` |
| `mediaMaxMb` | — | |

**Gotchas:**
- Beeper requires E2EE enabled + device verification in Element/other client
- If crypto module missing: `pnpm rebuild @matrix-org/matrix-sdk-crypto-nodejs`
- Crypto state: `~/.openclaw/matrix/accounts/<account>/<homeserver>__<user>/<token-hash>/crypto/`
- Token change = new device = must re-verify for encrypted rooms
- Legacy key: `channels.matrix.rooms` = same shape as `groups`
- Room/user names resolved to IDs at startup; unresolved entries ignored

---

## IRC
**Status:** Extension plugin. Classic IRC channels + DMs.
```json5
{ channels: { irc: { enabled: true, host: "irc.libera.chat", port: 6697, tls: true,
    nick: "openclaw-bot", channels: ["#openclaw"] } } }
```
| Field | Env | Default |
|-------|-----|---------|
| `host` | `IRC_HOST` | — |
| `port` | `IRC_PORT` | — |
| `tls` | `IRC_TLS` | — |
| `nick` | `IRC_NICK` | — |
| `channels` | `IRC_CHANNELS` (comma-sep) | — |
| `dmPolicy` | — | `pairing` |
| `groupPolicy` | — | `allowlist` |
| `groupAllowFrom` | — | global channel sender allowlist |
| `groups."#ch".allowFrom` | — | per-channel senders |
| `groups."#ch".requireMention` | — | `true` |
| `nickserv.password` | `IRC_NICKSERV_PASSWORD` | — |
| `nickserv.register` | — | disable after first use |

**Gotchas:**
- **`allowFrom` is for DMs only** — use `groupAllowFrom` or per-channel `allowFrom` for channels
- Log `drop group sender ... (policy=allowlist)` = sender not in group allowlist
- Log `drop channel ... (missing-mention)` = set `requireMention: false` for that channel
- `toolsBySender`: first match wins; `"*"` = wildcard fallback; can use full hostmask

---

## LINE
**Status:** Plugin required. DMs, groups, Flex messages, quick replies. No reactions/threads.
```bash
openclaw plugins install @openclaw/line
# LINE Developers Console: Messaging API channel → token + secret
# Enable webhook: https://gateway-host/line/webhook
```
```json5
{ channels: { line: { channelAccessToken: "...", channelSecret: "...", dmPolicy: "pairing" } } }
// Envs: LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
```
| Field | Default | Notes |
|-------|---------|-------|
| `webhookPath` | `/line/webhook` | |
| `allowFrom` | — | LINE user IDs: `U` + 32 hex (case-sensitive) |
| `groupPolicy` | `allowlist` | Group IDs: `C` + 32 hex |
| `textChunkLimit` | 5000 | |
| `mediaMaxMb` | 10 | |

Rich messages via `channelData.line`: `quickReplies`, `flexMessage`, `templateMessage`, `location`
Plugin command: `/card info "Title" "Body"` — Flex preset

**Gotchas:**
- LINE IDs are case-sensitive
- Webhook requires HTTPS
- Markdown stripped; code blocks/tables → Flex cards
- Streaming buffered (loading animation)

---

## Zalo (Official Bot API)
**Status:** Experimental. DMs only — groups "coming soon."
```bash
openclaw plugins install @openclaw/zalo
# bot.zaloplatforms.com → create bot → token
```
```json5
{ channels: { zalo: { botToken: "12345689:abc-xyz", dmPolicy: "pairing" } } }
// Env: ZALO_BOT_TOKEN
```
| Field | Default | Notes |
|-------|---------|-------|
| `allowFrom` | — | numeric user IDs only |
| `textChunkLimit` | 2000 | API limit |
| `mediaMaxMb` | 5 | |
| `webhookUrl`/`webhookSecret` | — | HTTPS; secret 8-256 chars |

**Gotchas:** Groups not supported. Polling + webhook mutually exclusive. 2000 char limit → streaming blocked.

---

## Zalo Personal (zalouser — unofficial)
> ⚠️ Unofficial — may cause account ban. Requires `zca` binary in PATH.

```bash
openclaw plugins install @openclaw/zalouser
openclaw channels login --channel zalouser  # scan QR with Zalo mobile
```
- `dmPolicy`: `pairing|allowlist|open|disabled`; `groupPolicy` default `open`; ~2000 char limit; streaming blocked
- Find IDs: `openclaw directory peers list --channel zalouser --query "name"`

---

## Twitch
**Status:** Plugin required. Chat via IRC. 500 char limit.
```bash
openclaw plugins install @openclaw/twitch
# twitchtokengenerator.com → Bot Token → scopes: chat:read + chat:write
# Get user ID: streamweasels.com/tools/convert-twitch-username-to-user-id/
```
```json5
{ channels: { twitch: { username: "botname", accessToken: "oauth:...", clientId: "...",
    channel: "streamerchannel", allowFrom: ["123456789"] } } }
// Env: OPENCLAW_TWITCH_ACCESS_TOKEN
```
| Field | Notes |
|-------|-------|
| `channel` | which chat room to join (required) |
| `allowFrom` | user IDs (permanent; usernames can change) |
| `allowedRoles` | `moderator\|owner\|vip\|subscriber\|all` |
| `requireMention` | `true` |
| `clientSecret` + `refreshToken` | auto token refresh |

**Gotchas:**
- **Use user IDs not usernames** (usernames changeable → impersonation)
- Token Generator tokens can't auto-refresh — need own Twitch app + `clientSecret`/`refreshToken`
- Each account needs its own token
- 500 char limit; markdown stripped
- `username` = who authenticates; `channel` = whose chat to join

---

## Mattermost
**Status:** Plugin required. DMs, channels, groups via bot token + WebSocket.
```bash
openclaw plugins install @openclaw/mattermost
# Create bot account → copy token + base URL
```
```json5
{ channels: { mattermost: { botToken: "mm-token", baseUrl: "https://chat.example.com", dmPolicy: "pairing" } } }
// Envs: MATTERMOST_BOT_TOKEN, MATTERMOST_URL (default account only)
```
| Field | Default | Notes |
|-------|---------|-------|
| `chatmode` | `oncall` | `oncall\|onmessage\|onchar` |
| `oncharPrefixes` | — | e.g. `[">", "!"]` |
| `groupPolicy` | `allowlist` | |
| `groupAllowFrom` | — | user IDs or `@username` |

Target formats: `channel:<id>`, `user:<id>`, `@username`

**Gotchas:** Env vars apply to `default` account only. `oncall` = must be in channel AND @mentioned.

---

## Nextcloud Talk
**Status:** Plugin required. DMs, rooms, reactions. No threads, no native media uploads.
```bash
openclaw plugins install @openclaw/nextcloud-talk
./occ talk:bot:install "OpenClaw" "<secret>" "<webhook-url>" --feature reaction
# Enable bot in room settings
```
```json5
{ channels: { "nextcloud-talk": { baseUrl: "https://cloud.example.com", botSecret: "secret", dmPolicy: "pairing" } } }
// Env: NEXTCLOUD_TALK_BOT_SECRET
```
| Field | Default | Notes |
|-------|---------|-------|
| `apiUser` + `apiPassword` | — | enables DM vs room type detection |
| `webhookPort` | 8788 | |
| `webhookPublicUrl` | — | if behind proxy |
| `allowFrom` | — | Nextcloud user IDs only (not display names) |
| `rooms."<token>"` | — | per-room config |

**Gotchas:** Bots can't initiate DMs. Without `apiUser`+`apiPassword`, DMs treated as rooms. Media = URL-only.

---

## Feishu / Lark
**Status:** Plugin required. WebSocket long connection — no public URL needed.
```bash
openclaw plugins install @openclaw/feishu
openclaw onboard  # or: openclaw channels add
# Feishu Open Platform: create app → permissions (batch import) → enable bot → event subscription (long connection, im.message.receive_v1) → publish
openclaw pairing approve feishu <CODE>
```
```json5
{ channels: { feishu: { domain: "lark",  // for international Lark tenants
    accounts: { main: { appId: "cli_xxx", appSecret: "xxx" } }, dmPolicy: "pairing" } } }
// Envs: FEISHU_APP_ID, FEISHU_APP_SECRET
```
| Field | Default | Notes |
|-------|---------|-------|
| `domain` | `feishu` | `lark` for international tenants |
| `dmPolicy` | `pairing` | |
| `allowFrom` | — | Open IDs `ou_xxx` |
| `groupPolicy` | `open` | |
| `groups.<chat_id>.requireMention` | `true` | |
| `textChunkLimit` | 2000 | |
| `mediaMaxMb` | 30 | |
| `streaming` | `true` | card-based |
| `blockStreaming` | `true` | |

**Gotchas:**
- **Gateway must be running before configuring event subscription** — setup may fail otherwise
- Group IDs: `oc_xxx`; User IDs: `ou_xxx` — find via `openclaw logs --follow`
- No native command menus — send commands as text
- App must be published + approved before receiving messages
- `bindings` config available for routing DMs/groups to different agents

---

## Nostr
**Status:** Optional plugin. DMs via NIP-04. No groups, no media.
```bash
nak key generate && openclaw plugins install @openclaw/nostr
export NOSTR_PRIVATE_KEY="nsec1..."
```
```json5
{ channels: { nostr: { privateKey: "${NOSTR_PRIVATE_KEY}", relays: ["wss://relay.damus.io","wss://nos.lol"], dmPolicy: "pairing" } } }
```
| Field | Default | Notes |
|-------|---------|-------|
| `privateKey` | required | `nsec...` or 64-char hex |
| `relays` | damus.io, nos.lol | 2-3 recommended |
| `allowFrom` | — | `npub...` or hex pubkeys |
| `profile` | — | NIP-01 kind:0 metadata |

**Gotchas:** DMs only (NIP-04); NIP-17 planned. Duplicate events from multiple relays deduplicated by event ID. Never commit private keys.

---

## Tlon (Urbit)
**Status:** Plugin required. DMs, group mentions, threads. No reactions/polls/native media.
```bash
openclaw plugins install @openclaw/tlon
```
```json5
{ channels: { tlon: { ship: "~sampel-palnet", url: "https://your-ship-host", code: "lidlut-..." } } }
```
| Field | Default | Notes |
|-------|---------|-------|
| `groupChannels` | — | explicit list; default: auto-discover |
| `autoDiscoverChannels` | `true` | |
| `dmAllowlist` | allow all | `["~zod"]` to restrict |
| `defaultAuthorizedShips` | — | default group auth |
| `authorization.channelRules."<ch>"` | — | `{mode: restricted\|open, allowedShips}` |

Delivery targets: `~sampel-palnet` (DM) / `chat/~host/channel` (group)

**Gotchas:** Group replies require @mention of bot ship. Media = text + URL fallback (no native upload).
