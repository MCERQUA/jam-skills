# JamBot skill allowlist + blocklist

Per anchor-18 (ClawHavoc + capability-evolver incident): the `/mnt/system/base/skills/` directory mounted into tenant containers is allowlist-only. New skills go through `playbooks/skill-install-vetting.md` before they reach this path.

## Allowlist (approved as of 2026-05-23)

| Skill | Source | Approved | Notes |
|---|---|---|---|
| `agentmail-expert` | internal | 2026-04-XX | Programmatic email; replaces Gmail OAuth (which gets accounts banned per r/openclaw 1r62ela) |
| `customer-comms` | internal | 2026-04-XX | Tenant-facing communication templates |
| `hermes-expert` | internal | 2026-04-XX | Hermes Agent docs router |
| `openclaw-expert` | internal | 2026-04-XX | This skill — OpenClaw docs router |
| `reddit` | internal | 2026-04-XX | Reddit JSON API client; no auth |
| `dataforseo` | internal | 2026-04-XX | SEO data |
| `jambot-openclaw` | internal | 2026-04-XX | JamBot ops |
| `jambot-performance` | internal | 2026-04-XX | Performance monitoring |
| `jambot-session-monitor` | internal | 2026-04-XX | Session monitoring |
| `jambot-voice-flow` | internal | 2026-04-XX | Voice gateway integration |
| `jambot-webdev` | internal | 2026-04-XX | Web dev tools |
| `marketing` | internal | 2026-04-XX | Marketing collateral |
| `netlify-site` | internal | 2026-04-XX | Netlify deploys |
| `pinokio` | internal | 2026-04-XX | Pinokio integration |
| `pricing-job-costing` | internal | 2026-04-XX | SweatShop Swag job pricing |
| `referral-program` | internal | 2026-04-XX | Referral tracking |
| `remotion-best-practices` | internal | 2026-04-XX | Remotion video patterns |
| `sales-scripts` | internal | 2026-04-XX | SweatShop Swag sales templates |
| `ssactivewear` | internal | 2026-04-XX | SSActivewear apparel catalog |
| `stitch` | internal | 2026-04-XX | (internal) |
| `twilio-dev` | internal | 2026-04-XX | Twilio integration |
| `x-api` | internal | 2026-04-XX | X/Twitter API |
| `maintenance-programs` | internal | 2026-04-XX | Tenant maintenance schedules |
| `skill-vetter` | clawhub.ai/spclaudehome | PENDING | Approve after first-tenant vetting per `playbooks/skill-install-vetting.md` |

## Blocklist (do NOT install)

| Skill | Reason | Source |
|---|---|---|
| `capability-evolver` | Exfiltration incident — data to Chinese cloud storage. Author removed but copycats may exist. | r/openclaw 1rlptnf, github.com/openclaw/clawhub#95 |
| `self-improving-agent` | 132 stars, unaudited per community signal | r/openclaw 1riiglv |
| Any ClawHub skill with author account < 30d old | Typosquatting risk per ClawHavoc campaign | anchor-18 |
| Any ClawHub skill with `scripts/` folder + no documented purpose | Code-execution surface — code review mandatory | playbook |
| `WORKFLOW_AUTO.md` skill packages | Known prompt-injection payload pattern | `annotations/security__prompt-injection.md` |

## Conditional / on-approval

| Skill | Status | Path to approval |
|---|---|---|
| `humanizer` (clawhub.ai/biostartechnology) | Pending vet | Run `playbooks/skill-install-vetting.md` on one tenant; 2-week monitor |
| `clawshell` runtime security layer | Pending vet | Same — particularly interested for multi-tenant security |
| `zero-rules` (math/timezone/currency local intercept) | Pending vet | Promising token-saver per r/openclaw 1qypanx |
| `QMD` (hybrid memory) | Pending vet — see anchor-20 | One-tenant pilot for 2 weeks before tenant-wide swap |

## Why this list is conservative

JamBot mounts `/mnt/system/base/skills/` into multiple tenant containers simultaneously. A compromised skill = mass exfiltration event. Even a popular skill with 35k installs was exfiltrating (capability-evolver). The cost of a slow allowlist is much lower than the cost of one missed scanner result.

## Adding a new skill (process)

1. Open a request: skill name, ClawHub URL, why we need it, what other skill it replaces (if any).
2. Run `playbooks/skill-install-vetting.md` on a single test tenant.
3. 2-week monitor: cost, egress, memory writes.
4. Mike-approved (production-affecting change per CLAUDE.md).
5. Add row above with `Approved <date>` and the source link.
6. Pin the version. Add to `/mnt/system/base/skills/` only AFTER all above.

## Removing a skill

1. If a security finding emerges, immediate uninstall on every tenant: `for t in $(docker ps --filter "name=jambot-" --format "{{.Names}}"); do docker exec $t openclaw skills uninstall <skill>; done`
2. Remove from this allowlist with reason.
3. Update `audit-anchors/anchor-18-clawhavoc-supply-chain.md` if relevant.

## References

- `audit-anchors/anchor-18-clawhavoc-supply-chain.md`
- `playbooks/skill-install-vetting.md`
- `annotations/skills__skill-vetter.md`
- `annotations/security__prompt-injection.md`
