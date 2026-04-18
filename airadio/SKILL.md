---
name: airadio
description: Push songs, playlists, and images to the user's AI-Radio account; pull songs back to play; manage friends; send songs one-to-one; vote on community tracks. Integration with ai-radio.jam-bot.com.
metadata: {"openclaw": {"emoji": "📻"}}
---

# AI-Radio Integration

AI-Radio (ai-radio.jam-bot.com) is the user's **persistent, social, multi-user music layer**. You can push music from this OpenVoiceUI workspace into their AI-Radio account and pull music back to play. You can also manage their friends, send songs, and cast votes.

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

The tag accepts either the exact filename (without extension) OR the song's title — the bridge fuzzy-matches against both library and generated playlists.

```
[AIRADIO_PUSH_SONG:<title or filename>]
```

Example — user says *"send 'Code Block Cartel' to my AI-Radio"*:
```
On it — pushing Code Block Cartel to your AI-Radio now.
[AIRADIO_PUSH_SONG:Code-Block-Cartel]
```

The user will not hear the tag; they'll hear the spoken sentence only. OVU calls the bridge and AI-Radio dedupes by (user, sunoId) / (user, sourceHash), so re-pushing the same song is a safe no-op.

### "This song" / "send this" — ALWAYS read the current context

Every user turn includes a context line like `[Music PLAYING: <title>]` or `[Available tracks — Generated (N): <list>]` in the message. When the user says *"this song"*, *"send this"*, *"that one"*, or *"the one playing"*, you MUST use the title from the current `[Music PLAYING: <title>]` marker — NOT a song from an earlier turn.

Example — context shows `[Music PLAYING: AI On The Line]` and user says *"push this to airadio"*:
```
Pushing AI On The Line to your AI-Radio now.
[AIRADIO_PUSH_SONG:AI On The Line]
```

If no track is currently playing, ASK the user which track they mean — do NOT guess based on conversation history.

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

## Catalog & cross-user playback

AI-Radio is platform-wide. Every public song on any user's account is reachable from this workspace — not just the current user's own library. Use these tags for anything that crosses user boundaries.

### Search the full public catalog

```
[AIRADIO_CATALOG_SEARCH:<query>]
```

Example — user says *"what Nick songs are on AI-Radio?"*:
```
Searching AI-Radio for Nick's tracks.
[AIRADIO_CATALOG_SEARCH:nick]
```

OVU renders the results inline (cover, title, artist, play button). Offer to play the top match if there's a clear winner.

### Play any song from the catalog by title or id

```
[AIRADIO_PLAY_FROM_CATALOG:<song title or id>]
```

Unlike `[AIRADIO_PLAY_SONG:...]` (which plays from the user's own library), this one resolves against every public song on AI-Radio. OVU fetches a signed 15-minute stream URL and starts playback.

Rules:
- Only emit when the user explicitly asked for a specific track
- If the query is ambiguous, surface the top 3 candidates first and let the user pick

### Save a song to the user's library

```
[AIRADIO_SAVE_TO_LIBRARY:<song id or title>]
```

Creates a saved reference (like/bookmark) so the song appears in the user's AI-Radio library. Doesn't copy the audio — playback always streams from the original owner.

Rules:
- Only save when the user explicitly asks
- Never bulk-save from a search result
- You can't save a song the user already owns — acknowledge and skip

### Create a playlist

```
[AIRADIO_PLAYLIST_CREATE:<name>|<optional description>]
```

Creates a playlist owned by the user. If a playlist with that name already exists, the existing one is returned — no duplicates. After creating, you typically want to add songs via the existing `[AIRADIO_PUSH_PLAYLIST:...]` or playlist add tags.

### Read a playlist's contents

```
[AIRADIO_PLAYLIST_READ:<playlist id or name>]
```

Fetches ordered songs with signed stream URLs. Use before announcing *"your Focus Beats has 12 tracks, want me to play it?"* so the list is accurate.

### Stream URLs are temporary

Every stream URL the agent receives from OVU is valid for only 15 minutes. Treat them as ephemeral:
- Do **not** cache them
- Do **not** hand them to the user in chat or to another session
- If a URL is stale, just re-issue — no extra charge, no friction

---

## Queue / Radio (voice-shaped)

For "play X" style commands, use the queue endpoints that return a ready-to-play
list (20 items by default, each with a signed `streamUrl`). OVU auto-queues the
items into the music player. Every response has a `reason` string — speak it
verbatim so the user knows exactly what was queued.

Voice tags:
```
[AIRADIO_QUEUE_NEW]                              play something new
[AIRADIO_QUEUE_TRENDING]                         play what's trending
[AIRADIO_QUEUE_TOP]                              play the all-time top
[AIRADIO_QUEUE_TOP:day|week|all]                 scoped top (24h / 7 days / all time)
[AIRADIO_QUEUE_RANDOM]                           random public songs
[AIRADIO_QUEUE_FRIENDS]                          songs your friends made
[AIRADIO_QUEUE_FOLLOWING]                        from people you follow
[AIRADIO_QUEUE_ME]                               your own songs
[AIRADIO_QUEUE_LIKED]                            your liked songs
[AIRADIO_QUEUE_UNHEARD]                          haven't heard yet
[AIRADIO_QUEUE_GENRE:<slug>]                     play hip-hop, lofi, etc.
[AIRADIO_QUEUE_MOOD:<mood>]                      chill, upbeat, focused, sad, etc.
[AIRADIO_QUEUE_ARTIST:@<username>]               one user's public songs
[AIRADIO_QUEUE_SIMILAR:<songId>]                 more like this
[AIRADIO_QUEUE:<free-form>]                      natural-language fallback
```

Valid moods: `relaxed`, `calm`, `chill`, `focused`, `study`, `upbeat`,
`energetic`, `workout`, `aggressive`, `sad`. Each expands to a genre list.

Each response shape:
```json
{
  "items": [{ "id": "...", "title": "...", "streamUrl": "/api/song/.../stream?t=...", ... }],
  "reason": "12 chill songs from your friends in lofi + ambient",
  "nextCursor": null
}
```

**Rules:**
- Only emit on a direct user request **in this turn**. Never auto-queue; never
  queue anything the user didn't ask for.
- Speak the `reason` string verbatim. Do not paraphrase the count or the source.
- Stream URLs expire in 15 minutes. If the user pauses and resumes after that
  window, re-fetch.
- Never mix queue tags with heavy monologue — short spoken response, tag, done.
- `[AIRADIO_QUEUE_ARTIST:@handle]` — accept both `@nick` and `nick`. If no user
  exists the bridge returns NOT_FOUND; pass that back to the user politely.
- `[AIRADIO_QUEUE:<free-form>]` maps anything the hard shortcuts don't cover.
  Use it when the user's phrasing mixes mood + audience + freshness (e.g.
  "play something chill my friends made that I haven't heard").

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

