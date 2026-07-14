# Suno Integration — KNOWN-GOOD BASELINE (frozen 2026-07-14, pre-v5.5/custom-voice update)

> **Why this file exists:** Mike asked to record EXACTLY how Suno works today before we
> update the skill/code to newer models + features (v5.5, custom voices, vocal/instrumental
> split, word replacement). If the new stuff underperforms, revert to these exact values.
> This is a factual snapshot of `routes/suno.py` @ commit `main` on 2026-07-14 and the live
> `SKILL.md` of the same date. **Do not edit — it is the rollback reference.**

## Transport (unchanged truth)
- **Wrapper base:** `https://api.sunoapi.org` (third-party `sunoapi.org` — NOT official Suno). Const `SUNO_API_BASE`.
- **Auth header:** `Authorization: Bearer <SUNO_API_KEY>` + `Content-Type: application/json` (`_suno_headers()`).
- **Agents NEVER call sunoapi.org directly** — they call the local `/api/suno` Flask wrapper (`openvoiceui:5001/api/suno`), which forwards, downloads the audio, saves to `generated_music/`, writes metadata. Agent key: `X-Agent-Key: $AGENT_API_KEY`.
- **Async model:** most generation is async + `callBackUrl` webhook → `/api/suno/callback`; poll via `?action=status&job_id=<id>`.

## Action → endpoint → DEFAULT MODEL (exact, as shipped 2026-07-14)

| local `action` | sunoapi.org endpoint | **default model** | notes |
|---|---|---|---|
| `generate` (full song) | `POST /api/v1/generate` | **`V5_5`** | `_action_generate`, lines ~436/448 |
| `jingle` (10-15s logo) | `POST /api/v1/generate` | **`V5`** | `_action_jingle` ~676/686 — DELIBERATELY V5, not V5_5 (V5.5 renders longer; V5 hits short-form tighter with the truncated `, [Intro` trick). Recipe v5, CONFIRMED 2026-05-05. |
| `sfx` (non-vocal SFX) | `POST /api/v1/generate/sounds` | **`V5_5`** | `_action_sfx` ~532; 2.5 credits |
| `extend` | `POST /api/v1/generate/extend` | `V5` (param-overridable) | ~1146 |
| `cover` | `POST /api/v1/generate/upload-cover` | `V5` (override) | ~1186 |
| `add_vocals` | `POST /api/v1/generate/add-vocals` | `V5` (override) | ~1225 |
| `add_instrumental` | `POST /api/v1/generate/add-instrumental` | `V5` (override) | ~1256 |
| `replace_section` | `POST /api/v1/generate/replace-section` | `V5` (override) | ~1275 |
| `generate_lyrics` | `POST /api/v1/lyrics` | n/a | ~1315 |
| `timestamped_lyrics` | `POST /api/v1/generate/get-timestamped-lyrics` | n/a | ~1357 |
| `wav_convert` | `POST /api/v1/wav/generate` | n/a | ~1389 |
| `stem_separate` | `POST /api/v1/vocal-removal/generate` | n/a | ~1408 — **2-way only** (vocals + instrumental). NOT the 12-track `split_stem`. |
| `style_boost` | `POST /api/v1/style/generate` | n/a | ~1432 |
| `music_video` | `POST /api/v1/mp4/generate` | n/a | ~1471 |
| `song_details`/`status` | `GET /api/v1/generate/record-info` | n/a | polling |
| `credits` | `GET /api/v1/account/credits` | n/a | |

## Voice-agent-facing defaults (the thing Mike wants to be able to revert)
- **Full songs → `V5_5`**
- **Jingles / audio logos → `V5`** (intentional short-form choice)
- **All edit/process endpoints (extend/cover/add-vocals/add-instrumental/replace-section) → `V5`**, each overridable by passing `model` in the request.

## What is NOT wired today (capability gaps at baseline)
- **Custom voices / personas** — no handler. `sunoapi.org` "Generate Persona" (0 credits) exists but is unused.
- **12-track `split_stem`** — only the 2-way `vocal-removal` is wired. The richer stem split (drums/bass/vocals/etc., ~50 credits) is not exposed.
- **Word/lyric replacement in an existing track** — `replace_section` exists (section-level) but no word-level replacement is documented/wired at baseline.

## Doc/code drift noted at snapshot time
- The live `SKILL.md` endpoint catalog still labels extend/cover/add-vocals/add-instrumental/replace-section as **"not yet wrapped"** — that is STALE; all are wired in `handle_suno()` as of the 2026-06-25 edit-endpoints addition. The update will correct the skill to match the code.

_Snapshot author: host@mesh, 2026-07-14. Companion to the update that follows._
