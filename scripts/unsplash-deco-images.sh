#!/usr/bin/env bash
# Get high-quality decoration images from Unsplash API

set -euo pipefail

# Usage
if [ $# -lt 1 ]; then
    echo "Usage: $0 <keyword> [count]"
    echo ""
    echo "Examples:"
    echo "  $0 \"scandinavian living room\" 4"
    echo "  $0 \"modern kitchen\" 2"
    echo "  $0 \"bedroom decor\" 3"
    exit 1
fi

KEYWORD="$1"
COUNT="${2:-4}"

# Unsplash Access Key (get one free at unsplash.com/developers)
# UNSPLASH_ACCESS_KEY="your-key-here"

if [ -z "${UNSPLASH_ACCESS_KEY:-}" ]; then
    echo "❌ Set UNSPLASH_ACCESS_KEY in your environment"
    echo "📝 Get a free key at: https://unsplash.com/developers"
    exit 1
fi

echo "🖼️  Fetching $COUNT images for: $KEYWORD"

# Search Unsplash
SEARCH_URL="https://api.unsplash.com/search/photos"
QUERY=$(echo "$KEYWORD" | sed 's/ /+/g')

RESPONSE=$(curl -s "$SEARCH_URL?query=$QUERY&per_page=$COUNT&orientation=landscape&order_by=popular" \
    -H "Authorization: Client-ID $UNSPLASH_ACCESS_KEY")

# Parse results
TOTAL=$(echo "$RESPONSE" | jq -r '.total // 0')
echo "📊 Found $TOTAL total results"

if [ "$TOTAL" -gt 0 ]; then
    echo "$RESPONSE" | jq -r '.results[] | "\(.urls.regular)|\(.alt_description // "Interior design")|\(.user.name)"' | while IFS='|' read -r url alt author; do
        # Generate filename
        filename="unsplash-$(echo "$KEYWORD" | sed 's/[^a-zA-Z0-9]/-/g')-$(date +%s).jpg"
        filepath="site/public/images/$filename"
        
        # Download
        mkdir -p "site/public/images"
        if curl -sL "$url" -o "$filepath"; then
            echo "✅ Downloaded: $filepath"
            echo "📝 Alt: $alt"
            echo "👤 Author: $author"
            echo "---"
        else
            echo "❌ Failed to download: $url"
        fi
    done
else
    echo "❌ No images found for: $KEYWORD"
fi