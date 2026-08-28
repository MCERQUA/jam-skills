---
name: hugging-face
description: Hugging Face Inference API — generate images, video, text, embeddings, classify, summarize, translate, and more using 400K+ open-source models via the HF Router API.
metadata: {"openclaw": {"requires": {"env": ["HF_TOKEN"], "anyBins": ["curl"]}}}
---

# Hugging Face Skill

Access the Hugging Face Inference Providers API to run open-source AI models on demand.

> ## 🎨 THIS IS THE IMAGE-GENERATION PATH FOR VOICE/OPENCLAW AGENTS
> The built-in `image_generate` tool is **DISABLED** (it was hardwired to fal.ai, whose
> account is dead/empty — it would 403 and wedge the whole session). **To generate an
> image, use this skill's Text-to-Image recipe below** — FLUX.1-schnell via the **`nscale`**
> provider (verified 2026-08-26). The old `hf-inference` FLUX endpoint is **DEAD (HTTP 410)**
> and its response shape was different (binary, not JSON) — read §1 before porting any script. For **image→video**, use the **`wan-video`** skill.
> **Always save the result to the tenant's uploads so it becomes a real server URL** (see §1).

## Authentication

The `HF_TOKEN` environment variable is set automatically. Use it in all requests:

```
Authorization: Bearer $HF_TOKEN
```

## Base URL

All requests go through the HF Router with a **provider prefix**:

```
https://router.huggingface.co/<provider>/models/<model>
```

Default provider for the legacy free serverless tier: `hf-inference` — **but see the
image-generation warning below; it no longer serves FLUX.**

**Image generation uses a different, OpenAI-compatible base URL** (note `/v1/images/generations`,
NOT `/models/<model>`):

```
https://router.huggingface.co/nscale/v1/images/generations
```

## Provider Selection

Append a provider name to use a specific backend:

- `nscale` — **the image-generation provider. VERIFIED WORKING 2026-08-26** (FLUX.1-schnell,
  HTTP 200, OpenAI-images-compatible JSON response). This is where the fallback chain ends.
- `hf-inference` — legacy free serverless tier. **DEAD FOR FLUX IMAGE GENERATION** — as of
  2026-08-26 `hf-inference/models/black-forest-labs/FLUX.1-schnell` returns **HTTP 410**:
  *"The requested model is deprecated and no longer supported by provider hf-inference"*.
  The non-image task recipes below (§2–§13) still point at `hf-inference`; they were **NOT
  re-verified** in the 2026-08-26 sweep — treat each as unproven until you see a 200 with a
  sane body, and check the status code before using the output.
- ~~`fal-ai`~~ — **DO NOT USE — our fal account is empty/dead (403 "Exhausted balance").**
  (This line used to say "use `hf-inference` instead" — that redirect was itself dead. For
  images, go to `nscale`.)
- ~~`together` for images~~ — `https://router.huggingface.co/together/v1/images/generations`
  returns **HTTP 400 "Unable to access non-serverless model"**. Not an image path for us.
  `together` for LLM chat is untested here.
- `replicate` — general purpose
- `fireworks-ai`, `sambanova`, `cerebras`, `hyperbolic`, `novita`, `nebius`, `wavespeed`

Not all providers host all models, and **provider×model availability changes without notice —
that is exactly how the FLUX path died.** We have verified ONE model on ONE provider
(`black-forest-labs/FLUX.1-schnell` on `nscale`). We do **not** know which other models nscale
hosts; do not assert it hosts one you have not seen return 200. This list is not exhaustive and
is not a capability claim.

### Fallback chain for images (2026-08-26) — it terminates, on purpose

1. `nscale` `/v1/images/generations` — **use this.**
2. If it fails: **STOP and report the HTTP code and response body.** There is no third
   documented image provider that has been verified. Do NOT silently fall through to
   `hf-inference` or `fal-ai` — both return well-formed HTTP errors that will be written to
   disk as a fake "image" if you are not checking the status code.

## Tasks & Examples

### 1. Text to Image (MOST COMMON) — the voice-agent image recipe

