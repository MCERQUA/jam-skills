#!/usr/bin/env bash
# check-sync.sh — is the shared copy of qa-audit-engine.py identical to the canonical host file?
# Exit 0 = identical · 1 = DRIFTED (re-copy from canonical) · 2 = CANNOT-TELL (canonical not readable from here)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANON=/home/mike/MIKE-AI/scripts/mesh-nightly-shipped/qa-audit-engine.py
[ -r "$CANON" ] || { echo "CANNOT-TELL: $CANON not readable from this node (run on the host)"; exit 2; }
a=$(sha256sum "$CANON" | cut -c1-64); b=$(sha256sum "$HERE/qa-audit-engine.py" | cut -c1-64)
if [ "$a" = "$b" ]; then echo "IN-SYNC $a"; exit 0; fi
echo "DRIFTED canonical=$a copy=$b — re-copy: cp -p $CANON $HERE/qa-audit-engine.py && update SOURCE.md"; exit 1
