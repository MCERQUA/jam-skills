#!/bin/sh
# archive_sources.sh — ARCHIVE (never delete) harvested source pages out of the
# live picker, with a manifest so anything can be restored. Proven on the
# Cortez cleanup (65 pages archived, client trust kept because nothing was lost).
#
# Usage: archive_sources.sh <sources-dir> <archive-dir> <captions.json>
#   Moves every source file named in captions.json (field "source") that still
#   lives in <sources-dir> into <archive-dir>/YYYYMMDD-HHMMSS/, writes MANIFEST.txt.
set -eu
SRC=${1:?sources dir}; ARC=${2:?archive dir}; JSN=${3:?captions.json}

[ -f "$JSN" ] || { echo "no json: $JSN" >&2; exit 1; }
STAMP=$(date +%Y%m%d-%H%M%S); DEST="$ARC/$STAMP"; mkdir -p "$DEST"

python3 - "$JSN" <<'EOF' > "$DEST/sources.txt"
import json,sys
for it in json.load(open(sys.argv[1])):
    print(it["source"])
EOF

MOVED=0
while IFS= read -r f; do
  [ -f "$SRC/$f" ] || continue
  mv "$SRC/$f" "$DEST/$f"; MOVED=$((MOVED+1))
done < "$DEST/sources.txt"

{ echo "archived $MOVED files from $SRC on $STAMP (from $JSN)"; cat "$DEST/sources.txt"; } \
  > "$DEST/MANIFEST.txt"
echo "archived $MOVED source page(s) -> $DEST (restore with: mv $DEST/* back)"
