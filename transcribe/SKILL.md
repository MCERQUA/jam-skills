---
name: transcribe
description: "Transcribe speech to text from any audio OR video file (mp4, mov, mp3, wav, m4a, webm) using the on-box Parakeet STT service. Use when the user asks what someone says in a clip, wants a transcript, captions, subtitles, or needs to read the words out of a video before posting or replying to it. Runs locally — no API key, no per-minute cost, nothing leaves the box."
metadata: {"openclaw": {"emoji": "📝", "requires": {"env": []}}}
---

# Transcribe (Parakeet STT)

Turns the words in an audio or video file into text. Runs in the `jambot-parakeet`
container on the shared network. **No API key. No usage cost. Nothing is sent to a third
party.**

> Do NOT use OpenAI Whisper / `OPENAI_API_KEY` for transcription on this box. That path is
> dead (the key 401s) and it costs money per minute. This service replaced it.

## When to use it

- "What does he say in this video?"
- "Transcribe this" / "get me the transcript" / "what's in this clip"
- Before posting, quoting, replying to, or captioning any media you have not heard
- Pulling a quote out of a call recording or voice note
- Generating captions/subtitles copy

## How to run it

One command. The field is `audio`, and it accepts **video files too** — no need to extract
the audio track first.

```bash
curl -s -X POST http://jambot-parakeet:8770/transcribe \
  -F "audio=@/path/to/file.mp4" \
  --max-time 600
```

Returns JSON:

```json
{"text": "the full transcript ..."}
```

### Save it next to the media (do this — the transcript is a durable artifact)

```bash
cd /home/node/.openclaw/workspace/uploads
f=YOURFILE.mp4
curl -s -X POST http://jambot-parakeet:8770/transcribe -F "audio=@$f" --max-time 600 \
  > "${f%.*}.transcript.json"
python3 -c "import json;print(json.load(open('${f%.*}.transcript.json'))['text'])" \
  > "${f%.*}.transcript.txt"
cat "${f%.*}.transcript.txt"
```

Writing the `.txt` beside the media means the next agent (or the next you, after a
compaction) can read it without paying for the work again.

### Check the service is up

```bash
curl -s http://jambot-parakeet:8770/health
# {"ok":true,"model":"istupakov/...","loaded":false,"idle_unload_s":900,"idle_s":1873}
```

**`"loaded": false` is NORMAL and does NOT mean the service is broken.** The model
is released from memory after 15 minutes with no traffic and reloaded on the next
request — it holds ~2 GB resident, which is too much to keep parked for a service
used a few times a day. `"ok": true` is the liveness signal; read that, not `loaded`.

The cost is real and worth planning around: a request after an idle period spends
**~18-35 seconds loading the model before it starts transcribing** (measured, not
estimated). So give the FIRST call after a quiet spell a generous `--max-time` — 300+.
If you are about to transcribe several files, the first one warms it and the rest run
at full speed. Do not mistake that first slow call for a hang.

## Notes and limits

- **Reachability:** the service listens on the `jambot-shared` docker network. Every tenant
  openclaw container is attached to it, so `jambot-parakeet:8770` resolves. It is NOT
  published on a host port — use the container hostname, not `localhost`.
- **Big files:** a ~6 MB / ~1 min video returns in a few seconds. Give long recordings a
  generous `--max-time`; a 60-minute file can take a couple of minutes.
- **English model.** Output is plain text with punctuation and sentence casing.
- **No speaker labels and no timestamps** in the response — it returns one `text` blob. If
  you need per-speaker or timed captions, say so rather than inventing them.
- **Never guess at content you have not transcribed.** If the service is down, say it is
  down. A fabricated quote from a client's video is far worse than "I couldn't read it."

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Could not resolve host: jambot-parakeet` | container not on `jambot-shared` | tell host@mesh — needs `docker network connect jambot-shared <your-container>` |
| connection refused | service down | `curl .../health`; if it fails, tell host@mesh |
| first call slow (~18-35s) | model reloading after idle | expected — see the health note above, not a fault. Use `--max-time 300`. |
| 422 | wrong field name | the form field must be exactly `audio` |
| empty `text` | file has no speech / no audio track | confirm the file actually has audio |
