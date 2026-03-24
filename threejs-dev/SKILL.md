---
name: threejs-dev
description: Complete Three.js 3D development for OpenVoiceUI canvas pages. Covers scene setup, geometry, materials, lighting, textures, animation, interaction, shaders, post-processing, asset loading, and game patterns. Use for ANY Three.js, WebGL, or 3D canvas page work.
---

# Three.js Canvas Page Development

Complete reference for building Three.js 3D games and experiences as OpenVoiceUI canvas pages.

---

## 1. CANVAS PAGE BOILERPLATE

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
  #loading .bar { width: 200px; height: 4px; background: #1e293b; border-radius: 2px; overflow: hidden; }
  #loading .bar-fill { height: 100%; background: #3b82f6; width: 0%; transition: width 0.3s; }
</style>
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
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0d1117);

const camera = new THREE.PerspectiveCamera(75, innerWidth / innerHeight, 0.1, 1000);
camera.position.set(0, 3, 8);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

scene.add(new THREE.AmbientLight(0xffffff, 0.4));
const sun = new THREE.DirectionalLight(0xffffff, 1.2);
sun.position.set(5, 10, 5);
sun.castShadow = true;
scene.add(sun);

// --- Your game objects here ---
const cube = new THREE.Mesh(
  new THREE.BoxGeometry(1, 1, 1),
  new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.4, metalness: 0.3 })
);
cube.castShadow = true;
cube.position.y = 1;
scene.add(cube);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(20, 20),
  new THREE.MeshStandardMaterial({ color: 0x1e293b })
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

document.getElementById('loading').style.display = 'none';

const clock = new THREE.Clock();
const fpsEl = document.getElementById('fps');
let frameCount = 0, fpsTime = 0;

function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  frameCount++;
  fpsTime += delta;
  if (fpsTime >= 1) { fpsEl.textContent = Math.round(frameCount / fpsTime); frameCount = 0; fpsTime = 0; }
  cube.rotation.y += delta * 0.5;
  controls.update();
  renderer.render(scene, camera);
}
animate();

window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
</script>
</body>
</html>
```

### Key Rules
- All CSS inline in `<style>` — no external stylesheets
- Dark theme: bg `#0d1117`, text `#e2e8f0`, accent `#3b82f6`
- Import map MUST come before any `type="module"` script
- Pin Three.js version (e.g. `@0.170.0`) — never `@latest`
- **Never use localStorage** — persist state via server API
- Assets from same-origin: `/pages/` for canvas dir, `/uploads/` for uploaded files
- CSP allows: `cdn.jsdelivr.net` scripts, `unsafe-inline`, `unsafe-eval`, `wasm-unsafe-eval`, `blob:`, HTTPS images, same-origin fetch
- CSP blocks: external `fetch()`, external stylesheets, external fonts

### Menu Button (always include)
```javascript
const menuBtn = document.createElement('button');
menuBtn.textContent = '☰';
menuBtn.style.cssText = 'position:fixed;top:12px;right:12px;z-index:100;width:40px;height:40px;border-radius:8px;background:rgba(30,41,59,0.8);color:#e2e8f0;border:1px solid rgba(100,116,139,0.3);font-size:20px;cursor:pointer;backdrop-filter:blur(8px)';
menuBtn.onclick = () => window.parent.postMessage({type:'canvas-action',action:'menu'}, '*');
document.body.appendChild(menuBtn);
```

### PostMessage API
```javascript
// Tell AI something (triggers voice response)
window.parent.postMessage({ type: 'canvas-action', action: 'speak', text: 'Game over! Score: 100' }, '*');
// Navigate to another page
window.parent.postMessage({ type: 'canvas-action', action: 'navigate', page: 'page-id' }, '*');
// Open canvas menu
window.parent.postMessage({ type: 'canvas-action', action: 'menu' }, '*');
// Close canvas
window.parent.postMessage({ type: 'canvas-action', action: 'close' }, '*');
```

### Game State Persistence (NEVER localStorage)
```javascript
async function saveGameState(state) {
  const authToken = window._canvasAuthToken;
  await fetch('/api/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream', 'X-Filename': 'game-state.json',
      ...(authToken ? { 'Authorization': `Bearer ${authToken}` } : {}) },
    body: JSON.stringify(state)
  });
}
async function loadGameState() {
  try { const r = await fetch('/uploads/game-state.json'); if (r.ok) return r.json(); } catch(e) {}
  return null;
}
```

