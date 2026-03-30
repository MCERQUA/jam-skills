---
name: threejs-canvas-integration
description: Three.js game and 3D development for OpenVoiceUI canvas pages. ALWAYS load this skill first when building any Three.js, WebGL, or 3D game as a canvas page. Covers import maps, canvas page boilerplate, asset loading, game state persistence, and postMessage integration.
---

# Three.js Canvas Page Integration

This skill covers how to build Three.js 3D games and experiences as OpenVoiceUI canvas pages. **Read this BEFORE using any other threejs-* skill.**

## Quick Reference: Two Approaches

| Approach | When to Use | How |
|----------|-------------|-----|
| **Single-file canvas page** | Simple games, demos, visualizations | Write complete HTML to `/app/runtime/canvas-pages/` |
| **Full project build** | Complex games with many assets, npm deps | Build in `~/Websites/`, copy output to canvas-pages |

## Approach 1: Single-File Canvas Page (Recommended)

### Import Map + ES Modules

Three.js is loaded from `cdn.jsdelivr.net` (whitelisted in the canvas CSP). Use an **import map** to resolve ES module imports:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My 3D Game</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0d1117; overflow: hidden; font-family: system-ui, sans-serif; }
  canvas { display: block; width: 100vw; height: 100vh; }
  #hud {
    position: fixed; top: 16px; left: 16px; z-index: 10;
    color: #e2e8f0; font-size: 14px;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
    pointer-events: none;
  }
  #hud .label { color: #64748b; font-size: 12px; }
  #hud .value { color: #3b82f6; font-weight: bold; }
  #loading {
    position: fixed; inset: 0; z-index: 100;
    background: #0d1117; display: flex;
    align-items: center; justify-content: center;
    color: #e2e8f0; font-size: 18px;
    flex-direction: column; gap: 12px;
  }
  #loading .bar {
    width: 200px; height: 4px; background: #1e293b;
    border-radius: 2px; overflow: hidden;
  }
  #loading .bar-fill {
    height: 100%; background: #3b82f6;
    width: 0%; transition: width 0.3s;
  }
</style>
<!-- Import Map: resolves bare "three" imports to jsdelivr CDN -->
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
  }
}
</script>
</head>
<body>
<div id="loading">
  <div>Loading 3D Engine...</div>
  <div class="bar"><div class="bar-fill" id="load-bar"></div></div>
</div>
<div id="hud">
  <div><span class="label">FPS</span> <span class="value" id="fps">--</span></div>
</div>

<script type="module">
// --- Three.js imports work normally thanks to the import map ---
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// --- Scene setup ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 3, 8);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.appendChild(renderer.domElement);

// --- Controls ---
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// --- Lighting ---
scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(5, 10, 5);
sun.castShadow = true;
scene.add(sun);

// --- Your game objects here ---
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.4, metalness: 0.3 });
const cube = new THREE.Mesh(geometry, material);
cube.castShadow = true;
cube.position.y = 1;
scene.add(cube);

// Ground
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(20, 20),
  new THREE.MeshStandardMaterial({ color: 0x1e293b })
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

// --- Hide loading screen ---
document.getElementById('loading').style.display = 'none';

// --- Animation loop ---
const clock = new THREE.Clock();
const fpsEl = document.getElementById('fps');
let frameCount = 0, fpsTime = 0;

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const elapsed = clock.getElapsedTime();

  // FPS counter
  frameCount++;
  fpsTime += delta;
  if (fpsTime >= 1) {
    fpsEl.textContent = Math.round(frameCount / fpsTime);
    frameCount = 0;
    fpsTime = 0;
  }

  // Update game objects
  cube.rotation.y += delta * 0.5;
  controls.update();
  renderer.render(scene, camera);
}
animate();

// --- Responsive ---
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
</script>
</body>
</html>
```

### Key Rules for Canvas Pages

1. **All CSS inline** in `<style>` tags — no external stylesheets
2. **Dark theme**: background `#0d1117`, text `#e2e8f0`, accent `#3b82f6`
3. **Import map MUST come before any `type="module"` script** — browser requirement
4. **Pin the Three.js version** in the import map (e.g., `@0.170.0`) — don't use `@latest`
5. **Never use localStorage** — persist state via server API (see Game State section)
6. **Assets load from same-origin** — `/pages/` for canvas dir, `/uploads/` for uploaded files

### Available Three.js Addons via Import Map

All addons from `three/addons/` are available. Common ones:

