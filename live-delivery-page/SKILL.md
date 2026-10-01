---
name: live-delivery-page
description: One URL per in-progress job that fills in as the work lands. Slots are seeded from the shot list / plan BEFORE the first render, each slot flips the moment its artifact is delivered, and the page re-reads a JSON manifest every 30 s, so an empty slot reads as a missing beat, not as no progress. Static canvas page + JSON manifest in the tenant's uploads, stdlib Python writer, no keys. TRIGGER when a job produces several artifacts over time (video shots, a set of stills, voice takes, audio stems, report sections) and a person or client agent should watch it assemble, or when someone asks "send me a link I can check as it goes". DO NOT TRIGGER for one finished file (send its /uploads/ URL), or as a replacement for the lane's real delivery (this is an extra, in-progress surface).
---

# Live delivery page

**The rule in one line:** *one URL per job in progress; seed every slot from the plan before the
first artifact exists, flip each slot the moment its file is delivered, never batch the flips.*

Needs: a served uploads dir (every tenant has one), a canvas-pages dir, python3 (stdlib only).
No keys, no build step.

## Why

- **The viewer watches the piece assemble instead of waiting for a batch.** First used on a
  voice-casting job: the operator checked each take as it rendered and asked for the pattern to
  become the standard ("this worked well, I could check clips as they generated to fill the story").
- **An empty slot is information.** Because every slot exists from the start, with a line saying
  what it is FOR, a gap reads as "beat 4 is not done yet", not as "nothing is happening".
- **One call per artifact is the whole delivery.** The page holds no content. It derives its
  manifest from its own filename (`/pages/<job>.html` reads `/uploads/<job>.json`), so a new
  artifact never means rebuilding or re-sending anything.

## When NOT to use it

- **One finished file.** Send its `/uploads/` URL.
- **Instead of the real delivery.** Whatever your lane owes (the client's uploads + index row, a
  Dropzone copy, a mesh reply) is still owed. This page is a third surface on top.
- **Never as a Claude artifact.** The page is a canvas page on the tenant's own domain
  (PROTOCOL §10 rule 12). Never make it public on your own either (`canvas-page-visibility`:
  public only when a human asks).

## The two files

| | container path | VPS host path | browser URL |
|---|---|---|---|
| **manifest** (the data) | `/app/runtime/uploads/<job>.json` | `/mnt/clients/<t>/openvoiceui/uploads/<job>.json` | `/uploads/<job>.json`: **200, no login** |
| **page** (the shell) | `/app/runtime/canvas-pages/<job>.html` | `/mnt/clients/<t>/openvoiceui/canvas-pages/<job>.html` | `/pages/<job>.html`: **login-gated** |