### Available Addons
```javascript
// Controls
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { FlyControls } from 'three/addons/controls/FlyControls.js';
import { FirstPersonControls } from 'three/addons/controls/FirstPersonControls.js';
// Loaders
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
// Post-processing
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
// Geometry/Objects
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
import { Sky } from 'three/addons/objects/Sky.js';
import { Water } from 'three/addons/objects/Water.js';
```

---

## 2. SCENE SETUP & CAMERAS

### PerspectiveCamera
```javascript
const camera = new THREE.PerspectiveCamera(75, innerWidth / innerHeight, 0.1, 1000);
camera.position.set(0, 5, 10);
camera.lookAt(0, 0, 0);
camera.updateProjectionMatrix(); // Call after changing fov/aspect/near/far
```

### OrthographicCamera
```javascript
const aspect = innerWidth / innerHeight;
const s = 10; // frustum size
const camera = new THREE.OrthographicCamera(-s*aspect/2, s*aspect/2, s/2, -s/2, 0.1, 1000);
```

### Scene
```javascript
scene.background = new THREE.Color(0x000000);  // or texture/cubeTexture
scene.environment = envMap;  // PBR environment map
scene.fog = new THREE.Fog(0xffffff, 1, 100);  // or FogExp2(color, density)
```

### WebGLRenderer Config
```javascript
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(w, h);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));  // Never above 2
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
```

### Animation Loop with Clock
```javascript
const clock = new THREE.Clock();
function animate() {
  requestAnimationFrame(animate);
  const delta = clock.getDelta();
  const elapsed = clock.getElapsedTime();
  // Use delta for frame-rate-independent motion
  mesh.rotation.y += delta * 0.5;
  controls.update();
  renderer.render(scene, camera);
}
animate();
```

### Responsive Resize
```javascript
window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
});
```

### Object3D Essentials
```javascript
obj.position.set(x, y, z);
obj.rotation.set(rx, ry, rz);  // Euler (radians)
obj.scale.set(sx, sy, sz);
obj.visible = false;
obj.add(child); obj.remove(child);
obj.traverse(child => { if (child.isMesh) child.castShadow = true; });
obj.getWorldPosition(new THREE.Vector3());
obj.layers.set(1);  // For selective rendering/raycasting
```

### MathUtils
```javascript
THREE.MathUtils.clamp(val, min, max);
THREE.MathUtils.lerp(a, b, t);
THREE.MathUtils.mapLinear(val, inMin, inMax, outMin, outMax);
THREE.MathUtils.degToRad(deg);
THREE.MathUtils.randFloat(min, max);
THREE.MathUtils.smoothstep(x, min, max);
```

### Cleanup
```javascript
mesh.geometry.dispose();
if (Array.isArray(mesh.material)) mesh.material.forEach(m => m.dispose());
else mesh.material.dispose();
texture.dispose();
renderer.dispose();
scene.remove(mesh);
```

---

## 3. GEOMETRY

### Built-in Shapes
```javascript
new THREE.BoxGeometry(w, h, d, wSeg, hSeg, dSeg);
new THREE.SphereGeometry(radius, wSeg, hSeg);
new THREE.PlaneGeometry(w, h, wSeg, hSeg);
new THREE.CylinderGeometry(radiusTop, radiusBot, height, radSeg);
new THREE.ConeGeometry(radius, height, radSeg);
new THREE.TorusGeometry(radius, tube, radSeg, tubSeg);
new THREE.TorusKnotGeometry(radius, tube, tubSeg, radSeg, p, q);
new THREE.CircleGeometry(radius, segments);
new THREE.RingGeometry(inner, outer, segments);
new THREE.CapsuleGeometry(radius, length, capSeg, radSeg);
new THREE.IcosahedronGeometry(radius, detail);  // Good cheap sphere
```

### Shape + ExtrudeGeometry
```javascript
const shape = new THREE.Shape();
shape.moveTo(0, 0); shape.lineTo(1, 0); shape.lineTo(1, 1); shape.lineTo(0, 1);
new THREE.ExtrudeGeometry(shape, { depth: 1, bevelEnabled: true, bevelThickness: 0.1, bevelSize: 0.1, bevelSegments: 3 });
```

### TubeGeometry
```javascript
const curve = new THREE.CatmullRomCurve3([
  new THREE.Vector3(-1,0,0), new THREE.Vector3(0,1,0), new THREE.Vector3(1,0,0)
]);
new THREE.TubeGeometry(curve, 64, 0.2, 8, false);
```

