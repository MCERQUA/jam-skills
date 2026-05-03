#!/usr/bin/env bash
# extract-logo-colors.sh
# Sample dominant colors from a logo file and emit .brand/colors.json.
# Used by Phase 1.5 (BRAND-EXTRACT) of the website-build pipeline.
#
# Usage:
#   extract-logo-colors.sh --logo <path-or-url> --output <colors.json>
#
# Exit codes:
#   0 - success, colors.json written
#   1 - logo not readable (download/copy/identify failed)
#   2 - no usable colors found (all white/black/transparent)

set -euo pipefail

LOGO=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --logo) LOGO="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$LOGO" || -z "$OUTPUT" ]]; then
  echo "ERROR: --logo and --output are both required" >&2
  exit 1
fi

# --- Resolve logo to a local file --------------------------------------------
TMPDIR_LOGO="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_LOGO"' EXIT
LOCAL_LOGO="$TMPDIR_LOGO/logo.in"

if [[ "$LOGO" =~ ^https?:// ]]; then
  if ! curl -fsSL "$LOGO" -o "$LOCAL_LOGO"; then
    echo "ERROR: failed to download logo from $LOGO" >&2
    exit 1
  fi
else
  if [[ ! -r "$LOGO" ]]; then
    echo "ERROR: logo file not readable: $LOGO" >&2
    exit 1
  fi
  cp "$LOGO" "$LOCAL_LOGO"
fi

if ! identify "$LOCAL_LOGO" >/dev/null 2>&1; then
  echo "ERROR: ImageMagick cannot identify logo file" >&2
  exit 1
fi

# --- Extract top colors via ImageMagick histogram ---------------------------
# Flatten transparency onto white, drop alpha, then bucket into 16 colors.
# We over-sample (16) so role-clustering has options after rejecting purple/white/black.
HIST="$(convert "$LOCAL_LOGO" \
  -background white -alpha remove -alpha off \
  -resize 256x256 \
  -depth 8 \
  +dither -colors 16 \
  -format "%c" histogram:info:- 2>/dev/null || true)"

if [[ -z "$HIST" ]]; then
  echo "ERROR: ImageMagick produced no histogram" >&2
  exit 1
fi

# --- Parse + cluster via embedded python ------------------------------------
mkdir -p "$(dirname "$OUTPUT")"

PYSCRIPT="$TMPDIR_LOGO/cluster.py"
cat >"$PYSCRIPT" <<'PYEOF'
import json, os, re, sys, colorsys

hist_text = sys.stdin.read()
output_path = os.environ["OUTPUT"]

# Histogram lines look like:
#   12345: ( 12, 34,255) #0C22FF srgb(12,34,255)
line_re = re.compile(
    r"^\s*(\d+):\s*\(\s*([\d.]+),\s*([\d.]+),\s*([\d.]+).*?\)\s*#([0-9A-Fa-f]{6,8})"
)

raw = []
for line in hist_text.splitlines():
    m = line_re.match(line)
    if not m:
        continue
    count = int(m.group(1))
    r = int(round(float(m.group(2))))
    g = int(round(float(m.group(3))))
    b = int(round(float(m.group(4))))
    hex_full = m.group(5)
    hex6 = hex_full[:6].upper()
    raw.append({"count": count, "r": r, "g": g, "b": b, "hex": "#" + hex6})

if not raw:
    print("ERROR: no colors parsed from histogram", file=sys.stderr)
    sys.exit(2)

def to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (h * 360.0, s * 100.0, l * 100.0)

def hsl_str(h, s, l):
    return f"{h:.0f} {s:.0f}% {l:.0f}%"

def is_near_white(r, g, b, l):
    # Cream / off-white / page-background colors. L > 88 is too light to be a brand color.
    return min(r, g, b) >= 220 or l >= 88.0
def is_near_black(r, g, b, l):
    return max(r, g, b) <= 25 or l <= 8.0
def is_purple(h, s):
    # Forbidden hue range per pipeline rules: indigo through violet.
    return 240.0 <= h <= 290.0 and s >= 15.0
def is_grayish(s):
    return s < 10.0

warnings = []

# Tag each color
tagged = []
for c in raw:
    h, s, l = to_hsl(c["r"], c["g"], c["b"])
    tag = "ok"
    if is_near_white(c["r"], c["g"], c["b"], l):
        tag = "white"
    elif is_near_black(c["r"], c["g"], c["b"], l):
        tag = "black"
    elif is_grayish(s):
        tag = "neutral"
    elif is_purple(h, s):
        tag = "purple"
    tagged.append({**c, "h": h, "s": s, "l": l, "tag": tag})

usable = [c for c in tagged if c["tag"] not in ("white", "black", "purple")]
chromatic = [c for c in usable if c["tag"] != "neutral"]
chromatic.sort(key=lambda c: c["count"], reverse=True)

if any(c["tag"] == "purple" for c in tagged):
    warnings.append("rejected purple/indigo color from logo palette (hue 240-290)")

is_monochrome = False
if not chromatic:
    # Monochrome logo (white-on-color, single-color, etc.)
    is_monochrome = True
    warnings.append("logo appears monochrome — no chromatic colors found, fallback should be applied by Phase 1.5")
    primary = {"hex": "#3B82F6", "h": 217.0, "s": 91.0, "l": 60.0}  # tailwind blue-500
    accent = {"hex": "#06B6D4", "h": 189.0, "s": 94.0, "l": 43.0}   # tailwind cyan-500
else:
    primary = chromatic[0]
    # accent = next chromatic with hue >= 30deg from primary, else 2nd chromatic, else primary
    accent = None
    for c in chromatic[1:]:
        if abs(c["h"] - primary["h"]) >= 30.0:
            accent = c
            break
    if accent is None:
        accent = chromatic[1] if len(chromatic) > 1 else primary

# Neutral: prefer mid-gray from tagged neutrals; else compute from primary luminance
neutrals = [c for c in tagged if c["tag"] == "neutral"]
if neutrals:
    neutrals.sort(key=lambda c: abs(c["l"] - 50.0))
    neutral = neutrals[0]
else:
    neutral = {"hex": "#64748B", "h": 215.0, "s": 19.0, "l": 35.0}  # tailwind slate-500

def role(c):
    return {"hex": c["hex"].upper(), "hsl": hsl_str(c["h"], c["s"], c["l"])}

dominant_hues = sorted({round(c["h"]) for c in chromatic[:5]})

result = {
    "primary": primary["hex"].upper(),
    "primaryHsl": hsl_str(primary["h"], primary["s"], primary["l"]),
    "accent": accent["hex"].upper(),
    "accentHsl": hsl_str(accent["h"], accent["s"], accent["l"]),
    "neutral": neutral["hex"].upper(),
    "neutralHsl": hsl_str(neutral["h"], neutral["s"], neutral["l"]),
    "dominantHues": dominant_hues,
    "isMonochrome": is_monochrome,
    "warnings": warnings,
    "_source": "extract-logo-colors.sh (ImageMagick histogram, 16-color quantization)",
}

# Sanity gate: even after rejection, if primary somehow lands purple, fail.
if 240.0 <= primary["h"] <= 290.0 and primary["s"] >= 15.0:
    print(f"ERROR: primary color {primary['hex']} is in forbidden hue range", file=sys.stderr)
    sys.exit(2)

# Flag near-monochrome palettes (logos with a single hue family) so Phase 4
# knows to compute a complementary accent rather than ship near-duplicate primary+accent.
if not is_monochrome and abs(primary["h"] - accent["h"]) < 20.0:
    warnings.append(
        f"primary ({primary['hex']}) and accent ({accent['hex']}) are within 20deg "
        f"hue — design-system phase should compute a complementary accent"
    )
    result["warnings"] = warnings  # ensure update visible in serialized result

with open(output_path, "w") as f:
    json.dump(result, f, indent=2)
    f.write("\n")

print(f"OK: wrote {output_path}")
print(f"  primary={result['primary']} accent={result['accent']} neutral={result['neutral']}")
if warnings:
    print(f"  warnings: {warnings}")
PYEOF

OUTPUT="$OUTPUT" python3 "$PYSCRIPT" <<<"$HIST"
