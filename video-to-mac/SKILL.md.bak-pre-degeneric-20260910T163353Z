---
name: video-to-mac
description: "How to hand ANY video job to the Mac. No agent on the VPS renders video — this is the only sanctioned path. Use for animation, music video, promo, HTML-to-video, image-to-video, any MP4/MOV/WebM output."
metadata:
  version: 1.2.0
---

# Video jobs go to the Mac. All of them.

## ⚠️ AUTOMATED single-shot requests (WO-8, 2026-09-10) — read this first if you are `wan-video-drain.sh` or a queue drop, not a live agent typing a request

The old automated lane — `wan-video-drain.sh` staging a job under
`/mnt/agent-mesh/mesh/video-jobs/<tenant>-<rid>/` and mesh-sending a task to `mac-claude@mesh` via
`route_to_mac()` — is **RETIRED**. The Mac's runner now REFUSES any task naming
`/mnt/agent-mesh/mesh/video-jobs/`. `route_to_mac()` stays on disk (never delete) but is not called
by anything any more.

Automated non-studio video asks (the mesh `wan-video-queue/` and the OVU Video Studio plugin's
`.wan-requests/`) are now staged as a **single-shot JobGroup** directly under
`/mnt/agent-mesh/mesh/studio-queue/<tenant>-<rid>/` — the SAME shape the Studio product uses
(`request.json` with `"profile":"single-shot"`, `episode.json`, one `shots/<rid>.json`, the still
under `assets/`). The Mac's one video drain (`com.jambot.studio-drain`) reads that directory
directly.

**Gate:** staging only happens once `/mnt/agent-mesh/mesh/studio-queue/.profiles/single-shot.accepted`
exists (mac-claude writes it when their drain accepts the profile). Until then, requests are held
in place with a `.held` sidecar and a `"status":"queued"` result — they are NOT sent to the Mac and
NOT staged. See `scripts/wan-video-drain.sh` on the VPS for the implementation.

**This does not change anything below** — a live agent typing a `mesh-send --to mac-claude@mesh
--kind task` request by hand (the handoff pattern in this doc) is unaffected; that is a different,
ad-hoc lane the Mac still accepts. This note only concerns the *automated* drain path.

---

**Mike, 2026-09-03:** *"any video tasks should always be sent to the mac — no VPS local video
tasks."* And on the image-to-video path specifically: *"wan video sucks."*

This binds **every** agent on this VPS: voice agents, SMS agents, tenant agents, desk workers,
sub-agents, coders. There is no size exception and no "just a quick one" exception.

**Remotion, ffmpeg, Chromium and the rest are installed here. That is not permission.** A render
pegs CPU for minutes against 27 live client containers on a box that already runs over its
scheduled-work budget. The Mac has the GPU and no client workload to damage.

---

## The handoff

    AGENT_URI=<your-uri> mesh-send --to mac-claude@mesh --kind task \
      --subject "video: <one line — what it is and who it's for>" \
      --end-of-turn "mac-claude@mesh — reply expected" <<'REQ'
    WHAT
      <the finished thing: length, aspect/format, where it will be shown, who sees it>

    LOOK / FEEL
      <style, pace, mood, reference links. If a persona owns it, name the persona —
       "in Kyle's voice" is a real instruction, not decoration.>

    ASSETS
      <ABSOLUTE paths under /mnt/agent-mesh/, or public URLs.
       The Mac demonstrably reads /mnt/agent-mesh (it publishes its own feeds there).
       Do NOT assume it can read /mnt/clients — that is unverified. If your asset lives
       under /mnt/clients, COPY it to /mnt/agent-mesh/mesh/handoff/<tenant>/ first and
       hand over that path. An asset the Mac cannot open is a job it cannot start.>

    AUDIO
      <track path/URL, voiceover text, or "none". If a voice is required, say whose.>

    DELIVER TO
      <exact path or URL where the finished file should land, AND who is waiting on it.
       Name the human and the channel — "Fitzy, by SMS on the BHB line" — so the Mac
       knows the reply is not just a file drop.>

    DEADLINE / URGENCY
      <a real one, or "no deadline". Never invent urgency you have not been given.>
    REQ

Then say so in your own voice. **You are not rendering it — but do not say that either.**

---

## If you are client-facing (voice, SMS, any agent a customer talks to)

Say nothing about the Mac, the GPU, rendering, queues, jobs or this skill. The person asked for
a video. They get *"I'm on it"* in your own voice, and later a video.

Do **not** promise a delivery time you have not been given by the Mac. "Soon as it's ready"
is honest; "in about ten minutes" is a promise you cannot keep and did not make.

---

## What NOT to run, ever, on this box

`npx remotion` · `remotion render` · `ffmpeg` producing MP4/MOV/WebM · headless-Chromium frame
capture · HyperFrames CLI · any image-to-video or text-to-video generator.

If a skill file shows you how to do one of these, it is describing what the **Mac** does. Reading
an instruction is not being authorised to run it.

**The only exceptions:** you ARE `mac-claude@mesh`, or a human has told you *in this session* to
render locally. A previous session's instruction does not carry.

---

## What the Mac can actually make (2026-09-07 — say what you need, not how)

You do not choose the tool; the Mac does. But naming the SHAPE saves a round trip:

| you want | the Mac's lane | realistic turnaround per finished clip |
|---|---|---|
| motion graphics, kinetic type, data/brand cards, templated social cuts | Remotion (CPU) | minutes |
| live-action-feeling film with SOUND generated together with picture — a person or mascot who **speaks** | MiniMax H3 on the RTX 3090 | ~15 min per 8.7 s at 1024x576; ~25 min at 1344x768 |
| a character intro / mascot bumper from existing title art | H3 `character-intro` scenario | ~15 min |
| an image made to move | H3 pinned from that image | ~15 min |

🔴 **H3 generates PICTURE AND AUDIO in one pass.** That means dialogue is not dubbed on
afterwards — the model casts the voice and animates the mouth together. Consequences for what you
ask for:
- **Give the exact words** you want spoken. A paraphrase becomes a different line.
- **Describe the VOICE** (age, weight, pace, texture) if it matters — with no reference audio the
  model casts from your description alone, and two characters described similarly will converge
  into one voice. Range and texture separate them; pitch alone does not.
- **Keep a line short for a short clip.** MiniMax's own guidance: a long speech in a three-second
  shot degrades quality and lip-sync. Roughly one sentence per 3 s of clip.
- **Two characters CAN both speak in one shot.** Say who speaks first and what each says.
- Expect ~8.7 s per generation. Longer pieces are several generations cut together, so ask for
  the CUT, not one long take.

**Aspect/resolution:** H3's native ceiling is 1344x768 (16:9). Vertical and square are produced by
framing and post, not by asking H3 for a 9:16 native render.

**What H3 is wrong for:** anything with on-screen text you need to be legible (it re-draws small
type as mush), logos that must be pixel-exact, and before/after claims. Those are Remotion's job,
or a real photo.

---

## Verifying what comes back

Use the `render-verify` skill on the returned file. A file that exists and has valid metadata is
not proof it plays — that skill exists because metadata-valid, visually-broken renders shipped
before. Verify the artifact, not the receipt.
