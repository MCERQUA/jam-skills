---
name: verification-pass
description: Run a 5-field verification pass on any artifact (script, doc, deliverable, RFC) before marking it done. Operationalizes Mike directive #3 (2026-05-20) — DoD requires proof artifact, failure-mode pre-mortem, could-be-better note, reviewer tag, failure-doc pointer. Produces a `cr.verification` JSON object drop-in compatible with src-desktop's reflection-to-action-closure RFC §3 schema and danielle-desktop's autonomy-guardrails RFC §6 tier table. Use BEFORE acking any worker deliverable, BEFORE marking any CR `verified`, BEFORE publishing any task-result with KIND=task-result. Trigger phrases — "verification pass", "verify deliverable", "DoD check", "is this done", "mark verified", "sign off", "/vp".
metadata:
  schema_alignment:
    - reflection-to-action-closure-rfc §3 (cr.verification)
    - reflection-to-action-closure-rfc §13 (DoD)
    - autonomy-guardrails-rfc §6 (verification × tier table)
  authority:
    - mike directive #3, 2026-05-20T01:30Z (via host@mesh announcement)
---

# verification-pass

A reviewer's mechanical checklist for closing the gap Mike named on 2026-05-20: *"plan and grow ASSUMING everything will fail. plan how to review the result, see what went wrong or what could be better, OR if it failed BEFORE we mark it done."*

This skill does NOT define the DoD — that lives in danielle-desktop's autonomy-guardrails RFC §6 and src-desktop's reflection-to-action-closure RFC §13. This skill is the **executable layer** that produces the verification artifact those RFCs require.

## When to invoke

- BEFORE acking a worker deliverable with KIND=task-result
- BEFORE marking a `cr.json` field `applied_state: verified`
- BEFORE publishing any "done" claim to host@mesh or chatroom
- WHEN a peer asks "is this done" or "sign this off"
- WHEN auto-applying a Lane A CR (verification still required, even if approval was auto)

## The 5 fields

Every verification produces an object with these keys. **Any null field = NOT verified.**

| Field | What it is | How to fill it |
|-------|-----------|----------------|
| `proof_artifact` | Concrete evidence the work happened | Path to: screenshot, curl 200 log, test pass output, row count from DB query, mesh file write-receipt. NOT "I ran it and it worked." NOT a description — an actual artifact path. |
| `failure_mode_premortem` | What could break, what did break | List of failure paths. Even if none materialized, document the ones you considered. Cite `failure_modes` enum if applicable (see reflection-closure RFC §12). |
| `could_be_better` | Honest critique even on success | What you'd do differently next time. "Nothing" is an invalid answer — at minimum, note what you didn't test or didn't optimize. |
| `reviewer_agent` | Who actually verified | URI of the agent that ran this pass. If `reviewer_agent == owner`, MUST also set `self_verified: true`. |
| `failure_doc_path` | Where failures (if any) were documented | Path to retrospective entry, dead-letter, or `null` if the work passed clean. NEVER memory-hole a failure. |

## Output schema (drop-in compatible)

```json
{
  "proof_artifact": "/peer-inbox/host/.read/2026-05-19-169-...verified.md",
  "failure_mode_premortem": "openclaw.json extraDirs path is dangling; future sync may use it as source-of-truth and wipe runtime",
  "could_be_better": "submesh-control + README.md still drift across set diff; mirror canonical both ways",
  "reviewer_agent": "josh-desktop@mesh",
  "self_verified": false,
  "failure_doc_path": null
}
```

This object lands directly into `cr.json.verification` (reflection-closure RFC §3 schema).

## Procedure

For each artifact under review:

1. **Locate the proof artifact.** If you cannot produce a path to evidence on disk, the work is NOT verified. Stop. Tell the owner what evidence to produce.

2. **Independently exercise the artifact.** Re-run the test suite. Re-read the script for the claim. Check the output file exists with non-zero size. Self-reports do NOT count — verify the substrate yourself.

3. **Cross-check against author claims.** If author's SHARED-NOTES or commit message describes behavior X, does the code/output actually do X? Drift between docs and code is the most common failure surface.

4. **Document the failure-mode pre-mortem.** Before declaring done, write down at least one way the work could break in production. Even green test suites have failure paths.

5. **Write a "could be better" line.** Always. If you can't think of one, you didn't review hard enough.

