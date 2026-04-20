---
name: 3d-models
description: Unified 3D model skill — FIND a ready-made free model (Objaverse, 800K library, no cost), or GENERATE a new one (Meshy primary, Tripo fallback), plus rig, animate, retexture, remesh, convert formats. Auto-saves GLB to canvas-pages for immediate in-browser display.
metadata: {"openclaw": {"requires": {"env": ["MESHY_API_KEY"], "anyBins": ["curl", "python3"]}}}
---

# 3D Models — Unified Skill

One skill for every 3D task. **Start by asking: can I FIND this instead of generating it?** Generation costs credits; the Objaverse catalog is free and has 800K+ models.

## Decision tree

| Goal | Path | Cost | Time |
|------|------|------|------|
| Common noun (chair, car, tree, cat, sword, robot…) | **FIND** → Objaverse | Free | ~3-10s |
| Specific/custom object a catalog won't have | **GENERATE** → Meshy | ~5-10 credits | ~1-3 min |
| Generate from a photo | **GENERATE** → Meshy (image-to-3d) | ~10 credits | ~1-2 min |
| Rigged + animated character (walking, running, combat, dancing…) | **GENERATE** → Meshy → RIG | varies | ~5 min |
| Already have a GLB, want new texture | **EDIT** → Meshy retexture | ~5 credits | ~1 min |
| Already have a GLB, need lower polycount / different format | **EDIT** → Meshy remesh | ~2 credits | ~30s |

**Fallback order when Meshy fails or is out of credits:** Tripo3D (needs `TRIPO_API_KEY`). Tripo has parity on text-to-3d, image-to-3d, rigging, retexture, remesh. Use identical outputs (GLB to `/app/runtime/canvas-pages/<name>.glb`).

## Destination convention (applies to every path)

Every final GLB lands at:
```
/app/runtime/canvas-pages/<name>.glb        (file on disk)
/pages/<name>.glb                           (browser URL, same origin as canvas)
```

Save thumbnails as `<name>.png` in the same dir. **Never reference a provider CDN URL in HTML** — all presigned URLs expire. Always download, always save locally.

---

# 1. FIND — Objaverse (free, 800K+ models)

**When to use:** generic / common objects. Objaverse is a giant CC-licensed catalog of user-uploaded 3D models. No API key, no credit cost. LVIS categories (~1,200 nouns) are the built-in search axis.

**Dataset:** https://huggingface.co/datasets/allenai/objaverse — ~800K GLBs, ~100GB total.
**Loader:** `pip install objaverse` (Python package — auto-handles caching + pathing).
**Cache dir:** `~/.objaverse/hf-objaverse-v1/glbs/` (survives across sessions, ~50-500KB per model).

## 1a. One-shot: find + download the first match for a keyword

```bash
pip install -q objaverse
NAME=chair
KEYWORD=chair   # must be an LVIS category

python3 <<PY
import objaverse, shutil, sys
lvis = objaverse.load_lvis_annotations()
# Fuzzy match: exact first, then substring
key = "$KEYWORD".lower()
if key not in lvis:
    matches = [k for k in lvis if key in k.lower()]
    if not matches:
        print(f"No LVIS category matches '$KEYWORD'. Try: " + ", ".join(sorted(lvis)[:20]))
        sys.exit(1)
    key = matches[0]
    print(f"Using category: {key}")
uids = lvis[key][:3]                        # first 3 candidates
objs = objaverse.load_objects(uids=uids)    # downloads GLBs, returns {uid: local_path}
first_uid, first_path = next(iter(objs.items()))
shutil.copy(first_path, "/app/runtime/canvas-pages/$NAME.glb")
print(f"saved → /app/runtime/canvas-pages/$NAME.glb  (browser /pages/$NAME.glb)")
print(f"uid={first_uid}")
PY
```

## 1b. Browse the LVIS category list

```bash
python3 -c "import objaverse; lvis = objaverse.load_lvis_annotations(); \
print('\n'.join(sorted(lvis.keys())))"  | head -50
```