### TextGeometry
```javascript
import { FontLoader } from 'three/addons/loaders/FontLoader.js';
import { TextGeometry } from 'three/addons/geometries/TextGeometry.js';
new FontLoader().load('fonts/helvetiker_regular.typeface.json', font => {
  const geo = new TextGeometry('Hello', { font, size: 1, depth: 0.2, curveSegments: 12,
    bevelEnabled: true, bevelThickness: 0.03, bevelSize: 0.02, bevelSegments: 5 });
  geo.center();
  scene.add(new THREE.Mesh(geo, material));
});
```

### Custom BufferGeometry
```javascript
const geo = new THREE.BufferGeometry();
const verts = new Float32Array([-1,-1,0, 1,-1,0, 1,1,0, -1,1,0]);
const indices = new Uint16Array([0,1,2, 0,2,3]);
const normals = new Float32Array([0,0,1, 0,0,1, 0,0,1, 0,0,1]);
const uvs = new Float32Array([0,0, 1,0, 1,1, 0,1]);
geo.setAttribute('position', new THREE.BufferAttribute(verts, 3));
geo.setIndex(new THREE.BufferAttribute(indices, 1));
geo.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
geo.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
```

### Modify BufferGeometry at Runtime
```javascript
const pos = geo.attributes.position;
pos.setXYZ(index, x, y, z);
pos.needsUpdate = true;
geo.computeVertexNormals();
geo.computeBoundingBox();
```

### InstancedMesh (many copies, one draw call)
```javascript
const mesh = new THREE.InstancedMesh(geometry, material, 1000);
const dummy = new THREE.Object3D();
for (let i = 0; i < 1000; i++) {
  dummy.position.set(Math.random()*20-10, Math.random()*20-10, Math.random()*20-10);
  dummy.rotation.set(Math.random()*Math.PI, Math.random()*Math.PI, 0);
  dummy.scale.setScalar(0.5 + Math.random());
  dummy.updateMatrix();
  mesh.setMatrixAt(i, dummy.matrix);
}
mesh.instanceMatrix.needsUpdate = true;
// Optional per-instance colors:
for (let i = 0; i < 1000; i++) mesh.setColorAt(i, new THREE.Color(Math.random(), Math.random(), Math.random()));
mesh.instanceColor.needsUpdate = true;
scene.add(mesh);
```

### Points Cloud
```javascript
const geo = new THREE.BufferGeometry();
const pos = new Float32Array(1000 * 3);
for (let i = 0; i < 3000; i++) pos[i] = (Math.random()-0.5)*10;
geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
scene.add(new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.1, color: 0xffffff })));
```

### Merge Static Geometries
```javascript
import * as BufferGeometryUtils from 'three/addons/utils/BufferGeometryUtils.js';
const merged = BufferGeometryUtils.mergeGeometries([geo1, geo2, geo3]);
```

### Edges & Wireframe
```javascript
const edges = new THREE.LineSegments(new THREE.EdgesGeometry(boxGeo, 15), new THREE.LineBasicMaterial({ color: 0xffffff }));
```

---

## 4. MATERIALS

### Overview
| Material | Use Case | Lighting |
|----------|----------|----------|
| MeshBasicMaterial | Unlit, flat | No |
| MeshLambertMaterial | Matte, fast | Diffuse only |
| MeshStandardMaterial | **PBR (recommended)** | Full PBR |
| MeshPhysicalMaterial | Glass, car paint, fabric | PBR+ |
| MeshToonMaterial | Cel-shaded | Toon |
| ShaderMaterial | Custom GLSL | Custom |

### MeshStandardMaterial (PBR)
```javascript
const mat = new THREE.MeshStandardMaterial({
  color: 0xffffff,
  roughness: 0.5,           // 0=mirror, 1=diffuse
  metalness: 0.0,           // 0=dielectric, 1=metal
  map: colorTex,            // Albedo (SRGBColorSpace)
  roughnessMap: roughTex,   // Per-pixel roughness (Linear — DON'T set colorSpace)
  metalnessMap: metalTex,   // Per-pixel metalness (Linear)
  normalMap: normalTex,     // Surface detail (Linear)
  normalScale: new THREE.Vector2(1, 1),
  aoMap: aoTex,             // Ambient occlusion (requires uv2!)
  aoMapIntensity: 1,
  emissive: 0x000000, emissiveIntensity: 1, emissiveMap: emissiveTex,
  displacementMap: dispTex, displacementScale: 0.1,
  envMap: envTex, envMapIntensity: 1,
});
// aoMap needs: geometry.setAttribute('uv2', geometry.attributes.uv);
```

