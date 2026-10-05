---
name: sec-overdue-scan
description: Ground-truth scanner for SEC tickets — which are genuinely OPEN past SLA, and where INDEX.md and the ticket file DISAGREE (both directions, MISMATCH rows). TRIGGER before reporting "N overdue SEC tickets", in any pulse/digest/enforcement loop, or when a ticket reads closed in one place and open in another. Never grep INDEX.md alone.
---

# sec-overdue-scan (v2)

Ground-truth scanner for the SECURITY ticket index. Answers: which SEC tickets are
genuinely OPEN and past SLA — and where the INDEX and the ticket file DISAGREE, in
either direction, plus every status it cannot classify.

## Why this exists

Two months of escalations at a RESOLVED ticket (SEC-035) came from a status-parse miss.
v1 fixed the open-side only; host review (2026-10-05) found v1 would have been a new
false reporter in the other direction (INDEX closed, ticket open — SEC-017/021 are real
instances). v2 checks both directions and never resolves a disagreement silently.

## Verdicts (per side: INDEX cell, ticket file's LATEST `**Status:` line)

- CLOSED: prefix resolved/done/closed/fixed (markers stripped)
- MITIGATED: prefix mitigated — own verdict, not closed (residuals stay visible)
- OPEN: prefix open
- CANNOT-TELL: no Status line, blank, or unrecognized first word — printed as such,
  never folded into open or closed

Ticket-side ground truth is the LATEST Status line (tail -1, not -m1: SEC-007 carries a
stale OVERDUE above its RESOLVED).

## Usage

```bash
bash sec-overdue-scan.sh                 # all tickets
bash sec-overdue-scan.sh SEC-007 SEC-045 # filter demo
SEC_DIR=/path/to/SECURITY bash sec-overdue-scan.sh
```

Output rows: both-OPEN (overdue, with age from the ticket's Filed date), MISMATCH
(verdicts differ — either direction), CANNOT-TELL, MITIGATED, ticket-file-missing,
and ticket files with no INDEX row whose own status is OPEN (NO-INDEX-ROW).
Exit 0 always; count rows yourself.

## Consumer contract

Any pulse, digest, or enforcement loop reporting "N overdue SEC tickets" calls this
script instead of grepping INDEX.md; sec-enforcement-loop is expected to CALL it so the
two tools cannot disagree (host commitment, 2026-10-05). See jamfact
`jamflow.sec_incidents_down_is_a_stale_index_not_an_incident` for the raw-grep failure mode.

Owner: security-officer@mesh. Source: workspaces/security-officer/bin/sec-overdue-scan.sh.
Fleet install: host hand (pending re-review of v2, 2026-10-05).
