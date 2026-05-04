# JamBot voice flow — quirks not in upstream docs

OpenClaw upstream docs cover the `voice-call` plugin (Twilio/Telnyx/Plivo) but JamBot's voice surface is OpenVoiceUI in-browser SpeechRecognition + WebSocket → OpenClaw. Different stack, different rules.

## Single-instance SpeechRecognition rule — NON-NEGOTIABLE

**NEVER destroy/recreate SpeechRecognition instances.** Both Wake Word Detector and main STT must exist from page load — only toggle `.start()` / `.stop()`. The WakeWordDetector abort loop is NORMAL.

Source patches that enforced this: see `/jambot-voice-flow` skill for file:line refs.

## Wake word + PTT lifecycle

| State | Wake Word Detector | Main STT |
|-------|-------------------|----------|
| Idle | listening (abort loop) | stopped |
| Wake detected | stopped | started |
| User speaking | stopped | streaming partial transcripts |
| User done | stopped | stopped after final |
| Agent speaking | stopped | stopped |
| Agent done | listening (abort loop) | stopped |

Race conditions between these states caused the 2026-04-18 nine-fix cascade.

## Bare "NO" / "YES" voice-agent leak — fixed 2026-05-02

Degenerate LLM bare-token output slipped through empty-retry path. Two-layer guard now in `routes/conversation.py`. Branch `fix/eradicate-bare-no-yes-responses` in `/mnt/system/base/OpenVoiceUI`. **Source is BAKED into image, no bind-mount** — needs commit + image rebuild to propagate to fresh containers.

Memory file: `bare-no-response-fix.md`.

## Empty `chat.final` from MiniMax-M2.7-highspeed

MiniMax returns `chat.final` with zero text 15+ times per 30 minutes. The 13-fix recovery cascade in `playbooks/debug-empty-final.md` (TODO migrate from `references/session-recovery-and-empty-finals.md`) handles this.

Related upstream concept: anchor #4 (embedded run timeout — may interact).

## queue.mode default flipped — anchor #14

v4.29 changed `messages.queue.mode` default to `steer` (was `collect`). For voice flow this is mostly an improvement: when a user keeps talking while agent is mid-stream, multiple messages get steered together at the next model boundary instead of one-at-a-time.

If a client wants strict turn-taking:
```json5
{ messages: { queue: { mode: "collect" } } }
```

## See also

- `/jambot-voice-flow` skill — STT, wake word, PTT, call lifecycle, file:line refs
- `docs/jambot/openvoiceui-system-prompt.md`
- `docs/jambot/mesh-topology-and-voice-agent-sync.md`
- `audit-anchors/anchor-14.md` — queue.mode default
- `playbooks/debug-empty-final.md` (TODO — migrate from references/session-recovery-and-empty-finals.md)
