---
upstream: https://docs.openclaw.ai/channels/index.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [12]
related_pages: [channels__access-groups, channels__channel-routing, channels__group-messages]
---

# Channels — JamBot annotation

## What docs say (TL;DR)

Channels = inbound/outbound message surfaces. Each channel has its own setup page (Slack, Discord, Telegram, WhatsApp, iMessage, Matrix, etc.). DM/group policies, mention gating, routing priority, session keys, message flow, reply tags. New v4.x: `messages.visibleReplies` global, `accessGroup:<name>` (Discord), `replyContextApiFallback`.

## JamBot uses none of these directly

JamBot's primary channel is **OpenVoiceUI WebChat** (in-browser). We don't currently use the bundled channels (Slack/Discord/Telegram/etc.) for client-facing agent surfaces.

The channels matter for:
- **Twilio voice-call project** (`/twilio-dev` skill) — uses voice-call plugin (anchor #12)
- **Cycle 6 ovui-desktop** — runs in container; not a "channel" per se
- **Mesh** — JamBot's custom inter-agent transport, NOT an OpenClaw channel

## Anchor #12 — externalization wave

Most channels moved to external `@openclaw/*` npm packages in v5.2:

| Channel | Status |
|---------|--------|
| Discord, WhatsApp, Voice Call, Brave, Codex, Memory LanceDB, Microsoft Teams, Diffs, Lobster, BlueBubbles, Mattermost, Matrix, Tlon, Google Chat, LINE, Nextcloud Talk, Nostr, Zalo, Zalo Personal, QQ Bot, Synology Chat, Twitch, Feishu, Google Meet, Yuanbao | External |
| ACPX, Diagnostics-OTel | Already on npm |

For any client we add a real channel to (e.g. customer-facing Telegram bot), use `openclaw plugins install npm:@openclaw/<channel>`.

## v4.29 messaging changes

| Surface | Source |
|---------|--------|
| `messages.visibleReplies` global | line 411 |
| `messages.groupChat.visibleReplies: "automatic"` (Discord default flipped to private) | line 936 (v4.26) |
| `accessGroup:<name>` for Discord | v5.2 |
| `channels.<>.replyContextApiFallback` | per-channel knob |
| `messages.tts.providers.<id>.apiKey` resolved through active runtime snapshot | v4.26 line 1212 |
| Telegram `pollingStallThresholdMs` raised to 120s (was 90s) | v4.20 line 2384 |
| Discord `applicationId` app-id lookup bypass | v4.29 line 549 |
| Discord `voice.model` LLM override | v4.25 line 1372 |
| Slack socketMode `clientPingTimeout` / `serverPingTimeout` / `pingPongLoggingEnabled` | v4.27 line 821 |
| BlueBubbles `replyContextApiFallback` opt-in | v5.2 line 26 |

## Key concepts (still valid from old skill)

- **DM scope** controls how DM conversations are isolated. Default `"main"` = all DMs share one session. Use `"per-channel-peer"` for multi-user setups.
- **Mention gating** in groups via `requireMention`
- **Routing priority** by binding rules

## Related JamBot files

- `audit-anchors/anchor-12-external-plugin-migration.md`
- `annotations/plugins__voice-call.md`
- `/twilio-dev` skill — relevant for any phone channel work
- `docs/jambot/client-registry.md` — per-client channel state (currently none beyond webchat)