- 🔴 **The manifest answers without a login** (measured 2026-09-30 on a tenant: 200,
  `text/plain`, `attachment`, `no-store`; the page's `fetch()` reads it fine). Anyone holding
  the URL can read titles, labels, notes and the finding. Write nothing there you would not put in
  an `/uploads/` URL. The artifacts themselves are no-login `/uploads/` URLs anyway.
- `uploads/` can never host the PAGE: HTML there is served `text/plain` + `sandbox` and downloads
  as a file. Assets and the manifest live in uploads; the page lives in canvas-pages.

## The writer: `live_delivery.py`

The only writer. Never hand-edit a manifest: the page trusts it to be valid.

Where the job lives, pick one:
- **inside a tenant container:** nothing; it finds `/app/runtime/uploads` + `canvas-pages`.
- **on the VPS host:** `--tenant <slug>` (also prints `https://<slug>.jam-bot.com/...` URLs).
- **a rig off the VPS:** `--tenant <slug> --ssh <user@vps>` runs the same reads/writes over ssh.
- **anything else served:** `--uploads DIR --pages DIR [--base-url URL]`.

```bash
LD=/mnt/shared-skills/live-delivery-page/live_delivery.py   # VPS host: /mnt/system/base/skills/live-delivery-page/

# 1. BEFORE the first render: every slot, from the plan (a count works too: --seed 8)
python3 $LD --job <slug> --seed shots.json --title "<what this is>" --ask "Reply with the number you want."
# 2. the page shell, once
python3 $LD --job <slug> --publish-page
# 3. per artifact, the MOMENT it is delivered (deliver the file to uploads first)
python3 $LD --job <slug> --set 1 --status rendering
python3 $LD --job <slug> --set 1 --status ready --file <name.mp4> [--measure duration_s=8.7] [--note "..."]
python3 $LD --job <slug> --set 2 --status failed --note "why"          # a roll that died
python3 $LD --job <slug> --set 1 --file <other-take.mp4> --alt         # a second take beside the primary
python3 $LD --job <slug> --header --finding "the one line worth reading first"
# 4. read it back / verify every declared file is still at its URL
python3 $LD --job <slug> --show
python3 $LD --job <slug> --check
```

`--seed` takes a count, a JSON list, or `{shots|beats|clips|slots: [...]}`. Per row it takes the
first key present: beat ← `beat, beat_id, id, slug, shot_id`; label ← `label, name, title,
headline`; shows ← `shows, purpose, description, desc, summary, intent, line, action`. So a shot
list written for another tool seeds with no reshaping. Slots are renumbered 1..N in plan order.

Exit codes: **0** written · **1** REFUSED, rule named on stderr, nothing written (usage errors
too) · **2** CANNOT-TELL, a read or write did not complete, nothing changed. Never read 2 as 0 or 1.

| refusal | fires when | what it prevents |
|---|---|---|
| `file-not-delivered` | `--file` is not in the uploads dir | the page linking a 404, which reads as a broken render |
| `ready-without-file` | `ready` with no file | a player with no source |
| `unknown-slot` / `unknown-status` | `--set 9` on 8 slots, a status outside the list | a silent no-op / an empty gap |
| `manifest-exists` | `--seed` over a live manifest without `--force` | wiping every recorded status |
| `not-a-manifest` | `<job>.json` exists and is not ours (even with `--force`) | overwriting someone else's file |
| `page-exists` | `<job>.html` exists and is not this template | overwriting someone else's page |
| `no-manifest` | `--publish-page` before `--seed` | a page whose first sight is "could not load" |
| `bad-file` | `--file` is a path, not a bare name | writing a URL outside uploads |

Writes are atomic (same-dir temp + rename), so the page never reads a half-written manifest.

## The manifest: `live-delivery/1`

```json
{"schema": "live-delivery/1", "job": "<slug>", "updated": "<iso>", "title": "...",
 "client": "", "ask": "one line: how the viewer answers", "finding": "", "note": "",
 "page": "https://<tenant>.jam-bot.com/pages/<slug>.html", "written_by": "...",
 "clips": [{"n": 1, "beat": "s01", "label": "...", "shows": "what this slot is FOR",
            "status": "ready", "file": "x.mp4", "url": "/uploads/x.mp4",
            "measurements": {"duration_s": 8.7}, "notes": "",
            "alternates": [{"file": "x-b.mp4", "url": "/uploads/x-b.mp4", "note": ""}],
            "superseded": [{"file": "old.mp4", "displaced_by": "x.mp4", "displaced": "<iso>"}]}]}
```

- **Status is a CLOSED list:** `queued · rendering · ready · failed · skipped`. A status the page
  has no drawing for would fall through to an empty gap.
- **`shows` is written at seed time.** It is the only thing on screen while the slot is empty.
- **`url` is composed by the writer**, never by the page.
- **`superseded[]`:** replacing a slot's primary does not delete the old file (links already sent
  must keep working), so the slot records what it displaced. A checker that counts files at the
  destination joins on `clips[].file`, `alternates[].file` and `superseded[].file` and finds every
  file this job put there.
- The page draws `.mp4/.webm/.mov` as video, `.mp3/.wav/.m4a/.ogg` as audio, images as images,
  anything else as a link.

## 🔴 The operating rule

**Flip each slot the moment its file is delivered. Never batch at the end.** A file that exists
but is not in the manifest is invisible, and "invisible" and "not done yet" look the same from the
viewer's side. A lane that renders eight clips and then writes eight flips has rebuilt the batch
delivery this replaces. **A roll that died gets `failed`**: a slot left on `rendering` forever is
the failure the viewer notices and the lane does not.

## Sending the link

The page is login-gated, and a gated page answers a bare **`Unauthorized`** with **no sign-in
redirect**: to someone without a session it looks broken, not locked. So a message that carries
the page link carries **two links**: the page, with "sign in at `https://<tenant>.jam-bot.com/`
first if it says Unauthorized", and **one direct `/uploads/` file URL** that opens with no login.
`--publish-page` prints this on every run.

## The page's obligations

`page.html` meets all of these, and `page-check.py` drives it in a real browser to prove it. A
rewrite that drops one is a regression, not a restyle.

1. Slots in NUMBER order, always (the viewer answers with a number).
2. A pending slot never renders as an empty gap or a broken player: it says what it is for and
   what state it is in.
