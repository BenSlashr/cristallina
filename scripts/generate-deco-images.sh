#!/usr/bin/env bash
# Generate decoration-specific images with multiple sources

set -euo pipefail

# Check if we're in the right directory
if [ ! -f "site/.env" ]; then
    echo "❌ Run from project root (site/.env not found)"
    exit 1
fi

# Load environment
source site/.env

# Usage
if [ $# -lt 2 ]; then
    echo "Usage: $0 <type> <keyword> [style]"
    echo ""
    echo "Types: salon, cuisine, chambre, sdb, deco-generale"
    echo "Styles: scandinave, moderne, boheme, industriel, classique"
    echo ""
    echo "Examples:"
    echo "  $0 salon \"canapé beige\" scandinave"
    echo "  $0 cuisine \"ilot central\" moderne"
    exit 1
fi

TYPE="$1"
KEYWORD="$2"
STYLE="${3:-moderne}"

# Image prompts by room type
declare -A ROOM_PROMPTS
ROOM_PROMPTS[salon]="cozy living room interior, comfortable seating, natural lighting, plants, warm atmosphere"
ROOM_PROMPTS[cuisine]="modern kitchen design, clean lines, functional layout, beautiful countertops"
ROOM_PROMPTS[chambre]="serene bedroom interior, soft textures, calming colors, cozy atmosphere"
ROOM_PROMPTS[sdb]="elegant bathroom design, spa-like atmosphere, natural materials, clean aesthetic"
ROOM_PROMPTS[deco-generale]="beautiful interior design, stylish decor, harmonious color scheme, inspiring space"

# Style modifiers
declare -A STYLE_PROMPTS
STYLE_PROMPTS[scandinave]="nordic minimalist style, light wood, white walls, natural textures"
STYLE_PROMPTS[moderne]="contemporary design, clean lines, neutral palette, sleek finishes"
STYLE_PROMPTS[boheme]="boho chic style, textured fabrics, warm earth tones, eclectic decor"
STYLE_PROMPTS[industriel]="industrial design, exposed materials, metal accents, urban aesthetic"
STYLE_PROMPTS[classique]="classic elegant style, timeless design, refined details, sophisticated palette"

# Build full prompt
BASE_PROMPT="${ROOM_PROMPTS[$TYPE]}"
STYLE_MODIFIER="${STYLE_PROMPTS[$STYLE]}"
FULL_PROMPT="no text, no letters. $BASE_PROMPT featuring $KEYWORD. $STYLE_MODIFIER. Professional interior photography style, soft natural lighting."

echo "🎨 Generating: $TYPE - $KEYWORD ($STYLE)"
echo "📝 Prompt: $FULL_PROMPT"

# Recraft V3 generation
FAL_PAYLOAD=$(jq -n --arg p "$FULL_PROMPT" \
    '{
        prompt: $p, 
        image_size: "landscape_16_9", 
        style: "digital_illustration",
        substyle: "hand_drawn",
        colors: [
            {r:255, g:248, b:250}, 
            {r:245, g:158, b:11}, 
            {r:139, g:92, b:246}
        ]
    }')

IMAGE_URL=$(curl -s --max-time 60 -X POST "https://fal.run/fal-ai/recraft-20b" \
    -H "Authorization: Key $FAL_KEY" \
    -H "Content-Type: application/json" \
    -d "$FAL_PAYLOAD" | jq -r '.images[0].url // empty')

if [ -n "$IMAGE_URL" ]; then
    echo "✅ Image générée: $IMAGE_URL"
    
    # Download to project
    OUTPUT_FILE="site/public/images/deco-${TYPE}-$(echo $KEYWORD | sed 's/ /-/g').webp"
    mkdir -p "site/public/images"
    
    curl -sL "$IMAGE_URL" -o "$OUTPUT_FILE"
    if [ -s "$OUTPUT_FILE" ]; then
        echo "💾 Sauvegardée: $OUTPUT_FILE"
    else
        echo "❌ Échec téléchargement"
    fi
else
    echo "❌ Échec génération"
fi