### MeshPhysicalMaterial
```javascript
// Glass
new THREE.MeshPhysicalMaterial({ color: 0xffffff, metalness: 0, roughness: 0,
  transmission: 1, thickness: 0.5, ior: 1.5 });
// Car paint
new THREE.MeshPhysicalMaterial({ color: 0xff0000, metalness: 0.9, roughness: 0.5,
  clearcoat: 1, clearcoatRoughness: 0.1 });
// Also supports: sheen (fabric), iridescence (soap bubbles), anisotropy (brushed metal)
```

### MeshToonMaterial
```javascript
const colors = new Uint8Array([0, 128, 255]);
const gradientMap = new THREE.DataTexture(colors, 3, 1, THREE.RedFormat);
gradientMap.minFilter = THREE.NearestFilter; gradientMap.magFilter = THREE.NearestFilter;
gradientMap.needsUpdate = true;
new THREE.MeshToonMaterial({ color: 0x00ff00, gradientMap });
```

### Common Material Properties
```javascript
mat.transparent = true; mat.opacity = 0.5;
mat.side = THREE.DoubleSide;  // FrontSide, BackSide, DoubleSide
mat.depthTest = true; mat.depthWrite = true;
mat.alphaTest = 0.5;  // Discard pixels below threshold
mat.blending = THREE.AdditiveBlending;  // Normal, Additive, Subtractive, Multiply
mat.wireframe = true;
```

---

## 5. LIGHTING & SHADOWS

### Light Types
| Light | Shadow | Cost |
|-------|--------|------|
| AmbientLight(color, intensity) | No | Very Low |
| HemisphereLight(sky, ground, intensity) | No | Very Low |
| DirectionalLight(color, intensity) | Yes | Low |
| PointLight(color, intensity, distance, decay) | Yes | Medium |
| SpotLight(color, intensity, distance, angle, penumbra, decay) | Yes | Medium |
| RectAreaLight(color, intensity, width, height) | No | High |

### DirectionalLight + Shadows
```javascript
const sun = new THREE.DirectionalLight(0xffffff, 1.5);
sun.position.set(5, 10, 5);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.near = 0.5; sun.shadow.camera.far = 50;
sun.shadow.camera.left = -10; sun.shadow.camera.right = 10;
sun.shadow.camera.top = 10; sun.shadow.camera.bottom = -10;
sun.shadow.bias = -0.0001;
sun.shadow.normalBias = 0.02;
scene.add(sun);
// Don't forget: renderer.shadowMap.enabled = true;
// mesh.castShadow = true; floor.receiveShadow = true;
```

### SpotLight
```javascript
const spot = new THREE.SpotLight(0xffffff, 1, 100, Math.PI/6, 0.5, 2);
spot.position.set(0, 10, 0);
spot.castShadow = true;
scene.add(spot);
```

### Three-Point Lighting Setup
```javascript
scene.add(new THREE.DirectionalLight(0xffffff, 1).position.set(5, 5, 5));   // Key
scene.add(new THREE.DirectionalLight(0xffffff, 0.5).position.set(-5, 3, 5)); // Fill
scene.add(new THREE.DirectionalLight(0xffffff, 0.3).position.set(0, 5, -5)); // Back
scene.add(new THREE.AmbientLight(0x404040, 0.3));
```

### HDR Environment (IBL) — canonical pattern
```javascript
import { RGBELoader } from 'three/addons/loaders/RGBELoader.js';
const pmrem = new THREE.PMREMGenerator(renderer);
pmrem.compileEquirectangularShader();
new RGBELoader().load('/pages/env.hdr', tex => {
  const envMap = pmrem.fromEquirectangular(tex).texture;
  scene.environment = envMap;
  scene.background = envMap;
  tex.dispose(); pmrem.dispose();
});
```

---

## 6. TEXTURES

### Color Space Rules (CRITICAL)
```javascript
colorTex.colorSpace = THREE.SRGBColorSpace;  // Color/albedo maps
// Data maps (normal, roughness, metalness, AO) — leave default (Linear). DO NOT set colorSpace.
```

### Configuration
```javascript
tex.wrapS = tex.wrapT = THREE.RepeatWrapping;  // or ClampToEdge, MirroredRepeat
tex.repeat.set(4, 4);
tex.offset.set(0.5, 0.5);
tex.rotation = Math.PI / 4; tex.center.set(0.5, 0.5);
tex.minFilter = THREE.LinearMipmapLinearFilter;  // Default, smooth
tex.magFilter = THREE.NearestFilter;  // Pixelated (retro games)
tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
```