6. **Assign reviewer.** If you are the artifact's author, set `reviewer_agent: <you>` AND `self_verified: true`. The autonomy-guardrails RFC §6 permits this at Tier 1; Tier 2/3 SHOULD have a non-author reviewer.

7. **Decide failure_doc_path.** Did anything fail or nearly fail? Document it at `/mesh/BLACKBOARD/failure-modes/<YYYY-MM-DD>-<slug>.md` and put that path in the field. If clean: `null` is acceptable.

8. **Emit the JSON object.** Write to the relevant `cr.json.verification` field, or include in the task-result body, or paste into the BLACKBOARD entry.

## Worked example (today, 2026-05-19 checkpoint-orchestrator)

```json
{
  "proof_artifact": "/workspace/.agents/checkpoint-orchestrator-2026-05-19/worker-c/run-all-result.txt (5/5 PASS)",
  "failure_mode_premortem": "SHARED-NOTES drift on point 3 (offline-reason text) — worker-a's notes claimed `timeout`, actual Phase 1 emits `send-failed-rc-3`. Caught at fixture-pin stage by worker-c. Would have shipped wrong-docs if reviewer had only read SHARED-NOTES without cross-reading the script.",
  "could_be_better": "Worker-a Phase 1 could normalize FAIL_REASON to plain `other` for cleaner enum; current `send-failed-rc-$rc` is informative but breaks enum-purity. Cosmetic — left to worker-a's call.",
  "reviewer_agent": "josh-desktop@mesh",
  "self_verified": false,
  "failure_doc_path": null
}
```

Notes on what this object enabled:
- The failure-mode pre-mortem became the in-place SHARED-NOTES correction.
- `reviewer_agent != author` satisfied Tier 2 reviewer-rotation (sub-mesh deliverable; non-author reviewer).
- `failure_doc_path: null` is correct — no failure occurred, just a documentation drift caught at fixture-pin time.

## Anti-patterns (auto-reject these)

- `proof_artifact: "ran the tests, they passed"` — not a path, not an artifact. Reject.
- `failure_mode_premortem: "nothing could go wrong"` — reject. There's always at least one failure path.
- `could_be_better: "N/A"` or `""` — reject. You didn't review hard enough.
- `reviewer_agent: <author>` with `self_verified: false` — schema violation. Either flip the flag or get a peer.
- `failure_doc_path: null` when the task transcript clearly shows a failed attempt — memory-holing. Reject and link the failure surface.

## Integration with sibling RFCs

- **autonomy-guardrails-rfc §6 (danielle-desktop):** the per-tier requirement matrix maps directly to this skill's output. Tier 1 allows `self_verified: true`. Tier 2 prefers peer reviewer; allows self with explicit tag. Tier 3 requires `reviewer_agent ≠ owner`.
- **reflection-to-action-closure-rfc §13 (src-desktop):** this skill produces the exact JSON shape required for CR transition `applied → verified`. The apply cron rejects the transition if any field is null — this skill's procedure prevents that rejection.
- **reflection-to-action-closure-rfc §11 Rule 6:** the citation in a `--vote=block --failure-mode=<enum>` IS this skill's `failure_mode_premortem` field for the block-as-CR-action. Drop-in compatible.

## Reviewer-rotation rule (proposed amendment to §11)

Companion to this skill — proposed Rule 7 for the smallest rule-set:

```
Rule 7 (Reviewer rotation): sub-mesh deliverables (any task-result from
    a worker pool destined for host or another tenant) MUST get reviewed
    by a non-author peer before the broadcast-ready ack. Author MAY
    self-review when no peer is available within the deadline window,
    but MUST tag self_verified=true and the pre-mortem field MUST be
    populated. Self-verified Tier 2+ work enters the request-triage rail
    at Mike-greenlit-or-skipped instead of auto-shipping.
```

Status: PROPOSED, agenda item H3 for tonight's BIG meeting. If accepted, becomes Rule 7 in src-desktop's RFC §11 and gets cross-referenced from danielle-desktop's autonomy-guardrails §6 reviewer-agent row.

## CLI variant (proposed, not yet built)

Future: `verification-pass --artifact <path> --owner <agent> --tier <1|2|3>` emits the JSON to stdout, with prompts for each unfilled field. Out of scope for tonight's deliverable — manual procedure above is the v0.1 shipping today.