Top categories include: `apple`, `armchair`, `backpack`, `ball`, `banana`, `baseball_cap`, `bed`, `bench`, `bicycle`, `book`, `bottle`, `bowl`, `bread`, `bus`, `cabinet`, `cake`, `camera`, `candle`, `car_(automobile)`, `carrot`, `cat`, `chair`, `chicken`, `clock`, `cowboy_hat`, `crab`, `cup`, `desk`, `dog`, `duck`, `fish`, `flower_arrangement`, `fork`, `glass_(drink_container)`, `guitar`, `hamburger`, `hammer`, `hat`, `horse`, `house`, `key`, `keyboard_(computer)`, `knife`, `lamp`, `laptop_computer`, `lemon`, `mug`, `pen`, `piano`, `pillow`, `pizza`, `plate`, `refrigerator`, `rocket`, `sandwich`, `sink`, `skateboard`, `sofa`, `spoon`, `sword`, `table`, `teddy_bear`, `telephone`, `television_set`, `tomato`, `tree`, `umbrella`, `vase`, `watch`, `wine_bottle`…

## 1c. Download specific UIDs directly (when you already have a UID)

```python
import objaverse
objs = objaverse.load_objects(uids=["f82039689f504922995936c68484aa61"])
# → {'f820...aa61': '/root/.objaverse/hf-objaverse-v1/glbs/000-120/f820...aa61.glb'}
```

## 1d. Get metadata (name, license, tags) before downloading

```python
import objaverse
anns = objaverse.load_annotations(uids=["f82039689f504922995936c68484aa61"])
# → {uid: { 'name': '...', 'tags': [...], 'license': 'CC-BY-4.0', 'viewCount': ..., ... }}
```

Use this to check the license — most are CC-BY-4.0 (free commercial use with attribution). A small number are CC-BY-NC (non-commercial). Skip anything that isn't CC-permissive if the end use is commercial.

## 1e. Direct HuggingFace URL pattern (no Python needed)

Each UID lives at:
```
https://huggingface.co/datasets/allenai/objaverse/resolve/main/glbs/<bucket>/<uid>.glb
```
Where `<bucket>` is deterministic from the UID — easier to let the `objaverse` package resolve it than compute it yourself. Use `objaverse.load_objects(...)` unless you have a very specific reason to curl directly.

## 1f. Limits & gotchas

- **No full-text search.** LVIS categories only. For free-text ("dragon with purple wings") you must GENERATE.
- **Model quality varies wildly.** These are user uploads. Inspect a few before committing — use the `viewCount` and `likeCount` in annotations as quality signals.
- **Topology is arbitrary.** No uniform polycount. If you need a specific budget, follow with a **remesh** pass (see EDIT section).
- **Rate limit:** HuggingFace allows generous unauthenticated downloads; `HF_TOKEN` env var raises limits further if set.

## 1g. Objaverse-XL — larger pool (~10.2M models, advanced)

The base Objaverse is ~800K curated models. If you need broader coverage (obscure categories, CAD parts, scanned objects), use the XL superset (~10.2M models pulled from GitHub, Smithsonian, Thingiverse, Sketchfab, Polycam). **Default to base Objaverse for agent workflows** — XL is slower and has per-source quirks.

- Repo: https://github.com/allenai/objaverse-xl
- Docs: https://objaverse.allenai.org/docs/objaverse-xl/
- Install: same `pip install objaverse` — XL is a submodule (`objaverse.xl`).

```python
import objaverse.xl as oxl
ann = oxl.get_annotations(download_dir="~/.objaverse")   # pandas DataFrame of all 10M sources
subset = ann[ann["source"] == "github"].head(5)          # pick a source (github|smithsonian|thingiverse|sketchfab)
oxl.download_objects(objects=subset, download_dir="~/.objaverse")
```

XL annotations are a pandas DataFrame — filter by `source`, `fileType`, `metadata`, etc. Each source has its own download mechanism (some require the GitHub API, Sketchfab models need an auth token). When in doubt, stay on base Objaverse (1.0) — LVIS categories cover almost everything a voice UI user asks for.

---

# 2. GENERATE — text → 3D (Meshy primary)

**Base URL:** `https://api.meshy.ai`
**Auth:** `Authorization: Bearer $MESHY_API_KEY`
**Flow:** preview (fast, untextured) → refine (slower, textured PBR).
**Models:** `meshy-6` (latest, best quality) · `meshy-5` (stable) · `latest` (alias → meshy-6).

## 2a. Preview (first stage)

```bash
RESP=$(curl -s https://api.meshy.ai/openapi/v2/text-to-3d \
  -H "Authorization: Bearer $MESHY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "preview",
    "prompt": "a low-poly stylized wooden cabin with snow on the roof",
    "ai_model": "meshy-6",
    "topology": "triangle",
    "target_polycount": 30000,
    "symmetry_mode": "auto",
    "should_remesh": true,
    "auto_size": true,
    "origin_at": "bottom",
    "target_formats": ["glb"]
  }')
PREVIEW_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['result'])")
```

