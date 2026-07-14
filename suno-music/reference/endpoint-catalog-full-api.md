---
name: suno-music-endpoint-catalog
description: Authoritative endpoint + model reference for the sunoapi.org wrapper. Verified against the live OpenAPI specs 2026-07-14. Superseded fields from the 2026-07-03 version are corrected here.
metadata: {"openclaw": {"emoji": "🎵"}}
---

# Suno API (sunoapi.org) — Full Endpoint Catalog

> **Verified 2026-07-14** against the live OpenAPI specs: `suno-api.json` (25 paths),
> `suno-voice-api.json`, `file-upload-api.json`. Field names, enums, and model strings are
> quoted verbatim. Machine index for re-extraction: `https://docs.sunoapi.org/llms.txt`.
> Rollback baseline of what OUR code did before this refresh: `../BASELINE-2026-07-14-pre-update.md`.

## Transport
- **Base URL:** `https://api.sunoapi.org` (all Suno + Suno Voice endpoints).
- **File Upload API is a DIFFERENT host:** `https://sunoapiorg.redpandaai.co`.
- **Auth (every endpoint):** `Authorization: Bearer <API_KEY>` (`bearerFormat: API Key`). Key: `https://sunoapi.org/api-key`.
- **NOT an official Suno product** — third-party reverse-engineered wrapper. (Legal/commercial-license posture: see SKILL.md "Website Subscription vs. API" section.)
- **Agents never call this host directly** — always the local `/api/suno` Flask wrapper. This file is for extending that wrapper.

## Async + callback model
1. `POST` returns sync `{"code":200,"msg":"success","data":{"taskId":"..."}}`.
2. Server later `POST`s the result to your `callBackUrl` (`application/json`, **15s timeout, must return HTTP 200**).
3. Or poll the matching `GET .../record-info?taskId=<id>`.

**Music-gen callback** (`data.callbackType` stages `text` → `first` → `complete`, or `error`):
`data.data[]` items carry `id`, `audio_url`, `source_audio_url`, `stream_audio_url`, `image_url`, `prompt`, `model_name` (legacy Chirp name e.g. `chirp-v3-5`), `title`, `tags`, `createTime`, `duration`.
**Callback status:** `200` ok · `400` bad/content-violation · `451` download failed · `500` server error.

**`record-info.data.status` enum:** `PENDING`, `TEXT_SUCCESS`, `FIRST_SUCCESS`, `SUCCESS`, `CREATE_TASK_FAILED`, `GENERATE_AUDIO_FAILED`, `CALLBACK_EXCEPTION`, `SENSITIVE_WORD_ERROR`. Poll for `SUCCESS`. Payload: `data.response.sunoData[]` → `id` (=audioId), `audioUrl`, `streamAudioUrl`, `imageUrl`, `prompt`, `modelName`, `title`, `tags`, `createTime`, `duration`. `data.operationType`: `generate|extend|upload_cover|upload_extend`.

**Global `ApiResponse.code`:** `200` ok · `400` invalid params · `401` unauthorized · `404` bad path · `405` rate-limit · `413` prompt too long · `429` **insufficient credits** · `430` call-frequency too high · `455` maintenance · `500` server error.

> ⚠️ **Read-back mismatch:** requests use `V4`/`V5`/`V5_5`; responses (`record-info.data.type`, callback `model_name`) use **legacy Chirp names** (`chirp-v3-5`, `chirp-v4`). Never parse the `V*` strings back out of a response.

> ⏳ **Retention:** generated files auto-delete after **15 days** — our wrapper already downloads to `generated_music/` on completion, so this only matters for un-downloaded taskIds.

## Models

| `model` string | Description (verbatim) | Notes |
|---|---|---|
| `V5_5` | "Unleash Your Voice: Custom Models Tailored to Your Unique Taste." | Latest; pairs with custom-voice/persona workflow. Renders **fuller/longer** (why jingles keep V5). |
| `V5` | "Superior musical expression, faster generation." | |
| `V4_5PLUS` | "richer sound, new ways to create, max 8 min." | **Default** for add-vocals/add-instrumental. |
| `V4_5ALL` | "better song structure, max 8 min." | |
| `V4_5` | "Superior genre blending… up to 8 minutes." | |
| `V4` | "Best audio quality with refined song structure, up to 4 minutes." | |

**Which models each endpoint accepts (verbatim enums):**
- generate / extend / upload-cover / upload-extend → `V4,V4_5,V4_5PLUS,V4_5ALL,V5,V5_5`
- mashup → `V4,V4_5,V4_5PLUS,V4_5ALL,V5` (**no V5_5**)
- add-vocals / add-instrumental → `V4_5PLUS`(default)`,V5,V5_5`
- sounds → docs enum = **`V5` only**, BUT our code **deliberately sends `V5_5`** (proven better quality in production, matches `routes/story.py` gen_suno_sound). Keep V5_5. ⚠️ Only IF sunoapi.org later enforces the enum and `sounds` starts returning 400 → fall back to `V5`.

