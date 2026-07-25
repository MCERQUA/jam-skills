---
name: site-deploy-preflight
description: "Prove a website actually builds BEFORE pushing it to an auto-deploying branch. Runs the real production build in a throwaway sandbox so the tenant's live dev server is never disturbed, and with NODE_ENV=production so the build doesn't fail for phantom reasons. TRIGGER: before any 'git push' of a website repo that auto-deploys (Netlify/Vercel), when a deploy has failed, or when asked to 'ship'/'deploy'/'publish' site changes. DO NOT TRIGGER for non-deploying repos or docs-only changes."
---

# site-deploy-preflight

**The rule: you do not push a site to a deploy branch until `preflight-build.sh` prints ✅.**

A failed Netlify build means the client's site sat broken and someone had to be pulled in to fix it. The build takes ~100s locally. Always cheaper than a failed deploy.

## Run it

```bash
bash /mnt/shared-skills/site-deploy-preflight/preflight-build.sh <site-dir>
```

- exit `0` + `✅ PREFLIGHT PASSED` → commit and push.
- exit `1` + `❌ PREFLIGHT FAILED` → **do not push.** Fix the error it printed, run it again.

It builds a throwaway copy. It never writes to your site directory and never deletes anything in it.

## The two traps this exists to defeat

Both of these made the naive advice — "just run `npm run build` first" — actively harmful, which is why agents stopped trusting it and pushed broken code anyway.

**Trap 1 — building in place takes the live site down.**
The tenant's webdev container serves the dev site straight out of `<site>/.next`. Running `next build` in the site directory overwrites that while it's being served. Symptom: the dev site 5xx's mid-build. Evidence it kept happening: `.next.old`, `.next.old2`, `.next.old3` piled up in the printguys repo. The script sidesteps this by building a copy.

**Trap 2 — `NODE_ENV=development` makes `next build` fail for a fake reason.**
The webdev containers set `NODE_ENV=development`. Under a non-standard `NODE_ENV`, a perfectly healthy Next 15 app fails at the prerender step with:

```
Error: <Html> should not be imported outside of pages/_document.
Export encountered an error on /_error: /404, exiting the build.
```

**That error is a lie.** It says nothing about your code. Verified 2026-07-24: commit `923fb52` — which Netlify had built and deployed successfully — reproduces this failure locally every time under `NODE_ENV=development`, and passes cleanly the moment `NODE_ENV=production` is set. The script forces `NODE_ENV=production`, so a red result is always a real result.

If you ever see that `<Html>` / `/_error: /404` message, your first question is "what is NODE_ENV?", not "what did I break?"

## Reading a failure

The script prints only the lines that matter (compile errors, TS errors, missing modules) and drops the full log at `/tmp/preflight-<site>-FAILED.log`.

The failure class that started all this — a JSX comment opened with `{/*` but closed with `*/` instead of `*/}`:

```
Error:   x Expected '</', got '{'
   ,-[src/components/layout/Footer.tsx:162:1]
```

Note the reported line (162) is **not** the broken line — it's the next element the parser choked on. The real damage was at line 143. With unterminated JSX comments, always look *above* the reported line.

## Where this fits

- Autosave (`jambot-workspace-autocommit.sh`) commits your edits within ~60s, unreviewed. It does **not** push. So the commit is not the dangerous step — **the push is.** Preflight gates the push.
- Related: `agent-git-push-workflow` (how to push), and each site's own `CLAUDE.md` (branch + env specifics).

## Prerequisites

`node_modules` must exist in the site dir. If it doesn't:

```bash
cd <site-dir> && pnpm install --prefer-offline    # store is local — this is quick
```

Always `pnpm`, never `npm install`.