```javascript
// Controls
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { FirstPersonControls } from 'three/addons/controls/FirstPersonControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { FlyControls } from 'three/addons/controls/FlyControls.js';

// Loaders
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { FBXLoader } from 'three/addons/loaders/FBXLoader.js';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

// Post-processing
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';

// Utilities
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { Water } from 'three/addons/objects/Water.js';
```

## Asset Loading

### Loading Models (.glb, .gltf, .obj, .fbx)

Assets must be served from same-origin. Save them to `/app/runtime/canvas-pages/` or `/app/runtime/uploads/`.

```javascript
// 1. Agent saves model file to canvas-pages directory:
// exec("cp ~/my-model.glb /app/runtime/canvas-pages/models/spaceship.glb")

// 2. Load in Three.js using the /pages/ URL:
const loader = new GLTFLoader();
loader.load('/pages/models/spaceship.glb', (gltf) => {
  const model = gltf.scene;
  model.scale.set(0.5, 0.5, 0.5);
  scene.add(model);
});
```

### Loading Textures

```javascript
const textureLoader = new THREE.TextureLoader();

// From canvas-pages directory (saved by agent)
const texture = textureLoader.load('/pages/textures/metal.jpg');
texture.colorSpace = THREE.SRGBColorSpace;

// From uploads directory (uploaded by user)
const photo = textureLoader.load('/uploads/abc123.jpg');
```

### Loading HDR Environments

```javascript
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';

const rgbeLoader = new RGBELoader();
rgbeLoader.load('/pages/environments/studio.hdr', (texture) => {
  texture.mapping = THREE.EquirectangularReflectionMapping;
  scene.environment = texture;
  scene.background = texture;
});
```

### Generating Assets with AI

```bash
# Generate a texture with Gemini
exec("curl -s 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=$GEMINI_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{\"contents\":[{\"parts\":[{\"text\":\"Seamless tileable dark metal texture with rivets, game asset\"}]}],\"generationConfig\":{\"responseModalities\":[\"TEXT\",\"IMAGE\"]}}' \
  | python3 -c \"import sys,json,base64; d=json.load(sys.stdin)
for p in d['candidates'][0]['content']['parts']:
  if 'inlineData' in p:
    with open('/app/runtime/canvas-pages/textures/metal.png','wb') as f: f.write(base64.b64decode(p['inlineData']['data']))
    print('Saved')\"")
```

Then reference in HTML: `textureLoader.load('/pages/textures/metal.png')`

## Game State Persistence

**NEVER use localStorage.** Save game state to the server:

```javascript
// Save game state
async function saveGameState(state) {
  const authToken = window._canvasAuthToken;
  await fetch('/api/upload', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/octet-stream',
      'X-Filename': 'game-state.json',
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {})
    },
    body: JSON.stringify(state)
  });
}

// Load game state
async function loadGameState() {
  try {
    const resp = await fetch('/uploads/game-state.json');
    if (resp.ok) return await resp.json();
  } catch (e) { /* first run, no save file */ }
  return null;
}

// Alternative: use a dedicated file in canvas-pages
// Agent creates endpoint or uses exec to read/write JSON
```

## PostMessage Integration with OpenVoiceUI

Canvas pages can communicate with the parent OpenVoiceUI shell:

```javascript
// Tell the AI something (triggers voice response)
function tellAI(message) {
  window.parent.postMessage({
    type: 'canvas-action',
    action: 'speak',
    text: message
  }, '*');
}

// Navigate to another canvas page
function goToPage(pageId) {
  window.parent.postMessage({
    type: 'canvas-action',
    action: 'navigate',
    page: pageId
  }, '*');
}

// Open the canvas page menu
function openMenu() {
  window.parent.postMessage({
    type: 'canvas-action',
    action: 'menu'
  }, '*');
}

// Close canvas (return to voice mode)
function closeCanvas() {
  window.parent.postMessage({
    type: 'canvas-action',
    action: 'close'
  }, '*');
}

// Example: game over → tell AI the score
function onGameOver(score) {
  tellAI(`Game over! I scored ${score} points. What's the high score?`);
}
```

### Adding a Back/Menu Button (Recommended)

```javascript
// Floating menu button (doesn't interfere with 3D canvas)
const menuBtn = document.createElement('button');
menuBtn.textContent = '☰';
menuBtn.style.cssText = `
  position: fixed; top: 12px; right: 12px; z-index: 100;
  width: 40px; height: 40px; border-radius: 8px;
  background: rgba(30,41,59,0.8); color: #e2e8f0;
  border: 1px solid rgba(100,116,139,0.3);
  font-size: 20px; cursor: pointer;
  backdrop-filter: blur(8px);
`;
menuBtn.onclick = () => window.parent.postMessage({type:'canvas-action', action:'menu'}, '*');
document.body.appendChild(menuBtn);
```

## Approach 2: Full Project with npm (Complex Games)

For games with many files, npm dependencies, or build steps:

```bash
# 1. Create project
exec("mkdir -p ~/Websites/my-3d-game/src && cd ~/Websites/my-3d-game && pnpm init")