**Custom-mode character limits:** `prompt` (=lyrics when `instrumental:false`): V4=3000, others=5000; non-custom prompt always ≤500. `style`: V4=200, others=1000. `title`: V4/V4_5ALL=80, others=100.

**Common optional controls** (generate/extend/upload-cover/upload-extend/mashup/add-vocals/add-instrumental): `negativeTags`, `vocalGender`(`m`/`f`), `styleWeight`(0–1), `weirdnessConstraint`(0–1), `audioWeight`(0–1), `personaId`, `personaModel`(`style_persona`(def)/`voice_persona`).

## Endpoint table

| Feature | Method + Path | Required | Key optional |
|---|---|---|---|
| Generate Music | `POST /api/v1/generate` | `customMode`,`instrumental`,`callBackUrl`,`model` | `prompt`,`style`,`title`,`personaId`,`personaModel`,controls |
| Generate Sounds (SFX) | `POST /api/v1/generate/sounds` | `prompt`(≤500),`model`(`V5`) | `soundLoop`,`soundTempo`(1–300),`soundKey`(`Any`…`B`),`grabLyrics`,`callBackUrl` |
| Extend Music | `POST /api/v1/generate/extend` | `defaultParamFlag`,`audioId`,`callBackUrl`,`model` | `prompt`,`style`,`title`,`continueAt`,persona,controls |
| Upload & Cover | `POST /api/v1/generate/upload-cover` | `uploadUrl`(≤8min),`customMode`,`instrumental`,`callBackUrl`,`model` | `prompt`,`style`,`title`,persona,controls |
| Upload & Extend | `POST /api/v1/generate/upload-extend` | `uploadUrl`,`defaultParamFlag`,`callBackUrl`,`model` | `instrumental`,`prompt`,`style`,`title`,`continueAt`,controls |
| Mashup (2 tracks) | `POST /api/v1/generate/mashup` | `uploadUrlList`(exactly 2),`customMode`,`callBackUrl`,`model` | `prompt`,`style`,`title`,`instrumental`,controls |
| Suno Cover (from taskId) | `POST /api/v1/suno/cover/generate` | `taskId`,`callBackUrl` | — |
| Add Vocals | `POST /api/v1/generate/add-vocals` | `uploadUrl`,`prompt`,`title`,`negativeTags`,`style`,`callBackUrl` | `vocalGender`,weights,`model`(def `V4_5PLUS`) |
| Add Instrumental | `POST /api/v1/generate/add-instrumental` | `uploadUrl`,`title`,`negativeTags`,`tags`,`callBackUrl` | `vocalGender`,weights,`model`(def `V4_5PLUS`) |
| Replace Section (inpaint) | `POST /api/v1/generate/replace-section` | `prompt`,`tags`,`title`,`infillStartS`,`infillEndS`,`fullLyrics` | `negativeTags`,`callBackUrl` |
| Generate Persona (style) | `POST /api/v1/generate/generate-persona` | `taskId`,`audioId`,`name`,`description` | `vocalStart`(0.0),`vocalEnd`(30.0; 10–30s seg),`style` |
| Boost Music Style | `POST /api/v1/style/generate` | `content` | — |
| Generate Lyrics | `POST /api/v1/lyrics` | `prompt`,`callBackUrl` | — |
| Timestamped Lyrics | `POST /api/v1/generate/get-timestamped-lyrics` | `taskId`,`audioId` | — |
| Separate Vocals / Stems | `POST /api/v1/vocal-removal/generate` | `taskId`,`audioId`,`stemName`,`callBackUrl` | `type` (see below) |
| MIDI from Audio | `POST /api/v1/midi/generate` | `taskId`(from a vocal-sep task),`callBackUrl` | `audioId`(a separated-track id) |
| Convert to WAV | `POST /api/v1/wav/generate` | `taskId`,`audioId`,`callBackUrl` | — |
| Create Music Video | `POST /api/v1/mp4/generate` | `taskId`,`audioId`,`callBackUrl` | `author`(≤50),`domainName`(≤50, watermark) |
| Get Music Gen Details | `GET /api/v1/generate/record-info?taskId=` | `taskId` | — |
| Get Lyrics Details | `GET /api/v1/lyrics/record-info?taskId=` | `taskId` | — |
| Get Vocal-Sep Details | `GET /api/v1/vocal-removal/record-info?taskId=` | `taskId` | — |
| Get MIDI Details | `GET /api/v1/midi/record-info?taskId=` | `taskId` | — |
| Get WAV Details | `GET /api/v1/wav/record-info?taskId=` | `taskId` | — |
| Get Video Details | `GET /api/v1/mp4/record-info?taskId=` | `taskId` | — |
| Get Cover Details | `GET /api/v1/suno/cover/record-info?taskId=` | `taskId` | — |
| Remaining Credits | `GET /api/v1/generate/credit` | — | integer balance |

