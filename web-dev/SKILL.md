---
name: web-dev
description: "How to work with the web-dev container that serves this client's live dev URL. Covers checking which website is currently loaded, switching to a different website, where projects live, where to find per-website edit docs (AGENTS.md / CLAUDE.md), how to verify changes against the live URL, and what NOT to do. Read FIRST whenever the user asks to edit, switch, or check a website."
---

# web-dev — Working with this client's webdev container

Read this whole file before touching ANY website. Then read the active project's
`AGENTS.md` (or `CLAUDE.md`) for project-specific edit recipes.

---

## Critical fact: the live URL is the dev URL

The client has **one** webdev container running `next dev`. It serves **one
website at a time** — whichever is set as the active project. That site is
deployed to a **live public URL on the internet** at:

```
https://dev-<client>.jam-bot.com
```

There is **no localhost**. There is **no separate preview**. When the user views
their site, they're hitting that live URL through Cloudflare → nginx → the
webdev container. Hot-reload is ~2-5 seconds end-to-end.

Find the dev URL via the active project's `AGENTS.md`, or:
```
cat ~/Websites/<project>/.build-status.json | grep -o '"devUrl":"[^"]*"'
```

---

## Where websites live

From inside this openclaw container:
```
~/Websites/                              ← top-level (you have read/write here)
~/Websites/.active-project               ← single-line file: name of currently-served project
~/Websites/<project-name>/               ← every project has its own dir
~/Websites/<project-name>/AGENTS.md      ← per-project edit guide (READ THIS)
~/Websites/<project-name>/CLAUDE.md      ← alias to AGENTS.md
~/Websites/<project-name>/docs/site-map.json
~/Websites/<project-name>/docs/content-registry.json
~/Websites/<project-name>/docs/design-tokens.json
~/Websites/<project-name>/tools/site-tools/   ← bulk-swap + grep helpers
```

Same volume is mounted into the webdev container at `/app/websites/`. Edits you
make from openclaw appear instantly to webdev (and to the user's browser via
hot-reload) — no copy step needed.

---

## Step 1 — find out which website is currently active

```
cat ~/Websites/.active-project
ls ~/Websites/
```

The first prints the slug of the active project. The second lists every
available project. Compare those two — if the user is asking about a project
that's NOT the active one, you have to switch (Step 2) before edits will appear
on the dev URL.

You can also confirm what webdev is actually serving by curl:
```
curl -sk https://dev-<client>.jam-bot.com/ -o /tmp/home.html
grep -E '<title>|<h1>' /tmp/home.html | head -3
```

The `<title>` typically matches the businessName from that project's
`.intake.json`.

---

## Step 2 — switch the active website

ONLY do this when the user explicitly asks to work on a different website.
Switching mid-edit on the wrong project will surprise the user.

1. Confirm the target project exists:
   ```
   ls ~/Websites/<target-project>/AGENTS.md
   ```
2. Set it as active:
   ```
   echo "<target-project>" > ~/Websites/.active-project
   ```
3. Wait ~6 seconds — a host-side watcher (3s poll) detects the change and
   restarts the webdev container with the new project as `WEBDEV_PROJECT_NAME`.
4. Verify the switch took:
   ```
   sleep 8
   curl -sk https://dev-<client>.jam-bot.com/ | grep -oE '<title>[^<]+</title>'
   ```
   The title should now reflect the new project's businessName.

If the curl still shows the old project after 15s, the watcher hasn't fired —
tell the user, don't keep retrying. The host operator can run
`bash scripts/jambot-switch-devsite.sh <client> <project>` from the host shell.

---

## Step 3 — find the per-website edit docs

Every project built by the website-builder pipeline has these auto-generated
files at its root:

| File | Purpose |
|---|---|
| `AGENTS.md` | Single-page primer: identity, full site map, design tokens, edit recipes, what-not-to-do. **Read first.** |
| `CLAUDE.md` | Alias to AGENTS.md (same content). |
| `docs/site-map.json` | Machine-readable: every page's slug, route, file, type, h1, h2 list, section count. |
| `docs/content-registry.json` | Every intake value (phone, email, business name, address) with every file path + line number where it appears. Phone is indexed across **all variants** (formatted, digits-only, `+1`, `tel:`). |
| `docs/design-tokens.json` | Colors + fonts auto-extracted from `tailwind.config.ts` + `globals.css`. |
| `tools/site-tools/find.py` | `python3 tools/site-tools/find.py "<text>"` — JSON list of `{path, line, snippet}`. |
| `tools/site-tools/swap-phone.py` | Bulk replace phone in EVERY variant. Idempotent. |
| `tools/site-tools/swap-email.py` | Bulk replace email + update intake. |
| `tools/site-tools/swap-business-name.py` | Bulk replace business name. |
| `tools/site-tools/page-summary.py` | `python3 tools/site-tools/page-summary.py <slug>` (use `home` for `/`). |
| `tools/site-tools/request-deploy.py` | Commits + drops a deploy/PR ticket. The agent never pushes to prod — see "Requesting a deploy" below. |

**Always read `AGENTS.md` first** — it has the project-specific identity,
keyword strategy, and edit recipes you'll need. The machine-readable docs are
references for tools, not for human reading.

---

## Step 4 — make a change

Pick the right tool for the change. Don't hand-edit when a swap script exists.

### Bulk content (phone / email / business name)
```
cd ~/Websites/<project>
python3 tools/site-tools/swap-phone.py "(425) 555-1234"
python3 tools/site-tools/swap-email.py info@example.com
python3 tools/site-tools/swap-business-name.py "New Name LLC"
```
After any of these, regenerate the docs so the registry stays accurate:
```
python3 /mnt/system/base/skills/website-builder/tools/build-agent-docs.py \
    --project . --intake .intake.json
```

### Find a string anywhere in the site
```
python3 tools/site-tools/find.py "King County"
```

### Inspect a single page
```
python3 tools/site-tools/page-summary.py services
python3 tools/site-tools/page-summary.py home
```

### Edit copy on a specific page
1. Find the file: `cat docs/site-map.json | grep -A2 '"slug": "<slug>"'` →
   `pages[].file`.
2. Make a focused `Edit` (small `old_string` / `new_string`).
3. **Don't reformat the file.** Stitch-converted pages preserve specific class
   signatures other tools key off of (logo wordmark, services dropdown).

### Add a new article to the blog
- Append a record to `src/app/blog/articles.ts`.
- The dynamic route `src/app/blog/[slug]/page.tsx` reads from there.

### Add a new service or location page
1. Clone an existing page: `cp -r src/app/<existing> src/app/<new-slug>`
2. Update H1/H2/intro to match the new keyword (`ai/research/keywords.md`).
3. Re-run finalize so the new page appears in dropdowns:
   ```
   python3 /mnt/system/base/skills/website-builder/tools/stitch-finalize.py \
       --project . --intake .intake.json
   ```
4. Re-run agent-docs so the site map picks up the new page.

### Update logo or palette
- New logo → drop at `public/images/intake/<filename>.<ext>`.
- Update the `<img src=...>` in any single page.tsx — navbar logo is identical
  across pages.
- Recolor → edit `src/app/globals.css` `--color-*` vars OR
  `tailwind.config.ts` theme.extend.colors.

---

## Step 5 — request a deploy (when the user is happy with the dev URL)

**You do NOT push to production. Ever.** The flow is:

| Stage | Who | What |
|---|---|---|
| Initial site creation | Voice agent + user | Build pipeline produces dev URL |
| **First production deploy** | Mike (manual) | Reviews dev URL → does first push to prod |
| Subsequent edits | Voice agent + user | Edit on `dev`/`web-dev` branch live on dev URL |
| **Update review** | Mike (manual) | Reviews PR → merges to `main` → triggers prod deploy |

When the user says "okay deploy this" / "push this live" / "let Mike know we're ready":

```
cd ~/Websites/<project>
python3 tools/site-tools/request-deploy.py --note "<plain-English summary of changes>"
```

What that does:
1. **Commits** any uncommitted edits on the current dev branch (typically `web-dev`)
   with a `voice-edit:` prefix so Mike can see exactly what changed in `git log`.