### DataTexture
```javascript
const size = 256, data = new Uint8Array(size * size * 4);
for (let i = 0; i < size*size; i++) {
  const v = Math.random() * 255;
  data[i*4] = data[i*4+1] = data[i*4+2] = v; data[i*4+3] = 255;
}
const tex = new THREE.DataTexture(data, size, size);
tex.needsUpdate = true;
```

### CanvasTexture
```javascript
const canvas = document.createElement('canvas'); canvas.width = canvas.height = 256;
const ctx = canvas.getContext('2d');
ctx.fillStyle = 'red'; ctx.fillRect(0, 0, 256, 256);
const tex = new THREE.CanvasTexture(canvas);
// Set tex.needsUpdate = true when canvas content changes
```

### VideoTexture
```javascript
const video = document.createElement('video');
video.src = 'video.mp4'; video.loop = true; video.muted = true; video.play();
const tex = new THREE.VideoTexture(video);
tex.colorSpace = THREE.SRGBColorSpace;
```

### Render Target
```javascript
const rt = new THREE.WebGLRenderTarget(512, 512);
renderer.setRenderTarget(rt);
renderer.render(scene, camera);
renderer.setRenderTarget(null);
material.map = rt.texture;
```

---

## 7. LOADING ASSETS

### GLTF/GLB with Draco
```javascript
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const draco = new DRACOLoader();
draco.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
const gltf = new GLTFLoader();
gltf.setDRACOLoader(draco);

gltf.load('/pages/models/model.glb', g => {
  const model = g.scene;
  model.traverse(c => { if (c.isMesh) { c.castShadow = true; c.receiveShadow = true; } });
  // Center and scale
  const box = new THREE.Box3().setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  model.position.sub(center);
  model.scale.setScalar(1 / Math.max(size.x, size.y, size.z));
  scene.add(model);
  // Animations
  if (g.animations.length) {
    const mixer = new THREE.AnimationMixer(model);
    g.animations.forEach(clip => mixer.clipAction(clip).play());
    // Update mixer in animate loop: mixer.update(delta)
  }
});
```

### LoadingManager
```javascript
const manager = new THREE.LoadingManager();
manager.onProgress = (url, loaded, total) => {
  document.getElementById('load-bar').style.width = (loaded/total*100) + '%';
};
manager.onLoad = () => document.getElementById('loading').style.display = 'none';
const texLoader = new THREE.TextureLoader(manager);
const gltfLoader = new GLTFLoader(manager);
```

### Promise Wrapper
```javascript
const loadGLTF = url => new Promise((res, rej) => new GLTFLoader().load(url, res, undefined, rej));
const loadTex = url => new Promise((res, rej) => new THREE.TextureLoader().load(url, res, undefined, rej));
const loadHDR = url => new Promise((res, rej) => new RGBELoader().load(url, t => {
  t.mapping = THREE.EquirectangularReflectionMapping; res(t);
}, undefined, rej));
// const [model, tex, env] = await Promise.all([loadGLTF('m.glb'), loadTex('t.jpg'), loadHDR('e.hdr')]);
```

### Asset Paths
- Agent saves to `/app/runtime/canvas-pages/` → load via `/pages/`
- User uploads → load via `/uploads/`

---

## 8. ANIMATION

### AnimationMixer Core Loop
```javascript
const mixer = new THREE.AnimationMixer(model);
const action = mixer.clipAction(clip);
action.play();
// In animate(): mixer.update(delta);
```

### GLTF Animations
```javascript
const clips = gltf.animations;
const walkClip = THREE.AnimationClip.findByName(clips, 'Walk');
const action = mixer.clipAction(walkClip);
action.play();
```

### AnimationAction API
```javascript
action.loop = THREE.LoopRepeat;    // LoopOnce, LoopPingPong
action.clampWhenFinished = true;   // Hold last frame
action.timeScale = 1;              // Speed (negative = reverse)
action.weight = 1;                 // 0-1 blend weight
action.fadeIn(0.5).play();
action.fadeOut(0.5);
action1.crossFadeTo(action2, 0.5, true);
```

