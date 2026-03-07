---
name: gemini-image
description: Generate images using Google Gemini's native image generation. Text-to-image and image editing via the Gemini API. Free tier available.
metadata: {"openclaw": {"requires": {"env": ["GEMINI_API_KEY"], "anyBins": ["curl"]}}}
---

# Gemini Image Generation Skill

Generate images using Google Gemini models with native image output. Supports text-to-image generation, image editing, and multimodal prompts.

## Available Models

| Model | Best For | Speed |
|-------|----------|-------|
| `gemini-2.0-flash-exp-image-generation` | General image gen, reliable | Fast |
| `gemini-2.5-flash-image` | Higher quality, newer | Fast |
| `gemini-3-pro-image-preview` | Best quality (preview) | Slower |
| `gemini-3.1-flash-image-preview` | Fast + quality (preview) | Fast |

## Text to Image

Generate an image from a text prompt. The response contains base64-encoded image data.

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"parts": [{"text": "A professional logo for a pest control company called BugBusters, modern flat design, green and white colors"}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
  }' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
parts = d['candidates'][0]['content']['parts']
for p in parts:
    if 'inlineData' in p:
        with open('/app/runtime/canvas-pages/generated-image.png', 'wb') as f:
            f.write(base64.b64decode(p['inlineData']['data']))
        print('Image saved to generated-image.png')
    elif 'text' in p:
        print(p['text'])
"
```

## Image Editing (Image + Text Prompt)

Send an existing image with instructions to modify it:

```bash
# Encode source image
IMG_B64=$(base64 -w0 /path/to/source.png)

curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"contents\": [{\"parts\": [
      {\"text\": \"Edit this image: make the background sunset orange\"},
      {\"inlineData\": {\"mimeType\": \"image/png\", \"data\": \"$IMG_B64\"}}
    ]}],
    \"generationConfig\": {\"responseModalities\": [\"TEXT\", \"IMAGE\"]}
  }" | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for p in d['candidates'][0]['content']['parts']:
    if 'inlineData' in p:
        with open('/app/runtime/canvas-pages/edited-image.png', 'wb') as f:
            f.write(base64.b64decode(p['inlineData']['data']))
        print('Edited image saved')
"
```

## One-Liner for Canvas Pages

Quick pattern for generating and displaying images:

```bash
# Generate image and save as canvas page asset
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp-image-generation:generateContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"YOUR PROMPT HERE"}]}],"generationConfig":{"responseModalities":["TEXT","IMAGE"]}}' \
  | python3 -c "import sys,json,base64;d=json.load(sys.stdin);[open('/app/runtime/canvas-pages/FILENAME.png','wb').write(base64.b64decode(p['inlineData']['data'])) for p in d['candidates'][0]['content']['parts'] if 'inlineData' in p]"
```

Then create an HTML canvas page that references the image, or tell the user the image is ready.

## Tips

- **responseModalities MUST include "IMAGE"** — without it, Gemini returns text only
- **Free tier:** ~15 requests/minute, 1500/day for image generation
- **Output format:** Always PNG, typically 1024x1024
- **Image editing:** Send the source image as base64 inlineData alongside your text instructions
- **Multiple images:** Ask for "4 variations" — Gemini may return multiple image parts
- **Style control:** Be specific in prompts: "watercolor style", "flat vector illustration", "photorealistic", "line art", "pixel art"
- **Errors:** 429 = rate limited (wait 60s), 400 = bad prompt (rephrase), 500 = retry

## When to Use This vs Other Tools

| Need | Use |
|------|-----|
| Quick image from text prompt | **This skill** (Gemini) — fast, free, good quality |
| High-quality art/photos | Hugging Face FLUX.1-dev — best open-source quality |
| Fast bulk generation | Hugging Face FLUX.1-schnell — fastest |
| Edit existing images | **This skill** (Gemini) — send image + edit instructions |
| UI mockups/screens | Stitch skill — purpose-built for UI design |