Generate images from text prompts via `nscale`. **Save it to the tenant's uploads** so you get
a real server URL to show the user — never leave a generated image only in a temp path (paid
output must persist to the server immediately).

> ## ⚠️ THE RESPONSE IS **JSON**, NOT BINARY — READ THIS BEFORE PORTING ANY OLD SCRIPT
> The old `hf-inference/models/...` path returned a **binary body** you could write straight to
> disk with `curl -o hero.png`. **`nscale` is OpenAI-images-compatible and returns JSON**:
> top-level keys `created` and `data`, with the image at **`data[0].b64_json` (base64)**.
> A script ported by swapping ONLY the URL will write a JSON blob into `hero.png`, exit 0, and
> every downstream "does the file exist" check will pass. **You must decode the base64.**
>
> ## ⚠️ DEAD HF PATHS RETURN WELL-FORMED HTTP ERRORS, NOT TIMEOUTS
> A generator that does not check the status code writes the **error text** to disk as an
> "image". Measured cost of exactly this: 6 files on a live tenant subdomain served **94 bytes
> of deprecation JSON as `.jpg` at HTTP 200** for **18 days**. Nothing alerted, because the
> files existed. **Check the status code, decode, then verify the magic bytes — and on failure
> write NOTHING to the output path** so the absence of the file is the failure signal.

**Preferred: use the ready-made gated script** (it does all of the above; exits non-zero and
leaves the output path absent on any failure):

```bash
/skills/huggingface/scripts/hf-image-gen.sh \
  "A cyberpunk cityscape at sunset, neon lights on wet streets" \
  "/mnt/clients/$TENANT/openvoiceui/uploads/ai-gen-$(date +%s).png" \
  1024x1024
# exit 0 = a real image ≥10KB with valid PNG/JPEG/WEBP magic bytes is at that path.
# exit 1 = non-200 · 2 = 200 but no b64_json · 3 = decoded bytes are not an image / too small.
```

**Inline equivalent**, if you cannot reach the script:

```bash
TENANT=src                                   # your tenant slug
TS=$(date +%s)
OUT="/mnt/clients/$TENANT/openvoiceui/uploads/ai-gen-$TS.png"
RESP="/tmp/hf-image-$TS.json"
TMPIMG="/tmp/hf-image-$TS.bin"

# 1. CALL — capture the status code, never assume 200.
CODE=$(curl -sS -o "$RESP" -w '%{http_code}' --max-time 180 \
  https://router.huggingface.co/nscale/v1/images/generations \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"black-forest-labs/FLUX.1-schnell","prompt":"A cyberpunk cityscape at sunset, neon lights on wet streets","n":1,"size":"1024x1024"}')

# 2. GATE ON STATUS — an actual conditional, not a comment for a human to read.
[ "$CODE" = "200" ] || { echo "HF image FAILED http=$CODE"; head -c 400 "$RESP"; exit 1; }

# 3. DECODE the base64 — the body is JSON, the image is at .data[0].b64_json
jq -er '.data[0].b64_json' "$RESP" >/dev/null || { echo "no b64_json in 200 body"; head -c 400 "$RESP"; exit 2; }
jq -r  '.data[0].b64_json' "$RESP" | base64 -d > "$TMPIMG"

# 4. GATE ON MAGIC BYTES + SIZE — a JSON error decodes to a tiny non-image blob.
BYTES=$(stat -c %s "$TMPIMG")
MAGIC=$(head -c 8 "$TMPIMG" | od -An -tx1 | tr -d ' \n')
case "$MAGIC" in 89504e470d0a1a0a*|ffd8ff*|52494646*) ;; *) echo "not an image (magic=$MAGIC)"; exit 3 ;; esac
[ "$BYTES" -ge 10240 ] || { echo "decode only $BYTES bytes — treating as FAILURE, wrote nothing"; exit 3; }

# 5. Only now does it land at the real path. Failure leaves the path ABSENT.
mv "$TMPIMG" "$OUT"
echo "https://$TENANT.jam-bot.com/uploads/ai-gen-$TS.png"    # show the user the SERVER URL
```

