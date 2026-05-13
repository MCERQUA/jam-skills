# pnpm 11 Requirements for webdev-built websites

**Read this BEFORE creating or scaffolding a new website project.** All `webdev-*` containers run `pnpm 11.1.1` since 2026-05-13. pnpm 11 added security-strict defaults that BLOCK installs/dev-server-starts unless your project's `package.json` declares what build scripts are allowed to run.

## Why this matters

pnpm 11 ships with `strictDepBuilds=true` by default — meaning native packages (sharp, canvas, bcrypt, esbuild, puppeteer, playwright, node-sass, etc.) **WILL NOT compile** unless you've explicitly approved them per-project. The webdev container's entrypoint runs `pnpm install` + `pnpm dev` on container start, so a missing approval = container restart loop = site unreachable.

This is good practice anyway — same principle as the TanStack supply chain attack mitigation. You're declaring trust at install time, not blindly running every package's lifecycle hooks.

## Required `package.json` config for ANY project using native build deps

```jsonc
{
  "name": "your-project",
  "dependencies": { "...": "..." },
  "pnpm": {
    "onlyBuiltDependencies": [
      "sharp"           // Next.js image optimization — almost ALWAYS needed
      // add others as needed: "canvas", "bcrypt", "@swc/core", etc
    ]
  }
}
```

## Common deps that need to be in `onlyBuiltDependencies`

| Dep | When | Notes |
|---|---|---|
| `sharp` | ANY Next.js project | Image optimization. Auto-installed transitively via Next. ALWAYS needed. |
| `canvas` | Image generation, OG cards | Native compile against libcairo |
| `bcrypt` | User auth with password hashing | Native compile against OpenSSL |
| `@swc/core` | If using non-Next bundlers with SWC | Sometimes auto-bundled |
| `esbuild` | Some bundlers / Astro | Native binary download |
| `puppeteer` / `playwright` | Browser automation | Downloads chromium |
| `node-sass` | Legacy Sass projects | Prefer `sass` (pure JS) instead |

## Required `package.json` config for ANY new project (template)

When you scaffold a new site, START WITH this baseline `pnpm` config:

```json
"pnpm": {
  "onlyBuiltDependencies": ["sharp"]
}
```

If any added dep complains `[ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: <name>` in container logs, ADD that name to `onlyBuiltDependencies` and re-lock.

## Lockfile discipline

pnpm 11's pre-command dep-status check (`runDepsStatusCheck`) compares `package.json` against `pnpm-lock.yaml` before EVERY pnpm command. If they diverge (someone added a dep without re-locking), it errors.

The webdev image overrides `frozen-lockfile=false` and `verify-deps-before-run=false` so this is non-fatal at boot — but you should still keep them in sync:

- After ANY change to `dependencies` / `devDependencies` in `package.json`: run `pnpm install` (regenerates lockfile)
- Commit BOTH `package.json` and `pnpm-lock.yaml` together. NEVER commit one without the other.

## What the webdev container does on start

The entrypoint script (`/usr/local/bin/webdev-entrypoint.sh`):
1. Reads `WEBDEV_PROJECT_NAME` env (or `.active-project` fallback)
2. `cd /app/websites/<project>`
3. If `node_modules` missing → runs `pnpm install` (this is the slow first-run)
4. Runs `pnpm next dev --port 3000 --hostname 0.0.0.0` (or vite/etc per detection)
5. pnpm 11 runs the dep-status check before next-dev launches → if package.json/lockfile drift OR build scripts ignored → ERR

## What the webdev image does to soften pnpm 11 strictness

The Dockerfile (`/mnt/system/base/webdev/Dockerfile`) sets these env vars:

```dockerfile
ENV NPM_CONFIG_CONFIRM_MODULES_PURGE=false   # don't prompt on lockfileVersion bump
ENV NPM_CONFIG_FROZEN_LOCKFILE=false         # auto-heal lockfile drift
ENV NPM_CONFIG_VERIFY_DEPS_BEFORE_RUN=false  # skip the verify check before non-pnpm commands
ENV NPM_CONFIG_STRICT_DEP_BUILDS=false       # warn-only on ignored build scripts (intent — pnpm may still error)
ENV PNPM_MINIMUM_RELEASE_AGE=1440            # supply-chain attack protection: 1 day delay
```

Plus pnpm@11 is installed directly. These cover MOST friction. The one thing they don't cover is `[ERR_PNPM_IGNORED_BUILDS]` — for that, your project MUST declare `pnpm.onlyBuiltDependencies`.

## Troubleshooting checklist for "container won't start"

1. `sg docker -c "docker logs <container-name>" | tail -30` — read the actual error
2. `[ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: <name>` → add `<name>` to `pnpm.onlyBuiltDependencies` in `package.json`
3. `[ERR_PNPM_OUTDATED_LOCKFILE]` → from project dir on host, run `pnpm install --no-frozen-lockfile`
4. `Module not found: <name>` → dep is in `package.json` but not `node_modules` — usually means a previous failed install. Wipe `node_modules` + re-run.
5. Port 4XXX returns 502/000 → container is restart-looping. See logs.

## When scaffolding a new site (AI agent checklist)

Before you `git push` or have webdev start the container, verify:

- [ ] `package.json` has `pnpm.onlyBuiltDependencies` covering at least `sharp` (for Next.js)
- [ ] `pnpm-lock.yaml` exists and was generated against the same `package.json` (run `pnpm install` after final dep set)
- [ ] No commits with `package.json` changes that don't include the corresponding lockfile changes
- [ ] If you added any native deps (canvas, bcrypt, etc), add them to `onlyBuiltDependencies` BEFORE expecting the dev server to start
