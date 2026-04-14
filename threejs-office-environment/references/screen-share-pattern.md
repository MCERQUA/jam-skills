# Screen Share via CanvasTexture

Reusable pattern for showing live screen share content on any 3D surface.

## Setup Per Screen

Each screen needs its own set of variables — they are fully independent:

```javascript
const screenCanvas = document.createElement('canvas');
screenCanvas.width = 640;
screenCanvas.height = 360;
const screenCtx = screenCanvas.getContext('2d');
const screenTexture = new THREE.CanvasTexture(screenCanvas);
const screenMat = new THREE.MeshBasicMaterial({ map: screenTexture });
let screenStream = null;
let screenVideo = null;
let screenSharing = false;
```

## Apply to 3D Surface

Replace the static screen material with the CanvasTexture material:

```javascript
// The display plane sits slightly in front of the frame
const display = new THREE.Mesh(new THREE.PlaneGeometry(width, height), screenMat);
display.position.z = 0.025; // Slightly in front of monitor frame
monitorGroup.add(display);
```

## Idle Animation

Show an animated screen when not sharing:

```javascript
function drawIdleScreen(time) {
  const grad = screenCtx.createLinearGradient(0, 0, screenCanvas.width, screenCanvas.height);
  grad.addColorStop(0, '#1e3a5f');
  grad.addColorStop(1, '#0f172a');
  screenCtx.fillStyle = grad;
  screenCtx.fillRect(0, 0, screenCanvas.width, screenCanvas.height);
  screenCtx.fillStyle = 'rgba(59,130,246,0.5)';
  screenCtx.font = 'bold 20px system-ui';
  screenCtx.textAlign = 'center';
  screenCtx.fillText('Click to Share Screen', screenCanvas.width/2, screenCanvas.height/2);
  screenTexture.needsUpdate = true;
}
```

## Start/Stop Share

```javascript
function startScreenShare() {
  if (screenSharing) { stopScreenShare(); return; }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
    screenCtx.fillStyle = 'rgba(255,255,255,0.8)';
    screenCtx.font = 'bold 20px system-ui';
    screenCtx.textAlign = 'center';
    screenCtx.fillText('Screen share not supported', screenCanvas.width/2, screenCanvas.height/2);
    screenTexture.needsUpdate = true;
    return;
  }
  navigator.mediaDevices.getDisplayMedia({ video: { width: 1280, height: 720 }, audio: false })
    .then(stream => {
      screenStream = stream;
      screenVideo = document.createElement('video');
      screenVideo.srcObject = stream;
      screenVideo.play();
      screenSharing = true;
      function drawFrame() {
        if (!screenSharing) return;
        screenCtx.drawImage(screenVideo, 0, 0, screenCanvas.width, screenCanvas.height);
        screenTexture.needsUpdate = true;
        requestAnimationFrame(drawFrame);
      }
      drawFrame();
      stream.getVideoTracks()[0].addEventListener('ended', () => stopScreenShare());
    })
    .catch(() => {});
}

function stopScreenShare() {
  if (screenStream) { screenStream.getTracks().forEach(t => t.stop()); screenStream = null; }
  if (screenVideo) { screenVideo.srcObject = null; screenVideo = null; }
  screenSharing = false;
}
```

## Make Clickable

Add to INTERACTIVE_OBJECTS and wire userData:

```javascript
display.userData = { name: 'Monitor Name', startShare: startScreenShare };
INTERACTIVE_OBJECTS.push(display);
```

The click detection (mouseup with < 5px drag distance) calls `userData.startShare()` on the hit object.

## Animate

In the animation loop:

```javascript
if (!screenSharing) drawIdleScreen(time);
```

## Button Alternative

For a HUD button instead of (or in addition to) click-on-3D-object:

```html
<button id="screen-share-btn">Share Screen</button>
```
```javascript
document.getElementById('screen-share-btn').addEventListener('click', () => {
  startScreenShare();
});
// Update button text:
// On start: document.getElementById('screen-share-btn').textContent = 'Stop Sharing';
// On stop: document.getElementById('screen-share-btn').textContent = 'Share Screen';
```
