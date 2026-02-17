#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# preprocess-article.sh
# Preprocessing pipeline for content articles
#
# Calls Tavily (research) + Slashr (SEO brief) + fal.ai (image),
# then assembles everything into /tmp/preprocess-{slug}/prompt-data.md
#
# Usage: ./scripts/preprocess-article.sh <slug> <keyword> <branch> <parent> <order>
# Batch: ./scripts/preprocess-article.sh slug1 kw1 b1 p1 o1 & \
#        ./scripts/preprocess-article.sh slug2 kw2 b2 p2 o2 & wait
# ============================================================

if [ $# -lt 5 ]; then
    echo "Usage: $0 <slug> <keyword> <branch> <parent> <order>"
    echo ""
    echo "  slug     Article slug (ex: first-steps)"
    echo "  keyword  Main SEO keyword (ex: \"getting started guide\")"
    echo "  branch   Content branch (ex: getting-started)"
    echo "  parent   Parent hub slug (ex: getting-started)"
    echo "  order    Order in branch (ex: 1)"
    exit 1
fi

SLUG="$1"
KEYWORD="$2"
BRANCH="$3"
PARENT="$4"
ORDER="$5"

# --- Paths ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SITE_DIR="$PROJECT_DIR/site"
# TODO: Adjust image path for your content structure
IMAGE_DIR="$SITE_DIR/public/images/guides"
IMAGE_PATH="$IMAGE_DIR/$SLUG.webp"
OUT="/tmp/preprocess-${SLUG}"

# --- Dependencies ---
for cmd in curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "[$SLUG] Error: '$cmd' required." >&2
        exit 1
    fi
done

# --- Environment ---
if [ ! -f "$SITE_DIR/.env" ]; then
    echo "[$SLUG] Error: $SITE_DIR/.env not found." >&2
    exit 1
fi
source "$SITE_DIR/.env"

# --- API key validation ---
TAVILY_AVAILABLE=true
if [ -z "${TAVILY_API_KEY:-}" ]; then
    echo "[$SLUG] Warning: TAVILY_API_KEY missing, Tavily search skipped." >&2
    TAVILY_AVAILABLE=false
fi

FAL_AVAILABLE=true
if [ -z "${FAL_KEY:-}" ]; then
    echo "[$SLUG] Warning: FAL_KEY missing, image generation skipped." >&2
    FAL_AVAILABLE=false
fi

UNSPLASH_AVAILABLE=true
if [ -z "${UNSPLASH_ACCESS_KEY:-}" ]; then
    echo "[$SLUG] Warning: UNSPLASH_ACCESS_KEY missing, Unsplash images skipped." >&2
    UNSPLASH_AVAILABLE=false
fi

# --- Setup ---
mkdir -p "$OUT" "$IMAGE_DIR"

echo "[$SLUG] Preprocessing..."

# ============================================================
# 1. TAVILY — Factual research
# ============================================================
if [ "$TAVILY_AVAILABLE" = true ]; then
    echo "[$SLUG]   Tavily..."
TAVILY_PAYLOAD=$(jq -n --arg q "$KEYWORD" --arg k "$TAVILY_API_KEY" \
    '{api_key: $k, query: $q, search_depth: "advanced", max_results: 5, include_answer: true}')
curl -s --max-time 30 -X POST "https://api.tavily.com/search" \
    -H "Content-Type: application/json" \
    -d "$TAVILY_PAYLOAD" \
    -o "$OUT/tavily.json" 2>/dev/null || echo '{}' > "$OUT/tavily.json"
echo "[$SLUG]   Tavily: $(jq -r '.results | length // 0' "$OUT/tavily.json" 2>/dev/null || echo 0) sources"
else
    echo "[$SLUG]   Tavily: skipped (no API key)"
    echo '{}' > "$OUT/tavily.json"
fi

# ============================================================
# 2. SEO BRIEF (Slashr)
# ============================================================
echo "[$SLUG]   Brief Slashr..."
BRIEF_PAYLOAD=$(jq -n --arg kw "$KEYWORD" \
    '{keyword: $kw, location: "France", language: "fr"}')
curl -s --max-time 60 -X POST "https://outils.agence-slashr.fr/brief-contenu/api/generate-brief" \
    -H "Content-Type: application/json" \
    -d "$BRIEF_PAYLOAD" \
    -o "$OUT/brief.json" 2>/dev/null || echo '{}' > "$OUT/brief.json"
BRIEF_WORDS=$(jq -r '.semanticData.recommended_words // 2500' "$OUT/brief.json" 2>/dev/null || echo 2500)
if [[ "$BRIEF_WORDS" =~ ^[0-9]+$ ]]; then
    : # valid number
else
    BRIEF_WORDS=2500
fi
echo "[$SLUG]   Brief: $BRIEF_WORDS recommended words"

# ============================================================
# 3. IMAGES - Unsplash (priority) or fal.ai
# ============================================================
if [ "$UNSPLASH_AVAILABLE" = true ]; then
    echo "[$SLUG]   Images Unsplash..."
    # Fetch 4 images for the article
    SEARCH_QUERY="$KEYWORD home decor interior design"
    SEARCH_URL="https://api.unsplash.com/search/photos"
    QUERY_ENCODED=$(echo "$SEARCH_QUERY" | sed 's/ /+/g')
    
    RESPONSE=$(curl -s --max-time 30 "$SEARCH_URL?query=$QUERY_ENCODED&per_page=4&orientation=landscape&order_by=popular" \
        -H "Authorization: Client-ID $UNSPLASH_ACCESS_KEY" || echo '{"total": 0}')
    
    TOTAL=$(echo "$RESPONSE" | jq -r '.total // 0')
    
    if [ "$TOTAL" -gt 0 ]; then
        # Download images
        echo "$RESPONSE" | jq -r '.results[] | "\(.urls.regular)|\(.alt_description // "Interior design")|\(.user.name)"' | head -4 | while IFS='|' read -r url alt author; do
            img_name="unsplash-$(echo "$SLUG" | sed 's/[^a-zA-Z0-9]/-/g')-$(date +%s%N | cut -b1-13).jpg"
            img_path="$IMAGE_DIR/$img_name"
            
            if curl -sL --max-time 20 "$url" -o "$img_path" && [ -s "$img_path" ]; then
                echo "[$SLUG]   Image: $img_name (by $author)"
            fi
        done
        IMAGE_OK="true"
        echo "[$SLUG]   Unsplash: $TOTAL images available, downloaded 4"
    else
        echo "[$SLUG]   Unsplash: no results, fallback to fal.ai"
        IMAGE_OK="false"
    fi
elif [ "$FAL_AVAILABLE" = true ]; then
    echo "[$SLUG]   Image fal.ai..."
    IMAGE_PROMPT="no text, no letters, no numbers, no words. Soft natural lighting digital illustration. Beautiful home interior scene depicting ${KEYWORD}. Warm and cozy atmosphere with soft pink and mauve accents. Modern feminine touch, clean minimal style, inviting and aspirational mood."
    FAL_PAYLOAD=$(jq -n --arg p "$IMAGE_PROMPT" \
        '{prompt: $p, image_size: "landscape_16_9", style: "digital_illustration", substyle: "hand_drawn", colors: [{r:255,g:240,b:245},{r:232,g:121,b:249},{r:249,g:115,b:22}]}')
    IMAGE_URL=$(curl -s --max-time 60 -X POST "https://fal.run/fal-ai/recraft-20b" \
        -H "Authorization: Key $FAL_KEY" \
        -H "Content-Type: application/json" \
        -d "$FAL_PAYLOAD" 2>/dev/null | jq -r '.images[0].url // empty' 2>/dev/null || true)
    IMAGE_OK="false"
    if [ -n "$IMAGE_URL" ]; then
        curl -sL --max-time 30 "$IMAGE_URL" -o "$IMAGE_PATH" 2>/dev/null || true
        if [ -s "$IMAGE_PATH" ]; then
            IMAGE_OK="true"
            echo "[$SLUG]   Image: OK"
        else
            echo "[$SLUG]   Image: download failed"
        fi
    else
        echo "[$SLUG]   Image: generation failed"
    fi
else
    echo "[$SLUG]   Images: no service available"
    IMAGE_OK="false"
fi

# ============================================================
# 4. PARENT HUB CONTENT
# ============================================================
# TODO: Adjust path for your content structure
PARENT_HUB="$SITE_DIR/src/content/guides/$PARENT/index.md"
if [ -f "$PARENT_HUB" ]; then
    cp "$PARENT_HUB" "$OUT/parent.md"
else
    echo "" > "$OUT/parent.md"
fi

# ============================================================
# 5. ASSEMBLE prompt-data.md
# ============================================================
BRIEF_H1=$(jq -r '.contentPlan.h1 // empty' "$OUT/brief.json" 2>/dev/null || true)
BRIEF_META=$(jq -r '.seoMetadata.metaDescription // empty' "$OUT/brief.json" 2>/dev/null || true)
TITLE_LINE="${BRIEF_H1:-SEO Title to write}"
DESC_LINE="${BRIEF_META:-SEO Description ~155 characters}"
IMAGE_FM=""
[ "$IMAGE_OK" = "true" ] && IMAGE_FM="image: \"/images/guides/$SLUG.webp\""

CONTENT_PATH="$SITE_DIR/src/content/guides/$PARENT/$SLUG.md"

cat > "$OUT/prompt-data.md" <<DATAEOF
# Preprocessed data for: $SLUG

## Target file
$CONTENT_PATH

## Suggested frontmatter
---
title: "$TITLE_LINE"
description: "$DESC_LINE"
type: guide
branch: $BRANCH
parent: $PARENT
order: $ORDER
${IMAGE_FM}
readingTime: "To calculate"
---

## SEO Brief

Recommended word count: $BRIEF_WORDS

### Required keywords
$(jq -r '.semanticData.KW_obligatoires // "Not available"' "$OUT/brief.json" 2>/dev/null || echo "Not available")

### Complementary keywords
$(jq -r '.semanticData.KW_complementaires // "Not available"' "$OUT/brief.json" 2>/dev/null || echo "Not available")

### Suggested content plan
$(jq -r '.contentPlan.sections // "Not available"' "$OUT/brief.json" 2>/dev/null || echo "Not available")

## Factual research (Tavily)

### Synthesis
$(jq -r '.answer // "No synthesis"' "$OUT/tavily.json" 2>/dev/null || echo "Not available")

### Sources
$(jq -r '.results[]? | "- \(.title) (\(.url))\n  \(.content[:500])\n"' "$OUT/tavily.json" 2>/dev/null || echo "No sources")

## Parent hub content (do not repeat)
DATAEOF

# Append parent content separately (avoids shell expansion of backticks/$ in markdown)
cat "$OUT/parent.md" >> "$OUT/prompt-data.md"

echo "[$SLUG] OK -> $OUT/prompt-data.md"