## 2b. Refine (PBR textures)

Wait until preview reaches `SUCCEEDED`, then:

```bash
RESP=$(curl -s https://api.meshy.ai/openapi/v2/text-to-3d \
  -H "Authorization: Bearer $MESHY_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"mode\": \"refine\",
    \"preview_task_id\": \"$PREVIEW_ID\",
    \"enable_pbr\": true,
    \"ai_model\": \"meshy-6\",
    \"target_formats\": [\"glb\"]
  }")
REFINE_ID=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['result'])")
```

Optional refine params:
- `texture_prompt` — separate texture-style prompt (max 600 chars)
- `texture_image_url` — reference image (public URL or base64 data URI)
- `remove_lighting` — bake lighting out so model works in any scene (meshy-6, default true)

## 2c. Fallback — Tripo text-to-3D (only if Meshy is down / out of credits)

```bash
TASK=$(curl -s https://api.tripo3d.ai/v2/openapi/task \
  -H "Authorization: Bearer $TRIPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text_to_model",
    "prompt": "a low-poly stylized wooden cabin",
    "model_version": "v2.5-20250123",
    "texture": true, "pbr": true, "auto_size": true
  }' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['task_id'])")
```

Tripo model versions: `v3.1-20260211` (best), `v2.5-20250123` (default), `Turbo-v1.0-20250506` (image-to-model only). Different poll endpoint — see section 5.

---

# 3. GENERATE — image → 3D (Meshy primary)

```bash
curl -s https://api.meshy.ai/openapi/v1/image-to-3d \
  -H "Authorization: Bearer $MESHY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/photo.jpg",
    "ai_model": "meshy-6",
    "enable_pbr": true,
    "should_texture": true,
    "topology": "triangle",
    "target_polycount": 30000,
    "symmetry_mode": "auto",
    "image_enhancement": true,
    "auto_size": true,
    "target_formats": ["glb"]
  }'
```

`image_url` accepts a public URL OR a `data:image/png;base64,...` data URI. For local files:

```bash
IMG_B64=$(base64 -w0 /path/to/photo.png)
# Pass "data:image/png;base64,$IMG_B64" as image_url
```

## 3a. Multi-image to 3D (1–4 views of the same object — better geometry)

```bash
curl -s https://api.meshy.ai/openapi/v1/multi-image-to-3d \
  -H "Authorization: Bearer $MESHY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": [
      "https://example.com/front.jpg",
      "https://example.com/right.jpg",
      "https://example.com/back.jpg",
      "https://example.com/left.jpg"
    ],
    "ai_model": "meshy-6",
    "enable_pbr": true,
    "target_formats": ["glb"]
  }'
```

## 3b. Fallback — Tripo image-to-3D

Two-step for local files: upload (multipart) → use returned `image_token`:

```bash
TOKEN=$(curl -s https://api.tripo3d.ai/v2/openapi/upload \
  -H "Authorization: Bearer $TRIPO_API_KEY" \
  -F "file=@/path/to/photo.jpg" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['image_token'])")

TASK=$(curl -s https://api.tripo3d.ai/v2/openapi/task \
  -H "Authorization: Bearer $TRIPO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"image_to_model\",\"file\":{\"type\":\"jpg\",\"file_token\":\"$TOKEN\"},\"model_version\":\"v2.5-20250123\",\"texture\":true,\"pbr\":true}")
```

---

# 4. RIG + ANIMATE (Meshy — 587 preset animations)

Meshy is the strong choice here. Tripo has rigging but a much smaller animation library.

## 4a. Rig a model (requires a prior text-to-3d or image-to-3d task)

```bash
curl -s https://api.meshy.ai/openapi/v1/rigging \
  -H "Authorization: Bearer $MESHY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input_task_id": "<prior task_id>",
    "height_meters": 1.8
  }'
# → {"result":"<rig_task_id>"}
```

Or pass a public `model_url` directly (GLB URL or data URI). Works best on humanoid bipeds; models >300K faces must be remeshed first. **Basic walking/running animations come free** with every successful rig.

Poll `GET /openapi/v1/rigging/:id`. On success you get:
- `rigged_character_glb_url` / `rigged_character_fbx_url`
- `basic_animations.walking_glb_url` / `.running_glb_url` / …armature versions

## 4b. Apply a preset animation from the 587-action library

