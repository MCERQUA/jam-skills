# OpenClaw Channels — Reference

---

## Supported Channels

| Channel | Plugin? | Transport | Notes |
|---------|---------|-----------|-------|
| WhatsApp | no | Baileys (WA Web) | QR pairing required; recommended on dedicated number |
| Telegram | no | Bot API / grammY | Fastest setup (just a bot token) |
| Discord | no | Discord Gateway | Guilds + DMs + threads |
| Slack | no | Bolt SDK / Socket Mode | Workspace app |
| Signal | no | signal-cli JSON-RPC + SSE | Separate bot number required |
| IRC | no | IRC TCP | Classic server support |
| BlueBubbles | no | REST API + webhook | Recommended for iMessage |
| iMessage (legacy) | no | `imsg` CLI | Deprecated; use BlueBubbles |
| Google Chat | yes | HTTP webhook | Needs public URL |
| Feishu/Lark | yes | WebSocket | Install separately |
| Mattermost | yes | Bot API + WebSocket | Install separately |
| Microsoft Teams | yes | Bot Framework | Azure Bot + install separately |
| LINE | yes | Messaging API | Install separately |
| Nextcloud Talk | yes | Webhook | Install separately |
| Matrix | yes | matrix-bot-sdk | E2EE support; install separately |
| Nostr | yes | NIP-04 DMs | Decentralized; install separately |
| Tlon/Urbit | yes | Ship REST | install separately |
| Twitch | yes | IRC connection | 500-char limit auto-chunked |
| Zalo (Bot) | yes | Bot API | Experimental; DM-only |
| Zalo (Personal) | yes | `zca-cli` QR | Unofficial; install separately |
| WebChat | built-in | WebSocket (Gateway UI) | Attaches to selected agent |

- Channels run **simultaneously** — configure multiple, Gateway routes per chat.
- Channels connect **through the Gateway** — model does not choose the outbound channel.

---

## DM Policies

Configured per-channel as `channels.<channel>.dmPolicy`:

| Policy | Behavior |
|--------|----------|
| `pairing` | Unknown senders get an 8-char code; message held until owner approves |
| `allowlist` | Only senders in `allowFrom` are accepted; others silently dropped |
| `open` | All senders accepted (requires `allowFrom: ["*"]`) |
| `disabled` | All DMs blocked |

**Default DM policy** is `pairing` for Telegram, WhatsApp, Discord, Signal, iMessage.

### Pairing codes
- 8 characters, uppercase, no ambiguous chars (`0`, `O`, `1`, `I`)
- Expire after **1 hour**
- Max **3 pending requests** per channel; extras ignored until one expires/approves

### Pairing CLI
```bash
openclaw pairing list telegram
openclaw pairing list whatsapp
openclaw pairing approve telegram <CODE>
```

Supported: `telegram`, `whatsapp`, `signal`, `imessage`, `discord`, `slack`

### State storage
- Pending requests: `~/.openclaw/credentials/<channel>-pairing.json`
- Approved allowlist: `~/.openclaw/credentials/<channel>-allowFrom.json`

### `allowFrom` format by channel
- WhatsApp/Signal: E.164 phone numbers (`+15551234567`)
- Telegram: numeric user IDs or `@username` (prefixes `telegram:` / `tg:` accepted)
- Discord: numeric user IDs, `user:<id>`, or `<@id>` mention
- Slack: user IDs or channel names

---

## Group Policies

### Decision flow (evaluated in order)
```
groupPolicy? disabled  → drop
groupPolicy? allowlist → group in allowlist? no → drop
requireMention? yes    → mentioned? no → store for context only
otherwise              → reply
```

### Policy values (`channels.<channel>.groupPolicy`)

| Policy | Behavior |
|--------|----------|
| `open` | Groups bypass allowlists; mention-gating still applies |
| `disabled` | Block all group messages |
| `allowlist` | Only allowed groups/rooms reply (default) |

- WhatsApp/Signal: `groupAllowFrom: ["+15551234567"]`
- Telegram: `groupAllowFrom: ["123456789", "@username"]`
- Discord: `guilds: { GUILD_ID: { channels: { help: { allow: true } } } }`
- Slack: `channels: { "#general": { allow: true } }`
- Matrix: `groups: { "!roomId:example.org": { allow: true } }`, `groupAllowFrom: ["@owner:example.org"]`

---

## Mention Gating

- Group messages require a **mention** unless `requireMention: false` is set.
- Replying to a bot message counts as implicit mention (Telegram, WhatsApp, Slack, Discord, Teams).
- `mentionPatterns` are **case-insensitive regexes** — fallback when native mentions stripped.
- Shared across all channels via `agents.list[].groupChat.mentionPatterns`.

