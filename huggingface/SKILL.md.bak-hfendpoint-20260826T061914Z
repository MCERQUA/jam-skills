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
> image, use this skill's Text-to-Image recipe below** (HF FLUX on the subscription quota
> we already pay for — not pay-per-call). For **image→video**, use the **`wan-video`** skill.
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

Default provider for free serverless inference: `hf-inference`

## Provider Selection

Append a provider name to use a specific backend:

- `hf-inference` — free serverless tier (default, best for image generation)
- ~~`fal-ai`~~ — **DO NOT USE — our fal account is empty/dead (403 "Exhausted balance"). Use `hf-inference`.**
- `together` — LLM chat
- `replicate` — general purpose
- `fireworks-ai`, `sambanova`, `cerebras`, `hyperbolic`, `novita`, `nebius`, `nscale`, `wavespeed`

Not all providers host all models. Use `hf-inference` for the broadest free access.

## Tasks & Examples

### 1. Text to Image (MOST COMMON) — the voice-agent image recipe

Generate images from text prompts. Returns binary image data (PNG). **Save it to the
tenant's uploads** so you get a real server URL to show the user — never leave a generated
image only in a temp path (paid output must persist to the server immediately).

```bash
# Save DIRECTLY into the tenant's OVU uploads → served at https://<tenant>.jam-bot.com/uploads/<file>
TENANT=src                                  # your tenant slug
TS=$(date +%s)
TMP="/tmp/ai-gen-$TS.bin"
# Capture the Content-Type header so we save with the RIGHT extension.
# NOTE: hf-inference FLUX returns JPEG (not PNG) — always derive the extension, never assume .png.
CT=$(curl -s -D /tmp/ai-gen-$TS.hdr -o "$TMP" \
  https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "A cyberpunk cityscape at sunset, neon lights reflecting on wet streets"}' \
  -w '%{content_type}')
case "$CT" in
  *jpeg*|*jpg*) EXT=jpg ;; *png*) EXT=png ;; *webp*) EXT=webp ;;
  *) EXT=jpg ;;                             # HF image default is JPEG
esac
OUT="/mnt/clients/$TENANT/openvoiceui/uploads/ai-gen-$TS.$EXT"
mv "$TMP" "$OUT"

# ALWAYS verify it's a real image, not a JSON error body (check magic bytes):
head -c 3 "$OUT" | od -An -tx1        # JPEG=ff d8 ff · PNG=89 50 4e — if you see "7b" ({), it's a JSON error: cat "$OUT"
# Then show the user the SERVER URL (not the filesystem path):
echo "https://$TENANT.jam-bot.com/uploads/ai-gen-$TS.$EXT"
```

> **Inside an openclaw voice container** your CWD maps to the tenant workspace and the uploads
> folder is reachable as `/app/runtime/uploads/` or via the tenant path above. If unsure of
> the exact mount, write to `uploads/ai-gen-<ts>.png` under the tenant's openvoiceui dir — the
> file MUST land somewhere served at `/uploads/...`. Confirm the URL loads before telling the user it's ready.

**Models:** `black-forest-labs/FLUX.1-schnell` (fast, RECOMMENDED — verified live), `black-forest-labs/FLUX.1-dev` (best quality, slower), `stabilityai/stable-diffusion-xl-base-1.0`.

**If HF returns HTTP 503 "model loading":** wait ~15s and retry once (cold ZeroGPU start). Don't fall back to fal — it's dead.

**Popular models:**
- `black-forest-labs/FLUX.1-schnell` — fast, good quality (RECOMMENDED)
- `black-forest-labs/FLUX.1-dev` — best quality, slower
- `stabilityai/stable-diffusion-xl-base-1.0` — SDXL classic

### 2. Text to Video

```bash
curl -s https://router.huggingface.co/hf-inference/models/Wan-AI/Wan2.1-T2V-14B \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "A cat playing piano"}' \
  -o /app/runtime/canvas-pages/generated-video.mp4
```

### 3. Image to Image

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

```bash
curl -s https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2 \
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

- **Rate limits:** Free `hf-inference` tier has rate limits per model. Authenticated requests (HF_TOKEN) get higher limits.
- **Binary responses:** Image/video/audio generation returns raw binary — always use `-o filename`.
- **JSON responses:** Text tasks return JSON. Parse with `jq` for clean output.
- **Model discovery:** Browse https://huggingface.co/models?inference_provider=all to find models with active inference.
- **Error handling:** 503 = model loading (retry in 20s), 429 = rate limited (back off), 422 = bad input, 404 = wrong provider/model combo.
- **Always verify images:** After generating, run `file <path>` to confirm it's actually image data, not an error message.

## Canvas Page Integration

When the user asks you to generate an image:
1. Generate the image with curl, saving to `/app/runtime/canvas-pages/`
2. Verify it's a real image: `file /app/runtime/canvas-pages/my-image.png`
3. Create an HTML canvas page that displays the image
4. Open it with `[CANVAS:page-name]`

Example workflow:
```bash
# Generate image
curl -s https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "A professional contractor at work, photorealistic"}' \
  -o /app/runtime/canvas-pages/contractor-photo.png

# Verify it's a real image
file /app/runtime/canvas-pages/contractor-photo.png
# Expected: PNG image data, ...

# Then create an HTML page that displays it, or tell the user about it
```

## Cost

Most inference calls are free on HF's serverless `hf-inference` tier. Heavy usage of large models may consume credits. The token has Inference Providers write permission.