### Speed-Based Animation Blending
```javascript
const idle = mixer.clipAction(idleClip); idle.play();
const walk = mixer.clipAction(walkClip); walk.play();
const run = mixer.clipAction(runClip); run.play();
function updateAnims(speed) {
  if (speed < 0.1) { idle.setEffectiveWeight(1); walk.setEffectiveWeight(0); run.setEffectiveWeight(0); }
  else if (speed < 5) { const t = speed/5; idle.setEffectiveWeight(1-t); walk.setEffectiveWeight(t); run.setEffectiveWeight(0); }
  else { const t = Math.min((speed-5)/5, 1); idle.setEffectiveWeight(0); walk.setEffectiveWeight(1-t); run.setEffectiveWeight(t); }
}
```

### Skeletal — Find Bone, Attach Objects
```javascript
const skinned = model.getObjectByProperty('type', 'SkinnedMesh');
const handBone = skinned.skeleton.bones.find(b => b.name === 'RightHand');
handBone.add(weaponMesh);
weaponMesh.position.set(0, 0, 0.5);
```

### Spring Physics
```javascript
class Spring {
  constructor(stiffness = 100, damping = 10) { this.k = stiffness; this.d = damping; this.pos = 0; this.vel = 0; this.target = 0; }
  update(dt) {
    this.vel += (-this.k * (this.pos - this.target) - this.d * this.vel) * dt;
    this.pos += this.vel * dt;
    return this.pos;
  }
}
```

### Procedural Motion
```javascript
const t = clock.getElapsedTime();
mesh.position.y = Math.sin(t * 2) * 0.5;                    // Sine wave
mesh.position.y = Math.abs(Math.sin(t * 3)) * 2;            // Bounce
mesh.position.x = Math.cos(t) * 2; mesh.position.z = Math.sin(t) * 2;  // Circle
```

### Morph Targets
```javascript
mesh.morphTargetInfluences[0] = 0.5;  // By index
const idx = mesh.morphTargetDictionary['smile'];
mesh.morphTargetInfluences[idx] = 1;  // By name
```

---

## 9. INTERACTION

### Raycaster (click/tap detection)
```javascript
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
function onClick(e) {
  mouse.x = (e.clientX / innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(clickables);
  if (hits.length) console.log('Hit:', hits[0].object, 'at:', hits[0].point);
}
window.addEventListener('click', onClick);
// Touch: same coords from e.touches[0].clientX/clientY
```

### OrbitControls (full config)
```javascript
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
const ctrl = new OrbitControls(camera, renderer.domElement);
ctrl.enableDamping = true; ctrl.dampingFactor = 0.05;
ctrl.minPolarAngle = 0; ctrl.maxPolarAngle = Math.PI / 2;
ctrl.minDistance = 2; ctrl.maxDistance = 50;
ctrl.autoRotate = true; ctrl.autoRotateSpeed = 2;
ctrl.target.set(0, 1, 0);
// In animate(): ctrl.update();
```

### PointerLockControls (FPS)
```javascript
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
const plc = new PointerLockControls(camera, document.body);
document.body.addEventListener('click', () => plc.lock());
// Movement with WASD — see keyboard input below
```

### Keyboard Input
```javascript
const keys = {};
window.addEventListener('keydown', e => keys[e.code] = true);
window.addEventListener('keyup', e => keys[e.code] = false);
function update(delta) {
  const speed = 5 * delta;
  if (keys['KeyW'] || keys['ArrowUp']) player.position.z -= speed;
  if (keys['KeyS'] || keys['ArrowDown']) player.position.z += speed;
  if (keys['KeyA'] || keys['ArrowLeft']) player.position.x -= speed;
  if (keys['KeyD'] || keys['ArrowRight']) player.position.x += speed;
  if (keys['Space']) player.position.y += speed;
}
```

### Hover Effect
```javascript
let hovered = null;
window.addEventListener('mousemove', e => {
  mouse.x = (e.clientX / innerWidth) * 2 - 1;
  mouse.y = -(e.clientY / innerHeight) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(hoverables);
  if (hovered) { hovered.material.color.set(hovered.userData.origColor); document.body.style.cursor = 'default'; }
  if (hits.length) {
    hovered = hits[0].object;
    if (!hovered.userData.origColor) hovered.userData.origColor = hovered.material.color.getHex();
    hovered.material.color.set(0xff6600);
    document.body.style.cursor = 'pointer';
  } else hovered = null;
});
```

