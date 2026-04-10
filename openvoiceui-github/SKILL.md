---
name: openvoiceui-github
description: OpenVoiceUI GitHub development workflow — release process, branch discipline, PR format, npm publishing, Pinokio compatibility, plugin repo management, and consistency checklists.
---

# OpenVoiceUI GitHub Development

This skill covers the full development workflow for the OpenVoiceUI project across all distribution channels. Follow these checklists exactly — consistency matters.

## Repositories

| Repo | Purpose | Branch Model |
|------|---------|-------------|
| `MCERQUA/OpenVoiceUI` | Main app | `dev` → PR → `main` (protected) |
| `MCERQUA/openvoiceui-plugins` | Community plugins | `main` only |

## Branch Discipline

- **All work happens on `dev`**. Never commit directly to `main`.
- **PRs from `dev` → `main`** for every release. No exceptions.
- **Never commit unrelated work to feature branches.** If you're fixing a bug while working on a feature, commit the fix separately on dev first.
- **Never force-push to main or dev.**

## Version Format

`YYYY.M.DD` — e.g. `2026.4.10` (April 10, 2026)

- `package.json` version MUST match the release tag (without the `v` prefix)
- Tag format: `v2026.4.10` (with `v` prefix)
- Release title format: `OpenVoiceUI 2026.4.10` (NO `v` prefix, includes project name)
- If multiple releases on the same day: `2026.4.10-1`, `2026.4.10-2`

## Release Checklist

Run through EVERY step. Do not skip any.

### Pre-Release

- [ ] All changes committed to `dev` and pushed
- [ ] `package.json` version bumped to new version
- [ ] Version bump committed: `chore: bump version to YYYY.M.DD`
- [ ] All plugin stubs in `plugins/` have up-to-date `plugin.json` + `README.md`
- [ ] No debug logging left in code (search for `### Gateway resolution`, `console.log("DEBUG`)
- [ ] No hardcoded JamBot paths (`/mnt/clients`, `/mnt/system`, `jam-bot.com`)

### Create PR

```bash
gh pr create --base main --head dev \
  --title "Release YYYY.M.DD — one-line summary" \
  --body "## Summary
- Feature 1
- Feature 2
- Fix 1"
```

### Merge & Tag

```bash
gh pr merge <PR_NUMBER> --merge --admin
```

### Create Release

```bash
gh release create vYYYY.M.DD \
  --target main \
  --title "OpenVoiceUI YYYY.M.DD" \   # NO 'v' prefix in title
  --notes "$(cat <<'NOTES'
## What's New

### Features
- **Feature Name** — one-line description
- **Feature Name** — one-line description

### Fixes
- Fix description
- Fix description

### Dependencies
- package X.Y.Z → A.B.C

### Plugins (separate repo)
- **Plugin Name** — what changed

**Full Changelog**: https://github.com/MCERQUA/OpenVoiceUI/compare/vPREVIOUS...vCURRENT
NOTES
)"
```

### Release Notes Format (MUST follow this exactly)

```markdown
## What's New

### Features
- **Bold Feature Name** — one-line description of what it does
- **Bold Feature Name** — one-line description

### Fixes
- Description of fix (no bold, just bullet)
- Description of fix

### Dependencies
- package old-version → new-version
- package old-version → new-version

### Plugins (separate repo)
- **Plugin Name** — what changed (only if plugin repo had changes)

**Full Changelog**: https://github.com/MCERQUA/OpenVoiceUI/compare/vOLD...vNEW
```

Rules:
- Features are **bold name** followed by em-dash and description
- Fixes are plain bullets, no bold
- Dependencies section only if deps changed
- Plugins section only if the plugins repo had related changes
- Full Changelog link is ALWAYS included (previous tag → new tag)
- Title is ALWAYS `OpenVoiceUI YYYY.M.DD` — not just the version number

### Post-Release Verification

- [ ] **npm** — auto-publishes via GitHub Actions on release. Verify: `npm view openvoiceui version` should show the new version within ~2 minutes
- [ ] **Pinokio** — uses `pinokio.js` in repo root. No manual action needed — Pinokio pulls from GitHub on user's next update. Verify `pinokio.js` version field is current if it has one.
- [ ] **GitHub release** — verify release page shows correct title, notes, and tag
- [ ] **Docker** — if OVU image changed, rebuild on JamBot: `bash scripts/jambot-build-images.sh`

## npm Publishing

**Automatic.** The `npm-publish.yml` workflow triggers on every GitHub release:
1. Checks out the code at the release tag
2. Syncs `package.json` version to match the tag (strips leading `v`)
3. Runs `npm publish --access public`

**Secrets required:** `NPM_TOKEN` in the `npm-release` environment.

