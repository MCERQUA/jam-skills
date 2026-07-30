---
name: grid-creator
description: Schedule a grid of AI-generated images (logos, mascots, characters, branded posts) when the owner asks in plain language — the request goes to the Mac creative node and shows up in the Grid Creator page.
when_to_use: The owner asks for MULTIPLE image options to choose from — "make me a grid of logos", "generate some mascot ideas", "I want a bunch of post options for X", "give me 12 logo concepts". Also handles the [GRID-GEN] line the Grid Creator page sends.
---

# Grid Creator — schedule a grid of image options

You are the bridge between the owner and the **Mac creative node**, which generates images (via a
ChatGPT browser — no per-image cost). You do NOT generate images yourself. Your job: understand the
request, then run ONE command that schedules it. The result appears in the owner's **Grid Creator**
canvas page and the Mac delivers the finished images into `uploads/`.

## When to use this
Use it whenever the owner wants **several image options to pick from**, either:
- **Plain language:** "make me a grid of logos", "generate 12 mascot ideas", "some branded post
  options about our winter special", "give me a few character designs".
- **The page:** a message that STARTS WITH `[GRID-GEN]` (the Grid Creator form sends this). Parse its
  `request_id=… type=… count=… aspect=… layout=… brief="…"` fields and submit them as-is.

Do NOT use it for a single specific image the owner describes exactly — that's a normal image request.
Use it for **exploration / options**.

## The one command
Run this (the brief goes on STDIN so quotes and newlines are safe). `--client` is THIS tenant's id —
it is pre-filled for you in TOOLS.md; use exactly that value:

```bash
grid-gen-submit --client <THIS_TENANT> --type <post|logo|character|mascot> \
  --count <N> --aspect <1:1|4:5|9:16|16:9> --layout <composite|separate> <<'BRIEF'
<the owner's intent in plain words — NOT a finished prompt>
BRIEF
```

- `--request-id` is optional; omit it and one is generated. The command prints the id + confirms
  the order shows on the Grid Creator page.
- It writes the order to the Mac's queue AND records it so the Grid Creator page shows it as
  `queued` right away.

## How to fill the fields from what the owner said
- **type** — `logo`, `mascot`, `character`, or `post` (branded social image). If unclear, ask ONE
  short question, or default to `post` for "content/images" and `logo` for "logo/brand".
- **count** — how many options. Default **9**. Honor an explicit number ("give me 12" → 12). Max 24.
- **aspect** — default `1:1`. Use `9:16` for "story/reel", `16:9` for "banner/wide", `4:5` for
  "portrait/feed".
- **layout** — `composite` (one grid image the owner cuts up in the image splitter — the default) or
  `separate` (N individual images). Default `composite` unless they clearly want separate files.
- **brief** — relay the owner's INTENT in plain words. Do NOT write a polished prompt; the Mac
  improves it per the client's brand kit. Keep what they actually asked for.

## Brand kit — only POSTS need one
- `post` grids use the client's brand kit (colors, logo, NAP, real photos) on the Mac. If this
  client has no kit, the Mac replies asking for palette + logo — relay that to the owner.
- `logo` / `mascot` / `character` are **greenfield** — no brand kit required. The point is to create
  fresh options to pick from. These always generate.

## After you submit
Say something short and concrete, e.g.:
> "Scheduled — I've sent 12 logo concepts to the creative node. Watch the **Grid Creator** page;
> they'll show up there as they finish (about 90 seconds per image), and you can cut the grid into
> individual images in the splitter."

Then STOP. Do NOT poll or wait — the Grid Creator page tracks status and shows the results. The Mac
delivers finished images into this tenant's `uploads/` and mesh-sends you when it's done; only then,
if the owner asked to be told, let them know.

## Never
- Never try to generate the images yourself.
- Never use `mesh-send --kind task` to the Mac for a grid — that auto-executes in a permissionless
  lane with no brand kit. ONLY `grid-gen-submit` is safe (it file-drops into the queue the Mac drains).
- Never invent a finished prompt in the brief — send intent; the Mac composes the prompt.
