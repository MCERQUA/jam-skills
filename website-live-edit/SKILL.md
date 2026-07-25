---
name: website-live-edit
description: How to edit the client's website(s) — the DEFAULT path (edit source in workspace, push to GitHub) vs the RARE live-edit session (load the site into the client's webdev dev container so they watch single-aspect changes hot-reload on screen in the voice app, then push the finished version). TRIGGER when the user asks to change/update/fix their website, or says "live edit," "show me the change live," "let me watch," or names a site to edit. DO NOT TRIGGER for building brand-new websites (website-setup flow) or deploy-only questions.
---

# Website Editing — default path vs live-edit session

There are TWO ways to change a client's website. Pick by ONE question:
**does the user want to WATCH the changes happen live on screen?**

## Path A — DEFAULT: direct edit + push (no webdev container)

Used for almost every edit request ("fix the phone number", "change that heading",
"update the hours"). The webdev container is NOT involved.

1. Edit the source directly in your workspace: `Websites/<project>/…`
2. Verify the change is coherent (read the surrounding file; don't break the build —
   if you can, run the project's lint/build check).
3. Push to GitHub using your normal push workflow (`agent-git-push-workflow` skill /
   push-request broker). Production (Netlify/host deploy lane) redeploys from GitHub.
4. Tell the user it's done and where to look.

## Path B — RARE: live-edit session (webdev dev container)

Only when the user wants to SEE changes update live while they direct you —
"live edit", "let me watch", "change it while I look at it". This is a
rarely-used feature; don't reach for it by default.

**The webdev container has exactly ONE purpose:** the client opens the dev site
inside the voice app (canvas iframe), asks for live changes to single aspects,
watches them hot-reload on screen until they're satisfied — then that finished
version gets PUSHED TO GITHUB. It is a live-editing surface, never hosting.

### The session flow

1. **Find the site's dev lane.** Your `TOOLS.md` website table lists each wired
   website with its devsite path. The dev URL shape is
   `https://<user>.jam-bot.com/devsite-<slug>/` (same-domain nginx proxy) or
   `https://dev-<user>.jam-bot.com`.
2. **WAKE THE PREVIEW FIRST — before you edit anything.**

   The preview container is **stopped by default** and starts on demand. Waking
   it takes about **17 seconds** (a Next.js dev server has to boot and compile
   its first request). You do NOT have to make the client sit through that —
   wake it the moment they ask, then edit while it boots:

   ```bash
   bash /mnt/shared-skills/website-live-edit/webdev-preview.sh wake
   ```

   This returns immediately. Say something natural — *"Sure, let me pull up your
   site — give me a few seconds while I make that change"* — then go straight
   into the edit. By the time you have the change made, the preview is warm and
   the client sees it hot-reload. **The 17s costs them nothing when it runs in
   parallel with work you are doing anyway.**

   ❌ Do NOT edit first and wake after — then the client watches a loading page.
   ❌ Do NOT announce "starting your container" as a step. It is plumbing; the
      client asked to see their website, not to hear about infrastructure.

   Before you hand them the URL, confirm it is actually serving:
   ```bash
   bash /mnt/shared-skills/website-live-edit/webdev-preview.sh wait 45   # → "ready"
   ```
   Only then open it: `[CANVAS_URL:https://<user>.jam-bot.com/devsite-<slug>/]`

   If `wait` times out, tell the user plainly that the preview is slow to start
   and you are checking — then escalate to host (step 4). Never open a canvas at
   a URL you have not confirmed is serving; a broken iframe reads as "the agent
   broke my website."

   **Other states:**
   - Wired but parked / not the active site → request a switch/start (step 4).
   - **Not in your workspace at all** (multi-site owners may name any of their
     sites) → request a load (step 4).
   - `webdev-preview.sh` returns 404 `no webdev container for this tenant` → the
     site was never wired for live preview; that is a host task (step 4), not
     something you can fix.
3. **Edit live.** Make the requested change in `Websites/<project>/…` — the dev
   server hot-reloads and the user sees it within seconds in the canvas. Keep
   edits SMALL and single-aspect; confirm each one with the user before the next.
4. **Anything needing docker/nginx/sudo, you REQUEST from the host** — you cannot
   run docker. Send a mesh task and tell the user their live-edit surface is
   being prepared (usually a minute or two):
   ```
   printf 'ACTION: <load|switch|start|park>\nTENANT: <you>\nSITE: <project-name-or-github-url>\nWHY: user requested live-edit session\n' \
     | mesh-send --to host@mesh --kind task --subject "webdev: <action> <site> for <tenant>"
   ```
   The host wires it (`jambot-add-website.sh` / `jambot-switch-website.sh`) and
   replies with the dev URL.
5. **Finish = push.** When the user says it's done, push the edited version to
   GitHub (same push workflow as Path A). A live-edit session that isn't pushed
   is unfinished work — the dev container is not where changes live.

   ⚠️ This matters more now that the preview is stopped when idle: the container
   is a **scratch surface**, and an unpushed edit is work sitting somewhere the
   client cannot see and you may not return to. Push before the session ends.

   **Keeping it awake mid-session is automatic** — every request the client's
   browser makes counts as activity, so a preview they are actively looking at
   is never reaped out from under them. If the client wanders off for a long
   while and the preview goes cold, just call `wake` again; the workspace files
   are untouched, only the server was stopped.
6. After the session the container can be parked (idle-suspension also handles
   this) — you don't need to ask for that unless memory pressure is mentioned.

## Hard rules

- NEVER start your own server/preview/container for a website — the per-site
  webdev container lane is the ONLY live-preview surface (one-off `docker run`
  previews are the anti-pattern; they rot for weeks).
- NEVER treat the dev URL as the live site; production serves from GitHub via
  the deploy lane.
- NEVER leave a finished live-edit session unpushed.
- Multi-site clients: any site they name follows the same flow — if it isn't in
  your workspace yet, that's just a `load` request (step 4), not a reason to say no.