> ⚠️ **Two catalog entries in the OLD (2026-07-03) version were WRONG — corrected above:**
> - Timestamped lyrics is `POST /api/v1/generate/get-timestamped-lyrics {taskId,audioId}` (old file said `GET /get_lyrics_timeline?song_id=`).
> - Vocal separation is `POST /api/v1/vocal-removal/generate` + `GET /api/v1/vocal-removal/record-info` (old file said `/separate_vocals` and `/api/v1/separate/record-info`).
> Our `routes/suno.py` already uses the CORRECT paths — the drift was only in this reference doc.

## Custom voices — the Suno Voice API (voice cloning)
Same host `https://api.sunoapi.org`, same BearerAuth. Full flow to mint a `voiceId`:
1. `POST /api/v1/voice/validate` — `{voiceUrl*, vocalStartS*, vocalEndS*(>start), language?(en/zh/es/fr/pt/de/ja/ko/hi/ru), callBackUrl?}` → `taskId` + a validation phrase.
2. `GET /api/v1/voice/validate-info?taskId=` → `data.validateInfo` (phrase) + `data.status` (`wait_processing`,`processing_validate`,`processing_validate_fail`,`wait_validating`,`success`,`fail`).
3. *(opt)* `POST /api/v1/voice/regenerate` — `{taskId*, calBackUrl*}` ⚠️ **field is `calBackUrl` (one L) here only**.
4. User records the phrase (**singing recommended**), hosts it (File Upload API) → a URL.
5. `POST /api/v1/voice/generate` — `{taskId*(from step 1), verifyUrl*(recording), voiceName?, description?, style?, singerSkillLevel?(beginner|intermediate|advanced|professional, def beginner), callBackUrl?}` → `taskId`.
6. `GET /api/v1/voice/record-info?taskId=` → `data.voiceId` + status. (Or via callback: `data.voiceId`.)
7. `POST /api/v1/voice/check-voice` — `{task_id}` ⚠️ **snake_case here** → `data.isAvailable`.

**USE the cloned voice in generation:** set `personaId = <voiceId>` **and** `personaModel = "voice_persona"` (custom mode only) on generate/extend/upload-cover/upload-extend. (A `generate-persona` STYLE persona instead uses `personaModel:"style_persona"` — the default.)

## Stem separation `type` (on `vocal-removal/generate`)
- `separate_vocal` (default) → 2 tracks: `vocal_url` + `instrumental_url` (+`origin_url`).
- `split_stem` → many at once: `vocal_url,backing_vocals_url,bass_url,brass_url,drums_url,fx_url,guitar_url,keyboard_url,percussion_url,strings_url,synth_url,woodwinds_url,origin_url`.
- `split_stem_advanced` → isolate ONE instrument via `stemName` (~100-value enum: `Lead Vocal`,`Backing Vocals`,`Drum Kit`,`Kick`,`Snare`,`Bass`,`Piano`,`Electric Guitar`,`Acoustic Guitar`,`Synth`,`Strings`,`Brass Section`,`Organ`,`Saxophone`,`Trumpet`,`Violin`,`Cello`,`Flute`,`Harp`,`808`,`Hi-Hat`,`Sitar`,`Banjo`,…). Output: `origin_data[]` each `{extract:{audio_url,...}, remove:{...}}` (isolated vs. removed).
- **Input is a Suno-generated `taskId`+`audioId`**, not an arbitrary file. `stemName` is required by the schema even for `separate_vocal`/`split_stem` (only meaningful for `_advanced`).

## Replace words / lyrics (`replace-section`)
Time-window **inpainting**, NOT per-word find/replace. `{prompt(new section lyrics), tags(style), title, infillStartS, infillEndS, fullLyrics(complete post-edit lyrics)}`. Window in seconds (2 decimals), `infillStartS<infillEndS`, and **`infillEndS−infillStartS` must be 6–60s**. No per-word primitive exists.

## File Upload API — host `https://sunoapiorg.redpandaai.co`
Produces the hosted `uploadUrl`/`voiceUrl`/`verifyUrl` other endpoints need.
- `POST /api/file-base64-upload` (json) — `{base64Data*, uploadPath*, fileName?}`
- `POST /api/file-stream-upload` (multipart) — `file*(binary), uploadPath*, fileName?`
- `POST /api/file-url-upload` (json) — `{fileUrl*, uploadPath*, fileName?}`
(`uploadPath` = path with no leading/trailing slashes.)

## New vs. our pre-2026-07-14 integration
**Not yet wired into `/api/suno`:** Suno Voice API (custom voices), `personaId`/`personaModel` passthrough, `generate-persona`, `split_stem`/`split_stem_advanced` types, MIDI, mashup, `suno/cover` (distinct from `upload-cover`), File Upload API.
**Already wired (correct paths):** generate, sounds, extend, cover(upload-cover), add-vocals, add-instrumental, replace-section, lyrics, timestamped-lyrics, wav, vocal-removal(2-way), style-boost, mp4 video, record-info, credits.
