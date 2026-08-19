---
name: custom-faces
description: "Create a custom FACE for the OpenVoiceUI interface — a fullscreen HTML/WebGL page that becomes the assistant's actual face (not a canvas page), reacting live to speech. Covers the postMessage contract (mood/amplitude/theme), meta tags, the promote endpoint, activation via profile face_mode, and where edits go afterward. TRIGGER: user asks for a new face, a custom face, an animated/visualizer face, 'make this page the face', or to change what the assistant looks like."
---

# Custom Faces — canvas page → the REAL face slot

The face-box renders custom faces in an **iframe** from `runtime/faces/` and pushes live
data into them via postMessage. Any HTML page can become the face in 3 steps.

## Step 0 — build the page (or reuse a canvas page)

Start from the official starter (shows the exact handler shape):

    exec("curl -s http://localhost:5001/api/custom-faces/template")

Requirements for the HTML:
1. **Meta tags** in `<head>` (the picker reads these):

       <meta name="face-name" content="My Face">
       <meta name="face-description" content="one line about it">
       <meta name="face-author" content="<your agent name>">

2. **postMessage listener** — the face-box posts `{mood, amplitude, theme}`:

       window.addEventListener('message', (e) => {
         const d = e.data || {};
         if (typeof d !== 'object') return;
         // amplitude: 0..1 while the assistant speaks — drive your visuals from it
         // mood: e.g. idle / listening / thinking / speaking — map to your states
         // theme: current UI theme/color — optional tint
       });

   A face that ignores amplitude looks dead while the assistant talks — always wire it.
3. Same canvas HTML rules as pages: **no external CDN scripts**, all CSS/JS inline.
   Fullscreen: style `html,body{margin:0;height:100%;overflow:hidden}`.

## Step 0.5 — TEST IT FIRST (performance gate — do not skip)

The face runs **permanently** in an iframe next to voice, STT, and TTS — a heavy face makes
the whole interface stutter and drains laptop/phone batteries. Before promoting:

1. **Open it as a canvas page first** (`[CANVAS:PAGE_ID]`) and let it run 2+ minutes while
   you keep talking — the interface must stay responsive with the page animating.
2. **Measure, don't eyeball** — add this temporary snippet to the page while testing (remove
   before promote), then read the numbers from the page or ask the user what it shows:

       let _f=0,_t0=performance.now();
       (function tick(){_f++;const el=performance.now()-_t0;
         if(el>5000){document.title=`${(_f/el*1000)|0}fps`;_f=0;_t0=performance.now();}
         requestAnimationFrame(tick)})();

   **Pass bar:** ≥50 fps sustained **during FULL-LOAD animation** — the face's heaviest
   visual state, not idle. Idle fps is a false pass: a face that idles at 60 and drops to
   20 the moment the assistant speaks fails. Force the heavy state while measuring:

       // temporary, alongside the fps snippet — simulates loud continuous speech
       setInterval(() => window.postMessage(
         { mood: 'speaking', amplitude: 0.9 + Math.random() * 0.1 }, '*'), 50);

   plus whatever else triggers your max effects (transients, state changes, theme shifts).

   **The measurement is ENFORCED, not honor-system:** collect per-second fps for ≥30s under
   that forced load and POST it — promote will REFUSE (HTTP 428) without a passing report:

       // full probe: measure 35s at full load, then auto-report
       const fpsSamples=[];let f=0,t0=performance.now();
       const amp=setInterval(()=>window.postMessage({mood:'speaking',amplitude:0.9+Math.random()*0.1},'*'),50);
       (function tick(){f++;const el=performance.now()-t0;
         if(el>=1000){fpsSamples.push(f*1000/el);f=0;t0=performance.now();}
         if(fpsSamples.length<35)requestAnimationFrame(tick);
         else{clearInterval(amp);fetch('/api/custom-faces/perf-report',{method:'POST',
           headers:{'Content-Type':'application/json'},
           body:JSON.stringify({page_id:location.pathname.split('/').pop().replace('.html',''),
             samples:fpsSamples,user_agent:navigator.userAgent})})
           .then(r=>r.json()).then(v=>{document.title=v.verdict;console.log('PERF',v);});}
       })();

   The response says PASS or FAIL with the measured fps_low vs the threshold (FACE_MIN_FPS,
   default 50). The report is pinned to the page's content hash — **edit the page, re-test**
   — and expires after 7 days.
   The rest of the UI (mic button, chat) must stay instant throughout. If the user is on a
   phone/kiosk (piguy Pi5!), test THERE — a desktop pass proves nothing about a Pi.
3. **Budget rules for a face** (stricter than a canvas page, because it never closes):
   - requestAnimationFrame ONLY — never setInterval for rendering.
   - **Pause when hidden:** on `document.visibilitychange` stop the RAF loop; also idle-down
     when amplitude has been 0 for a few seconds (no full-speed rendering while silent).
   - Cap device pixel ratio: `Math.min(devicePixelRatio, 1.5)` on canvas sizing — full DPR
     on a 4K screen is 4x the pixels for zero visible gain in a face box.
   - Particle/geometry counts: start LOW and raise until it looks good — not the reverse.
   - No unbounded arrays/history (memory grows forever in a never-closed page).
4. If it fails the bar: reduce counts/DPR first, re-test, THEN promote. Report the measured
   FULL-LOAD fps to the user when you declare the face ready — a number, not "it seems smooth."

## Step 1 — promote it into the face slot

Promotion is GATED on the perf attestation above: without a fresh passing report for the
CURRENT page bytes you get HTTP 428 with the reason (never measured / failed the bar /
stale / page changed since measurement). Fix, re-run the probe, retry. `{"force": true}`
exists for admins only and is logged — do not use it to skip the bar.

If the page lives in canvas-pages (id = filename without .html):

    exec("curl -s -X POST http://localhost:5001/api/custom-faces/promote -H 'Content-Type: application/json' -d '{\"canvas_page_id\": \"PAGE_ID\"}'")

This COPIES it to `runtime/faces/PAGE_ID.html` and registers it.
⚠️ **After promotion, edits go to `runtime/faces/PAGE_ID.html`** (in your workspace that is
`workspace/../runtime` — OVU path `/app/runtime/faces/`), NOT the canvas page. The copy
survives app updates (runtime is gitignored). You can also write a face there directly and
`GET /api/custom-faces` auto-registers it on the next list.

## Step 2 — activate it

    exec("curl -s -X PUT http://localhost:5001/api/profiles/default -H 'Content-Type: application/json' -d '{\"ui\": {\"face_mode\": \"custom:PAGE_ID\"}}'")

(`default` = active profile id; `GET /api/profiles` if the user runs named profiles.)
Or tell the user: **Face picker → your face's name** — same thing, and it persists
server-side per profile (all their devices follow).

## Verify (never report done without this)

    exec("curl -s http://localhost:5001/api/custom-faces")   # your face id listed?

Then ask the user to confirm the face switched, or check the profile:
`GET /api/profiles/default` → `ui.face_mode == "custom:PAGE_ID"`.

## Admin panel

Mike/admins can also promote + edit faces at `/admin` → Custom Faces tab (the promote
dropdown syncs the canvas manifest as of 2026-08-18 — fresh pages appear immediately).

## Gotchas
- The face iframe has the canvas CSP: **inline everything**; `style-src` has no `'self'`.
- `DELETE /api/custom-faces/<id>` archives to `.bak` — never hard-deletes.
- Promote is a snapshot copy — re-promote after canvas-page edits, or edit the faces/ copy.