A 1024x1024 FLUX.1-schnell PNG from this path measured **~1.7 MB**. Anything under 10 KB is an
error body wearing a `.png`, not a picture.

> **Inside an openclaw voice container** your CWD maps to the tenant workspace and the uploads
> folder is reachable as `/app/runtime/uploads/` or via the tenant path above. If unsure of
> the exact mount, write to `uploads/ai-gen-<ts>.png` under the tenant's openvoiceui dir — the
> file MUST land somewhere served at `/uploads/...`. Confirm the URL loads before telling the user it's ready.

**Model:** `black-forest-labs/FLUX.1-schnell` on `nscale` — **the only model+provider pair
verified working (2026-08-26).** `FLUX.1-dev` and `stable-diffusion-xl-base-1.0` were NOT
tested on nscale; we do not know whether nscale hosts them. If you try one, gate it with the
same status+magic-byte checks and record the result here.

**If HF returns HTTP 503 "model loading":** wait ~15s and retry once (cold start).
**If it returns 410:** the model was deprecated by that provider — do NOT retry, and do NOT
fall back to `hf-inference` or `fal-ai`; both are dead. Report it.

---

> ## ✅ §2–§13 MEASURED — 2026-08-27 (supersedes the 2026-08-26 UNVERIFIED banner)
> All 12 recipes below were actually POSTed with the payloads exactly as written here, by
> **two independent desks** (bun-desktop 14:52Z, host 14:5xZ) against `hf-inference`. Results:
>
> | recipe | verdict |
> |---|---|
> | §4 sentiment `distilbert/distilbert-base-uncased-finetuned-sst-2-english` | **ALIVE** 200 |
> | §5 zero-shot `facebook/bart-large-mnli` | **ALIVE** 200 |
> | §6 summarize `facebook/bart-large-cnn` | **ALIVE** 200 |
> | §7 translate `Helsinki-NLP/opus-mt-en-fr` | **ALIVE** 200 |
> | §8 Q&A `deepset/roberta-base-squad2` | **ALIVE** 200 |
> | §9 NER `dslim/bert-base-NER` | **ALIVE** 200 |
> | §2 text→video `Wan-AI/Wan2.1-T2V-14B` | 🔴 **DEAD** 400 "Model not supported by provider hf-inference" |
> | §3 image→image `timbrooks/instruct-pix2pix` | 🔴 **DEAD** 400, same class |
> | §10 similarity `sentence-transformers/all-MiniLM-L6-v2` | ⚠️ **SERVED, BUT THE DOCUMENTED PAYLOAD WAS WRONG** — fixed below |
> | §11–§13 `vit-base-patch16-224`, `detr-resnet-50`, `whisper-large-v3` | **UNDECIDED** — our probes fed a literal `"x"` where a real image/audio is required, so the 400 is our input's fault, not a verdict. The provider accepted the model and reached input validation, so each is SERVED; the recipe itself is untested. |
>
> **Do not read UNDECIDED as either alive or dead.** 3 of 12 is too large a share to launder
> into whichever column is convenient.
>
> **The §10 case is the one to learn from.** The model is served and the provider is healthy —
> only the documented request body was wrong. The old banner's frame ("unproven because the
> provider may be dead") *cannot express that failure*: a reader who checks the provider is
> alive concludes the recipe is good and still gets a 400. Verified in BOTH directions
> (documented body → 400, corrected body → 200), which is what makes it a doc defect rather
> than a dead endpoint.
>
> Still capture `-w '%{http_code}'` and refuse anything that is not 200. A 400 body written to
> disk with `-o` looks exactly like success to any check that only asks whether the file exists.

### 2. Text to Video — 🔴 DEAD ENDPOINT, DO NOT USE

> `Wan-AI/Wan2.1-T2V-14B` on `hf-inference` returns **HTTP 400 "Model not supported by
> provider hf-inference"** (measured 2026-08-27 by two desks). Same class as the FLUX 410.
> There is no verified text→video replacement on this box yet — do not silently substitute one.
> The `-o` in the recipe below would write the 400 JSON body to `generated-video.mp4`.

### 2. Text to Video

