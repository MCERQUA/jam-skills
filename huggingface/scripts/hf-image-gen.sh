#!/usr/bin/env bash
# hf-image-gen.sh — the ONE verified HF text-to-image path (2026-08-26).
#
#   usage: hf-image-gen.sh "<prompt>" <output-path> [size] [model]
#
# Provider: nscale (OpenAI-images-compatible → JSON body, base64 image).
# The old hf-inference binary path is DEAD (HTTP 410, model deprecated by provider).
#
# This script FAILS LOUD: a non-200, a missing b64_json, wrong magic bytes, or a
# decode under 10 KB all exit non-zero and write NOTHING to the output path.
# Dead HF endpoints return well-formed HTTP errors, not timeouts — an unchecked
# generator writes the error text to disk and every "does the file exist" check
# downstream passes. That happened: 6 files on a live tenant subdomain served
# 94 bytes of deprecation JSON as .jpg at HTTP 200 for 18 days.
set -uo pipefail

PROMPT="${1:?prompt required}"
OUT="${2:?output path required}"
# SIZE — "WxH". nscale SILENTLY IGNORES width/height keys (the shape the old hf-inference
# path used); it honours only `size`. A script ported by translating the URL but keeping
# width/height gets a 1024x1024 SQUARE with no error and no warning — a real, valid image
# of the wrong shape, which passes `file`, passes the magic-byte gate, and passes the size
# gate. Measured by josh-desktop 2026-08-26, same minute, same token:
#     {"width":1280,"height":853}  -> 1024x1024   (keys ignored entirely)
#     {"size":"1280x853"}          -> 1280x848    (honoured, snapped to a multiple of 16)
#     {"size":"1280x832"}          -> 1280x832    (exact)
# So prefer dimensions that are already multiples of 16, or expect a silent snap.
# The 1024x1024 DEFAULT here is deliberate but is a SQUARE — callers wanting a hero/banner
# MUST pass size explicitly. Defaulting is how every hero silently became 1:1.
SIZE="${3:-1024x1024}"
MODEL="${4:-black-forest-labs/FLUX.1-schnell}"
MIN_BYTES=10240

: "${HF_TOKEN:?HF_TOKEN not set}"
command -v jq >/dev/null || { echo "hf-image-gen: jq required" >&2; exit 4; }

TS=$(date +%s)-$$
RESP="/tmp/hf-image-$TS.json"
TMPIMG="/tmp/hf-image-$TS.bin"

CODE=$(curl -sS -o "$RESP" -w '%{http_code}' --max-time 180 \
  https://router.huggingface.co/nscale/v1/images/generations \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --arg m "$MODEL" --arg p "$PROMPT" --arg s "$SIZE" \
        '{model:$m, prompt:$p, n:1, size:$s}')")

if [ "$CODE" != "200" ]; then
  echo "hf-image-gen: FAILED http=$CODE (response kept at $RESP)" >&2
  head -c 400 "$RESP" >&2; echo >&2
  exit 1
fi

if ! jq -er '.data[0].b64_json' "$RESP" > /dev/null 2>&1; then
  echo "hf-image-gen: FAILED — 200 but no .data[0].b64_json (response kept at $RESP)" >&2
  head -c 400 "$RESP" >&2; echo >&2
  exit 2
fi

jq -r '.data[0].b64_json' "$RESP" | base64 -d > "$TMPIMG"

BYTES=$(stat -c %s "$TMPIMG" 2>/dev/null || echo 0)
MAGIC=$(head -c 8 "$TMPIMG" | od -An -tx1 | tr -d ' \n')
case "$MAGIC" in
  89504e470d0a1a0a*) EXT=png ;;
  ffd8ff*)           EXT=jpg ;;
  52494646*)         EXT=webp ;;   # RIFF....WEBP
  *) echo "hf-image-gen: FAILED — decoded bytes are not PNG/JPEG/WEBP (magic=$MAGIC, kept $TMPIMG)" >&2; exit 3 ;;
esac

if [ "$BYTES" -lt "$MIN_BYTES" ]; then
  echo "hf-image-gen: FAILED — decoded only $BYTES bytes (< $MIN_BYTES); kept $TMPIMG, wrote nothing" >&2
  exit 3
fi

# Only now does anything land at the real path. On failure the output path stays absent,
# so a downstream "does the file exist" check correctly reads FAIL instead of false-green.
case "$OUT" in
  *.$EXT) ;;
  *) echo "hf-image-gen: WARNING — output path is $OUT but the bytes are $EXT" >&2 ;;
esac
mkdir -p "$(dirname "$OUT")"
mv "$TMPIMG" "$OUT"
echo "hf-image-gen: OK $OUT ($BYTES bytes, $EXT)"
