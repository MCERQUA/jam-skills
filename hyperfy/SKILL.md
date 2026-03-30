# Hyperfy 3D World Builder Skill

Build, script, and manage objects in Hyperfy — an open-source 3D virtual world engine.

## Overview

Hyperfy is a web-based multiplayer 3D world engine. You interact with it by creating **apps** — scripted objects placed in the world. Each app has a JavaScript script that runs in an isolated compartment.

**Your Hyperfy instance:** `https://3d-test-dev.jam-bot.com`
**World data:** `Websites/hyperfy/world/` (assets + SQLite DB)
**Source code:** `Websites/hyperfy/src/` (READ-ONLY — never modify)

## CRITICAL RULES

- **NEVER modify files in `Websites/hyperfy/src/`** — engine source is locked and read-only
- **NEVER modify `Websites/hyperfy/package.json`** or build scripts
- **NEVER replace, overwrite, or "rebuild" the Hyperfy installation**
- **ONLY interact through the approved methods below**

## How to Build in Hyperfy

### Method 1: REST API (PRIMARY — use this)

The Hyperfy server has AI-powered REST endpoints. Objects appear in the live world in ~5-15 seconds. No restart needed.

**Auth:** Add `?key=admin420` to POST/DELETE requests.

**Create an object (AI generates the script from your description):**
```bash
curl -X POST "https://3d-test-dev.jam-bot.com/api/ai/create?key=admin420" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a glowing blue portal ring floating and slowly spinning", "position": [0, 2, -5]}'
```
Returns `{"status":"generating", "blueprintId":"...", "entityId":"..."}`. The AI generates a Hyperfy script and the object materializes in the world for all connected clients.

**Edit an existing object:**
```bash
curl -X POST "https://3d-test-dev.jam-bot.com/api/ai/edit?key=admin420" \
  -H "Content-Type: application/json" \
  -d '{"blueprintId": "ID_FROM_BLUEPRINTS_LIST", "prompt": "make it bigger and add particle effects"}'
```

**List all objects (to find IDs for editing/removing):**
```bash
curl https://3d-test-dev.jam-bot.com/api/ai/entities
curl https://3d-test-dev.jam-bot.com/api/ai/blueprints
```

**Move/reposition an object:**
```bash
curl -X POST "https://3d-test-dev.jam-bot.com/api/ai/entity/ENTITY_ID/move?key=admin420" \
  -H "Content-Type: application/json" \
  -d '{"position": [5, 0, -3], "rotation": [0, 90, 0], "scale": [2, 2, 2]}'
```
Position = [x,y,z] meters. Rotation = [x,y,z] degrees. Scale = [x,y,z] multiplier. All fields optional.

**Remove an object:**
```bash
curl -X DELETE "https://3d-test-dev.jam-bot.com/api/ai/entity/ENTITY_ID?key=admin420"
```

**Check AI status:**
```bash
curl https://3d-test-dev.jam-bot.com/api/ai/status
```

**Get scene settings (lighting, fog, sky):**
```bash
curl https://3d-test-dev.jam-bot.com/api/ai/scene
```

**Update scene settings (sun, fog, HDR):**
```bash
curl -X POST "https://3d-test-dev.jam-bot.com/api/ai/scene?key=admin420" \
  -H "Content-Type: application/json" \
  -d '{"props": {"intensity": 2.5, "horizontalRotation": 180, "verticalRotation": 60, "fogColor": "#1a1a2e", "fogNear": 100, "fogFar": 500}}'
```
Scene props: `intensity` (sun brightness 0-10), `horizontalRotation` (sun direction 0-360), `verticalRotation` (sun elevation 0-360), `fogColor` (hex string, blank=no fog), `fogNear`/`fogFar` (meters), `rotationY` (sky rotation degrees).

### Method 2: Write scripts directly + upload

For when you want full control over the script code instead of AI generation:

```bash
# 1. Write your script locally
cat > /tmp/my-app.js << 'EOF'
const box = app.create('prim', {
  type: 'box', size: [1, 1, 1], color: '#ff0000',
  physics: 'static', position: [0, 0.5, 0]
})
app.add(box)
EOF

# 2. Upload to Hyperfy assets
curl -X POST https://3d-test-dev.jam-bot.com/api/upload -F "file=@/tmp/my-app.js"
```
Then create a blueprint+entity in the DB (see Database Schema section) and restart.