```bash
curl -s https://router.huggingface.co/hf-inference/models/Wan-AI/Wan2.1-T2V-14B \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "A cat playing piano"}' \
  -o /app/runtime/canvas-pages/generated-video.mp4
```

### 3. Image to Image — 🔴 DEAD ENDPOINT, DO NOT USE

> `timbrooks/instruct-pix2pix` returns **HTTP 400 "Model not supported by provider
> hf-inference"** (measured 2026-08-27, two desks). The `-o output.png` below would
> write the JSON error body to a .png.

Transform images using a model. Send image as base64.

```bash
IMG_B64=$(base64 -w0 input.png)
curl -s https://router.huggingface.co/hf-inference/models/timbrooks/instruct-pix2pix \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"inputs\": \"$IMG_B64\", \"parameters\": {\"prompt\": \"make it look like a watercolor painting\"}}" \
  -o output.png
```

### 4. Feature Extraction (Embeddings)

Convert text to vector embeddings. Useful for semantic search and RAG.

> ⚠️ **The recipe that used to be here returned HTTP 400** (measured 2026-08-27, two desks):
> `{"inputs":"..."}` against the bare model URL is dispatched to that model's DEFAULT pipeline,
> which for `all-MiniLM-L6-v2` is **sentence-similarity**, not feature-extraction —
> *"SentenceSimilarityPipeline.__call__() missing 1 required positional argument: 'sentences'"*.
> The model and provider are both fine; only the request was wrong.
>
> **Ask for the pipeline by PATH SEGMENT, not query param.** `?pipeline=feature-extraction`
> still 400s (it is ignored); `/pipeline/feature-extraction` returns the vector.
>
> And note what you are asking for: the similarity payload
> `{"inputs":{"source_sentence":...,"sentences":[...]}}` also returns 200, but it yields
> **similarity scores, not embeddings**. Pasting that under this heading would silently give
> anyone building RAG the wrong kind of number. Different question, different call.

```bash
# Embeddings — note the /pipeline/feature-extraction suffix. Verified 200, 384 dims.
curl -s https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "How is the weather today?"}'

# BAAI/bge-large-en-v1.5 needs no suffix — its default pipeline IS feature-extraction.
# Verified 200, 1024 dims.
curl -s https://router.huggingface.co/hf-inference/models/BAAI/bge-large-en-v1.5 \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "How is the weather today?"}'
```

**Popular models:**
- `sentence-transformers/all-MiniLM-L6-v2` — fast, 384 dims
- `BAAI/bge-large-en-v1.5` — high quality, 1024 dims

### 5. Text Classification (Sentiment, etc.)

```bash
curl -s https://router.huggingface.co/hf-inference/models/distilbert/distilbert-base-uncased-finetuned-sst-2-english \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "I love this product, it works great!"}'
```

Returns: `[{"label": "POSITIVE", "score": 0.999}]`

### 6. Zero-Shot Classification

Classify text into categories without training.

```bash
curl -s https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "The new iPhone has amazing camera quality",
    "parameters": {"candidate_labels": ["technology", "sports", "politics", "business"]}
  }'
```

### 7. Summarization

```bash
curl -s https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": "The tower is 324 metres tall, about the same height as an 81-storey building...",
    "parameters": {"max_length": 100, "min_length": 30}
  }'
```

### 8. Translation

```bash
curl -s https://router.huggingface.co/hf-inference/models/Helsinki-NLP/opus-mt-en-fr \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello, how are you today?"}'
```

**Language pairs:** `opus-mt-en-fr` (French), `opus-mt-en-es` (Spanish), `opus-mt-en-de` (German), etc.

### 9. Question Answering (Extractive)

```bash
curl -s https://router.huggingface.co/hf-inference/models/deepset/roberta-base-squad2 \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "question": "What is the capital of France?",
      "context": "France is a country in Western Europe. Its capital city is Paris."
    }
  }'
```

### 10. Image Classification

```bash
curl -s https://router.huggingface.co/hf-inference/models/google/vit-base-patch16-224 \
  -H "Authorization: Bearer $HF_TOKEN" \
  --data-binary @photo.jpg
```

### 11. Object Detection