```bash
curl -s https://api.meshy.ai/openapi/v1/animations \
  -H "Authorization: Bearer $MESHY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "rig_task_id": "<rig task_id>",
    "action_id": 515,
    "post_process": { "operation_type": "change_fps", "fps": 30 }
  }'
```

`post_process.operation_type` ∈ `change_fps` | `fbx2usdz` | `extract_armature`.
`post_process.fps` ∈ `24` | `25` | `30` | `60`.

### Animation library cheat sheet (pick the median value in a category)

| Category | action_id range | Safe default |
|----------|-----------------|--------------|
| Idle | 243–258 | 248 |
| Walking | 540–567 | 547 |
| Running | 509–539 | 515 |
| Jumping | 460–472 | 465 |
| Falling | 487–508 | 497 |
| Climbing | 434–448 | 441 |
| Crouch walk | 520–529 | 524 |
| Swimming | 568–570 | 569 |
| Dancing | 63–84 | 73 |
| Attack (weapon) | 222–241 | 230 |
| Punching | 191–221 | 206 |
| Blocking | 138–155 | 146 |
| Casting spell | 125–137 | 130 |
| Getting hit | 172–180 | 176 |
| Dying | 181–190 | 185 |
| Sleeping | 263–272 | 267 |
| Pushing | 259–262 | 260 |
| Working out | 319–331 | 325 |
| Picking up | 273–284 | 278 |
| Interacting | 285–318 | 300 |
| Looking around | 333–341 | 337 |
| Transitioning | 344–372 | 358 |
| Body acting | 375–422 | 398 |
| Drinking | 342–343 | 342 |

## 4c. Full character pipeline (text → rigged + running animation)

```bash
# 1. Generate character (preview → refine) — see section 2, end with $CHAR as refined task_id
# 2. Rig
RIG=$(curl -s https://api.meshy.ai/openapi/v1/rigging \
  -H "Authorization: Bearer $MESHY_API_KEY" -H "Content-Type: application/json" \
  -d "{\"input_task_id\":\"$CHAR\",\"height_meters\":1.8}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['result'])")
# (poll until SUCCEEDED)

# 3. Animate — run
ANIM=$(curl -s https://api.meshy.ai/openapi/v1/animations \
  -H "Authorization: Bearer $MESHY_API_KEY" -H "Content-Type: application/json" \
  -d "{\"rig_task_id\":\"$RIG\",\"action_id\":515,\"post_process\":{\"operation_type\":\"change_fps\",\"fps\":30}}" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['result'])")
# (poll and download animation_glb_url)
```

---

# 5. EDIT — retexture, remesh, convert format

## 5a. Retexture an existing model (Meshy)

```json
POST /openapi/v1/retexture
{
  "input_task_id": "<prior task id>",
  "object_prompt": "a wooden cabin",
  "style_prompt": "burnt oak with moss, weathered paint",
  "enable_pbr": true,
  "ai_model": "meshy-6",
  "target_formats": ["glb"]
}
```

Or supply your own model via `model_url` (GLB/GLTF/OBJ/FBX/STL public URL or data URI). Use `texture_image_url` to style by reference image.

Poll at `GET /openapi/v1/retexture/:id`.

## 5b. Remesh / reduce polycount (Meshy)

```json
POST /openapi/v1/remesh
{
  "input_task_id": "<prior task id>",
  "target_polycount": 5000,
  "topology": "quad",
  "target_formats": ["glb", "fbx"],
  "auto_size": true
}
```

Set `convert_format_only: true` to skip retopology and ONLY change encoding (e.g. GLB→FBX).

Poll at `GET /openapi/v1/remesh/:id`.

## 5c. Tripo equivalents (fallback)

- Retexture: `{"type":"texture_model","original_model_task_id":"<task>","texture":true,"pbr":true,"texture_quality":"detailed"}`
- Remesh / low-poly: `{"type":"highpoly_to_lowpoly","original_model_task_id":"<task>","face_limit":5000,"quad":true}`
- Convert format: `{"type":"convert_model","original_model_task_id":"<task>","format":"FBX","texture_size":2048}`
  - `format` ∈ `GLTF | USDZ | FBX | OBJ | STL | 3MF`

---

# 6. Poll a task until done + download

## 6a. Meshy polling