### World ↔ Screen Conversion
```javascript
// World to screen
function worldToScreen(pos, cam) {
  const v = pos.clone().project(cam);
  return { x: (v.x+1)/2 * innerWidth, y: (-(v.y-1))/2 * innerHeight };
}
// Screen to world (on ground plane)
function screenToWorld(sx, sy, cam, y=0) {
  const v = new THREE.Vector3((sx/innerWidth)*2-1, -(sy/innerHeight)*2+1, 0.5).unproject(cam);
  const dir = v.sub(cam.position).normalize();
  return cam.position.clone().add(dir.multiplyScalar((y - cam.position.y) / dir.y));
}
```

### Ray-Plane Intersection
```javascript
const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);  // Ground
const pt = new THREE.Vector3();
raycaster.setFromCamera(mouse, camera);
raycaster.ray.intersectPlane(plane, pt);
```

---

## 10. SHADERS

### ShaderMaterial
```javascript
const mat = new THREE.ShaderMaterial({
  uniforms: { time: { value: 0 }, color: { value: new THREE.Color(0xff0000) }, map: { value: texture } },
  vertexShader: `
    varying vec2 vUv;
    uniform float time;
    void main() {
      vUv = uv;
      vec3 pos = position;
      pos.z += sin(pos.x * 5.0 + time) * 0.1;  // Wave displacement
      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `,
  fragmentShader: `
    varying vec2 vUv;
    uniform vec3 color;
    uniform sampler2D map;
    void main() {
      vec4 tex = texture2D(map, vUv);
      gl_FragColor = vec4(color * tex.rgb, 1.0);
    }
  `,
  transparent: true, side: THREE.DoubleSide,
});
// Update: mat.uniforms.time.value = clock.getElapsedTime();
```

### Built-in Uniforms (auto-provided by ShaderMaterial)
```glsl
uniform mat4 modelMatrix, modelViewMatrix, projectionMatrix, viewMatrix;
uniform mat3 normalMatrix;
uniform vec3 cameraPosition;
attribute vec3 position, normal;
attribute vec2 uv;
```

### Uniform Types
```javascript
// JS → GLSL: number→float, Vector2→vec2, Vector3→vec3, Vector4→vec4,
// Color→vec3, Matrix3→mat3, Matrix4→mat4, Texture→sampler2D
```

### Fresnel Effect
```glsl
// In fragment shader (vNormal, vWorldPosition from vertex):
vec3 viewDir = normalize(cameraPosition - vWorldPosition);
float fresnel = pow(1.0 - dot(viewDir, vNormal), 3.0);
gl_FragColor = vec4(mix(baseColor, rimColor, fresnel), 1.0);
```

### Noise Functions
```glsl
float random(vec2 st) { return fract(sin(dot(st, vec2(12.9898, 78.233))) * 43758.5453); }
float noise(vec2 st) {
  vec2 i = floor(st), f = fract(st);
  float a = random(i), b = random(i + vec2(1,0)), c = random(i + vec2(0,1)), d = random(i + vec2(1,1));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}
```

### Extend Built-in Materials (onBeforeCompile)
```javascript
const mat = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
mat.onBeforeCompile = shader => {
  shader.uniforms.time = { value: 0 };
  shader.vertexShader = 'uniform float time;\n' + shader.vertexShader;
  shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>',
    `#include <begin_vertex>\ntransformed.y += sin(position.x * 10.0 + time) * 0.1;`);
  mat.userData.shader = shader;
};
// Update: if (mat.userData.shader) mat.userData.shader.uniforms.time.value = elapsed;
```

### Common Injection Points
```javascript
'#include <begin_vertex>'        // After position calculated
'#include <project_vertex>'      // After gl_Position
'#include <color_fragment>'      // After diffuse color
'#include <output_fragment>'     // Final output
```

### GLSL Built-in Functions
```glsl
// Math: abs, sign, floor, ceil, fract, mod, min, max, clamp, mix, step, smoothstep
// Trig: sin, cos, tan, asin, acos, atan, radians, degrees
// Exp: pow, exp, log, sqrt, inversesqrt
// Vector: length, distance, dot, cross, normalize, reflect, refract
// Texture: texture2D(sampler, coord)  [GLSL 1.0]
```

---

## 11. POST-PROCESSING

### EffectComposer Setup
```javascript
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
// Add effect passes... then in animate(): composer.render(); (NOT renderer.render)
```

### Bloom
```javascript
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 1.5, 0.4, 0.85);
// strength, radius, threshold
composer.addPass(bloom);
```

### FXAA
```javascript
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { FXAAShader } from 'three/addons/shaders/FXAAShader.js';
const fxaa = new ShaderPass(FXAAShader);
fxaa.material.uniforms['resolution'].value.set(1/innerWidth, 1/innerHeight);
composer.addPass(fxaa);
// Update on resize: fxaa.material.uniforms['resolution'].value.set(1/w, 1/h);
```

### SSAO
```javascript
import { SSAOPass } from 'three/addons/postprocessing/SSAOPass.js';
const ssao = new SSAOPass(scene, camera, innerWidth, innerHeight);
ssao.kernelRadius = 16; ssao.minDistance = 0.005; ssao.maxDistance = 0.1;
composer.addPass(ssao);
```

### Depth of Field
```javascript
import { BokehPass } from 'three/addons/postprocessing/BokehPass.js';
const dof = new BokehPass(scene, camera, { focus: 10, aperture: 0.025, maxblur: 0.01 });
composer.addPass(dof);
```

### Custom ShaderPass
```javascript
const CustomEffect = {
  uniforms: { tDiffuse: { value: null }, time: { value: 0 }, intensity: { value: 1.0 } },
  vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float time, intensity; varying vec2 vUv;
    void main() {
      vec2 uv = vUv;
      uv.x += sin(uv.y * 10.0 + time) * 0.01 * intensity;
      gl_FragColor = texture2D(tDiffuse, uv);
    }
  `
};
const customPass = new ShaderPass(CustomEffect);
composer.addPass(customPass);
```

### Chromatic Aberration
```javascript
const ChromAb = {
  uniforms: { tDiffuse: { value: null }, amount: { value: 0.005 } },
  vertexShader: `varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: `
    uniform sampler2D tDiffuse; uniform float amount; varying vec2 vUv;
    void main() {
      vec2 dir = vUv - 0.5; float dist = length(dir);
      float r = texture2D(tDiffuse, vUv - dir * amount * dist).r;
      float g = texture2D(tDiffuse, vUv).g;
      float b = texture2D(tDiffuse, vUv + dir * amount * dist).b;
      gl_FragColor = vec4(r, g, b, 1.0);
    }
  `
};
```

### Other Quick Effects
```javascript
import { FilmPass } from 'three/addons/postprocessing/FilmPass.js';
composer.addPass(new FilmPass(0.35, 0.5, 648, false));  // grain, scanlines

