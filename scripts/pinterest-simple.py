#!/usr/bin/env python3
"""
Pinterest Simple Scraper - Version furtive
Utilise des techniques de scraping avancées pour contourner les protections
"""

import requests
import json
import re
import time
import random
from urllib.parse import quote_plus
import sys

def get_pinterest_images(query, count=3):
    """Version simplifiée mais plus efficace"""
    
    # User agents rotatifs
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    try:
        # Première visite sur Pinterest pour récupérer les cookies
        print("🔐 Initialisation session Pinterest...")
        init_response = session.get('https://www.pinterest.fr/', timeout=10)
        
        # Pause réaliste
        time.sleep(random.uniform(2, 4))
        
        # Recherche avec les bons headers
        query_encoded = quote_plus(query)
        search_url = f'https://www.pinterest.fr/search/pins/?q={query_encoded}'
        
        print(f"🔍 Recherche: {search_url}")
        
        response = session.get(search_url, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return []
        
        # Extraction via regex des URLs d'images
        # Pinterest utilise des patterns prévisibles pour les images
        image_patterns = [
            r'"url":"(https://i\.pinimg\.com/[^"]+\.jpg)"',
            r'"url":"(https://i\.pinimg\.com/[^"]+\.png)"',
            r'"url":"(https://i\.pinimg\.com/[^"]+\.webp)"',
        ]
        
        images = set()  # Éviter les doublons
        
        for pattern in image_patterns:
            matches = re.findall(pattern, response.text)
            for match in matches:
                # Nettoyer l'URL
                clean_url = match.replace('\\u002F', '/').replace('\\', '')
                if clean_url and len(images) < count * 2:  # Buffer pour filtrer
                    images.add(clean_url)
        
        # Filtrer pour garder les meilleures images (haute résolution)
        high_res_images = []
        for img_url in images:
            if any(size in img_url for size in ['736x', '564x', 'originals']):
                high_res_images.append(img_url)
                if len(high_res_images) >= count:
                    break
        
        if not high_res_images:
            # Fallback avec toutes les images trouvées
            high_res_images = list(images)[:count]
        
        print(f"✅ Trouvé {len(high_res_images)} images haute résolution")
        return high_res_images
        
    except Exception as e:
        print(f"❌ Erreur scraping: {e}")
        return []

def download_image(url, filename):
    """Télécharge une image avec headers appropriés"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://www.pinterest.fr/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Téléchargé: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Échec téléchargement {filename}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pinterest-simple.py 'requête' [nombre]")
        sys.exit(1)
    
    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    print(f"🎨 Pinterest Simple Scraper")
    print(f"🔍 Requête: {query}")
    print(f"📸 Images: {count}")
    
    # Récupération des URLs
    image_urls = get_pinterest_images(query, count)
    
    if not image_urls:
        print("❌ Aucune image trouvée")
        return
    
    # Téléchargement
    downloaded = 0
    for i, url in enumerate(image_urls):
        timestamp = int(time.time() * 1000) + i
        filename = f"site/public/images/pinterest-simple-{query.replace(' ', '-').lower()}-{timestamp}.jpg"
        
        if download_image(url, filename):
            downloaded += 1
            
        # Pause entre téléchargements
        time.sleep(random.uniform(1, 3))
    
    print(f"\n🎉 Téléchargement terminé: {downloaded}/{len(image_urls)} images")

if __name__ == "__main__":
    main()