**If it fails:** Check Actions tab. Common issues:
- Token expired → regenerate in npmjs.com → update GitHub secret
- Version already exists → you published twice (fix: bump version, re-release)
- Package name conflict → should never happen (`openvoiceui` is ours)

**Manual publish (emergency only):**
```bash
cd /mnt/system/base/OpenVoiceUI
npm publish --access public
```

## Pinokio Compatibility

`pinokio.js` in the repo root is the Pinokio launcher. It controls the install/start/update/stop flow.

**Key files:**
- `pinokio.js` — menu structure and state detection
- `install.js` — one-time setup (clone, install deps, create config)
- `start.js` — launch the app
- `stop.js` — stop the app
- `update.js` — pull latest + reinstall deps

**Rules:**
- Pinokio uses the `main` branch. Users see what's on main.
- `pinokio.js` version field (`version: "3.7"`) is the Pinokio API version, NOT the app version. Don't change it unless Pinokio API changes.
- Test Pinokio-breaking changes (new env vars, new deps, changed ports) by checking the install/start scripts handle them.
- Pinokio users don't have Docker. Anything that requires Docker (Hermes, OpenClaw, Supertonic) must be optional or have a non-Docker fallback.

## Plugin Repo Management

### Adding a new plugin to the plugins repo

1. Create directory in `openvoiceui-plugins/` with: `plugin.json`, `README.md`, and all plugin code
2. Add entry to `registry.json`
3. Commit and push to `main`

### Adding the stub to the main repo

Every plugin in the plugins repo MUST also have a stub in `OpenVoiceUI/plugins/`:
- `plugins/<name>/plugin.json` — full manifest (same as plugins repo)
- `plugins/<name>/README.md` — full readme (same as plugins repo)

The `.gitignore` must have exclusions for each plugin:
```
!plugins/<name>/
plugins/<name>/*
!plugins/<name>/plugin.json
!plugins/<name>/README.md
```

### Plugin JSON requirements

Every `plugin.json` must have at minimum:
```json
{
  "id": "plugin-id",
  "name": "Display Name",
  "version": "1.0.0",
  "description": "One-line description",
  "type": "face|page|gateway|openclaw-extension",
  "author": "Author Name",
  "license": "MIT",
  "repository": "https://github.com/MCERQUA/openvoiceui-plugins"
}
```

Gateway plugins must also have:
```json
{
  "gateway_class": "ClassName",
  "container": {
    "image": "org/image:pinned-version",
    "hostname": "name",
    "port": 12345
  }
}
```

### Registry JSON format

```json
{
  "id": "plugin-id",
  "name": "Display Name",
  "version": "1.0.0",
  "description": "One-line description",
  "type": "face|page|gateway|openclaw-extension",
  "author": "Author Name"
}
```

## PR Format

### Title
Short, under 70 chars. Prefix with type:
- `feat:` — new feature
- `fix:` — bug fix
- `chore:` — maintenance, version bumps
- `docs:` — documentation only

### Body
```markdown
## Summary
- Bullet 1
- Bullet 2
- Bullet 3
```

No test plan section. No "Generated with Claude Code" footer.

## Commit Messages

Format: `type: short description`

Types:
- `feat` — new feature
- `fix` — bug fix
- `chore` — maintenance (version bump, dep update, cleanup)
- `docs` — documentation
- `refactor` — code restructure without behavior change

Examples:
```
feat: plugin config API + admin settings panel for gateway plugins
fix: canvas auth token bridge variable name
chore: bump version to 2026.4.10
docs: remove fake email from README footer
```

Multi-line body for complex changes:
```
feat: plugin config API + admin settings panel for gateway plugins

Add configure-before-install for gateway plugins. Users enter API keys
and select provider in admin panel before installing.

- routes/plugins.py: GET/PUT config endpoints
- services/plugins.py: config service layer
- src/admin.html: config panel UI
```

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `npm-publish.yml` | Release published | Publish to npm |
| `tests.yml` | PR to main | Run test suite |
| `security.yml` | PR + schedule | Trivy security scan |
| `docs.yml` | Push to main | Deploy docs to GitHub Pages |

## Common Mistakes to Avoid

- **Releasing without Full Changelog link** — always include it
- **Inconsistent release note format** — follow the template exactly
- **Forgetting plugin stubs** — every plugin needs `plugin.json` + `README.md` in main repo
- **Debug logging in releases** — search and remove before tagging
- **Using `:latest` for container images** — always pin versions
- **Committing directly to main** — always go through dev → PR → main
- **Skipping npm verification** — always check `npm view openvoiceui version` after release
- **Mismatched versions** — `package.json`, tag, and release title must all agree