### Mention config
```json5
{
  channels: {
    whatsapp: {
      groups: {
        "*": { requireMention: true },
        "123@g.us": { requireMention: false },
      },
    },
    telegram: {
      groups: { "*": { requireMention: true } },
    },
  },
  agents: {
    list: [
      {
        id: "main",
        groupChat: {
          mentionPatterns: ["@?openclaw", "\\+?15555550123"],
          historyLimit: 50,
        },
      },
    ],
  },
}
```

### Activation command (owner-only)
```
/activation mention
/activation always
```
- `/activation always` → agent replies every message (returns `NO_REPLY` token when nothing to add)
- `/activation mention` → default gated mode
- Only WhatsApp currently respects `/activation`; others ignore it

---

## Channel Routing to Agents

### Routing priority (6-step, first match wins)
1. **Exact peer match** — `bindings` with `peer.kind` + `peer.id`
2. **Guild match** — Discord `guildId`
3. **Team match** — Slack `teamId`
4. **Account match** — `accountId` on the channel
5. **Channel match** — any account on that channel type
6. **Default agent** — `agents.list[].default`, else first list entry, fallback to `main`

### Binding config example
```json5
{
  agents: {
    list: [{ id: "support", name: "Support", workspace: "~/.openclaw/workspace-support" }],
  },
  bindings: [
    { match: { channel: "slack", teamId: "T123" }, agentId: "support" },
    { match: { channel: "telegram", peer: { kind: "group", id: "-100123" } }, agentId: "support" },
  ],
}
```

### Broadcast groups (multiple agents, same peer)
```json5
{
  broadcast: {
    strategy: "parallel",
    "120363403215116621@g.us": ["alfred", "baerbel"],
    "+15555550123": ["support", "logger"],
  },
}
```
Strategies: `parallel` (simultaneous), `sequential` (one at a time).

---

## Session Keys

### Key shapes
| Context | Session key pattern |
|---------|-------------------|
| DM (default) | `agent:<agentId>:main` |
| WhatsApp group | `agent:<agentId>:whatsapp:group:<jid>` |
| Telegram group | `agent:<agentId>:telegram:group:<chatId>` |
| Telegram forum topic | `agent:<agentId>:telegram:group:<chatId>:topic:<threadId>` |
| Discord channel | `agent:<agentId>:discord:channel:<channelId>` |
| Discord thread | `agent:<agentId>:discord:channel:<channelId>:thread:<threadId>` |
| Slack channel | `agent:<agentId>:slack:channel:<channelId>` |
| Slack thread | `agent:<agentId>:slack:channel:<channelId>:thread:<threadId>` |
| Discord slash cmd | `agent:<agentId>:discord:slash:<userId>` |

- DM sessions share the **main** session key by default (`session.dmScope=main`).
- Heartbeats are **skipped** for group sessions.
- Session files: `~/.openclaw/agents/<agentId>/sessions/sessions.json`
- JSONL transcripts live alongside the session store.

### Pattern: personal DMs + sandboxed groups (single agent)
```json5
{
  agents: {
    defaults: {
      sandbox: {
        mode: "non-main",    // groups/channels get sandboxed
        scope: "session",    // one container per group
        workspaceAccess: "none",
      },
    },
  },
  tools: {
    sandbox: {
      tools: {
        allow: ["group:messaging", "group:sessions"],
        deny: ["group:runtime", "group:fs", "group:ui", "nodes", "cron", "gateway"],
      },
    },
  },
}
```

---

## Message Flow

### Inbound (channel → agent)
1. Channel receives message, normalizes into shared envelope
2. Access control checked: DM policy → group policy → mention gating
3. Routing selects agent (6-step priority)
4. Session key resolved
5. Group context injected (pending messages since last reply, default 50)
6. Message dispatched to agent for inference

