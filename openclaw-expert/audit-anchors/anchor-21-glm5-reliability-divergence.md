---
anchor: 21
slug: glm5-reliability-divergence
status: partially-confirmed
introduced: 2026-05 community observation window
changelog_line: null
upstream_pages:
  - https://docs.openclaw.ai/providers/zai.md
  - https://docs.openclaw.ai/providers/glm.md
old_behavior: "GLM-5-turbo (via z.ai) treated as a stable cheap-and-good primary for agentic tasks across the community."
new_behavior: "Community reports diverge sharply in mid-2026: some users report GLM 5.1 as 'absolute garbage' for agentic tasks (floods chat with code dumps), others run GLM-5 fine 24/7. Likely depends on SOUL.md + anti-loop rules being well-formed. No single regression — front-load discipline matters."
skill_files_affected:
  - annotations/providers__zai.md (extend with the divergence + JamBot triage)
  - overrides/glm5-turbo-pin.md (new — JamBot version-pin policy + fallback chain)
sources:
  - https://reddit.com/comments/1sdd32v (228/213 — OP migrated off GLM 5.1 "absolute garbage for agentic tasks")
  - https://reddit.com/comments/1qzyibu (301/91 — GLM Coding Plan $3/mo cited as working primary)
  - https://reddit.com/comments/1r4t9q8 (384/80 — u/Strange_Squirrel_886: GLM-5 has "some success")
  - https://reddit.com/comments/1sbshpu (637/429 — u/PureSignalLove: GLM 5.1 / MiniMax 2.7 / Tri-* "1/10th the price or less")
related_anchors:
  - 9 (GLM-5 consecutive-turn context-preservation fix in v5.2 — different issue)
---

# Anchor #21 — GLM-5 reliability diverges sharply across community

## What changed

This isn't a version flip in the OpenClaw codebase — it's a divergent community signal on GLM-5/5.1 (via z.ai) as an agentic-task primary. As of mid-2026:

- **Negative signal (r/openclaw 1sdd32v):** OP retracted earlier endorsement of MiniMax 2.7 (1s3c8b0); migrated to Codex Pro $100; called GLM 5.1 "absolute garbage for agentic tasks" — floods Telegram with code dumps instead of following protocol.
- **Neutral signal (1r4t9q8 u/Strange_Squirrel_886, +7):** "GLM-5 + MiniMax + Kimi + Stepfun 3.5 + DeepSeek 3.2 all some success."
- **Positive signal (1qzyibu u/TacomaKMart +11):** GLM Coding Plan $3/month + MiniMax + Kimi runs fine; first-month negotiable to $0.99.
- **Positive signal (1sbshpu u/PureSignalLove +9):** "GLM 5.1 / MiniMax 2.7 / Tri-* are 1/10th the price or less" — endorsing cheap-primary route.
- **Positive signal (1sdd32v u/Blade999666 +13):** GLM 5 running 24/7 fine on his setup.

## Hypothesis

Per the broader r/openclaw discourse (1riiglv, 1r71you, 1r4t9q8): rule adherence degrades over long sessions regardless of model; fix is SHORTER + SHARPER rules, not adding more. GLM-5 may be more sensitive to rule load than Sonnet — if a tenant has a 50-line SOUL.md + 12 conflicting skills, GLM-5 degrades faster than Sonnet would.

## Why it matters for JamBot

JamBot pins GLM-5-turbo via z.ai as primary (per memory `glm-primary-temporary-swap`). The community divergence means:

1. **Don't panic-switch** when a tenant reports an off day. First check SOUL.md + skill count + anti-loop rules.
2. **Pin a known-good GLM model version** at the gateway level; don't ride z.ai's silent server-side updates.
3. **Have a documented fallback chain** that is NOT also GLM-via-z.ai (see anchor-9 for the consecutive-turn fix that only helps when both calls actually reach z.ai).

## Triage when a tenant reports "GLM is acting weird"

1. Get a sample bad turn from `~/.openclaw/logs/`. Look for: code dumps where prose was asked, chunked-format violations, rule violations.
2. Check the **rule budget** — count lines in SOUL.md, AGENTS.md, MEMORY.md, TOOLS.md. If total system prompt is approaching the prompt-cache budget, GLM-5 degrades faster than Sonnet. See anchor-05 (per-file bootstrap caps).
3. Check anti-loop rules are present (canonical block in `annotations/security__anti-loop.md`).
4. Check `meta.lastTouchedVersion` (anchor-7) — did gateway upgrade to a new build without the migration running cleanly?
5. Only AFTER 1-4: consider escalating to Sonnet via API for the affected workflow.

## JamBot fallback chain recommendation

```
primary:   zai/glm-5-turbo                (account A)
fallback:  zai/glm-5-turbo                (account B, same model)
fallback:  anthropic/claude-haiku-4-5     (token-pay only when both Z.AI fail)
```

Adding direct-Anthropic as a third fallback was already flagged in SKILL.md §1A as a recurring need. This anchor formalizes it.

## References

- Reddit threads cited above (the divergence is the data — not a single source)
- Related: anchor-9 (consecutive-turn context preservation in v5.2 — solves a DIFFERENT GLM issue, don't confuse)
- JamBot memory: `glm-primary-temporary-swap.md` for the original primary-flip context
