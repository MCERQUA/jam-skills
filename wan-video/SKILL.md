---
name: wan-video
description: Image-to-video generation — animate a still image into a short cinematic video clip using Wan 2.2 (14B) on our own HuggingFace ZeroGPU Space. Runs on the HF subscription quota (not pay-per-call). Voice/openclaw agents request it via a queue; the video lands in the tenant's uploads.
metadata: {"openclaw": {"requires": {"anyBins": ["bash"]}}}
---

# Wan Video Skill — animate a still image into a short video

Turn a still image (a product photo, shop front, logo, scene) into a short animated/cinematic
**video clip**. Powered by **Wan 2.2 14B** on **our own HuggingFace Space** (`mikecerqua/wan22-video`,
ZeroGPU) — so it runs on the **HF subscription quota we already pay for**, not fal/per-call billing.

This is **image-to-video** (it animates an existing image). You MUST supply an image. It is NOT
text-to-video.

## How you (a voice/tenant agent) invoke it — the request queue

You can't run the GPU call yourself; you **request** it and the host generates it. Drop a JSON
request into the shared queue, then poll for the result. The finished `.mp4` is saved into YOUR
tenant's uploads (so it's a real server URL you can show in the canvas/UI).

### 1. Drop the request
```bash
TENANT=<your-tenant>          # e.g. azrim
RID="wan-$(date +%s)-$RANDOM"
cat > /mnt/agent-mesh/mesh/wan-video-queue/${RID}.json <<JSON
{"tenant":"${TENANT}","image":"<path-or-url-to-the-image>","prompt":"<what should move — e.g. 'the rim slowly rotates, studio lighting'>","duration":3.5,"id":"${RID}"}
JSON
```
- `image` (REQUIRED) — a local path the host can read (e.g. an existing upload
  `/mnt/clients/<tenant>/openvoiceui/uploads/<file>`) OR a public URL.
- `prompt` — describe the motion (camera move, what comes alive). Keep it short + concrete.
- `duration` — seconds (default 3.5; longer uses more ZeroGPU quota).

### 2. Poll for the result (host drain runs every ~minute; generation takes ~30-60s)
```bash
for i in $(seq 1 12); do
  R="/mnt/agent-mesh/mesh/wan-video-queue/.done/${RID}.result.json"
  [ -f "$R" ] && { cat "$R"; break; }
  sleep 10
done
```
Result JSON:
```json
{"id":"...","status":"ok","video_url":"/uploads/ai-gen-wan-<ts>.mp4","video_path":"/mnt/clients/<tenant>/openvoiceui/uploads/ai-gen-wan-<ts>.mp4","tenant":"..."}
```
- On `status:"ok"` → show the video from `video_url` (it's already saved on your server — a real
  file, never an in-memory blob). On `status:"error"` → read `reason` (cold space / quota / bad image).

## Examples (request bodies)
```json
// animate a client's product photo already in their uploads
{"tenant":"azrim","image":"/mnt/clients/azrim/openvoiceui/uploads/wheel.jpg","prompt":"the rim slowly rotates, studio lighting","duration":3.5,"id":"wan-123"}

// animate from a public URL
{"tenant":"josh","image":"https://site.com/storefront.png","prompt":"camera pushes in, gentle motion","duration":5,"id":"wan-456"}
```

## Notes / limits
- **Quota:** runs on our HF PRO ZeroGPU daily quota — heavy/long clips use more; space them out.
- **Cold start:** if the Space was idle it wakes in ~30-60s; the first request after a wake may
  queue. The poll loop above handles it; if it errors "cold/queued," just request again.
- **Always saved to the server** (per the AI-output rule) — you get a `/uploads/...` URL to display.
- **Tracked:** every generation lights `prov:huggingface` on the JamFlow live map.
- Our Space is a version-pinned duplicate of `r3gm/wan2-2-fp8da-aoti-preview-2` (stable; won't
  break when the upstream preview changes).

## (host/admin only) direct CLI
On the host, `bash /home/mike/MIKE-AI/scripts/wan-video.sh --image <x> --prompt <y> --tenant <t>`
runs it directly (gradio_client + HF_TOKEN live on the host). Tenant agents use the queue above.
