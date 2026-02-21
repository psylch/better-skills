#!/usr/bin/env bash
# Skill profile analyzer for skill-iterate.
# Extracts structured facts about a skill directory as JSON.
#
# Usage: analyze.sh <skill-path>
#
# Output: JSON profile to stdout, errors to stderr.

set -uo pipefail

if [ $# -lt 1 ]; then
    echo '{"error": "missing_path", "hint": "Usage: analyze.sh <skill-path>", "recoverable": true}' >&2
    exit 1
fi

SKILL_PATH="$(cd "$1" 2>/dev/null && pwd)" || {
    echo "{\"error\": \"invalid_path\", \"hint\": \"Not a valid directory: $1\", \"recoverable\": true}" >&2
    exit 1
}

SKILL_MD="$SKILL_PATH/SKILL.md"

if [ ! -f "$SKILL_MD" ]; then
    echo "{\"error\": \"no_skill_md\", \"hint\": \"SKILL.md not found in $SKILL_PATH\", \"recoverable\": true}" >&2
    exit 1
fi

# --- Extract frontmatter fields ---
NAME=""
DESC=""
in_frontmatter=false
frontmatter_found=false

while IFS= read -r line; do
    if [ "$line" = "---" ]; then
        if [ "$frontmatter_found" = false ]; then
            in_frontmatter=true
            frontmatter_found=true
            continue
        else
            break
        fi
    fi
    if [ "$in_frontmatter" = true ]; then
        case "$line" in
            name:*)
                NAME="$(echo "$line" | sed 's/^name:[[:space:]]*//' | sed 's/^["'\'']//' | sed 's/["'\'']$//')"
                ;;
            description:*)
                DESC="$(echo "$line" | sed 's/^description:[[:space:]]*//' | sed 's/^["'\'']//' | sed 's/["'\'']$//')"
                ;;
        esac
    fi
done < "$SKILL_MD"

DESC_LEN=${#DESC}

# --- Detect skill level ---
LEVEL="l0"
HAS_SCRIPTS=false
HAS_REFERENCES=false
SCRIPT_FILES="[]"
REFERENCE_FILES="[]"

if [ -d "$SKILL_PATH/scripts" ]; then
    HAS_SCRIPTS=true
    # Collect script filenames
    SCRIPT_LIST=""
    for f in "$SKILL_PATH/scripts"/*; do
        [ -f "$f" ] || continue
        fname="$(basename "$f")"
        SCRIPT_LIST="${SCRIPT_LIST:+$SCRIPT_LIST, }\"scripts/$fname\""
    done
    SCRIPT_FILES="[${SCRIPT_LIST}]"

    # Detect level by script type
    if compgen -G "$SKILL_PATH/scripts/*.py" >/dev/null 2>&1; then
        LEVEL="l1"
    elif compgen -G "$SKILL_PATH/scripts/*.sh" >/dev/null 2>&1; then
        LEVEL="l0plus"
    fi
fi

if [ -d "$SKILL_PATH/references" ]; then
    HAS_REFERENCES=true
    REF_LIST=""
    for f in "$SKILL_PATH/references"/*; do
        [ -f "$f" ] || continue
        fname="$(basename "$f")"
        [ "$fname" = ".gitkeep" ] && continue
        REF_LIST="${REF_LIST:+$REF_LIST, }\"references/$fname\""
    done
    REFERENCE_FILES="[${REF_LIST}]"
fi

# --- Count lines ---
TOTAL_LINES=$(wc -l < "$SKILL_MD" | tr -d ' ')

SCRIPT_TOTAL_LINES=0
if [ "$HAS_SCRIPTS" = true ]; then
    for f in "$SKILL_PATH/scripts"/*; do
        [ -f "$f" ] || continue
        lines=$(wc -l < "$f" | tr -d ' ')
        SCRIPT_TOTAL_LINES=$((SCRIPT_TOTAL_LINES + lines))
    done
fi

# --- Extract markdown sections (## headings) ---
SECTIONS=""
while IFS= read -r line; do
    heading="$(echo "$line" | sed 's/^##[[:space:]]*//')"
    SECTIONS="${SECTIONS:+$SECTIONS, }\"$heading\""
done < <(grep '^## ' "$SKILL_MD")
SECTIONS="[${SECTIONS}]"

# --- Feature detection in SKILL.md content ---
CONTENT="$(cat "$SKILL_MD")"

has_pattern() {
    grep -qi "$1" "$SKILL_MD" && echo true || echo false
}

HAS_PREFLIGHT=$(has_pattern "preflight")
HAS_SETUP=$(has_pattern "setup")
HAS_DEGRADATION=$(has_pattern "degradation")
HAS_TROUBLESHOOTING=$(has_pattern "troubleshooting")
HAS_CREDENTIAL_TABLE=$(has_pattern "credential")

# --- TODO count ---
TODO_COUNT=$(grep -c -i '\bTODO\b' "$SKILL_MD" 2>/dev/null || true)
TODO_COUNT=${TODO_COUNT:-0}

# --- Template placeholder count ---
TEMPLATE_COUNT=$(grep -c -E '\{\{[A-Z_]+\}\}' "$SKILL_MD" 2>/dev/null || true)
TEMPLATE_COUNT=${TEMPLATE_COUNT:-0}

# --- Detect environment strategy (L1 only) ---
ENV_STRATEGY="none"
if [ "$LEVEL" = "l1" ]; then
    ENV_STRATEGY="stdlib"
    # Check for uv (PEP 723 header) or venv (run.sh wrapper exists)
    if [ -f "$SKILL_PATH/scripts/main.py" ]; then
        if grep -q '# /// script' "$SKILL_PATH/scripts/main.py" 2>/dev/null; then
            ENV_STRATEGY="uv"
        fi
    fi
    if [ -f "$SKILL_PATH/scripts/run.sh" ]; then
        ENV_STRATEGY="venv"
    fi
fi

# --- Detect trigger phrases in description ---
HAS_TRIGGER_PHRASES=false
if echo "$DESC" | grep -qiE "use when|should be used|when the user says|trigger"; then
    HAS_TRIGGER_PHRASES=true
fi

# --- Output JSON ---
cat <<ENDJSON
{
  "status": "ok",
  "profile": {
    "name": "$NAME",
    "level": "$LEVEL",
    "has_frontmatter": $frontmatter_found,
    "description_length": $DESC_LEN,
    "description_has_trigger_phrases": $HAS_TRIGGER_PHRASES,
    "total_lines": $TOTAL_LINES,
    "sections": $SECTIONS,
    "has_scripts": $HAS_SCRIPTS,
    "script_files": $SCRIPT_FILES,
    "script_total_lines": $SCRIPT_TOTAL_LINES,
    "has_references": $HAS_REFERENCES,
    "reference_files": $REFERENCE_FILES,
    "has_preflight": $HAS_PREFLIGHT,
    "has_setup": $HAS_SETUP,
    "has_degradation": $HAS_DEGRADATION,
    "has_troubleshooting": $HAS_TROUBLESHOOTING,
    "has_credential_table": $HAS_CREDENTIAL_TABLE,
    "todo_count": $TODO_COUNT,
    "template_placeholder_count": $TEMPLATE_COUNT,
    "env_strategy": "$ENV_STRATEGY"
  },
  "hint": "Skill profile extracted. Level: $LEVEL, $TOTAL_LINES lines, $TODO_COUNT TODO(s)."
}
ENDJSON