### Method 3: Direct database (bulk building, needs restart)

```bash
sqlite3 Websites/hyperfy/world/db.sqlite << 'SQL'
INSERT INTO blueprints (id, data, createdAt, updatedAt) VALUES (
  'my-app-001',
  '{"id":"my-app-001","version":0,"name":"Red Box","model":null,"script":"asset://my-script.js","props":{},"preload":false,"public":false,"locked":false,"unique":false,"scene":false,"disabled":false}',
  datetime('now'), datetime('now')
);
INSERT INTO entities (id, data, createdAt, updatedAt) VALUES (
  'entity-001',
  '{"id":"entity-001","type":"app","blueprint":"my-app-001","position":[0,0,0],"quaternion":[0,0,0,1],"scale":[1,1,1],"mover":null,"uploader":null,"pinned":false,"state":{}}',
  datetime('now'), datetime('now')
);
SQL
```
Note: DB changes require server restart to take effect (server loads DB into memory on boot).

### Method 4: Chat commands (user types in Hyperfy UI)

User must first type `/admin admin420` to get builder access, then:
- `/create <description>` — AI generates and spawns a scripted object
- `/edit <description>` — AI edits the object you're looking at
- `/fix` — AI fixes a crashed script

### Integration with OpenVoiceUI Canvas

The user views the Hyperfy world inside the OpenVoiceUI canvas iframe. The voice agent (you) runs in OpenClaw and can call the REST API directly via `exec` tool — no browser extension needed.

**Typical workflow:**
1. User says "build me a glowing portal in the world"
2. You call `curl -X POST https://3d-test-dev.jam-bot.com/api/ai/create?key=admin420 -H "Content-Type: application/json" -d '{"prompt":"a glowing portal","position":[0,2,0]}'`
3. Object appears in the user's canvas iframe in ~5-15 seconds
4. User says "make it bigger" → you call the edit endpoint with the blueprintId
5. User says "remove it" → you call the delete endpoint

**To show the Hyperfy world in the user's canvas:**
```
[CANVAS_URL:https://3d-test-dev.jam-bot.com]
```

**IMPORTANT — Pointer Lock does NOT work in iframes:**
The Hyperfy world in the canvas iframe is view-only for mouse look. `requestPointerLock()` is blocked by browsers inside iframes. The user can see the world and click UI elements, but cannot enter builder mode or use mouse-look in the iframe. For full mouse control (builder mode, grab/move objects), the user must click "Open Full Screen" to open Hyperfy in a new browser tab. Your REST API endpoints work regardless — create, edit, move, and delete objects via curl whether the user is in iframe or full screen.