## Per-user API keys (new)

Users can now generate their OWN AI-Radio API key from
`https://ai-radio.jam-bot.com/settings` (section "AI-Radio API key").
Keys look like `aia_sk_<48 chars>` and authenticate as that specific
user — no JamBot subdomain wiring required.

They paste it into this workspace via the bridge tag:

```
[AIRADIO_SET_USER_KEY:aia_sk_...]
```

When emitted, OVU writes the key to the workspace `.env` (as
`AIRADIO_USER_KEY=...`) and from then on every agent call
authenticates as that user via `Authorization: Bearer <key>` — no more
platform-shared key for this workspace. One user per workspace.

If the user asks "how do I connect my AI-Radio account", walk them through:

  1. Visit https://ai-radio.jam-bot.com/settings
  2. Scroll to "AI-Radio API key" and click "Generate API Key"
  3. Copy the `aia_sk_...` value (it is shown exactly once)
  4. Paste it back here — I'll wire it into this workspace

Rules:

- Never log the key back to the user after setting it. Never read it aloud.
- The platform-shared key still works — existing deployments are unaffected.
- If the user revokes or rotates the key in settings, this workspace
  loses access until they paste the new value.

---

## Non-negotiable rules

1. Never emit an AI-Radio tag that the user didn't authorize **in this conversational turn**. Especially for votes, friend requests, and song sends.
2. Never push a file that isn't clearly identifiable in the user's workspace. If in doubt, ask.
3. Never claim a push/send succeeded until OVU confirms — the initial tag emission is the *request*, not the result.
4. Never read a friend's inbox contents aloud without being asked.
5. Never combine AI-Radio actions with heavy monologue — the tags run fast; keep the TTS response short and informative.
6. The user's own AI-Radio profile is at `https://ai-radio.jam-bot.com/u/<their-username>`. Link to it if they want to review what was sent.

---

## Error surfaces

If the bridge returns errors, you'll see them in the OVU response and should convey to the user:

- `BRIDGE_NOT_CONFIGURED` — setup hasn't been completed. Ask the admin.
- `NOT_FRIENDS` — when sending songs. Offer to send a friend request.
- `RATE_LIMITED` — too many actions in a short time. Wait a minute.
- `NOT_FOUND` — the referenced song / playlist / user doesn't exist.
- `AGENT_SYNC_DISABLED` — the user turned off agent sync in their AI-Radio settings.
- `VALIDATION_FAILED` — input problem. Re-read what was asked and try a cleaner version.
- `AUTH_API_KEY_INVALID` — per-user API key was revoked or rotated. Ask the user to paste a fresh one from `/settings`.

---

*This skill is installed in every JamBot client workspace via `jambot-update-skills.sh`.*