```bash
OUT_DIR=/app/runtime/canvas-pages
NAME=cabin
KIND=text-to-3d          # or image-to-3d, retexture, remesh, rigging, animations, multi-image-to-3d
VER=v2                   # v2 for text-to-3d, v1 for everything else
TASK_ID="$REFINE_ID"

while true; do
  R=$(curl -s "https://api.meshy.ai/openapi/$VER/$KIND/$TASK_ID" \
    -H "Authorization: Bearer $MESHY_API_KEY")
  S=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['status'])")
  P=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin).get('progress',0))")
  echo "status=$S progress=$P%"

  case "$S" in
    SUCCEEDED)
      URL=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin)['model_urls']['glb'])")
      curl -sL "$URL" -o "$OUT_DIR/$NAME.glb"
      THUMB=$(echo "$R" | python3 -c "import sys,json;print(json.load(sys.stdin).get('thumbnail_url') or '')")
      [ -n "$THUMB" ] && curl -sL "$THUMB" -o "$OUT_DIR/$NAME.png"
      echo "saved $OUT_DIR/$NAME.glb  →  /pages/$NAME.glb"
      break ;;
    FAILED|CANCELED)
      echo "task ended: $S"; echo "$R" | python3 -m json.tool; exit 1 ;;
  esac
  sleep 5
done
```

Status values: `PENDING`, `IN_PROGRESS`, `SUCCEEDED`, `FAILED`, `CANCELED`.

## 6b. Meshy SSE stream (preferred — faster UI feedback)

```bash
curl -N https://api.meshy.ai/openapi/v2/text-to-3d/$TASK_ID/stream \
  -H "Authorization: Bearer $MESHY_API_KEY"
# emits `data: {...}` frames on status/progress changes, ends on SUCCEEDED/FAILED
```

## 6c. Tripo polling (different shape)

```bash
while :; do
  RESP=$(curl -s "https://api.tripo3d.ai/v2/openapi/task/$TASK" \
    -H "Authorization: Bearer $TRIPO_API_KEY")
  STATUS=$(echo "$RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['status'])")
  case "$STATUS" in
    success)
      URL=$(echo "$RESP" | python3 -c "import sys,json;d=json.load(sys.stdin)['data']['output'];print(d.get('pbr_model') or d.get('model'))")
      curl -sL "$URL" -o "/app/runtime/canvas-pages/$NAME.glb"; break ;;
    failed|cancelled|banned|expired)
      echo "$RESP"; exit 1 ;;
  esac
  sleep 5
done
```

Status values: `queued`, `running`, `success`, `failed`, `cancelled`, `banned`, `expired`.

---

# 7. Auto-save via platform webhook (Meshy — preferred, zero polling)

The JamBot VPS runs a webhook receiver that **automatically downloads the finished GLB into the tenant's `canvas-pages/`** — no manual polling or download step from the agent. Use this whenever possible.

## 7a. Create → register → wait

```bash
# 1. Create the task (same as section 2)
TASK=$(curl -s https://api.meshy.ai/openapi/v2/text-to-3d \
  -H "Authorization: Bearer $MESHY_API_KEY" -H "Content-Type: application/json" \
  -d '{"mode":"preview","prompt":"a red mug","ai_model":"meshy-6","target_formats":["glb"]}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['result'])")

# 2. Register with the tracker (tenant header required — env has JAMBOT_TENANT pre-set)
curl -s http://172.17.0.1:6350/api/meshy/track \
  -H "Content-Type: application/json" -H "X-Tenant: $JAMBOT_TENANT" \
  -d "{\"task_id\":\"$TASK\",\"filename\":\"mug\",\"kind\":\"text-to-3d-preview\"}"

# 3. Wait. Meshy webhook → receiver → auto-download to /pages/mug.glb
```

## 7b. Check saved location when ready

```bash
curl -s http://172.17.0.1:6350/api/meshy/task/$TASK
# → { ok: true, record: { status: "SUCCEEDED", saved_glb: "...", finished_at: ... }, public_url: "/pages/mug.glb" }
```

If `status` is still `pending` / `IN_PROGRESS`, the webhook hasn't fired yet — wait a few seconds or fall back to SSE/polling.

## 7c. Platform endpoints (all at `172.17.0.1:6350`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/meshy/track` | Register task_id → tenant + filename (X-Tenant header required) |
| GET | `/api/meshy/task/:id` | Look up status + saved path |
| GET | `/api/meshy/balance` | Credits remaining (no auth) |
| GET | `/api/meshy/events?limit=50` | Recent webhook deliveries (debug) |

Tripo does not have an equivalent platform webhook — use manual polling (6c).

---

