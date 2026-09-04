---
name: wan-video
description: "SUPERSEDED — do not render video on this VPS. All video jobs go to the Mac. See the video-to-mac skill."
metadata:
  version: 2.0.0
  superseded_by: video-to-mac
---

# wan-video — RETIRED AS A LOCAL RENDERER

**Mike, 2026-09-03:** *"any video tasks should always be sent to the mac — no VPS local video
tasks. You can take off wan or whatever skills for video and change them into instructions how
to send jobs to the mac properly with all info, assets and instructions."*

This skill used to tell you how to produce video **here**. It no longer does, because doing so
pegs CPU against 27 live client containers on a box already over its scheduled-work budget —
and in wan-video's case because the output quality was not worth it ("wan video sucks").

## Do this instead

**Read the `video-to-mac` skill and follow it.** It carries the full handoff format: what the
video is, look/feel, assets (with the path rules — the Mac reads /mnt/agent-mesh, NOT reliably
/mnt/clients), audio, deliver-to-and-who-is-waiting, and deadline.

Short form:

    AGENT_URI=<your-uri> mesh-send --to mac-claude@mesh --kind task \
      --subject "video: <what it is>" \
      --end-of-turn "mac-claude@mesh — reply expected" <<'REQ'
    WHAT / LOOK-FEEL / ASSETS / AUDIO / DELIVER TO / DEADLINE
    REQ

Client-facing agents: say nothing about the Mac, GPU, rendering or queues. "I'm on it", then a
video.

## The original instructions are not deleted

The previous version of this file is preserved beside it as
`SKILL.md.SUPERSEDED-by-video-to-mac-20260903T194234Z` — it remains accurate as a description of **how the
Mac does the work**, and is reference for whoever is doing the rendering. It is not permission
for this machine.
