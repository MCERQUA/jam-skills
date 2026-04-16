---
name: airadio
description: Push songs, playlists, and images to the user's AI-Radio account; pull songs back to play; manage friends; send songs one-to-one; vote on community tracks. Integration with radio.jam-bot.com.
metadata: {"openclaw": {"emoji": "📻"}}
---

# AI-Radio Integration

AI-Radio (radio.jam-bot.com) is the user's **persistent, social, multi-user music layer**. You can push music from this OpenVoiceUI workspace into their AI-Radio account and pull music back to play. You can also manage their friends, send songs, and cast votes.

**All AI-Radio actions are done by emitting voice tags** that OpenVoiceUI parses — the tags are stripped from TTS so the user hears the surrounding words but not the tag itself.

---

## When to use this skill

Trigger on phrases like:
- "send this to my AI-Radio" / "send this song to AI-Radio" / "push to radio"
- "send my [playlist name] to AI-Radio"
- "play [song] from AI-Radio" / "pull [song] from radio"
- "send this song to [friend name]"
- "add [name] as a friend on AI-Radio"
- "what songs did my friends send me"
- "upvote this" / "downvote this" (when playing a song from AI-Radio)
- "change my AI-Radio profile picture" / "update the cover for [song]"

If the user is just asking generic music questions (generate, play local, skip), use the `suno-music` skill or `[MUSIC_PLAY]` tags instead. This skill is specifically the AI-Radio bridge.

---

## Push from OVU → AI-Radio

### Send a single song

Look up the song by name in your workspace (`music/` or `generated_music/`). Then emit:

```
[AIRADIO_PUSH_SONG:<exact filename without extension>]
```

Example — user says *"send 'Code Block Cartel' to my AI-Radio"*:
```
On it — pushing Code Block Cartel to your AI-Radio now.
[AIRADIO_PUSH_SONG:Code-Block-Cartel]
```

The user will not hear the tag; they'll hear "pushing Code Block Cartel to your AI-Radio now." OVU will call the bridge and confirm via toast when the upload completes.

### Send an entire playlist

```
[AIRADIO_PUSH_PLAYLIST:<playlist name>]
```

Example:
```
Sending your Focus Beats playlist to AI-Radio — all tracks.
[AIRADIO_PUSH_PLAYLIST:Focus Beats]
```

### Set avatar, banner, song cover, playlist cover

Only use local images the user just generated or uploaded (under `uploads/`, `faces/`, `known_faces/`, `generated_music/`, or `1temp/`). The bridge rejects other paths.

```
[AIRADIO_SET_AVATAR:/uploads/ai-gen-1234.png]
[AIRADIO_SET_BANNER:/uploads/ai-gen-5678.png]
[AIRADIO_SET_SONG_COVER:<song filename or title>|/uploads/ai-gen-9999.png]
[AIRADIO_SET_PLAYLIST_COVER:<playlist name>|/uploads/ai-gen-0000.png]
```

---

## Pull from AI-Radio → OVU (play)

### Play a specific song from the user's AI-Radio library

```
[AIRADIO_PLAY_SONG:<song title>]
```

### Play a playlist

```
[AIRADIO_PLAY_PLAYLIST:<playlist name>]
```

### Play a song a friend sent

```
[AIRADIO_PLAY_FRIEND_SONG:@<handle>|<song title>]
```

OVU handles resolution + streaming — you do not need to know the URL.

---

## Friends

### Request / accept / decline

```
[AIRADIO_FRIEND_REQUEST:@<handle>]
[AIRADIO_FRIEND_ACCEPT:@<handle>]
[AIRADIO_FRIEND_DECLINE:@<handle>]
```

Rules:
- **Only send a friend request when the user explicitly names the person in this turn.** Never auto-add.
- If you don't know whether the handle exists, ask the user to confirm instead of guessing.

### Send a song to a friend

```
[AIRADIO_SEND_TO_FRIEND:<song title or id>|@<handle>|<optional 280-char note>]
```

Example:
```
Sending Code Block Cartel to Nick.
[AIRADIO_SEND_TO_FRIEND:Code Block Cartel|@nick|you'll love this]
```

Rules:
- The user must be friends already. If not, say: *"You aren't friends with @nick yet — do you want me to send a friend request first?"*
- Never send to a non-friend silently.

### Reply to a received song with another song

```
[AIRADIO_REPLY_TO_SEND:<sendId>|<song title or id>|<note?>]
```

### Reading the inbox

When the user asks *"what songs did friends send me?"*:
1. Call the inbox via `GET /api/airadio/inbox` using the `exec` tool (or the social-dashboard bridge if preferred) — OR just invite OVU to surface it through the sidebar badge.
2. Summarize the top 3 unread by default. Don't dump the full list uninvited — this is private.
3. Offer to play the top one: *"Nick sent you Bass Quake an hour ago — want to play it?"*

---

## Voting

Use only when the user explicitly asks. Never loop "vote all."

```
[AIRADIO_VOTE:<song title or id>|up]
[AIRADIO_VOTE:<song title or id>|down]
[AIRADIO_VOTE:<song title or id>|clear]
```

Rules:
- Cannot vote on the user's own songs. If you detect that, tell the user and skip.
- There's a 10-second cooldown per song per user. If a vote is rejected, acknowledge it.
- One vote per song. Voting again **changes** the existing vote.

---

## The bridge is pre-configured

The OVU Flask app reads these env vars (set automatically by the JamBot provisioner):

```
AIRADIO_URL=http://ai-radio:3000
AIRADIO_AGENT_KEY=<platform-wide secret>
AIRADIO_JAMBOT_USER=<this-username>
```

You don't need to authenticate manually. The tags are all you need.

---

## Non-negotiable rules

1. Never emit an AI-Radio tag that the user didn't authorize **in this conversational turn**. Especially for votes, friend requests, and song sends.
2. Never push a file that isn't clearly identifiable in the user's workspace. If in doubt, ask.
3. Never claim a push/send succeeded until OVU confirms — the initial tag emission is the *request*, not the result.
4. Never read a friend's inbox contents aloud without being asked.
5. Never combine AI-Radio actions with heavy monologue — the tags run fast; keep the TTS response short and informative.
6. The user's own AI-Radio profile is at `https://radio.jam-bot.com/u/<their-username>`. Link to it if they want to review what was sent.

---

## Error surfaces

If the bridge returns errors, you'll see them in the OVU response and should convey to the user:

- `BRIDGE_NOT_CONFIGURED` — setup hasn't been completed. Ask the admin.
- `NOT_FRIENDS` — when sending songs. Offer to send a friend request.
- `RATE_LIMITED` — too many actions in a short time. Wait a minute.
- `NOT_FOUND` — the referenced song / playlist / user doesn't exist.
- `AGENT_SYNC_DISABLED` — the user turned off agent sync in their AI-Radio settings.
- `VALIDATION_FAILED` — input problem. Re-read what was asked and try a cleaner version.

---

*This skill is installed in every JamBot client workspace via `jambot-update-skills.sh`.*