**Coordinate tips (since you can't see the world):**
- `[0, 0, 0]` = world center (where the scene origin is)
- Y is up — `[0, 1, 0]` is 1 meter off the ground
- Spread objects out: use `[5, 0, 0]`, `[-5, 0, 3]`, `[0, 0, -8]` etc.
- Ask the user where they want things if precise placement matters
- List existing entities with `/api/ai/entities` to see what's already placed and where

## Writable Paths

| Path | Purpose |
|---|---|
| `Websites/hyperfy/world/assets/` | Script files (.js), models (.glb), textures |
| `Websites/hyperfy/world/db.sqlite` | Blueprints + entities (world state) |
| `Websites/hyperfy/.env` | Configuration |

## Read-Only Paths (NEVER modify)

| Path | Purpose |
|---|---|
| `Websites/hyperfy/src/` | Engine source code |
| `Websites/hyperfy/scripts/` | Build system |
| `Websites/hyperfy/package.json` | Dependencies |

---

## Hyperfy Scripting Reference

### Environment

Apps are individual objects in a 3D virtual world. Each app has its own transform (position, rotation, scale). Scripts execute in isolated JavaScript compartments.

**Coordinate system:** Three.js (X = Right, Y = Up, Z = Forward). Units = meters. Rotations = radians.
**Players:** ~1.7m tall, jump ~1.5m high, ~5m distance running+jumping.

### Available Globals

```
Math.*          — all Math functions
Vector3         — three.js Vector3
Euler           — three.js Euler
Quaternion      — three.js Quaternion
DEG2RAD         — multiply degrees to get radians
RAD2DEG         — multiply radians to get degrees
uuid            — generate unique IDs
prng            — seeded pseudo-random number generator
app             — the current app instance
world           — world object (isServer, isClient, etc.)
```

**IMPORTANT:** Only these globals exist. `Date`, `window`, `document`, `setTimeout`, `setInterval` do NOT exist and will crash the script silently (infinite loading).

### SANDBOX SAFETY — Scripts that crash will load forever with NO error shown to user

These WILL crash:
- `Date.now()` — use an `elapsed` counter: `let t=0; app.on('animate', d => { t += d })`
- `Math.random()` — use `prng(seed)` instead (deterministic across clients)
- `console.log()` — may not exist in all contexts
- `setTimeout()` / `setInterval()` — not available, use `app.on('animate')` with elapsed time
- Invalid prim types — ONLY: `box`, `sphere`, `cylinder`, `cone`, `torus`, `plane`

### Valid Prim Types (ONLY these exist)

| Type | Size format |
|---|---|
| `box` | `[width, height, depth]` |
| `sphere` | `[radius]` |
| `cylinder` | `[topRadius, bottomRadius, height]` |
| `cone` | `[radius, height]` |
| `torus` | `[radius, tubeRadius]` |
| `plane` | `[width, height]` |

There is NO `octahedron`, `ring`, `capsule`, `pyramid`, or other types.

### Creating Shapes (Prims)

```javascript
// Box
const box = app.create('prim', { type: 'box', size: [1, 2, 3], color: '#ff0000' })

// Sphere
const sphere = app.create('prim', { type: 'sphere', size: [0.5], color: '#00ff00' })

// Cylinder
const cyl = app.create('prim', { type: 'cylinder', size: [0.5, 0.5, 1], color: '#0000ff' })

// MUST add to app to make visible
app.add(box)
```

### Transforms

```javascript
const box = app.create('prim', {
  type: 'box', size: [1,1,1],
  position: [0, 2, 0],       // xyz meters
  rotation: [0, 45*DEG2RAD, 0], // xyz radians
  scale: [1, 1, 1],
})

// Modify after creation
box.position.set(0, 4, 0)
box.rotation.y += 10 * DEG2RAD
```

### App Origin

Players place apps on surfaces. Origin = ground level. Lift objects up:
```javascript
const box = app.create('prim', {
  type: 'box', size: [1,1,1],
  position: [0, 0.5, 0]  // lift so it sits ON the ground
})
```

### Collision/Physics

```javascript
const wall = app.create('prim', {
  type: 'box', size: [5, 3, 0.2],
  physics: 'static',    // null, 'static', or 'kinematic'
})
```

### Groups & Hierarchy

```javascript
const wheel = app.create('group')
const tire = app.create('prim', { type: 'cylinder', size: [0.5,0.5,0.2], color: 'black' })
wheel.add(tire)
const w2 = wheel.clone(true) // deep clone
app.add(wheel)
app.add(w2)
```

### Animation

```javascript
app.on('animate', delta => {
  box.rotation.y += 45 * DEG2RAD * delta  // 45 deg/sec
})

// Subscribe/unsubscribe for performance
const spin = delta => { box.rotation.y += delta }
app.on('animate', spin)    // start
app.off('animate', spin)   // stop
```

### Bloom/Glow

```javascript
const light = app.create('prim', {
  type: 'sphere', size: [0.2], color: 'red',
  emissive: 'red', emissiveIntensity: 5  // 0=none, 5=nice, 10=mega
})
```

### Opacity

```javascript
const glass = app.create('prim', {
  type: 'box', size: [2,2,0.1], color: 'blue', opacity: 0.5
})
```

### Interaction (Actions)

```javascript
const action = app.create('action', {
  label: 'Open Door',
  position: [0, 1, 0],
  onTrigger: () => { door.rotation.y = 90 * DEG2RAD }
})
app.add(action)
```

### Trigger Zones

```javascript
const zone = app.create('prim', {
  type: 'box', size: [4,4,4], opacity: 0,
  physics: 'static', trigger: true,
  onTriggerEnter: e => { if (e.isLocalPlayer) console.log('entered') },
  onTriggerLeave: e => { if (e.isLocalPlayer) console.log('left') }
})
```

### Networking (Multiplayer)

```javascript
if (world.isServer) {
  app.state.score = 0
  app.state.ready = true
  app.send('init', app.state)
}

if (world.isClient) {
  app.on('init', state => { /* initialize from server state */ })
}

// Send events
app.send('hit', { damage: 10 })  // client→server or server→all
app.on('hit', data => { /* handle */ })
```

### Configurable Props

```javascript
app.configure([
  { key: 'color', type: 'text', label: 'Color' },
  { key: 'size', type: 'number', label: 'Size' },
  { key: 'image', type: 'file', kind: 'texture', label: 'Image' },
  { key: 'speed', type: 'range', label: 'Speed' },
  { key: 'enabled', type: 'toggle', label: 'Enabled' },
])
// Access via props.color, props.size, etc.
```

### UI (World-Space Panels)

```javascript
const ui = app.create('ui', { width: 200, height: 100, billboard: 'y' })
const text = app.create('uitext', { value: 'Hello World', fontSize: 16, color: '#fff' })
ui.add(text)
app.add(ui)
```

### Audio

```javascript
const sound = app.create('audio', {
  src: 'asset://sound.mp3',
  volume: 0.5, loop: true, spatial: true
})
app.add(sound)
sound.play()
```

### Particles

```javascript
const particles = app.create('particles', {
  rate: 10, duration: 2,
  speed: [1, 3], size: [0.1, 0],
  color: ['#ff0000', '#ffff00'],
  gravity: -1
})
app.add(particles)
```

### Randomization (Deterministic)

```javascript
const rng = prng(42)           // seeded — same result on all clients
const val = rng(0, 100, 2)    // min, max, decimalPlaces
```

### Golden Rules

1. Match real-world dimensions (doors ~2m, tables ~0.75m, chairs ~0.45m seat)
2. Most prims need `physics: 'static'` or `'kinematic'` — players fall through without it
3. Never add animation/networking unless requested — it's expensive
4. Default to minimalistic blocky/voxel style unless asked otherwise
5. Avoid overlapping faces (z-fighting) — use small offsets
6. Stay under ~10K prims per app, no infinite loops

---

## Reference Repos (cloned locally)

These repos are cloned and available for browsing, copying assets, and studying patterns:

### 1. `repos/hyperfy-apps/` — 203 Working App Examples

**The most important reference.** 203 real Hyperfy V2 apps with source code.

```bash
# List all apps
ls repos/hyperfy-apps/v2/

# Read an app's script
cat repos/hyperfy-apps/v2/<app-name>/index.js

# Each app directory contains:
#   index.js          — the app script
#   <Name>.json       — blueprint definition
#   assets/           — models, textures, audio (if any)
```

**App categories by feature tags:** particles, audio, vehicle, npc, combat, camera, physics, ui, environment, animation, interaction, building, teleport, media-player, multiplayer, 3d-model

**Finding examples by feature:**
```bash
# Search for particle effects
grep -rl "particles" repos/hyperfy-apps/v2/*/index.js

# Search for networking/multiplayer
grep -rl "world.isServer" repos/hyperfy-apps/v2/*/index.js

# Search for physics
grep -rl "physics.*kinematic\|RigidBody" repos/hyperfy-apps/v2/*/index.js

# Search for UI panels
grep -rl "app.create.*ui" repos/hyperfy-apps/v2/*/index.js
```

### 2. `repos/hyperfy-docs/` — Official Documentation

Community-maintained docs covering worlds, avatars, controls, developer guides.

```bash
ls repos/hyperfy-docs/docs/
ls repos/hyperfy-docs/docs/developers/
```

### 3. `repos/hyperfy-recipes/` — V1 Example Patterns

Simple recipe apps (dialog, door, elevator, teleporter, trigger, web3 integration).

```bash
ls repos/hyperfy-recipes/apps/
```

### 4. `repos/eliza-3d-hyperfy-starter/` — AI Agent Plugin

ElizaOS plugin for running an AI agent inside a Hyperfy world. Useful for:
- Agent movement and navigation patterns
- Voice chat integration
- Emote system
- World perception (screenshot + vision LLM)

```bash
ls repos/eliza-3d-hyperfy-starter/src/
```

### 5. Full Scripting API Docs

```bash
# All node types
ls docs/scripting/nodes/types/

# World and App API
cat docs/scripting/world/World.md
cat docs/scripting/app/App.md

# Networking
cat docs/scripting/Networking.md

# Individual node docs
cat docs/scripting/nodes/types/Prim.md
cat docs/scripting/nodes/types/Particles.md
cat docs/scripting/nodes/types/UI.md
# etc.
```

---

## Database Schema

The world state lives in `Websites/hyperfy/world/db.sqlite`:

```
blueprints (id TEXT PK, data JSON, createdAt, updatedAt)
entities   (id TEXT PK, data JSON, createdAt, updatedAt)
config     (key TEXT PK, value TEXT)  — key="settings" for world metadata
users      (id TEXT PK, name, avatar, rank INT, createdAt)
```

**Ranks:** 0=visitor, 1=builder, 2=admin

**Blueprint data JSON:**
```json
{
  "id": "uuid", "version": 0, "name": "My App",
  "model": "asset://model.glb",    // optional 3D model
  "script": "asset://script.js",   // the app script
  "props": {},                       // default prop values
  "preload": false, "public": false, "locked": false,
  "unique": false, "scene": false, "disabled": false
}
```

**Entity data JSON:**
```json
{
  "id": "uuid", "type": "app", "blueprint": "blueprint-id",
  "position": [x, y, z], "quaternion": [x, y, z, w],
  "scale": [1, 1, 1],
  "mover": null, "uploader": null, "pinned": false, "state": {}
}
```

---

## Quick Patterns

### Spinning Glowing Cube
```javascript
const cube = app.create('prim', {
  type: 'box', size: [1,1,1], color: '#00ffff',
  emissive: '#00ffff', emissiveIntensity: 3,
  physics: 'kinematic', position: [0, 1, 0]
})
app.add(cube)
app.on('animate', d => { cube.rotation.y += d * 1.5 })
```

### Interactive Door
```javascript
let open = false
const door = app.create('prim', {
  type: 'box', size: [1, 2.2, 0.1], color: '#8B4513',
  physics: 'kinematic', position: [0, 1.1, 0]
})
const btn = app.create('action', {
  label: 'Toggle Door', position: [0, 1, 0.5],
  onTrigger: () => {
    open = !open
    door.rotation.y = open ? 90 * DEG2RAD : 0
  }
})
app.add(door)
app.add(btn)
```

### Multiplayer Score Counter
```javascript
if (world.isServer) {
  app.state.score = 0
  app.state.ready = true
  app.send('init', app.state)
  app.on('addPoint', () => {
    app.state.score++
    app.send('scoreUpdate', app.state.score)
  })
}
if (world.isClient) {
  let score = 0
  const ui = app.create('ui', { width: 100, height: 50, billboard: 'y', position: [0,2,0] })
  const txt = app.create('uitext', { value: 'Score: 0', fontSize: 20, color: '#fff' })
  ui.add(txt)
  app.add(ui)
  const btn = app.create('action', {
    label: '+1', position: [0,1,0],
    onTrigger: () => app.send('addPoint')
  })
  app.add(btn)
  app.on('init', s => { score = s.score; txt.value = 'Score: ' + score })
  app.on('scoreUpdate', s => { score = s; txt.value = 'Score: ' + score })
}
```

---

## .hyp File Format (Portable App Packages)

A `.hyp` file is a binary container that bundles a complete Hyperfy app: blueprint config + all assets (3D models, scripts, textures, audio) in one file. Drag-and-drop into a world to instantly place it.

### Binary Structure
```
[4 bytes: header size (uint32 LE)] [Header JSON] [Asset1 binary] [Asset2 binary] ...
```

### Header JSON
```json
{
  "blueprint": {
    "id": "string", "version": 0, "name": "App Name",
    "model": "asset://sha256hash.glb",
    "script": "asset://sha256hash.js",
    "props": {}, "preload": false, "public": false,
    "locked": false, "frozen": false, "unique": false,
    "scene": false, "disabled": false
  },
  "assets": [
    { "type": "model", "url": "asset://hash.glb", "size": 12345, "mime": "model/gltf-binary" },
    { "type": "script", "url": "asset://hash.js", "size": 678, "mime": "text/plain" }
  ]
}
```

### Creating a .hyp File

**Using the Python tool:**
```bash
# Inspect an existing .hyp
python3 repos/hyperfy-apps/scripts/hyp_tool.py info repos/hyperfy-apps/v2-hyp/SomeApp.hyp

# Extract a .hyp to source files
python3 repos/hyperfy-apps/scripts/hyp_tool.py unbundle repos/hyperfy-apps/v2-hyp/SomeApp.hyp /tmp/output/

# Bundle source files into a .hyp
python3 repos/hyperfy-apps/scripts/hyp_tool.py bundle /tmp/my-app/ /tmp/my-app.hyp
```

**Programmatically (Python):**
```python
import struct, json, hashlib

def create_hyp(blueprint, assets):
    """
    blueprint: dict (the blueprint JSON)
    assets: list of {'type','url','data':bytes,'mime'}
    """
    meta = []
    blob = b''
    for a in assets:
        meta.append({'type': a['type'], 'url': a['url'], 'size': len(a['data']), 'mime': a['mime']})
        blob += a['data']
    header = json.dumps({'blueprint': blueprint, 'assets': meta}, separators=(',',':')).encode()
    return struct.pack('<I', len(header)) + header + blob
```

### Deploying .hyp to a World

**Option 1: Collections folder (survives restarts)**
```bash
# Place .hyp files in the world's collections directory
mkdir -p Websites/hyperfy/world/collections/my-collection
echo '{"name":"My Collection","apps":["MyApp.hyp"]}' > Websites/hyperfy/world/collections/my-collection/manifest.json
cp my-app.hyp Websites/hyperfy/world/collections/my-collection/
# Restart Hyperfy — apps appear in the sidebar "Add" panel
```

**Option 2: Extract + upload via API**
```bash
# Extract .hyp to get assets + blueprint
python3 repos/hyperfy-apps/scripts/hyp_tool.py unbundle SomeApp.hyp /tmp/extracted/
# Upload each asset
for f in /tmp/extracted/assets/*; do
  curl -X POST https://3d-test-dev.jam-bot.com/api/upload -F "file=@$f"
done
# Then create via the AI API or insert blueprint into DB
```

**Option 3: Drag-and-drop** — in full-screen Hyperfy, drag a .hyp file onto the viewport (requires builder mode + pointer lock).

### Available .hyp Libraries

```bash
# 174 production apps (303MB) — models, vehicles, NPCs, particles, UI, environments
ls repos/hyperfy-apps/v2-hyp/

# Extra apps — plants, rain, neon signs, links
ls repos/hyp-apps-extra/

# Utility scripts — doors, elevators
ls repos/hyperfy-app-scripts/
cat repos/hyperfy-app-scripts/SimpleDoor.js

# Essentials — chair, door, elevator, sky
ls repos/hyperfy-essentials/
cat repos/hyperfy-essentials/door/index.js

# 203 extracted V2 app sources (script + blueprint + assets)
ls repos/hyperfy-apps/v2/
cat repos/hyperfy-apps/v2/<app-name>/index.js
```

### Finding Specific .hyp Apps
```bash
# Search by name
ls repos/hyperfy-apps/v2-hyp/ | grep -i "car\|vehicle\|door\|portal\|npc"

# Search extracted sources by feature
grep -rl "particles" repos/hyperfy-apps/v2/*/index.js
grep -rl "world.isServer" repos/hyperfy-apps/v2/*/index.js
grep -rl "app.create.*audio" repos/hyperfy-apps/v2/*/index.js
grep -rl "onTrigger" repos/hyperfy-apps/v2/*/index.js
```
