#!/bin/bash
# Suno Music Generation - OpenClaw Integration
# Generates AI music using Official Suno API at sunoapi.org
# Saves to OpenVoiceUI generated_music folder

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SUNO_OUTPUT_DIR:-/home/mike/WEBSITES/OpenVoiceUI/generated_music}"
PYTHON="${SUNO_PYTHON:-python3}"

# Source environment if .env exists
if [ -f "${SCRIPT_DIR}/.env" ]; then
    source "${SCRIPT_DIR}/.env"
fi

# API Configuration (Official Suno API)
SUNO_API_BASE="${SUNO_API_BASE:-https://api.sunoapi.org}"
SUNO_API_KEY="${SUNO_API_KEY:-}"
SUNO_CALLBACK_URL="${SUNO_CALLBACK_URL:-}"

# Help function
show_help() {
    cat << EOF
Suno Music Generation for OpenClaw (Official API)

Usage: $(basename "$0") [OPTIONS] PROMPT

Arguments:
  PROMPT                  Music description or lyrics

Options:
  -m, --model MODEL       Model version: v4, v4_5, v4_5PLUS, v4_5ALL, v5 (default: v5)
  -t, --title TITLE       Song title (for custom mode)
  -g, --tags TAGS         Style tags (for custom mode)
  -i, --instrumental      Generate instrumental only
  -c, --custom            Custom mode with lyrics
  -l, --lyrics-only       Generate lyrics only (no music)
  --credits               Show account credits
  --list                  List local songs
  -h, --help              Show this help

Models:
  v4         - Improved Vocals (4 min max)
  v4_5       - Smart Prompts (8 min max)
  v4_5PLUS   - Richer Tones (8 min max, highest quality)
  v4_5ALL     - Better Structure (8 min max)
  v5         - Latest Model (NEW)

Environment Variables:
  SUNO_API_KEY            API key (REQUIRED - get at https://sunoapi.org/api-key)
  SUNO_API_BASE           API base URL (default: https://api.sunoapi.org)
  SUNO_OUTPUT_DIR         Output directory (default: /home/mike/WEBSITES/OpenVoiceUI/generated_music)

Examples:
  # Generate from prompt
  $(basename "$0") "dark trap beat with heavy 808s"

  # Generate instrumental
  $(basename "$0") --instrumental "epic cinematic orchestral"

  # Generate custom song
  $(basename "$0") --custom --title "Code Dreams" --tags "electronic, synthwave" "my lyrics here"

  # Use latest model
  $(basename "$0") --model v5 "futuristic electronic track with glitchy bass"

  # Generate lyrics only
  $(basename "$0") --lyrics-only "a song about AI taking over the world"

  # Check credits
  $(basename "$0") --credits

  # List local songs
  $(basename "$0") --list

Official API: https://docs.sunoapi.org/
Get API Key: https://sunoapi.org/api-key
EOF
}

# Parse arguments
PROMPT=""
CUSTOM=false
INSTRUMENTAL=false
LYRICS_ONLY=false
TITLE=""
TAGS=""
MODEL="v5"
SHOW_CREDITS=false
LIST_SONGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -t|--title)
            TITLE="$2"
            shift 2
            ;;
        -g|--tags)
            TAGS="$2"
            shift 2
            ;;
        -i|--instrumental)
            INSTRUMENTAL=true
            shift
            ;;
        -c|--custom)
            CUSTOM=true
            shift
            ;;
        -l|--lyrics-only)
            LYRICS_ONLY=true
            shift
            ;;
        --credits)
            SHOW_CREDITS=true
            shift
            ;;
        --list)
            LIST_SONGS=true
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            show_help
            exit 1
            ;;
        *)
            PROMPT="$1"
            shift
            ;;
    esac
done

# Check for API key
if [ -z "$SUNO_API_KEY" ] && [ "$LIST_SONGS" = false ]; then
    echo "Error: SUNO_API_KEY is required." >&2
    echo "" >&2
    echo "Get your API key at: https://sunoapi.org/api-key" >&2
    echo "" >&2
    echo "Set it with:" >&2
    echo "  export SUNO_API_KEY=\"your-api-key\"" >&2
    echo "" >&2
    echo "Or use a .env file in the skill directory." >&2
    exit 1
fi

# Check Python
if ! command -v "$PYTHON" &> /dev/null; then
    echo "Error: Python not found. Set SUNO_PYTHON or install python3."
    exit 1
fi

# Handle special commands
if [ "$SHOW_CREDITS" = true ]; then
    echo "Checking credits..."
    $PYTHON "${SCRIPT_DIR}/suno_client.py" --api-base "$SUNO_API_BASE" --api-key "$SUNO_API_KEY" --credits 2>/dev/null || {
        echo "Use the Python client directly to check credits:"
        echo "$PYTHON ${SCRIPT_DIR}/suno_client.py"
    }
    exit 0
fi

if [ "$LIST_SONGS" = true ]; then
    METADATA_FILE="$OUTPUT_DIR/generated_metadata.json"
    if [ -f "$METADATA_FILE" ]; then
        echo "Local songs:"
        echo "=============="
        # Extract just filenames and titles for cleaner output
        if command -v jq &> /dev/null; then
            jq -r 'to_entries | .[] | "\(.key) -> \(.value.title)"' "$METADATA_FILE"
        else
            cat "$METADATA_FILE"
        fi
    else
        echo "No metadata file found at $METADATA_FILE"
    fi
    exit 0
fi

# Validate prompt
if [ -z "$PROMPT" ] && [ "$LYRICS_ONLY" = false ]; then
    echo "Error: PROMPT is required." >&2
    show_help
    exit 1
fi

# Build Python command
PYTHON_CMD="$PYTHON ${SCRIPT_DIR}/suno_client.py"

# Build arguments
ARGS="--model $MODEL --api-base $SUNO_API_BASE --api-key $SUNO_API_KEY"

if [ "$INSTRUMENTAL" = true ]; then
    ARGS="$ARGS --instrumental"
fi

if [ "$CUSTOM" = true ]; then
    ARGS="$ARGS --custom"
    if [ -n "$TITLE" ]; then
        ARGS="$ARGS --title \"$TITLE\""
    fi
    if [ -n "$TAGS" ]; then
        ARGS="$ARGS --tags \"$TAGS\""
    fi
fi

# Execute
echo "Generating music with Suno API..."
echo "API: $SUNO_API_BASE"
echo "Model: $MODEL"
echo "Prompt: $PROMPT"
echo ""

# Run Python client
eval "$PYTHON_CMD $ARGS \"$PROMPT\""