import { VignetteShader } from 'three/addons/shaders/VignetteShader.js';
const vig = new ShaderPass(VignetteShader); vig.uniforms['offset'].value = 1; vig.uniforms['darkness'].value = 1;

import { GlitchPass } from 'three/addons/postprocessing/GlitchPass.js';
composer.addPass(new GlitchPass());

import { OutlinePass } from 'three/addons/postprocessing/OutlinePass.js';
const outline = new OutlinePass(new THREE.Vector2(innerWidth, innerHeight), scene, camera);
outline.selectedObjects = [mesh1, mesh2]; outline.edgeStrength = 3;
```

### Resize Handling
```javascript
window.addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  composer.setSize(innerWidth, innerHeight);
  if (fxaa) fxaa.material.uniforms['resolution'].value.set(1/innerWidth, 1/innerHeight);
});
```

---

## 12. GAME PATTERNS & PERFORMANCE

### Collision Detection (Sphere)
```javascript
function collides(a, b, r1, r2) { return a.position.distanceTo(b.position) < r1 + r2; }
```

### Object Pooling
```javascript
const pool = []; const active = new Set();
function spawn() {
  const obj = pool.length ? pool.pop() : createNew();
  obj.visible = true; active.add(obj); return obj;
}
function recycle(obj) { obj.visible = false; active.delete(obj); pool.push(obj); }
```

### Performance Checklist
1. `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))` — never above 2
2. Use `requestAnimationFrame` — never `setInterval`
3. Call `.dispose()` on removed geometries, materials, textures
4. Use `InstancedMesh` for many copies (trees, bullets, particles)
5. Shadows: only on key lights, use PCFSoftShadowMap, mapSize 1024-2048
6. Textures: power-of-2 (512, 1024, 2048), resize before loading
7. Object pooling: reuse bullets/particles/enemies
8. Use `clock.getDelta()` for consistent speed regardless of framerate
9. Merge static geometries with `mergeGeometries`
10. Throttle raycasts on mousemove (20fps max)

### Axes Helper (Debug)
```javascript
scene.add(new THREE.AxesHelper(5));  // Red=X, Green=Y, Blue=Z
```

### LOD
```javascript
const lod = new THREE.LOD();
lod.addLevel(highMesh, 0); lod.addLevel(medMesh, 50); lod.addLevel(lowMesh, 100);
scene.add(lod);
```
