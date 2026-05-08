---
name: audio-clips
description: "Generate, save, list, and email TTS audio clips as MP3 files. Use when the user asks for an audio version, a recording, a voiceover, or wants to send a narration of some text. Distinct from live voice agent speech — this saves a permanent file."
metadata: {"openclaw": {"emoji": "🎙", "requires": {"env": []}}}
---

# Audio Clips Skill

Persist a TTS-generated MP3 to the server. The clip is saved on disk, indexed in a manifest, and can be downloaded, played, or emailed via AgentMail.

**This is different from `/api/tts/generate`** — that endpoint streams ephemeral audio for live voice. Use this skill when the user wants a *file* they can keep, share, or send.

## When to suggest this proactively

If the user says any of these and the conversation has narratable text on the table, OFFER an audio clip:
- "Read this back to me" *(when used repeatedly on the same text — they may be capturing it)*
- "Can I get a recording of that"
- "Make an audio version"
- "I want to send this as a voicemail"
- "Voice over"
- "Narrate this"

Also offer when the user is dealing with a letter, a script, a message they want to convey via audio (e.g. responding to a billing dispute, sending a personalized reply).

## Open the canvas page

The user-facing UI is at `/pages/audio-clip-creator.html`. To open it for the user:

```
canvas:show audio-clip-creator
```

The page lets the user paste text, pick from all available voices (Orpheus / Supertonic / Qwen3 / Resemble / ElevenLabs depending on what's configured), preview each voice, generate, download, and email.

## Direct API (when the agent generates without the UI)

### Generate a clip

```bash
curl -sS -X POST http://localhost:5001/api/audio-clips/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Text to narrate (max 8000 chars).",
    "provider": "groq",
    "voice": "autumn",
    "label": "delphina-letter",
    "leading_silence_ms": 1000
  }'
```

**Response:** clip metadata including `id`, `url` (`/uploads/audio-clips/<id>.mp3`), `duration_ms`, `size_bytes`.

**Defaults & rules:**
- `provider` defaults to `groq` (Orpheus). Other options: `supertonic`, `qwen3`, `resemble`, `elevenlabs`.
- `voice` is provider-specific. Orpheus voices: autumn, diana, hannah (F); austin, daniel, troy (M).
- `leading_silence_ms` defaults to 1000ms — Groq Orpheus clips the first 1-2 seconds, so the silence pad protects the opening word. Set to 0 only when you specifically want no silence.
- `label` is for clip-history display.
- Max text 8000 chars (vs 2000 for the live `/api/tts/generate` endpoint).

### List saved clips

```bash
curl -sS http://localhost:5001/api/audio-clips/list
```

### Email a saved clip

```bash
curl -sS -X POST http://localhost:5001/api/audio-clips/email \
  -H 'Content-Type: application/json' \
  -d '{
    "clip_id": "20260507-160729-...",
    "to": ["recipient@example.com"],
    "cc": ["other@example.com"],
    "subject": "Recording attached",
    "body": "Hi — here'\''s the audio version of the letter."
  }'
```

Uses the tenant's AgentMail key (from `AGENTMAIL_API_KEY` env). Auto-discovers the inbox if `AGENTMAIL_INBOX` isn't set.

**SECURITY:** Sending email is a visible-action — when YOU (the agent) trigger an email send on the user's behalf, follow the AgentMail double-confirmation rule. The canvas page already enforces this in its UI.

### Soft-delete a clip

```bash
curl -sS -X DELETE http://localhost:5001/api/audio-clips/<clip_id>
```

This sets `soft_deleted: true` in the manifest. **The MP3 file is never deleted from disk** — per CLAUDE.md, AI-generated paid content is permanent.

## Why every clip is saved

Every TTS generation costs money (Groq, ElevenLabs, Resemble all charge per character or per minute). The save-to-disk-immediately pattern means:
- The user doesn't lose work if the page closes
- Clips can be re-used without regenerating
- The manifest is the single source of truth (no localStorage, no in-memory loss)

## Files

- Server route: `/mnt/system/base/OpenVoiceUI/routes/audio_clips.py`
- Canvas page: `/mnt/system/base/OpenVoiceUI/app/static/canvas-pages/audio-clip-creator.html`
- Auth bypass: `/mnt/system/base/OpenVoiceUI/app.py` line ~123 (`/api/audio-clips/`)
- Per-tenant clip storage: `/mnt/clients/<tenant>/openvoiceui/uploads/audio-clips/`