# 8. Display in a canvas page

**Canvas CSP allows `cdn.jsdelivr.net` for scripts — DO NOT use `unpkg.com`, it will be blocked.**

## 8a. `<model-viewer>` — simplest

```html
<script type="module"
  src="https://cdn.jsdelivr.net/npm/@google/model-viewer@4/dist/model-viewer.min.js"></script>

<model-viewer src="/pages/cabin.glb" camera-controls auto-rotate ar
              alt="3D model" poster="/pages/cabin.png"
              style="width:100%;height:500px;background:#111"></model-viewer>
```

## 8b. three.js + GLTFLoader (custom scenes)

```html
<canvas id="scene" style="width:100%;height:500px"></canvas>
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }
}
</script>
<script type="module">
  import * as THREE from 'three';
  import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

  const canvas = document.getElementById('scene');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(50, canvas.clientWidth/canvas.clientHeight, 0.1, 100);
  camera.position.set(2, 2, 3);
  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const dir = new THREE.DirectionalLight(0xffffff, 1); dir.position.set(5,5,5); scene.add(dir);
  new GLTFLoader().load('/pages/cabin.glb', gltf => {
    scene.add(gltf.scene);
    (function loop(){ requestAnimationFrame(loop); gltf.scene.rotation.y += 0.01; renderer.render(scene, camera); })();
  });
</script>
```

GLBs are served at `/pages/*.glb` on the same origin. Content-Type is `model/gltf-binary` (MIME fix deployed 2026-04-19). For `.fbx` / `.obj` use `FBXLoader` / `OBJLoader` from `three/addons/loaders/`.

---

# 9. Balance, rate limits, errors

## 9a. Check balances

```bash
# Meshy credits
curl -s https://api.meshy.ai/openapi/v1/balance \
  -H "Authorization: Bearer $MESHY_API_KEY"
# → {"balance": 2660}

# Tripo credits
curl -s https://api.tripo3d.ai/v2/openapi/user/balance \
  -H "Authorization: Bearer $TRIPO_API_KEY"
# → { "data": { "balance": 123.45, "frozen": 2.0 } }

# Via platform bridge (no auth header needed, internal only)
curl -s http://172.17.0.1:6350/api/meshy/balance
```

Always check balance before a batch run. Cost rule-of-thumb:
- Meshy text-to-3d preview ≈ 5 credits, refine ≈ 10 credits
- Meshy image-to-3d ≈ 10 credits, multi-image ≈ 15 credits
- Meshy retexture ≈ 5 credits, remesh ≈ 2 credits
- Objaverse FIND: 0 credits

## 9b. Meshy rate limits

| Tier | Requests/sec | Concurrent tasks |
|------|-------------:|-----------------:|
| Pro | 20 | 10 |
| Studio | 20 | 20 |
| Enterprise | 100 | 50 |

Violations return `429` — "Request Hit" (req/sec) or "Queue Hit" (concurrent). Back off with exponential retry.

## 9c. Error codes

| HTTP | Meaning | Action |
|------|---------|--------|
| 401 | Bad API key | Verify via `/balance` |
| 402 | Out of credits | Top up, or FIND via Objaverse, or fall back to Tripo |
| 400 | Bad params (prompt > 600 chars, unknown model, preview not SUCCEEDED, etc.) | Read response `message` field |
| 429 | Rate / queue limit | Back off + retry |
| 5xx | Provider transient | Retry with exponential backoff |

Task-level failures surface as `status: "FAILED"` with `task_error.message`. **Do not retry the same task** — create a new one with corrected inputs.

---

# 10. Quick reference — "which path do I use?"

```
need a 3D model
├── is it a common noun (chair, car, tree, cat, …)?
│   └── yes → FIND: Objaverse (section 1)
│
├── is it custom / specific / stylized?
│   └── GENERATE from text (section 2) — Meshy primary
│
├── do I have a reference image?
│   └── GENERATE from image (section 3) — Meshy primary
│
├── is it a humanoid that needs to move?
│   └── GENERATE → RIG → ANIMATE (section 4) — Meshy, 587 presets
│
├── do I already have a model?
│   ├── wrong texture → EDIT retexture (section 5a)
│   ├── too high-poly / wrong format → EDIT remesh/convert (section 5b–c)
│   └── untextured → apply texture via retexture
│
└── always: land the GLB at /app/runtime/canvas-pages/<name>.glb
          display via <model-viewer src="/pages/<name>.glb">  (section 8)
```