2. **Detects request type** from `.build-status.json` `firstDeployedAt` field:
   - `firstDeployedAt` unset → `type=first-deploy` — Mike does the first manual push
   - `firstDeployedAt` set → `type=pr-request` — host opens PR vs `main`, Mike reviews + merges
3. **Drops a ticket** at `/mnt/clients/<client>/tickets/deploy-requests/<ts>-<project>.json`
   (preserved per never-delete policy).
4. **Appends to queue** at `/mnt/system/base/queue/deploy-requests.jsonl` —
   host-side automation reads this to push branches and email Mike.
5. **Mesh-notifies** `mike-host@mesh` and `admin@mesh` with summary +
   commit SHA + dev URL + ticket path. Surfaces in Mike's mesh inbox in the
   next session.
6. **Stamps `.build-status.json`** with the deployRequest entry so the canvas
   Build Monitor shows "queued for review".

**After you run `request-deploy.py`, stop editing.** Tell the user:
> "Queued for Mike's review. He'll merge and push when he's at his desk."

Don't push to remote yourself. Don't try to email. Don't open the PR. The
host owns those steps and there's a host-side cron that emails Mike when
new entries land in the queue.

---

## Step 6 — verify the change is live

```
# Hot-reload usually picks up edits in 2-5 seconds.
sleep 4
curl -sk https://dev-<client>.jam-bot.com/<route> | head -c 800
```

For a deeper check (catches type errors that only break at build time):
```
sg docker -c "docker exec webdev-<container> sh -c 'cd /app/websites/<project> && pnpm tsc --noEmit'" 2>&1 | tail -10
```

If hot-reload didn't pick the change up:
- Confirm the file you edited is in the **active project** (`cat ~/Websites/.active-project`).
- Check webdev's recent logs from the host: `docker logs --tail 50 webdev-<container>` — a syntax error will appear here as a Next.js compile failure.
- Check the file extension is `.tsx` (not `.tsx.bak` or similar).

---

## What NOT to do

- **Don't run `pnpm install` from openclaw.** Its pnpm store differs from the
  webdev container's. Builds + hot-reload happen in webdev. Edit files from
  openclaw, let webdev rebuild.
- **Don't restart the webdev container manually.** The host watcher handles
  restarts when `.active-project` changes. Manual restarts can desync the env.
- **Don't deploy to production from here.** Webdev is dev only. Production
  deploy is a separate flow (Netlify / nginx / etc.) handled by the host.
- **Don't delete `.archive-failed-runs/` from any project.** It preserves prior
  build outputs (project-wide policy: never delete).
- **Don't reformat or auto-rewrite Stitch-converted pages.** The class
  signatures matter for downstream tools (`stitch-finalize`, etc).
- **Don't edit `~/Websites/.active-project` for any reason other than switching
  to a different project.** Don't blank it. Don't add comments. Don't add a
  trailing path. Just the slug, on one line.

---

## Quick reference card

```
# What's loaded
cat ~/Websites/.active-project

# What's available
ls ~/Websites/

# Switch
echo "<project>" > ~/Websites/.active-project   # wait ~6s

# Confirm switch
sleep 8 && curl -sk https://dev-<client>.jam-bot.com/ | grep -oE '<title>[^<]+</title>'

# Find a string
cd ~/Websites/<project> && python3 tools/site-tools/find.py "<text>"

# Bulk swaps
python3 tools/site-tools/swap-phone.py "(xxx) yyy-zzzz"
python3 tools/site-tools/swap-email.py x@y.com
python3 tools/site-tools/swap-business-name.py "Name"

# Refresh docs
python3 /mnt/system/base/skills/website-builder/tools/build-agent-docs.py \
    --project . --intake .intake.json

# Refresh navbar dropdowns after adding pages
python3 /mnt/system/base/skills/website-builder/tools/stitch-finalize.py \
    --project . --intake .intake.json

# Request deploy / PR review (commits + tickets + mesh-notifies; agent does NOT push)
python3 tools/site-tools/request-deploy.py --note "what changed in plain English"
```
