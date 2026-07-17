---
name: maps
description: Build interactive Google Maps canvas pages — directions, route/trip planning, nearby places search, location display. Covers the /api/maps/config key endpoint, 5 copy-ready page templates, Directions/Places/Geocoding patterns, voice narration via speak(), and trip persistence.
---

# Maps — Interactive Map Canvas Pages

Read this skill for ANY map, directions, navigation, route planning, trip planning,
"near me", or "where is X" request. You build these as canvas pages (read the
`canvas-pages` skill first if you haven't — write to `/app/runtime/canvas-pages/`,
open with `[CANVAS:page-name]`).

## Which template for which request

| User says | Build |
|---|---|
| "get directions to X" / "how do I get to X" / "navigate to X" | **2. Directions** |
| "plan a trip" / "road trip" / route with multiple stops | **3. Route Planner** |
| "find restaurants near me" / "nearby gas stations / hotels" | **4. Nearby Places** |
| "show me X on a map" / "where is X" (a place/city/area) | **1. Map Explorer** |
| "show [business name]" / "directions to [one specific business]" | **5. Embed Map with Marker** |

For a quick spoken answer with NO page (user just wants the ETA), you can skip the
canvas entirely and call the server-side directions endpoint (section "Server-side
directions" below), then speak the summary.

---

## 1. Getting the API key (NEVER hardcode it)

The Google Maps key lives server-side. Every map page fetches it at runtime:

```javascript
// In canvas page JS — use authFetch when the auth bridge injected it (long sessions),
// plain fetch otherwise. /api/maps/config requires auth; authFetch carries the Clerk JWT.
async function loadMaps(libs) {
  const f = window.authFetch || fetch;
  const res = await f('/api/maps/config');
  const cfg = await res.json();
  if (!cfg.ok) throw new Error(cfg.error || 'Maps API key not configured');
  return new Promise((resolve, reject) => {
    window.__mapsReady = resolve;
    const s = document.createElement('script');
    s.src = 'https://maps.googleapis.com/maps/api/js?key=' + cfg.google_maps_api_key
          + '&libraries=' + (libs || 'places') + '&callback=__mapsReady&loading=async';
    s.onerror = () => reject(new Error('Google Maps JS failed to load'));
    document.head.appendChild(s);
  });
}
```

`maps.googleapis.com` is an ALLOWED external script source in canvas pages (it is a
legitimate API CDN, not one of the banned CSS frameworks).

- ❌ NEVER paste the API key into page HTML — always fetch from `/api/maps/config`.
- ❌ NEVER use localStorage for anything (trips, recent searches) — server API only.

## 2. Shared helpers — paste into EVERY map page

Every template below assumes this block exists. Templates 2–5 reference it with a
comment instead of repeating it — you must paste it in.

```javascript
// ---- SHARED MAP HELPERS ----
function speak(text) { window.parent.postMessage({type:'canvas-action', action:'speak', text:text}, '*'); }
function nav(page)   { window.parent.postMessage({type:'canvas-action', action:'navigate', page:page}, '*'); }

// Dark map style matching the canvas dark theme (skip if the tenant's ACTIVE-STYLE is light)
const DARK_MAP = [
  {elementType:'geometry', stylers:[{color:'#1a1d24'}]},
  {elementType:'labels.text.fill', stylers:[{color:'#8b95a7'}]},
  {elementType:'labels.text.stroke', stylers:[{color:'#0d1117'}]},
  {featureType:'poi', elementType:'labels', stylers:[{visibility:'off'}]},
  {featureType:'road', elementType:'geometry', stylers:[{color:'#2a2f3a'}]},
  {featureType:'road.highway', elementType:'geometry', stylers:[{color:'#3b4252'}]},
  {featureType:'water', elementType:'geometry', stylers:[{color:'#0f2438'}]},
  {featureType:'transit', elementType:'geometry', stylers:[{color:'#232733'}]},
  {featureType:'landscape', elementType:'geometry', stylers:[{color:'#161a21'}]}
];

function makeMap(el, center, zoom) {
  return new google.maps.Map(el, {
    center: center || {lat: 39.5, lng: -98.35},  // continental US fallback
    zoom: zoom || 4,
    styles: DARK_MAP,
    fullscreenControl: false, streetViewControl: false, mapTypeControl: false
  });
}

// Geolocate with graceful fallback — NEVER assume permission is granted
function locateUser(onOk, onFail) {
  if (!navigator.geolocation) return onFail('Geolocation not supported');
  navigator.geolocation.getCurrentPosition(
    p => onOk({lat: p.coords.latitude, lng: p.coords.longitude}),
    e => onFail(e.message || 'Location permission denied'),
    {timeout: 8000}
  );
}

// Fullscreen toggle — wire to a button with id="btn-fullscreen"
// CSS: #btn-fullscreen { position:absolute; top:10px; right:10px; z-index:20; ... }
// Icons: #ico-expand / #ico-compress SVGs toggled on fullscreenchange
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    (document.documentElement.requestFullscreen || document.documentElement.webkitRequestFullscreen || function(){}).call(document.documentElement);
  } else {
    (document.exitFullscreen || document.webkitExitFullscreen || function(){}).call(document);
  }
}
document.addEventListener('fullscreenchange', () => {
  const fs = !!document.fullscreenElement;
  const exp = document.getElementById('ico-expand');
  const com = document.getElementById('ico-compress');
  if (exp) exp.style.display = fs ? 'none' : '';
  if (com) com.style.display = fs ? '' : 'none';
});
// ---- END SHARED HELPERS ----
```

## 3. Page boilerplate rules (from canvas-pages skill — non-negotiable)

- `<meta name="viewport" content="width=device-width, initial-scale=1">`
- `<meta name="page-icon" content="interactive-map">` — this icon type exists, use it for map pages
- Dark background `#0d1117`, text `#e2e8f0`, accents blue `#3b82f6` / cyan `#06b6d4` — NO purple/pink
- All CSS/JS inline; check `ACTIVE-STYLE.md` first (canvas-pages skill Step 0) — if the
  tenant has a light style, drop `styles: DARK_MAP` and restyle the chrome to match
- **Map MUST fill 100% of the screen** — use `position:absolute; inset:0` on `#map`. NEVER use a side-panel or split layout where the map is only part of the screen. All controls (search, directions, lists) MUST float OVER the map using `position:absolute; z-index:>10`. This is the Google Maps pattern — the map is the background; UI overlays it.
- Results/directions panels slide up from the BOTTOM as an overlay sheet (`position:absolute; bottom:0; left:0; right:0; max-height:50vh; transform:translateY(100%)`), revealed by toggling a CSS class. Never squeeze the map.
- The map div needs an explicit height — use `position:absolute; inset:0` (do NOT use flex with map as `flex:1`)
- No emoji icons — inline SVG or plain text labels

---

## Template 1 — Basic Map Explorer

Full-screen map + search bar + locate-me + click-to-get-address. This one is shown
COMPLETE including the shared helpers — copy it as the base for everything else.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="page-icon" content="interactive-map">
<title>Map Explorer</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { height:100%; background:#0d1117; color:#e2e8f0; font-family:system-ui,sans-serif; }
  #map { position:absolute; inset:0; }
  .topbar { position:absolute; top:12px; left:12px; right:12px; z-index:5; display:flex; gap:8px; }
  .topbar input { flex:1; padding:12px 14px; border-radius:10px; border:1px solid #2a2f3a;
    background:#161a21ee; color:#e2e8f0; font-size:15px; outline:none; }
  .topbar input:focus { border-color:#3b82f6; }
  .btn { padding:12px 16px; border-radius:10px; border:1px solid #2a2f3a; background:#161a21ee;
    color:#06b6d4; font-size:14px; cursor:pointer; white-space:nowrap; }
  .btn:active { background:#1f2530; }
  #status { position:absolute; bottom:14px; left:12px; right:12px; z-index:5; background:#161a21ee;
    border:1px solid #2a2f3a; border-radius:10px; padding:10px 14px; font-size:14px; display:none; }
  .err { position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
    flex-direction:column; gap:10px; text-align:center; padding:24px; }
</style>
</head>
<body>
<div class="topbar">
  <input id="q" type="text" placeholder="Search a place or address..." autocomplete="off">
  <button class="btn" onclick="doSearch()">Search</button>
  <button class="btn" onclick="doLocate()" title="My location">Locate me</button>
</div>
<div id="map"></div>
<div id="status"></div>

<script>
/* ---- SHARED MAP HELPERS (section 2 of the maps skill) ---- */
function speak(text){window.parent.postMessage({type:'canvas-action',action:'speak',text:text},'*');}
function nav(page){window.parent.postMessage({type:'canvas-action',action:'navigate',page:page},'*');}
const DARK_MAP=[{elementType:'geometry',stylers:[{color:'#1a1d24'}]},{elementType:'labels.text.fill',stylers:[{color:'#8b95a7'}]},{elementType:'labels.text.stroke',stylers:[{color:'#0d1117'}]},{featureType:'poi',elementType:'labels',stylers:[{visibility:'off'}]},{featureType:'road',elementType:'geometry',stylers:[{color:'#2a2f3a'}]},{featureType:'road.highway',elementType:'geometry',stylers:[{color:'#3b4252'}]},{featureType:'water',elementType:'geometry',stylers:[{color:'#0f2438'}]},{featureType:'transit',elementType:'geometry',stylers:[{color:'#232733'}]},{featureType:'landscape',elementType:'geometry',stylers:[{color:'#161a21'}]}];
function makeMap(el,center,zoom){return new google.maps.Map(el,{center:center||{lat:39.5,lng:-98.35},zoom:zoom||4,styles:DARK_MAP,fullscreenControl:false,streetViewControl:false,mapTypeControl:false});}
function locateUser(onOk,onFail){if(!navigator.geolocation)return onFail('Geolocation not supported');navigator.geolocation.getCurrentPosition(p=>onOk({lat:p.coords.latitude,lng:p.coords.longitude}),e=>onFail(e.message||'Location permission denied'),{timeout:8000});}
async function loadMaps(libs){const f=window.authFetch||fetch;const res=await f('/api/maps/config');const cfg=await res.json();if(!cfg.ok)throw new Error(cfg.error||'Maps API key not configured');return new Promise((resolve,reject)=>{window.__mapsReady=resolve;const s=document.createElement('script');s.src='https://maps.googleapis.com/maps/api/js?key='+cfg.google_maps_api_key+'&libraries='+(libs||'places')+'&callback=__mapsReady&loading=async';s.onerror=()=>reject(new Error('Google Maps JS failed to load'));document.head.appendChild(s);});}
function toggleFullscreen(){if(!document.fullscreenElement){(document.documentElement.requestFullscreen||document.documentElement.webkitRequestFullscreen||function(){}).call(document.documentElement);}else{(document.exitFullscreen||document.webkitExitFullscreen||function(){}).call(document);}}
document.addEventListener('fullscreenchange',()=>{const fs=!!document.fullscreenElement;const exp=document.getElementById('ico-expand');const com=document.getElementById('ico-compress');if(exp)exp.style.display=fs?'none':'';if(com)com.style.display=fs?'':'none';});
/* ---- END SHARED HELPERS ---- */

let map, geocoder, marker;

function setStatus(html) {
  const el = document.getElementById('status');
  el.style.display = html ? 'block' : 'none';
  el.innerHTML = html || '';
}

function dropMarker(pos, title) {
  if (marker) marker.setMap(null);
  marker = new google.maps.Marker({map, position: pos, title: title || ''});
}

function doSearch() {
  const q = document.getElementById('q').value.trim();
  if (!q) return;
  geocoder.geocode({address: q}, (results, status) => {
    if (status === 'OK' && results[0]) {
      const r = results[0];
      map.setCenter(r.geometry.location); map.setZoom(14);
      dropMarker(r.geometry.location, r.formatted_address);
      setStatus(r.formatted_address);
    } else {
      setStatus('No results for "' + q + '"');
      speak("I couldn't find " + q + " on the map.");
    }
  });
}

function doLocate() {
  locateUser(pos => {
    map.setCenter(pos); map.setZoom(15);
    dropMarker(pos, 'You are here');
    setStatus('Centered on your location.');
  }, err => {
    setStatus('Location unavailable (' + err + '). Type an address in the search bar instead.');
  });
}

async function init() {
  try {
    await loadMaps('places');
    map = makeMap(document.getElementById('map'));
    geocoder = new google.maps.Geocoder();
    // Click anywhere → reverse-geocode to an address
    map.addListener('click', e => {
      geocoder.geocode({location: e.latLng}, (results, status) => {
        if (status === 'OK' && results[0]) {
          dropMarker(e.latLng, results[0].formatted_address);
          setStatus(results[0].formatted_address);
        }
      });
    });
    document.getElementById('q').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
    doLocate();  // best-effort — falls back to US view if denied
  } catch (err) {
    document.body.innerHTML = '<div class="err"><strong>Map loading failed</strong><span>' +
      err.message + '</span></div>';
    speak("I couldn't load the map. " + err.message);
  }
}
init();
</script>
</body>
</html>
```

---

## Template 2 — Directions / Navigation

Origin + destination + travel mode selector + step-by-step panel + route on map.
Narrates distance and ETA over voice.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="page-icon" content="interactive-map">
<title>Directions</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { height:100%; overflow:hidden; background:#0d1117; color:#e2e8f0; font-family:system-ui,sans-serif; }
  /* Map fills 100% of screen — NEVER use a side-panel that shrinks the map */
  #map { position:absolute; inset:0; }
  /* Search/controls float over the map at the top */
  .controls { position:absolute; top:0; left:0; right:0; z-index:20; padding:12px 12px 0;
    display:flex; flex-direction:column; gap:8px;
    background:linear-gradient(to bottom,rgba(13,17,23,0.95) 70%,transparent); }
  .controls input, .controls select { padding:12px 14px; border-radius:10px; border:1px solid #2a2f3a;
    background:#161a21ee; color:#e2e8f0; font-size:15px; outline:none; }
  .controls input:focus { border-color:#3b82f6; }
  .go { padding:13px; border-radius:10px; border:none; background:#3b82f6; color:#fff;
    font-size:15px; font-weight:700; cursor:pointer; }
  /* Results panel slides up from bottom like Google Maps */
  .panel { position:absolute; bottom:0; left:0; right:0; z-index:20;
    background:#11151cee; border-top:1px solid #2a2f3a; border-radius:16px 16px 0 0;
    max-height:50vh; display:flex; flex-direction:column; backdrop-filter:blur(8px);
    transform:translateY(100%); transition:transform 0.3s ease; }
  .panel.open { transform:translateY(0); }
  .handle { width:40px; height:4px; background:#3b4252; border-radius:2px; margin:10px auto 0;
    flex-shrink:0; cursor:pointer; }
  #summary { padding:12px 16px; font-size:15px; font-weight:600; color:#06b6d4;
    flex-shrink:0; border-bottom:1px solid #1a1f28; }
  #steps { flex:1; overflow-y:auto; padding:4px 0 16px; }
  .step { padding:10px 16px; font-size:13.5px; border-bottom:1px solid #1a1f2866; display:flex; gap:10px; }
  .step .n { color:#3b82f6; font-weight:700; min-width:22px; flex-shrink:0; }
  .step .d { color:#8b95a7; margin-left:auto; white-space:nowrap; font-size:12px; }
</style>
</head>
<body>
<div id="map"></div>
<div class="controls">
  <input id="origin" placeholder="From (blank = use my location)" autocomplete="off">
  <input id="dest" placeholder="To — destination address" autocomplete="off">
  <select id="mode">
    <option value="DRIVING">Driving</option>
    <option value="WALKING">Walking</option>
    <option value="BICYCLING">Cycling</option>
    <option value="TRANSIT">Transit</option>
  </select>
  <button class="go" onclick="route()">Get Directions</button>
</div>
<div class="panel" id="panel">
  <div class="handle" onclick="togglePanel()"></div>
  <div id="summary"></div>
  <div id="steps"></div>
</div>

<script>
/* PASTE the SHARED MAP HELPERS block from the maps skill here:
   speak, nav, DARK_MAP, makeMap, locateUser, loadMaps */

let map, dirService, dirRenderer;

async function resolveOrigin() {
  const v = document.getElementById('origin').value.trim();
  if (v && !/^my location$/i.test(v)) return v;
  return new Promise((res, rej) => locateUser(
    pos => res(pos),
    err => rej(new Error('Location denied — type a starting address instead'))));
}

async function route() {
  const dest = document.getElementById('dest').value.trim();
  if (!dest) { speak('Where do you want to go?'); return; }
  let origin;
  try { origin = await resolveOrigin(); }
  catch (e) { document.getElementById('summary').style.display='block';
              document.getElementById('summary').textContent = e.message; return; }

  const mode = document.getElementById('mode').value;
  dirService.route({
    origin, destination: dest,
    travelMode: google.maps.TravelMode[mode],
    provideRouteAlternatives: false
  }, (result, status) => {
    const sum = document.getElementById('summary');
    const stepsEl = document.getElementById('steps');
    if (status !== 'OK') {
      sum.style.display = 'block';
      sum.textContent = 'No route found (' + status + ')';
      stepsEl.innerHTML = '';
      speak('Sorry, I could not find a ' + mode.toLowerCase() + ' route to ' + dest + '.');
      return;
    }
    dirRenderer.setDirections(result);
    const leg = result.routes[0].legs[0];
    sum.style.display = 'block';
    sum.textContent = leg.distance.text + ' · about ' + leg.duration.text;
    stepsEl.innerHTML = leg.steps.map((s, i) =>
      '<div class="step"><span class="n">' + (i+1) + '</span><span>' +
      s.instructions + '</span><span class="d">' + s.distance.text + '</span></div>'
    ).join('');
    // Narrate the summary — the user is on a VOICE assistant
    speak('Route found. It is ' + leg.distance.text + ' and takes about ' +
          leg.duration.text + ' ' + mode.toLowerCase() + '. The directions are on screen.');
  });
}

async function init() {
  try {
    await loadMaps('places');
    map = makeMap(document.getElementById('map'), null, 5);
    dirService = new google.maps.DirectionsService();
    dirRenderer = new google.maps.DirectionsRenderer({
      map, panel: null,
      polylineOptions: {strokeColor: '#3b82f6', strokeWeight: 5}
    });
    document.getElementById('dest').addEventListener('keydown', e => { if (e.key==='Enter') route(); });
  } catch (err) {
    document.body.innerHTML = '<div style="padding:40px;text-align:center">Map loading failed: ' + err.message + '</div>';
    speak("I couldn't load the map for directions.");
  }
}
init();
</script>
</body>
</html>
```

**Pre-filling:** when the user already told you origin/destination in conversation,
set the input values in the HTML (`value="123 Main St"`) and call `route()` at the
end of `init()` so the page opens WITH the route drawn — don't make them re-type.

---

## Template 3 — Route Planner / Trip Planner

Multiple stops, reorder, numbered waypoint markers, total distance/time, save/load
trips server-side. Uses `optimizeWaypoints` when the user asks for "best order".

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="page-icon" content="interactive-map">
<title>Trip Planner</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { height:100%; background:#0d1117; color:#e2e8f0; font-family:system-ui,sans-serif; }
  .wrap { display:flex; height:100vh; }
  .panel { width:360px; background:#11151c; border-right:1px solid #2a2f3a; display:flex;
    flex-direction:column; padding:14px; gap:8px; overflow-y:auto; }
  input { padding:10px 12px; border-radius:8px; border:1px solid #2a2f3a; background:#161a21;
    color:#e2e8f0; font-size:14px; width:100%; outline:none; }
  .stop { display:flex; gap:6px; align-items:center; }
  .stop .idx { color:#f59e0b; font-weight:700; min-width:20px; }
  .stop button { background:#161a21; border:1px solid #2a2f3a; color:#8b95a7; border-radius:6px;
    padding:8px 10px; cursor:pointer; }
  .row { display:flex; gap:8px; }
  .btn { flex:1; padding:11px; border-radius:8px; border:none; background:#3b82f6; color:#fff;
    font-weight:600; cursor:pointer; }
  .btn.alt { background:#161a21; border:1px solid #2a2f3a; color:#06b6d4; }
  #totals { color:#10b981; font-size:14px; padding:6px 2px; }
  #map { flex:1; }
  /* On mobile map still fills screen; panel floats as bottom sheet */
  @media (max-width:640px){ .panel{width:100%;min-width:0;position:absolute;top:auto;bottom:0;right:0;border-right:none;border-top:1px solid #2a2f3a;border-radius:16px 16px 0 0;max-height:55vh} }
</style>
</head>
<body>
<div class="wrap">
  <div class="panel">
    <div id="stops"></div>
    <button class="btn alt" onclick="addStop('')">+ Add stop</button>
    <div class="row">
      <button class="btn" onclick="calc(false)">Route in order</button>
      <button class="btn alt" onclick="calc(true)">Best order</button>
    </div>
    <div id="totals"></div>
    <div class="row">
      <button class="btn alt" onclick="saveTrip()">Save trip</button>
      <button class="btn alt" onclick="loadTrip()">Load trip</button>
    </div>
  </div>
  <div id="map"></div>
</div>

<script>
/* PASTE the SHARED MAP HELPERS block from the maps skill here */

let map, dirService, dirRenderer, stops = ['', ''];
const TRIP_KEY = 'trip-planner';   // saved at /api/canvas/data/trip-planner.json

function render() {
  document.getElementById('stops').innerHTML = stops.map((s, i) =>
    '<div class="stop"><span class="idx">' + (i+1) + '</span>' +
    '<input value="' + s.replace(/"/g,'&quot;') + '" onchange="stops[' + i + ']=this.value"' +
    ' placeholder="' + (i===0 ? 'Start' : i===stops.length-1 ? 'End' : 'Stop ' + i) + '">' +
    (i>0 ? '<button onclick="moveUp(' + i + ')" title="Move up">&#8593;</button>' : '') +
    (stops.length>2 ? '<button onclick="removeStop(' + i + ')" title="Remove">&#215;</button>' : '') +
    '</div>').join('');
}
function addStop(v){ stops.push(v); render(); }
function removeStop(i){ stops.splice(i,1); render(); }
function moveUp(i){ [stops[i-1], stops[i]] = [stops[i], stops[i-1]]; render(); }

function calc(optimize) {
  const filled = stops.map(s => s.trim()).filter(Boolean);
  if (filled.length < 2) { speak('I need at least a start and an end point.'); return; }
  dirService.route({
    origin: filled[0],
    destination: filled[filled.length-1],
    waypoints: filled.slice(1,-1).map(w => ({location: w, stopover: true})),
    optimizeWaypoints: optimize,
    travelMode: google.maps.TravelMode.DRIVING
  }, (result, status) => {
    if (status !== 'OK') {
      document.getElementById('totals').textContent = 'No route found (' + status + ')';
      speak('I could not find a route through those stops.');
      return;
    }
    dirRenderer.setDirections(result);
    const legs = result.routes[0].legs;
    const meters = legs.reduce((a,l)=>a+l.distance.value,0);
    const secs   = legs.reduce((a,l)=>a+l.duration.value,0);
    const miles = (meters/1609.34).toFixed(0);
    const hrs = Math.floor(secs/3600), mins = Math.round((secs%3600)/60);
    const t = miles + ' mi total · ' + (hrs? hrs+'h ':'') + mins + 'm driving';
    document.getElementById('totals').textContent = t;
    speak('Trip planned: ' + filled.length + ' stops, ' + t + '.');
  });
}

async function saveTrip() {
  const f = window.authFetch || fetch;
  const res = await f('/api/canvas/data/' + TRIP_KEY + '.json', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({stops, saved_at: new Date().toISOString()})
  });
  const ok = res.ok;
  speak(ok ? 'Trip saved.' : 'Saving the trip failed.');
}

async function loadTrip() {
  const f = window.authFetch || fetch;
  const data = await (await f('/api/canvas/data/' + TRIP_KEY + '.json')).json();
  if (data.stops && data.stops.length) { stops = data.stops; render(); calc(false); }
  else speak('No saved trip found yet.');
}

async function init() {
  try {
    await loadMaps('places');
    map = makeMap(document.getElementById('map'), null, 4);
    dirService = new google.maps.DirectionsService();
    dirRenderer = new google.maps.DirectionsRenderer({map,
      polylineOptions:{strokeColor:'#3b82f6', strokeWeight:5}});
    render();
    loadTrip();  // restore last trip on open — server is the state store
  } catch (err) {
    document.body.innerHTML = '<div style="padding:40px;text-align:center">Map loading failed: ' + err.message + '</div>';
    speak("I couldn't load the trip planner map.");
  }
}
init();
</script>
</body>
</html>
```

**Trip persistence:** trips save to the SERVER at `/api/canvas/data/<name>.json`
(GET returns `{}` when nothing is saved yet; POST requires auth — `authFetch` handles
it). Use a distinct filename per trip if the user has several
(`trip-vegas.json`, `trip-cabin.json`). NEVER localStorage.

**DirectionsRenderer numbers waypoints A/B/C automatically.** If the user wants
numbered markers (1, 2, 3...), set `suppressMarkers: true` on the renderer and drop
your own `google.maps.Marker` per leg start with `label: String(i+1)`.

---

## Template 4 — Nearby Places Finder

Search by place type near the user (or a typed location). Markers + ratings + info windows.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="page-icon" content="interactive-map">
<title>Nearby Places</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { height:100%; background:#0d1117; color:#e2e8f0; font-family:system-ui,sans-serif; }
  .topbar { position:absolute; top:12px; left:12px; right:12px; z-index:5; display:flex; gap:8px; flex-wrap:wrap; }
  .topbar input, .topbar select { padding:11px 12px; border-radius:10px; border:1px solid #2a2f3a;
    background:#161a21ee; color:#e2e8f0; font-size:14px; outline:none; }
  .topbar input { flex:1; min-width:140px; }
  .btn { padding:11px 16px; border-radius:10px; border:none; background:#3b82f6; color:#fff;
    font-weight:600; cursor:pointer; }
  #map { position:absolute; inset:0; }
  #list { position:absolute; bottom:0; left:0; right:0; z-index:5; max-height:32vh; overflow-y:auto;
    background:#11151cee; border-top:1px solid #2a2f3a; display:none; }
  .place { padding:10px 14px; border-bottom:1px solid #1a1f28; font-size:14px; cursor:pointer; }
  .place:hover { background:#161a21; }
  .place .meta { color:#8b95a7; font-size:12.5px; }
  .place .rating { color:#f59e0b; }
</style>
</head>
<body>
<div class="topbar">
  <select id="type">
    <option value="restaurant">Restaurants</option>
    <option value="gas_station">Gas stations</option>
    <option value="hotel">Hotels</option>
    <option value="cafe">Coffee</option>
    <option value="pharmacy">Pharmacies</option>
    <option value="grocery_or_supermarket">Groceries</option>
    <option value="hospital">Hospitals</option>
  </select>
  <input id="near" placeholder="Near... (blank = my location)">
  <button class="btn" onclick="search()">Find</button>
</div>
<div id="map"></div>
<div id="list"></div>

<script>
/* PASTE the SHARED MAP HELPERS block from the maps skill here */

let map, places, geocoder, infoWin, markers = [];

function clearMarkers(){ markers.forEach(m => m.setMap(null)); markers = []; }

function showResults(results, center) {
  clearMarkers();
  map.setCenter(center); map.setZoom(13);
  const list = document.getElementById('list');
  list.style.display = 'block';
  list.innerHTML = '';
  results.slice(0, 20).forEach(p => {
    const m = new google.maps.Marker({map, position: p.geometry.location, title: p.name});
    m.addListener('click', () => {
      infoWin.setContent('<div style="color:#111;font-size:14px"><strong>' + p.name + '</strong><br>' +
        (p.vicinity || p.formatted_address || '') + '<br>' +
        (p.rating ? '★ ' + p.rating + ' (' + (p.user_ratings_total||0) + ')' : 'No ratings') + '</div>');
      infoWin.open(map, m);
    });
    markers.push(m);
    const row = document.createElement('div');
    row.className = 'place';
    row.innerHTML = '<strong>' + p.name + '</strong> ' +
      (p.rating ? '<span class="rating">★ ' + p.rating + '</span>' : '') +
      '<div class="meta">' + (p.vicinity || p.formatted_address || '') +
      (p.opening_hours && p.opening_hours.open_now !== undefined
        ? (p.opening_hours.open_now ? ' · Open now' : ' · Closed') : '') + '</div>';
    row.onclick = () => { map.panTo(p.geometry.location); map.setZoom(16);
                          google.maps.event.trigger(m, 'click'); };
    list.appendChild(row);
  });
  const label = document.getElementById('type').selectedOptions[0].text.toLowerCase();
  speak('I found ' + results.length + ' ' + label + ' nearby. The closest ones are on the map.');
}

function runNearby(center) {
  places.nearbySearch({
    location: center, radius: 5000,
    type: document.getElementById('type').value
  }, (results, status) => {
    if (status === google.maps.places.PlacesServiceStatus.OK && results.length) {
      showResults(results, center);
    } else {
      speak('I did not find any results in that area.');
    }
  });
}

function search() {
  const near = document.getElementById('near').value.trim();
  if (near) {
    geocoder.geocode({address: near}, (r, s) => {
      if (s === 'OK' && r[0]) runNearby(r[0].geometry.location);
      else speak("I couldn't find the area " + near + '.');
    });
  } else {
    locateUser(pos => runNearby(pos),
      () => speak('I could not get your location — type a city or address in the Near box.'));
  }
}

async function init() {
  try {
    await loadMaps('places');
    map = makeMap(document.getElementById('map'));
    places = new google.maps.places.PlacesService(map);
    geocoder = new google.maps.Geocoder();
    infoWin = new google.maps.InfoWindow();
  } catch (err) {
    document.body.innerHTML = '<div style="padding:40px;text-align:center">Map loading failed: ' + err.message + '</div>';
    speak("I couldn't load the places map.");
  }
}
init();
</script>
</body>
</html>
```

**Arbitrary queries:** for "find vegan sushi near downtown" use
`places.textSearch({query: 'vegan sushi near downtown Phoenix'}, cb)` instead of
`nearbySearch` — textSearch takes free text, nearbySearch takes a type + radius.
Pre-select the type / pre-fill the query from the conversation before writing the page.

---

## Template 5 — Embed Map with Marker (single business/location)

For "show me where X is" / "directions to [business]". Small, fast, one marker,
info card with address + a directions link. Geocode server-known info if you have
it, or let the page geocode the name.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="page-icon" content="interactive-map">
<title>Location</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { height:100%; background:#0d1117; color:#e2e8f0; font-family:system-ui,sans-serif; }
  #map { position:absolute; inset:0; }
  .card { position:absolute; left:12px; bottom:14px; right:12px; z-index:5; background:#11151cf2;
    border:1px solid #2a2f3a; border-radius:12px; padding:16px; max-width:420px; }
  .card h2 { font-size:17px; margin-bottom:4px; }
  .card .addr { color:#8b95a7; font-size:14px; margin-bottom:10px; }
  .card a, .card button { display:inline-block; margin-right:8px; padding:9px 14px; border-radius:8px;
    background:#3b82f6; color:#fff; text-decoration:none; font-size:14px; border:none; cursor:pointer; }
  .card .alt { background:#161a21; border:1px solid #2a2f3a; color:#06b6d4; }
</style>
</head>
<body>
<div id="map"></div>
<div class="card">
  <h2 id="name"></h2>
  <div class="addr" id="addr"></div>
  <a id="gmaps" target="_blank" rel="noopener">Open in Google Maps</a>
  <button class="alt" onclick="speak('Get me directions to ' + PLACE.name)">Get directions</button>
</div>

<script>
/* PASTE the SHARED MAP HELPERS block from the maps skill here */

// FILL THIS IN when writing the page — everything you already know from the
// conversation / the user's Office files / a places lookup:
const PLACE = {
  name: 'Example Coffee Co.',
  query: 'Example Coffee Co, 123 Main St, Phoenix AZ',  // used for geocoding + the external link
  phone: '(555) 123-4567'   // optional — shown if present
};

async function init() {
  try {
    await loadMaps('places');
    const map = makeMap(document.getElementById('map'), null, 14);
    const geocoder = new google.maps.Geocoder();
    document.getElementById('name').textContent = PLACE.name;
    document.getElementById('gmaps').href =
      'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(PLACE.query);
    geocoder.geocode({address: PLACE.query}, (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        map.setCenter(loc);
        const marker = new google.maps.Marker({map, position: loc, title: PLACE.name});
        document.getElementById('addr').textContent =
          results[0].formatted_address + (PLACE.phone ? ' · ' + PLACE.phone : '');
        const iw = new google.maps.InfoWindow({content:
          '<div style="color:#111"><strong>' + PLACE.name + '</strong><br>' +
          results[0].formatted_address + '</div>'});
        marker.addListener('click', () => iw.open(map, marker));
      } else {
        document.getElementById('addr').textContent = 'Location not found on the map.';
        speak("I couldn't pin " + PLACE.name + ' on the map, but the Google Maps link still works.');
      }
    });
  } catch (err) {
    document.body.innerHTML = '<div style="padding:40px;text-align:center">Map loading failed: ' + err.message + '</div>';
    speak("I couldn't load the map for " + PLACE.name + '.');
  }
}
init();
</script>
</body>
</html>
```

Note the "Get directions" button: it routes THROUGH THE CONVERSATION via `speak()` —
you'll hear the request and can then build the Directions page with origin = user's
location. That keeps one page simple instead of cramming both modes in.

---

## Server-side directions (no canvas page needed)

For a quick spoken answer ("how long to the airport?") call the Flask proxy from
your exec tool — the key stays server-side:

```bash
curl -s -X POST http://openvoiceui:5001/api/maps/directions \
  -H "Content-Type: application/json" -H "X-Agent-Key: $AGENT_API_KEY" \
  -d '{"origin":"Phoenix, AZ","destination":"Sky Harbor Airport","mode":"driving"}'
```

Body fields: `origin`, `destination` (required), `mode` (`driving`|`walking`|`bicycling`|
`transit` — `cycling` is auto-aliased), `waypoints` (list of strings), `optimize`
(true = let Google reorder waypoints). Response is Google's Directions JSON plus
`ok: true/false` (`false` + `status` field on ZERO_RESULTS / NOT_FOUND).

Pull the summary from `routes[0].legs[0].distance.text` and `.duration.text`, then
just say it: "About 22 minutes, 14 miles, mostly on the 202."

## Key API patterns cheat sheet

| Need | API |
|---|---|
| Address → coordinates | `new google.maps.Geocoder().geocode({address}, cb)` |
| Coordinates → address | `geocoder.geocode({location: latLng}, cb)` |
| Route between points | `DirectionsService.route({origin, destination, travelMode}, cb)` + `DirectionsRenderer` |
| Multi-stop route | add `waypoints: [{location, stopover:true}]`, `optimizeWaypoints: true` |
| Places by type near point | `PlacesService.nearbySearch({location, radius, type}, cb)` |
| Places by free text | `PlacesService.textSearch({query}, cb)` |
| Popup on marker | `new google.maps.InfoWindow({content}).open(map, marker)` |
| Custom marker icon | `new google.maps.Marker({map, position, icon: {url|path}, label})` |
| Remove marker | `marker.setMap(null)` — keep your own `markers[]` array |
| User's position | `navigator.geolocation.getCurrentPosition` (ALWAYS with a failure fallback) |

**InfoWindow content is rendered on Google's default WHITE background** — style its
inner HTML with dark text (`color:#111`), not your page's light-on-dark palette.

## Error handling — required in every map page

1. **Maps JS fails to load** (bad key, network, quota): catch in `init()`, replace the
   body with a plain "Map loading failed" message, and `speak()` the failure — plus, if
   you already know the answer (e.g. you ran the server-side directions call), speak
   the directions as text so the user still gets what they asked for.
2. **Geolocation denied**: never a dead end — show the text input for their location
   and say so: "I can't see your location — tell me where you're starting from."
3. **Route/geocode/places returns non-OK status**: show it in the UI AND narrate it
   ("No transit route found from A to B"). Google statuses worth handling:
   `ZERO_RESULTS` (no route/results), `NOT_FOUND` (bad address), `OVER_QUERY_LIMIT`
   (quota — tell the user to try again in a minute).
4. **Never retry in a loop** — one failure message, one spoken sentence, stop
   (TOOLS.md failing-tools rule applies inside canvas JS too).

## Voice behavior with map pages

- Announce the page as you open it: "Here's the route — 22 minutes by car. [CANVAS:directions-airport]"
- After the page computes something (route, place list), the page itself narrates via
  `speak()` — keep those one sentence, data-first (distance, ETA, count of results).
- Buttons that need YOU (get directions, add stop by voice) go through
  `speak('...')` postMessage so the request lands in the conversation.
- Don't read step-by-step directions aloud unless asked — summarize, the steps are on screen.

## Checklist before you're done (per canvas-pages skill)

1. Wrote page to `/app/runtime/canvas-pages/<name>.html` with viewport + `page-icon` meta
2. Opened it with `[CANVAS:<name>]` in your spoken response
3. Verified with `curl -s http://openvoiceui:5001/api/canvas/context`
4. Linted with `curl -s http://openvoiceui:5001/api/canvas/lint/<name>`
5. Checked the three viewports (desktop / 768px / 375px) — the panel+map layouts above
   already stack on mobile, keep that when you customize
