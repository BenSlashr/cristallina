#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# verify-articles.sh
# Quality verification for content articles
#
# Checks: accents, forbidden words, typographic chars, callouts,
# word count, frontmatter, and optional build.
#
# Usage: ./scripts/verify-articles.sh <slug1> [slug2] [slug3] ...
#        ./scripts/verify-articles.sh --all
#        ./scripts/verify-articles.sh --all --build
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SITE_DIR="$PROJECT_DIR/site"
# TODO: Adjust content directory for your project
CONTENT_DIR="$SITE_DIR/src/content/guides"
RUN_BUILD=false

# --- Parse args ---
SLUGS=()
for arg in "$@"; do
    if [ "$arg" = "--build" ]; then
        RUN_BUILD=true
    elif [ "$arg" = "--all" ]; then
        while IFS= read -r f; do
            [ -n "$f" ] && SLUGS+=("$(basename "$f" .md)")
        done < <(find "$CONTENT_DIR" -name "*.md" ! -name "index.md" -type f 2>/dev/null)
    else
        SLUGS+=("$arg")
    fi
done

if [ ${#SLUGS[@]} -eq 0 ]; then
    echo "Usage: $0 <slug1> [slug2] ... [--build]"
    echo "       $0 --all [--build]"
    echo ""
    echo "  --all    Verify all articles (excluding index.md)"
    echo "  --build  Run Astro build after verification"
    exit 1
fi

# --- Forbidden words pattern ---
# TODO: Customize this list for your domain and language
FORBIDDEN='crucial|fondamental|primordial|incontournable|néanmoins|toutefois|dorénavant|dès lors|il convient de|captivant|fascinant|révolutionnaire|novateur|époustouflant|majestueux|remarquable|exceptionnel|inégalé|indéniablement|assurément|indubitablement|incontestablement|véritablement|considérablement|substantiellement|pléthore|myriade|subséquent|tapisserie|pierre angulaire|fer de lance|exacerber|appréhender|corroborer|éluder|entraver|préconiser|prôner|stipuler|soulignons que|notons que|mentionnons que'

# --- Typographic chars to detect (em-dash, smart quotes, ellipsis) ---
BAD_PATTERN="[—–$(printf '\xe2\x80\x98\xe2\x80\x99\xe2\x80\x9c\xe2\x80\x9d')…]"

# --- Header ---
printf "%-35s %6s %5s %4s %4s %5s  %s\n" "Article" "Words" "Acc" "Fbd" "Typo" "Call" "Status"
printf "%-35s %6s %5s %4s %4s %5s  %s\n" "---" "-----" "---" "---" "----" "----" "------"

TOTAL_ERRORS=0

for SLUG in "${SLUGS[@]}"; do
    # Find file
    FILEPATH=$(find "$CONTENT_DIR" -name "$SLUG.md" -type f 2>/dev/null | head -1)
    if [ -z "$FILEPATH" ]; then
        printf "%-35s %6s %5s %4s %4s %5s  %s\n" "$SLUG" "-" "-" "-" "-" "-" "NOT FOUND"
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
        continue
    fi

    # Metrics
    WORDS=$(awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$FILEPATH" | wc -w | tr -d ' ') || WORDS=0
    ACCENTS=$(grep -o '[éèêëàâùûîïôçÉÈÊËÀÂÙÛÎÏÔÇ]' "$FILEPATH" | wc -l | tr -d ' ') || ACCENTS=0
    INTERDIT=$(grep -ciE "$FORBIDDEN" "$FILEPATH") || INTERDIT=0
    TYPO=$(grep -c "$BAD_PATTERN" "$FILEPATH") || TYPO=0
    CALLOUTS=$(grep -c '> \[!' "$FILEPATH") || CALLOUTS=0
    MERMAID=$(grep -c '\`\`\`mermaid' "$FILEPATH") || MERMAID=0

    # Status
    ERRORS=0
    ISSUES=""
    [ "$ACCENTS" -lt 50 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}acc "
    [ "$INTERDIT" -gt 0 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}fbd "
    [ "$TYPO" -gt 0 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}typo "
    [ "$CALLOUTS" -lt 3 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}call< "
    [ "$CALLOUTS" -gt 5 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}call> "
    [ "$MERMAID" -lt 1 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}mmd< "
    [ "$MERMAID" -gt 3 ] && ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}mmd> "
    [ "$WORDS" -gt 3000 ] && ISSUES="${ISSUES}long "
    if ! head -1 "$FILEPATH" | grep -q '^---'; then
        ERRORS=$((ERRORS+1)) && ISSUES="${ISSUES}fm "
    fi

    if [ "$ERRORS" -gt 0 ]; then
        STATUS="ERR: ${ISSUES}"
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
    elif [ -n "$ISSUES" ]; then
        STATUS="WARN: ${ISSUES}"
    else
        STATUS="OK"
    fi

    printf "%-35s %6s %5s %4s %4s %5s %4s  %s\n" "$SLUG" "$WORDS" "$ACCENTS" "$INTERDIT" "$TYPO" "$CALLOUTS" "$MERMAID" "$STATUS"
done

# --- Detail of forbidden words ---
echo ""
HAS_VIOLATIONS=false
for SLUG in "${SLUGS[@]}"; do
    FILEPATH=$(find "$CONTENT_DIR" -name "$SLUG.md" -type f 2>/dev/null | head -1)
    [ -z "$FILEPATH" ] && continue
    VIOLS=$(grep -niE "$FORBIDDEN" "$FILEPATH" 2>/dev/null || true)
    if [ -n "$VIOLS" ]; then
        HAS_VIOLATIONS=true
        echo "--- $SLUG : forbidden words ---"
        echo "$VIOLS" | head -5
        echo ""
    fi
done
$HAS_VIOLATIONS || echo "No forbidden words detected."

# --- Build ---
if [ "$RUN_BUILD" = true ]; then
    echo ""
    echo "Building Astro..."
    if BUILD_OUTPUT=$(cd "$SITE_DIR" && npm run build 2>&1); then
        echo "Build: OK"
    else
        echo "Build: FAILED"
        echo "$BUILD_OUTPUT" | tail -5
        TOTAL_ERRORS=$((TOTAL_ERRORS + 1))
    fi
fi

# --- Summary ---
echo ""
if [ "$TOTAL_ERRORS" -gt 0 ]; then
    echo "=== $TOTAL_ERRORS article(s) with errors ==="
    exit 1
else
    echo "=== ${#SLUGS[@]} article(s) verified ==="
fi
