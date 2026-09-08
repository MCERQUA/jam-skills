# SOURCE — where this engine copy comes from

CANONICAL: /home/mike/MIKE-AI/scripts/mesh-nightly-shipped/qa-audit-engine.py (MIKE-AI repo, host VPS)
THIS COPY: verbatim, synced 2026-09-08 by host@mesh
SHA256 AT SYNC: 1f9f894b1a782002225cea2c3be13af13a6260b140f03befebeb5e9c5a924dc0

The canonical file is the one the QA cron runs (qa-audit-next.sh, crontab 15,45 * * * *).
This copy exists so every node can READ the exact checks and so a node that has Python
Playwright can run the same instrument. It is not a second authority: if the two differ,
the canonical one is right and this one is stale. Run: bash check-sync.sh