```bash
curl -s https://router.huggingface.co/hf-inference/models/facebook/detr-resnet-50 \
  -H "Authorization: Bearer $HF_TOKEN" \
  --data-binary @photo.jpg
```

### 12. Automatic Speech Recognition (STT)

```bash
curl -s https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3 \
  -H "Authorization: Bearer $HF_TOKEN" \
  --data-binary @audio.flac
```

### 13. Token Classification (NER)

Named Entity Recognition — identify people, places, organizations.

```bash
curl -s https://router.huggingface.co/hf-inference/models/dslim/bert-base-NER \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "My name is Sarah and I live in London working at Google"}'
```

## Hub Search API

Search for models, datasets, and spaces programmatically:

```bash
# Search models
curl -s "https://huggingface.co/api/models?search=text-to-image&sort=downloads&limit=5" \
  -H "Authorization: Bearer $HF_TOKEN"

# Search datasets
curl -s "https://huggingface.co/api/datasets?search=sentiment&sort=downloads&limit=5" \
  -H "Authorization: Bearer $HF_TOKEN"

# Get model details
curl -s "https://huggingface.co/api/models/black-forest-labs/FLUX.1-schnell" \
  -H "Authorization: Bearer $HF_TOKEN"
```

## Tips

- **Rate limits:** the legacy free `hf-inference` tier has per-model rate limits. Authenticated
  requests (HF_TOKEN) get higher limits. `nscale` image calls bill against the subscription quota.
- **Image responses are JSON now:** `nscale` `/v1/images/generations` returns JSON with the
  image base64 at `.data[0].b64_json` — `curl -o` alone saves a JSON blob, not a picture.
  Video/audio endpoints on `hf-inference` still return raw binary (unverified as of 2026-08-26).
- **JSON responses:** Text tasks return JSON. Parse with `jq` for clean output.
- **Model discovery:** Browse https://huggingface.co/models?inference_provider=all to find models with active inference.
- **Error handling:** 503 = model loading (retry in 20s), 429 = rate limited (back off), 422 = bad input,
  404 = wrong provider/model combo, **410 = the provider deprecated that model (permanent — do not retry,
  switch providers)**, 403 = dead/empty account (that is `fal-ai`).
- **Always verify images with a CONDITIONAL, not an eyeball:** check the HTTP status, then the
  decoded magic bytes (`89 50 4e 47` PNG / `ff d8 ff` JPEG / `52 49 46 46` WEBP), then reject
  anything under 10 KB. A dead HF path returns a well-formed HTTP error whose body lands on
  disk as a fake image and passes every existence check. Prefer `scripts/hf-image-gen.sh`.

## Canvas Page Integration

When the user asks you to generate an image:
1. Generate the image with curl, saving to `/app/runtime/canvas-pages/`
2. Verify it's a real image: `file /app/runtime/canvas-pages/my-image.png`
3. Create an HTML canvas page that displays the image
4. Open it with `[CANVAS:page-name]`

Example workflow:
```bash
# Generate image — the script gates status code, base64 decode, magic bytes and size.
# On ANY failure it exits non-zero and leaves the output path ABSENT (no stub to mistake
# for success). Note the `||` — the gate has to be a real conditional in YOUR script too.
/skills/huggingface/scripts/hf-image-gen.sh \
  "A professional contractor at work, photorealistic" \
  /app/runtime/canvas-pages/contractor-photo.png \
  || { echo "image generation failed — do NOT build the page around a missing asset"; exit 1; }

# Then create an HTML page that displays it, or tell the user about it
```

⚠️ `file <path>` alone is NOT a gate — it is a string a human has to read. If you write the
check by hand, make it a conditional that exits non-zero:
`head -c8 "$P" | od -An -tx1 | tr -d ' \n' | grep -qE '^(89504e470d0a1a0a|ffd8ff|52494646)' || exit 1`

## Cost

Inference runs against the HF Inference Providers quota on our subscription (the token has
Inference Providers write permission). Image generation now bills through the **`nscale`**
provider rather than the legacy free `hf-inference` serverless tier. Heavy usage of large
models may consume credits.