# 2. Install Three.js
exec("cd ~/Websites/my-3d-game && pnpm add three")

# 3. Install build tool (Vite is fastest)
exec("cd ~/Websites/my-3d-game && pnpm add -D vite")

# 4. Write source files (use write() tool)
# src/main.js, src/Game.js, index.html, vite.config.js, etc.

# 5. Build
exec("cd ~/Websites/my-3d-game && npx vite build --outDir dist")

# 6. Copy built output to canvas pages
exec("cp ~/Websites/my-3d-game/dist/index.html /app/runtime/canvas-pages/my-game.html")
exec("cp -r ~/Websites/my-3d-game/dist/assets /app/runtime/canvas-pages/my-game-assets/")
```

**Or serve as a dev site** (hot-reload during development):
```bash
# Set as active project for the webdev container
echo "my-3d-game" > ~/Websites/.active-project
# Now accessible at https://dev-<username>.jam-bot.com
# Show in canvas: [CANVAS_URL:https://dev-<username>.jam-bot.com]
```

### Vite Config for Three.js

```javascript
// vite.config.js
import { defineConfig } from 'vite';

export default defineConfig({
  base: '/pages/my-game-assets/',
  build: {
    outDir: 'dist',
    assetsDir: '.',
    rollupOptions: {
      output: {
        inlineDynamicImports: true
      }
    }
  }
});
```

## Using maxcode for Large Games

For games over ~500 lines, delegate to maxcode (MiniMax M2.7 high-speed coder):

```bash
exec("maxcode -p 'Build a complete 3D space shooter game as a single HTML file at /app/runtime/canvas-pages/space-shooter.html.

Requirements:
- Use Three.js loaded via import map from cdn.jsdelivr.net/npm/three@0.170.0
- Use <script type=\"module\"> for all game code
- Dark theme: background #0d1117, text #e2e8f0, accent #3b82f6
- Full viewport (100vw x 100vh), no scrollbars
- Spaceship with WASD/arrow controls, mouse aim
- Asteroid field with collision detection
- Particle effects for explosions and engine trails
- HUD showing score, health, level
- Progressive difficulty
- Include a loading screen
- Include OrbitControls import for debug camera
- NO localStorage — all state in memory only
- Add a menu button (top-right) that calls: window.parent.postMessage({type:\"canvas-action\", action:\"menu\"}, \"*\")
' --allowedTools 'Edit,Write,Read' 2>&1 | tail -20")
```

## Performance Tips for Canvas Pages

1. **Limit pixel ratio**: `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` — never go above 2x
2. **Use `requestAnimationFrame`** — never `setInterval` for render loops
3. **Dispose unused resources**: Call `.dispose()` on geometries, materials, textures when removing objects
4. **Instance meshes**: Use `THREE.InstancedMesh` for many copies of the same geometry (trees, particles, bullets)
5. **Use `BufferGeometry`**: All geometries in modern Three.js are already BufferGeometry
6. **Shadows are expensive**: Only enable on key lights, use `PCFSoftShadowMap`, keep shadow map size reasonable (1024 or 2048)
7. **Texture sizes**: Keep textures power-of-2 (512x512, 1024x1024). Resize before loading, not after.
8. **Frustum culling**: Enabled by default — don't disable it unless you have a specific reason
9. **Object pooling**: Reuse bullets, particles, enemies instead of creating/destroying
10. **`clock.getDelta()`**: Use delta time for consistent speed regardless of frame rate

## CSP Compatibility Notes

The canvas page CSP allows:
- `cdn.jsdelivr.net` for scripts (Three.js + addons) ✅
- `'unsafe-inline'` for inline scripts and styles ✅
- `'unsafe-eval'` for shader compilation ✅
- `'wasm-unsafe-eval'` for WebAssembly (Draco decoder, etc.) ✅
- `blob:` for workers and dynamic content ✅
- `https:` for images from any HTTPS source ✅
- Same-origin `fetch()` for loading models/textures from `/pages/` and `/uploads/` ✅

**NOT allowed:**
- `fetch()` to external domains (connect-src is restricted) — load all assets from `/pages/` or `/uploads/`
- External stylesheets (use inline `<style>` only)
- External fonts (use system fonts: `system-ui, -apple-system, sans-serif`)

## Common Game Patterns

### Keyboard Input

```javascript
const keys = {};
window.addEventListener('keydown', (e) => { keys[e.code] = true; });
window.addEventListener('keyup', (e) => { keys[e.code] = false; });

function update(delta) {
  const speed = 5 * delta;
  if (keys['KeyW'] || keys['ArrowUp']) player.position.z -= speed;
  if (keys['KeyS'] || keys['ArrowDown']) player.position.z += speed;
  if (keys['KeyA'] || keys['ArrowLeft']) player.position.x -= speed;
  if (keys['KeyD'] || keys['ArrowRight']) player.position.x += speed;
}
```

### Mouse Look / Camera Controls

**CRITICAL: PointerLockControls DOES NOT WORK in canvas iframes.** The browser's iframe security model blocks `requestPointerLock()` entirely — the click handler never fires. This applies to ALL iframes (sandboxed or not, same-origin or cross-origin).

**USE OrbitControls INSTEAD** — click-and-drag to rotate, scroll to zoom. No special browser permissions needed, works perfectly inside iframes:

```javascript
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxPolarAngle = Math.PI * 0.85; // prevent flipping under ground
```

**Distinguishing clicks from drags** (for interactive objects):
```javascript
let mouseDownPos = { x: 0, y: 0 };
renderer.domElement.addEventListener('mousedown', e => {
  mouseDownPos = { x: e.clientX, y: e.clientY };
});
renderer.domElement.addEventListener('mouseup', e => {
  const dx = e.clientX - mouseDownPos.x;
  const dy = e.clientY - mouseDownPos.y;
  if (Math.sqrt(dx*dx + dy*dy) < 5) {
    // This was a click, not a drag — handle object interaction
    handleClick(e);
  }
});
```

**NEVER use PointerLockControls** in canvas pages. They will silently fail with no error.

### Collision Detection (Simple Sphere)

```javascript
function checkCollision(obj1, obj2, radius1, radius2) {
  const dist = obj1.position.distanceTo(obj2.position);
  return dist < (radius1 + radius2);
}
```

### Particle System

```javascript
function createParticles(count) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 10;
    positions[i + 1] = Math.random() * 10;
    positions[i + 2] = (Math.random() - 0.5) * 10;
    colors[i] = Math.random();
    colors[i + 1] = Math.random();
    colors[i + 2] = 1;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.1,
    vertexColors: true,
    transparent: true,
    opacity: 0.8
  });

  return new THREE.Points(geometry, material);
}
```

### Scene Transitions

```javascript
// Fade to black, load new scene, fade in
function transitionScene(loadNewScene) {
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed; inset: 0; z-index: 200;
    background: #0d1117; opacity: 0;
    transition: opacity 0.5s;
    pointer-events: none;
  `;
  document.body.appendChild(overlay);

  requestAnimationFrame(() => {
    overlay.style.opacity = '1';
    setTimeout(() => {
      loadNewScene();
      overlay.style.opacity = '0';
      setTimeout(() => overlay.remove(), 500);
    }, 500);
  });
}
```

## File Organization for Game Assets

```
/app/runtime/canvas-pages/
├── my-game.html              ← Main game file
├── my-game-assets/           ← Subfolder for this game's assets
│   ├── models/
│   │   ├── player.glb
│   │   └── enemy.glb
│   ├── textures/
│   │   ├── ground.jpg
│   │   └── sky.hdr
│   └── audio/
│       ├── shoot.mp3
│       └── explosion.mp3
```

Load with: `loader.load('/pages/my-game-assets/models/player.glb', ...)`

## See Also

- `threejs-fundamentals` — Scene, Camera, Renderer, Object3D, math utilities
- `threejs-geometry` — All geometry types, BufferGeometry, InstancedMesh
- `threejs-materials` — PBR, shader materials, material properties
- `threejs-lighting` — Light types, shadows, IBL environments
- `threejs-textures` — Texture loading, UV mapping, render targets
- `threejs-animation` — Mixer, skeletal, morph targets, procedural animation
- `threejs-loaders` — GLTF, OBJ, FBX loading, Draco compression
- `threejs-shaders` — Custom GLSL shaders, extending materials
- `threejs-postprocessing` — Bloom, SSAO, DOF, custom effects
- `threejs-interaction` — Raycasting, controls, mouse/touch input
