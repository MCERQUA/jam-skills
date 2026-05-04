---
upstream: https://docs.openclaw.ai/plugins/voice-call.md
relevance: jambot-critical
last-verified: 2026-05-04
audit_anchors: [12]
related_overrides: [voice-flow-quirks.md]
related_pages: [cli__voicecall]
---

# Voice Call plugin — JamBot annotation

## What docs say (TL;DR)

Plugin `@openclaw/voice-call` enables phone-call agents via Twilio (Programmable Voice + Media Streams), Telnyx (Call Control v2), Plivo (Voice API + XML), or mock for dev. Runs in-Gateway (must be on the gateway machine). Realtime voice OR streaming transcription, not both. Per-number routing. CLI: `voicecall setup`, `voicecall smoke`, `call`, `continue`, `speak`, `dtmf`, `end`, `status`, `tail`, `latency`, `expose`. Agent tool: `voice_call`.

## Anchor #12 — externalization

v5.2 wholesale externalized voice-call to `@openclaw/voice-call` npm package. Install:
```
openclaw plugins install npm:@openclaw/voice-call
```

## JamBot's voice surface is NOT this plugin

JamBot's primary voice surface is OpenVoiceUI's in-browser SpeechRecognition + WebSocket → OpenClaw. This is NOT the voice-call plugin (which is for phone-call telephony).

The voice-call plugin would be relevant for the Twilio voice-call project documented in `/twilio-dev` skill — outbound contractor morning check-in workflow + inbound calls.

## Where this matters for JamBot

| Use case | Plugin needed? |
|----------|----------------|
| Browser voice agent (current OpenVoiceUI) | NO |
| Outbound phone calls (twilio-dev project) | YES — install `@openclaw/voice-call` |
| Inbound phone agent | YES |
| Multi-tenant phone routing (per-domain numbers) | YES — plugin's `numbers` per-number routing |

## Key plugin features

- **Realtime voice** via Google Gemini Live or OpenAI Realtime — full-duplex; cannot coexist with streaming mode
- **Streaming transcription** via Deepgram, ElevenLabs, Mistral, OpenAI, xAI — real-time forwarding
- **Per-number routing**: `numbers` config gives different greetings/prompts/agents/voices per dialed number
- **Inbound caller-ID allowlist**: `inboundPolicy: "allowlist"` + `allowFrom` (filter only, not strong identity)
- **Stale-call reaper** `staleCallReaperSeconds` (recommend 120-300s) auto-ends calls lacking terminal webhooks
- **Replay protection** for Twilio + Plivo via per-turn tokens
- **Stream grace period** 2-second window before auto-end on Twilio media stream disconnect
- **Webhook security**: signature verification + `allowedHosts` + `trustedProxyIPs` + header trust controls

## Setup verification

```bash
openclaw voicecall setup       # validates plugin enablement, credentials, webhook exposure, audio mode exclusivity
openclaw voicecall smoke --yes  # actual test call (default dry-run)
```

## Realtime + consult

Realtime calls can invoke `openclaw_agent_consult` for deeper reasoning between voice exchanges. Tool policies: `safe-read-only`, `owner`. Optional indexed memory search (fast context) before falling back to full consult agent.

## TTS integration

Uses core `messages.tts.providers.<id>.*` config with deep-merge overrides. **Microsoft Speech is unsupported for calls.**

## Related JamBot files

- `audit-anchors/anchor-12-external-plugin-migration.md`
- `overrides/voice-flow-quirks.md` — OpenVoiceUI in-browser voice (NOT this plugin)
- `/twilio-dev` skill — JamBot Twilio voice-call project (uses this plugin)
- `cli__voicecall` annotation (TODO)
