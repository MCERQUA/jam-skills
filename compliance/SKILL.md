---
name: compliance
description: Research and monitor regulatory compliance obligations for this business. Use when the user asks about licensing, regulations, HIPAA, GDPR, OSHA, PCI, CCPA, state/federal rules, data security laws, compliance audits, or says things like "what do I need to follow legally" or "am I compliant". NEVER gives legal advice — always cites authoritative sources and recommends consulting qualified counsel.
---

# Compliance Monitoring Skill

This skill owns the per-client regulatory compliance workflow: intake, research, report generation, questionnaire scoring, and weekly monitoring of regulatory changes.

**Storage (per-client):** `~/.openclaw/workspace/business/compliance/`

```
compliance/
├── profile.json            # business facts + jurisdictions + topics
├── report.html             # canvas-ready HTML report
├── report-source.md        # markdown source the HTML was built from
├── assessment.json         # current questionnaire answers
├── action-plan.json        # prioritized actions from scoring
├── snapshots/<date>.json   # regulatory state at each run (ADDITIVE, never delete)
├── alerts.json             # { open: [], resolved: [] }
└── research/<date>/        # raw research from each run (ADDITIVE, never delete)
    ├── raw-searches.jsonl
    ├── sources.jsonl
    └── notes.md
```

## When the human agent is talking to the user

If the user asks about compliance, regulations, licensing, data security laws, HIPAA, GDPR, OSHA, PCI, CCPA, etc:

1. First check if a profile already exists: `cat ~/.openclaw/workspace/business/compliance/profile.json`
2. If it exists, answer from the report + alerts. Read `report-source.md` and `alerts.json`.
3. If no profile exists, tell the user: "I can run a full compliance research pass for your business. Open the Compliance dashboard from your desktop (or say 'open compliance') and fill in the intake form — it takes 5-10 minutes and produces a tailored report with action plan."
4. Never invent citations. Every regulation you mention must be backed by something in `research/<date>/sources.jsonl` or the live report.
5. Never offer legal advice. Always end compliance discussions with: "This is informational only — consult qualified legal counsel before acting on any specific obligation."

## When this skill is invoked by a social-dashboard spawn

The social-dashboard will exec this container with a prompt that starts with one of these headers:

- `# COMPLIANCE INTAKE RESEARCH` — follow `intake-research.md`
- `# COMPLIANCE MONITOR RUN` — follow `monitor.md` (not yet shipped in Cycle A)
- `# COMPLIANCE ASSESSMENT SCORING` — follow `assessment-score.md` (not yet shipped in Cycle A)

The spawn will include the full intake JSON or monitor input as part of the prompt body. Read it, follow the workflow in the referenced file at `/mnt/shared-skills/compliance/<file>`, and write outputs to disk. Update the run status file at `~/.openclaw/workspace/business/compliance/runs/<run_id>.json` as you progress.

## Core rules

- **Server-side storage only.** Everything you produce is written to disk inside `~/.openclaw/workspace/business/compliance/` before you report done.
- **Additive, never delete.** Snapshots, research notes, and alerts are permanent. Monitor runs write new files; they never replace old ones. Resolved alerts move to the `resolved` array, they don't vanish.
- **No hallucinated citations.** Every factual claim in the report must be traceable to a URL you actually fetched during the research pass. Sources go in `research/<date>/sources.jsonl` with `{url, title, fetched_at, content_hash}`.
- **No legal advice.** The report and every alert end with the "consult qualified legal counsel" disclaimer.
- **No emoji, no purple.** Report HTML follows the JamBot dark theme — steel-blue `#3b82f6`, amber `#f59e0b` for priority, neutral text. Never use purple, never use emoji in labels/headers.
- **Mobile first.** Report is readable on a 375px-wide phone screen. Grid layouts collapse to single column below 700px.
- **Cost discipline.** Intake research is budgeted at 40 DataForSEO/Serper calls and 80 web fetches maximum. Monitor runs are capped at 20 searches / 40 fetches.
- **Disclosure.** The generated report explicitly lists the sources monitored for this business so the user knows exactly what IS and ISN'T being watched.
