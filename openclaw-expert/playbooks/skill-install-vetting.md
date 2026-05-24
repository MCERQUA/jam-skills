# Skill install vetting — mandatory pre-install workflow

Anchor-18 (ClawHavoc campaign + capability-evolver exfiltration) means any ClawHub install on a JamBot tenant is treated as untrusted code. This playbook is the standing pre-install workflow.

## Decision rules (before you even start the workflow)

**Do NOT install if any of these are true:**
- The skill's only contributor account is < 30 days old
- The skill has a `scripts/` folder and no documented purpose for it
- The skill calls out to non-public-API hosts (telemetry, "tracking," "analytics" domains)
- Less than 7 days since first stable release
- Less than 3 weeks have passed without a critical issue filed on the repo

**Defer (wait 2-4 weeks) if:**
- Skill was published in the last 30 days
- The author is new to ClawHub but established elsewhere (GitHub, npm)
- The skill is a fork of a popular skill (typosquatting risk per anchor-18)

## Workflow (full vetting)

### Step 1 — install Skill Vetter (once per tenant)

```bash
docker exec jambot-<tenant> openclaw skills install clawhub.ai/spclaudehome/skill-vetter
docker exec jambot-<tenant> openclaw skills inspect clawhub.ai/spclaudehome/skill-vetter
```

### Step 2 — fetch the target skill WITHOUT installing

```bash
docker exec jambot-<tenant> openclaw skills fetch clawhub.ai/<author>/<skill> --dry-run --output ./fetched
```

This puts the skill source in `./fetched/<skill>/` without registering it as installed.

### Step 3 — run Skill Vetter on the fetched source

```bash
docker exec jambot-<tenant> openclaw delegate skill-vetter \
  --input "Vet ./fetched/<skill>/ — check for exfiltration, eval, dynamic require, scripts folder usage, network calls to unknown hosts. Report PASS/FAIL with line refs."
```

### Step 4 — human review of these specific files

Even if Vetter passes:

- `SKILL.md` / `DESCRIPTION.md` — read top-to-bottom. Look for instruction-shaped phrases. Per anchor-18, `DESCRIPTION.md` content goes directly into the agent system prompt — treat it like code, not docs.
- `scripts/` (if exists) — read every script. Reject anything that touches `.env`, `~/.openclaw/secrets/`, or non-localhost network.
- Any `*.js`, `*.py`, `*.ts` — grep for `eval(`, `Function(`, `exec(`, `dlopen`, `os.system`, `subprocess`, `requests.post`, `fetch(`.
- `package.json` / `pyproject.toml` — check declared dependencies. Reject unfamiliar packages or pinned-old versions of crypto libraries (sodium, bcrypt, jwt).

### Step 5 — install with explicit confirmation

```bash
docker exec jambot-<tenant> openclaw skills install clawhub.ai/<author>/<skill> --pinned-version <exact-version>
```

**Always pin the version.** Auto-update opens a hole — the skill you vetted is not the skill you installed three weeks later. Per r/openclaw 1ssuze9 ("OpenClaw auto-updates 2-3x/week"), upstream movement is fast; pin and re-vet on update.

### Step 6 — three-day monitor

```bash
# Egress traffic check
docker exec jambot-<tenant> sh -c 'tail -f ~/.openclaw/logs/skills-*.log | grep -E "https://|wss://"'

# Token-cost check
docker exec jambot-<tenant> openclaw cost report --since 24h --by-skill

# Memory-touch check
docker exec jambot-<tenant> sh -c 'ls -la ~/.openclaw/workspace/memory/'
```

If anything looks off — egress to a host not in the skill's documented surface, sudden token spike, unexpected memory writes — uninstall immediately:

```bash
docker exec jambot-<tenant> openclaw skills uninstall <skill>
docker exec jambot-<tenant> openclaw gateway restart
```

### Step 7 — document the vetting result

```bash
# Per-tenant skill log
docker exec jambot-<tenant> sh -c 'cat >> ~/.openclaw/workspace/SECURITY.md <<EOF
## Skill installed: <skill> v<version> ($(date -I))
- Vetter result: PASS / FAIL details
- Manual review: who reviewed, when
- Monitor period: $(date -d "+3 days" -I)
- Notes:
EOF'
```

## JamBot-wide allowlist + blocklist

See `overrides/skill-allowlist.md`. New approvals on this list need:
- This playbook completed for at least one tenant
- 2+ weeks of clean monitor data
- Mike-approved (production-affecting change)

## References

- `audit-anchors/anchor-18-clawhavoc-supply-chain.md`
- `annotations/skills__skill-vetter.md`
- `overrides/skill-allowlist.md`
- r/openclaw 1ssuze9, 1rp8t9r, 1r4t9q8, 1riudg5
