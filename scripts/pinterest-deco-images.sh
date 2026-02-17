#!/bin/bash

# Pinterest Deco Images - Script wrapper pour Cristallina
# Usage: ./pinterest-deco-images.sh "salon moderne" 3
# 
# Télécharge des images déco Pinterest haute qualité
# ZERO rate limit contrairement à Unsplash !

set -e

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/../site/public/images"
PYTHON_SCRIPT="$SCRIPT_DIR/pinterest-scraper.py"

# Vérifications
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Usage: $0 \"requête de recherche\" [nombre_images]${NC}"
    echo -e "${YELLOW}💡 Exemple: $0 \"salon scandinave déco\" 5${NC}"
    exit 1
fi

QUERY="$1"
COUNT="${2:-3}"  # Default 3 images

# Messages informatifs
echo -e "${BLUE}🎨 Pinterest Deco Scraper - Cristallina${NC}"
echo -e "${YELLOW}🔍 Requête: ${QUERY}${NC}"
echo -e "${YELLOW}📸 Images: ${COUNT}${NC}"
echo -e "${YELLOW}📁 Sortie: ${OUTPUT_DIR}${NC}"
echo ""

# Création du dossier de sortie
mkdir -p "$OUTPUT_DIR"

# Vérification Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 requis mais non installé${NC}"
    exit 1
fi

# Installation des dépendances si nécessaire
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installation des dépendances Python...${NC}"
    pip3 install requests --quiet || {
        echo -e "${RED}❌ Échec installation dépendances${NC}"
        exit 1
    }
fi

# Exécution du scraper
echo -e "${GREEN}🚀 Lancement du scraping Pinterest...${NC}"
echo ""

python3 "$PYTHON_SCRIPT" \
    "$QUERY" \
    --count "$COUNT" \
    --output "$OUTPUT_DIR" \
    --prefix "pinterest-deco"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Scraping Pinterest terminé avec succès !${NC}"
    echo -e "${BLUE}📁 Images sauvées dans: ${OUTPUT_DIR}${NC}"
    
    # Listing des nouveaux fichiers
    echo -e "${YELLOW}📋 Nouveaux fichiers:${NC}"
    find "$OUTPUT_DIR" -name "pinterest-deco-*" -type f -newer "$PYTHON_SCRIPT" 2>/dev/null | head -10 | while read file; do
        filename=$(basename "$file")
        echo -e "   ${GREEN}✓${NC} $filename"
    done
    
    echo ""
    echo -e "${BLUE}💡 Usage dans Astro: /images/pinterest-deco-...jpg${NC}"
    
else
    echo -e "${RED}❌ Échec du scraping Pinterest${NC}"
    exit 1
fi