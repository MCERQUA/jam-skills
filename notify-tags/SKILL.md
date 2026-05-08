---
name: notify-tags
description: UI notification, face registration, and camera vision tags. Covers [NOTIFY:*], [REGISTER_FACE:*], [CAMERA VISION:*]. Read when the user wants to show a popup, register a face, or you receive a camera-vision system message.
---

# Notify, Face, and Camera Tags

## Notifications

Embed in your spoken response. The popup is visual — your spoken words tell the user what's happening.

| Tag | Effect |
|---|---|
| `[NOTIFY:message]` | Show popup with message |
| `[NOTIFY_TITLE:text]` | Set popup title |
| `[NOTIFY_PROGRESS:N/M]` | Show progress (e.g. `3/10`) |
| `[NOTIFY_STATUS:text]` | Update status text inside popup |
| `[NOTIFY_CLOSE]` | Hide popup |
| `[NOTIFY_COMPLETE]` | Mark done, auto-dismiss |

## Face Registration

```
[REGISTER_FACE:Name]
```

Save a face from the camera. **Only when the user explicitly asks** ("remember my face", "register me as Mike"). Never auto-register.

## Camera Vision (incoming, not outgoing)

When you see `[CAMERA VISION: ...]` in a system message, that's the camera describing what it currently sees. Describe naturally to the user:

- ✅ "Looks like you're at your desk."
- ❌ Don't repeat the raw description verbatim
- ❌ Don't quote the bracket text

## Rules

- Tags are invisible to voice — always include spoken words alongside
- Don't notify for trivial events (every step) — only meaningful state changes
- For long jobs, prefer one `[NOTIFY_TITLE:]` + `[NOTIFY_PROGRESS:]` updates over multiple separate notifications
