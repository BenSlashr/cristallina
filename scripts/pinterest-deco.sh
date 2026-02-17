#!/bin/bash

# Pinterest Déco Scraper - Script wrapper Cristallina
# Usage: ./pinterest-deco.sh "salon moderne" 3
# 
# RÉVOLUTIONNAIRE : Scraping Pinterest avec Playwright !
# ✅ Aucun rate limit
# ✅ Images haute qualité 
# ✅ Navigation humaine réaliste

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLAYWRIGHT_SCRIPT="$SCRIPT_DIR/pinterest-playwright.py"

# Usage
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Usage: $0 \"requête déco\" [nombre_images]${NC}"
    echo -e "${YELLOW}💡 Exemples:${NC}"
    echo -e "   $0 \"salon scandinave cosy\" 5"
    echo -e "   $0 \"cuisine moderne 2026\" 3"  
    echo -e "   $0 \"chambre bohème chic\" 4"
    echo ""
    echo -e "${BLUE}🎭 Powered by Playwright - Navigation humaine réelle !${NC}"
    exit 1
fi

QUERY="$1"
COUNT="${2:-5}"  # 5 images par défaut

# Header impressionnant
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  🎨 PINTEREST SCRAPER RÉVOLUTIONNAIRE - CRISTALLINA${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎭 Navigation humaine avec Playwright${NC}"
echo -e "${GREEN}✅ Contournement total des protections Pinterest${NC}"
echo -e "${GREEN}✅ Images haute qualité originales${NC}"
echo -e "${GREEN}✅ Aucune limitation de rate limit${NC}"
echo ""
echo -e "${YELLOW}🔍 Requête: ${QUERY}${NC}"
echo -e "${YELLOW}📸 Nombre d'images: ${COUNT}${NC}"
echo -e "${YELLOW}🔇 Mode headless - Aucune fenêtre ne s'ouvrira${NC}"
echo ""

# Vérifications
if [ ! -f "$PLAYWRIGHT_SCRIPT" ]; then
    echo -e "${RED}❌ Script Playwright non trouvé: $PLAYWRIGHT_SCRIPT${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 requis${NC}"
    exit 1
fi

# Vérifier Playwright
if ! python3 -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installation de Playwright...${NC}"
    pip3 install playwright --break-system-packages
    python3 -m playwright install chromium
fi

# Lancement du scraping
echo -e "${GREEN}🚀 Lancement du scraping Pinterest...${NC}"
echo ""

# Exécuter le script Playwright
if python3 "$PLAYWRIGHT_SCRIPT" "$QUERY" "$COUNT"; then
    echo ""
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 SUCCÈS ! Images Pinterest téléchargées${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}📁 Localisation: site/public/images/${NC}"
    echo -e "${BLUE}📸 Format: pinterest-[query]-[timestamp].jpg${NC}"
    echo -e "${BLUE}💡 Usage Astro: /images/pinterest-...jpg${NC}"
    echo ""
    
    # Listing des nouvelles images Pinterest
    echo -e "${YELLOW}📋 Nouvelles images Pinterest:${NC}"
    find "site/public/images" -name "pinterest-*" -type f -newer "$PLAYWRIGHT_SCRIPT" 2>/dev/null | tail -10 | while read file; do
        filename=$(basename "$file")
        filesize=$(ls -lah "$file" | awk '{print $5}')
        echo -e "   ${GREEN}✓${NC} $filename (${filesize})"
    done
    
    echo ""
    echo -e "${PURPLE}🎭 Pinterest Scraper - Révolution terminée !${NC}"
    
else
    echo ""
    echo -e "${RED}❌ Échec du scraping Pinterest${NC}"
    echo -e "${YELLOW}💡 Vérifiez votre connexion internet${NC}"
    exit 1
fi