### Inbound group context injection (WhatsApp/all channels)
- Pending messages (those that didn't trigger a run) injected under:
  ```
  [Chat messages since your last reply - for context]
  ...messages...
  [Current message - respond to this]
  ```
- Sender surfaced as: `[from: Sender Name (+E164)]`
- Already-in-session messages are **not** re-injected

### Context fields set on inbound group messages
- `ChatType=group`
- `GroupSubject` (if known)
- `GroupMembers` (if known)
- `WasMentioned`
- `MessageThreadId`, `IsForum` (Telegram forum topics)

### Outbound (agent → channel)
1. Agent produces text (+ optional media, buttons, reply tags)
2. Text chunked if over channel limit
3. Reply tags applied (`[[reply_to_current]]`, `[[reply_to:<id>]]`)
4. Typing indicator sent (if configured)
5. Message sent back to originating channel

### Reply context (inbound)
- `ReplyToId`, `ReplyToBody`, `ReplyToSender` when available
- Quoted context appended to `Body` as `[Replying to ...]`
- Consistent across all channels

---

## Text Chunking and Streaming

### Per-channel text limits

| Channel | Default limit | Config key |
|---------|--------------|------------|
| Telegram | 4000 chars | `channels.telegram.textChunkLimit` |
| Discord | (Discord API limit) | `channels.discord.textChunkLimit` |
| Twitch | 500 chars | auto-chunked (hardcoded) |
| Zalo | 2000 chars | hardcoded |

- `chunkMode: "newline"` — prefers paragraph boundaries before length splitting
- `channels.discord.maxLinesPerMessage` — additional line-count limit

### Telegram draft streaming
- `channels.telegram.streamMode`:
  - `off` — no streaming
  - `partial` (default) — frequent draft updates from partial text
  - `block` — chunked drafts using `draftChunk` settings
- `draftChunk` defaults (block mode): `minChars: 200`, `maxChars: 800`, `breakPreference: "paragraph"`
- `maxChars` clamped by `textChunkLimit`
- Draft streaming: **DM-only**; groups do not use draft bubbles
- `channels.telegram.blockStreaming: true` — sends real Telegram messages instead of draft updates
- Telegram-only: `/reasoning stream` sends reasoning to draft bubble while generating

---

## Typing Indicators

- Controlled by `agents.defaults.typingMode`
- Default: `message` (send typing while generating a reply)
- Groups use typing mode from `agents.defaults.typingMode`; typing targets group/topic thread
- Telegram: sends `typing` action, targets `message_thread_id` for forum topics
- WhatsApp: ack reactions (`sendReadReceipts` behavior varies)
- Telegram: **no read-receipt support** (`sendReadReceipts` does not apply)

---

## Reply Tags

Tags can appear in agent output to control threading:

| Tag | Behavior |
|-----|---------|
| `[[reply_to_current]]` | Reply to the triggering message |
| `[[reply_to:<id>]]` | Reply to a specific message ID |
| `[[audio_as_voice]]` | Telegram: send audio as voice note |

### `replyToMode` per channel

| Channel | Default | Config key |
|---------|---------|-----------|
| Telegram | `first` | `channels.telegram.replyToMode` |
| Discord | `off` | `channels.discord.replyToMode` |

Values: `off`, `first`, `all`

---

## Media Handling

- Inbound media normalized into shared channel envelope with media placeholders
- `channels.telegram.mediaMaxMb` — default `5` MB; caps inbound media download size
- `channels.discord.mediaMaxMb` — similar cap
- Static images/media are processed; some types skipped (Telegram: animated TGS, video WEBM stickers)

### Telegram stickers
- Static WEBP: downloaded, processed → `<media:sticker>` placeholder
- Animated TGS: skipped
- Video WEBM: skipped
- Sticker context fields: `Sticker.emoji`, `Sticker.setName`, `Sticker.fileId`, `Sticker.cachedDescription`
- Cache: `~/.openclaw/telegram/sticker-cache.json`

### Telegram audio/video
- Audio: defaults to file; tag `[[audio_as_voice]]` to force voice note
- Video: tag `asVideoNote: true` in message action for video note (no captions)

### WhatsApp media
- Ephemeral/view-once messages unwrapped before text/mention extraction
- Media normalization handled by Baileys layer

---

## Group/Channel Tool Restrictions

```json5
{
  channels: {
    telegram: {
      groups: {
        "*": { tools: { deny: ["exec"] } },
        "-1001234567890": {
          tools: { deny: ["exec", "read", "write"] },
          toolsBySender: {
            "123456789": { alsoAllow: ["exec"] },
          },
        },
      },
    },
  },
}
```

**Resolution order (most specific wins):**
1. group/channel `toolsBySender` match
2. group/channel `tools`
3. default `"*"` `toolsBySender` match
4. default `"*"` `tools`

- Group restrictions are **additive** to global/agent tool policy (deny still wins).
- Discord nests: `guilds.*.channels.*`
- Slack nests: `channels.*`
- Teams nests: `teams.*.channels.*`

---

## Node Device Pairing

For iOS/Android/macOS/headless nodes connecting as `role: node`:

```bash
# Recommended: via Telegram (device-pair plugin)
# 1. In Telegram: /pair
# 2. Bot replies with setup code (base64 JSON with url + token)
# 3. Paste in iOS app → Settings → Gateway
# 4. In Telegram: /pair approve

# CLI
openclaw devices list
openclaw devices approve <requestId>
openclaw devices reject <requestId>
```

State:
- `~/.openclaw/devices/pending.json`
- `~/.openclaw/devices/paired.json`

---

## Troubleshooting

### Diagnostic ladder (run in order)
```bash
openclaw status
openclaw gateway status
openclaw logs --follow
openclaw doctor
openclaw channels status --probe
```

**Healthy baseline:** `Runtime: running`, `RPC probe: ok`, channel probe shows connected/ready

### WhatsApp failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| Connected but no DM replies | `openclaw pairing list whatsapp` | Approve sender or switch DM policy/allowlist |
| Group messages ignored | Check `requireMention` + mention patterns | Mention bot or relax mention policy for that group |
| Random disconnect/relogin loops | `openclaw channels status --probe` + logs | Re-login, verify credentials directory is healthy |

### Telegram failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| `/start` but no usable reply flow | `openclaw pairing list telegram` | Approve pairing or change DM policy |
| Bot online but group stays silent | Verify mention requirement and bot privacy mode | Disable privacy mode for group visibility or mention bot |
| Send failures with network errors | Inspect logs for Telegram API call failures | Fix DNS/IPv6/proxy routing to `api.telegram.org` |

### Discord failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| Bot online but no guild replies | `openclaw channels status --probe` | Allow guild/channel and verify message content intent |
| Group messages ignored | Check logs for mention gating drops | Mention bot or set guild/channel `requireMention: false` |
| DM replies missing | `openclaw pairing list discord` | Approve DM pairing or adjust DM policy |

### Slack failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| Socket mode connected but no responses | `openclaw channels status --probe` | Verify app token + bot token and required scopes |
| DMs blocked | `openclaw pairing list slack` | Approve pairing or relax DM policy |
| Channel message ignored | Check `groupPolicy` and channel allowlist | Allow the channel or switch policy to `open` |

### iMessage / BlueBubbles failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| No inbound events | Verify webhook/server reachability and app permissions | Fix webhook URL or BlueBubbles server state |
| Can send but no receive on macOS | Check macOS privacy permissions for Messages automation | Re-grant TCC permissions and restart channel process |
| DM sender blocked | `openclaw pairing list imessage` or `openclaw pairing list bluebubbles` | Approve pairing or update allowlist |

### Signal failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| Daemon reachable but bot silent | `openclaw channels status --probe` | Verify signal-cli daemon URL/account and receive mode |
| DM blocked | `openclaw pairing list signal` | Approve sender or adjust DM policy |
| Group replies do not trigger | Check group allowlist and mention patterns | Add sender/group or loosen gating |

### Matrix failure signatures
| Symptom | Fastest check | Fix |
|---------|--------------|-----|
| Logged in but ignores room messages | `openclaw channels status --probe` | Check `groupPolicy` and room allowlist |
| DMs do not process | `openclaw pairing list matrix` | Approve sender or adjust DM policy |
| Encrypted rooms fail | Verify crypto module and encryption settings | Enable encryption support and rejoin/sync room |

---

## Quick Reference: Config Key Locations

| Concern | Config path |
|---------|------------|
| DM policy | `channels.<ch>.dmPolicy` |
| DM allowlist | `channels.<ch>.allowFrom` |
| Group policy | `channels.<ch>.groupPolicy` |
| Group sender allowlist | `channels.<ch>.groupAllowFrom` |
| Per-group settings | `channels.<ch>.groups.<id>` |
| Default group settings | `channels.<ch>.groups."*"` |
| Mention patterns (agent) | `agents.list[].groupChat.mentionPatterns` |
| Mention patterns (global) | `messages.groupChat.mentionPatterns` |
| Group history limit | `channels.<ch>.historyLimit` / `messages.groupChat.historyLimit` |
| DM history limit | `channels.<ch>.dmHistoryLimit` |
| Text chunk limit | `channels.<ch>.textChunkLimit` |
| Chunk mode | `channels.<ch>.chunkMode` |
| Streaming mode (Telegram) | `channels.telegram.streamMode` |
| Reply threading | `channels.<ch>.replyToMode` |
| Typing mode | `agents.defaults.typingMode` |
| Broadcast groups | `broadcast.<peerId>: [agentId, ...]` |
| Agent bindings | `bindings[].match` + `bindings[].agentId` |