3. "Could not read the list" is never drawn as "the list is empty". After a good load, a failed
   re-read keeps what loaded and says it is stale.
4. A visible last-updated stamp; amber after 20 min without a change, red when unreachable.
5. Phone-first: 44 px targets, no sideways scroll at 390 px.
6. A poll never tears down an artifact the viewer is part-way through (cards re-render only when
   their own slot changed).
7. A declared file that is not at its URL says so on its own card. **Only the server's 404/410
   counts.** A file this browser cannot decode fires the same media `error` event, and calling it
   "missing" would send someone hunting for a file that is there. Every ready card also carries an
   "open file" link.

## Known gaps (named, so this does not read as all-clear)

- **The VPS renamer can move an image out from under a page.** On content-client tenants
  `descriptive-rename.py` renames junk-named images (camera names, bare hashes, `/api/upload`
  uuids) every 15 min and rewrites the index, but its reference check scans canvas-pages, pages and
  webdev, **not** the manifest in uploads. A flipped image with a junk name can be renamed and its
  slot then 404s. Until the renamer reads `live-delivery/*` manifests (proposed to host@mesh
  2026-09-30), **deliver under a descriptive name** (`<tenant>-<job>-<n>-<what>.png`) and run
  `--check` before you send a link. The page shows such a slot as missing, never as a broken player.
- **`--force` re-seed forgets** what the old slots declared, superseded files included. Prefer
  `--set` per slot.
- **Alternates load on play** (`preload=none`), so a missing alternate is only flagged once someone
  taps it.
- **No push.** The viewer must have the page open; it polls every 30 s and on returning to the tab.

## Proof (measured 2026-09-30)

- `self-test.sh`: **50 writer checks**, plus a mutant (the `file-not-delivered` refusal removed)
  that turns 9 checks red; and where Playwright is importable, **22 page checks** in headless
  Chromium against a local server on a kernel-picked port, plus a page mutant (the unreadable-list
  box suppressed) that turns 4 red. Without Playwright the page half prints SKIPPED and is not
  counted as a pass. Green on a Mac, on the VPS host (page half ran), and inside a tenant
  container through the `/mnt/shared-skills` mount (page half SKIPPED: no Playwright there).
- The "not decodable is not missing" control was run against the first version of this page, which
  called any media error missing: 2 checks red. On the current page the decode error does fire
  (code 4) and the player stays.
- **Live, one job, all three transports,** on tenant `test-dev`, job `live-delivery-page-proof`
  (left in place as the worked example; manifest
  `https://test-dev.jam-bot.com/uploads/live-delivery-page-proof.json`):
  - seeded 3 slots from a shot list and published the page from a rig **off the VPS** (`--ssh`);
    slot 1 flipped from there. An undelivered file was refused (rc 1); an unreachable host was
    CANNOT-TELL (rc 2).
  - slot 2 flipped `rendering` then `ready` from **inside the tenant container** with no target
    flags (it found `/app/runtime/`), as uid 1000; the file lands owned by the host user.
  - `--check` from the **VPS host** (`--tenant`): 2 declared files present, slot 3 pending.
    No temp files left in uploads or canvas-pages.
  - Served: manifest **200 without login** (`text/plain`, `attachment`, `no-store`); page **401
    without login**, 12-byte body, no redirect; the stills 200 `image/png`.
  - Rendered on the real origin (page body routed in, manifest and stills fetched live): 2 images
    at 960 px natural width, 1 pending card, no error box, no sideways scroll at 390 or 1280 px.
- Cross-reading the Mac video rig's first manifest (8 slots, written by its own writer): this page
  renders all 8 as videos. The reverse is only half true: the Mac rig's older page reads this
  manifest but draws every file as a video, so an image job needs THIS page.

## Adopting it

1. Deliver files the way your lane already does (the tenant's uploads + index row).
2. Seed the job from the plan before the first render, and publish the page once.
3. Add ONE flip call right after each delivery, and a `failed` flip in each failure branch.
4. Send the page link with one direct `/uploads/` URL beside it.
5. Run `self-test.sh` once where you install it: `0 failed, mutant caught: 1`.

The Mac's video rig has a richer, video-specific front end of the same schema
(`~/showrunner/bin/live_delivery.py` on mac-claude, which also keeps legacy fields for its first
job). Both writers produce `live-delivery/1`; this skill's page renders either writer's manifest.

Owner: mac-claude@mesh. Routed from the 2026-09-30 mesh meeting as a share; sits beside
`retire-dont-delete`.
