#!/usr/bin/env python3
"""
Pinterest Scraper avec Playwright - Navigation humaine
Simule un vrai utilisateur pour contourner toutes les protections
"""

import asyncio
import random
import time
import sys
import json
import re
from pathlib import Path
import requests
from urllib.parse import quote_plus

async def scrape_pinterest_with_playwright(query, count=3):
    """Scrape Pinterest avec vraie navigation browser"""
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright non installé. Installation...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # Lancer Chrome en mode headless optimisé
        browser = await p.chromium.launch(
            headless=True,  # Mode invisible
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-web-security',
                '--disable-features=TranslateUI',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Plus rapide
                '--disable-javascript',  # Pas besoin pour le scraping
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Masquer l'automatisation
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        print("🌐 Ouverture Pinterest...")
        # Navigation plus rapide avec timeout réduit
        await page.goto('https://www.pinterest.fr/', wait_until='domcontentloaded', timeout=15000)
        
        # Pause réduite en mode headless
        await page.wait_for_timeout(random.randint(1000, 2000))
        
        # Scrolling naturel pour charger les ressources
        print("📜 Scrolling naturel...")
        for i in range(3):
            await page.mouse.wheel(0, random.randint(200, 500))
            await page.wait_for_timeout(random.randint(800, 1500))
        
        # Navigation vers la recherche
        print(f"🔍 Recherche: {query}")
        search_url = f'https://www.pinterest.fr/search/pins/?q={quote_plus(query)}'
        
        await page.goto(search_url, wait_until='domcontentloaded', timeout=15000)
        await page.wait_for_timeout(random.randint(2000, 3000))
        
        # Scrolling pour charger plus d'images
        print("📸 Chargement des images...")
        for i in range(5):
            await page.mouse.wheel(0, random.randint(500, 1000))
            await page.wait_for_timeout(random.randint(1000, 2000))
        
        # Extraction des images
        print("🎯 Extraction des URLs d'images...")
        
        # Attendre que les images se chargent
        await page.wait_for_selector('img[src*="pinimg.com"]', timeout=10000)
        
        # Récupérer toutes les images Pinterest
        image_elements = await page.query_selector_all('img[src*="pinimg.com"]')
        
        image_urls = []
        for img_element in image_elements:
            src = await img_element.get_attribute('src')
            if src and 'pinimg.com' in src:
                # Convertir en URL haute résolution
                high_res_url = convert_to_high_res(src)
                if high_res_url and high_res_url not in image_urls:
                    image_urls.append(high_res_url)
                    if len(image_urls) >= count:
                        break
        
        print(f"✅ Trouvé {len(image_urls)} images haute résolution")
        
        await browser.close()
        return image_urls

def convert_to_high_res(pinterest_url):
    """Convertit une URL Pinterest en version haute résolution"""
    if not pinterest_url or 'pinimg.com' not in pinterest_url:
        return None
    
    # Pinterest utilise des patterns prévisibles pour les tailles
    # Remplacer par la plus haute résolution disponible
    url = pinterest_url
    
    # Remplacements pour obtenir la meilleure qualité
    replacements = [
        ('236x/', 'originals/'),
        ('474x/', 'originals/'),
        ('564x/', 'originals/'),
        ('736x/', 'originals/'),
        ('200x150/', 'originals/'),
        ('/150x150/', '/originals/'),
    ]
    
    for old, new in replacements:
        if old in url:
            url = url.replace(old, new)
            break
    
    return url

def download_image(url, filename):
    """Télécharge une image avec headers Pinterest"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.pinterest.fr/',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        
        response = requests.get(url, headers=headers, timeout=15, stream=True)
        response.raise_for_status()
        
        # Créer le dossier si nécessaire
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Téléchargé: {Path(filename).name}")
        return True
        
    except Exception as e:
        print(f"❌ Échec téléchargement {Path(filename).name}: {e}")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pinterest-playwright.py 'requête' [nombre]")
        print("Exemple: python3 pinterest-playwright.py 'salon moderne déco' 3")
        sys.exit(1)
    
    query = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5  # 5 images minimum
    
    print("🎭 Pinterest Playwright Scraper")
    print(f"🔍 Requête: {query}")
    print(f"📸 Images: {count}")
    print("🔇 Mode headless - Aucune fenêtre ne s'ouvrira")
    print()
    
    # Scraping avec navigation réelle
    image_urls = await scrape_pinterest_with_playwright(query, count)
    
    if not image_urls:
        print("❌ Aucune image trouvée")
        return
    
    print(f"🎯 {len(image_urls)} images à télécharger")
    print()
    
    # Téléchargement
    output_dir = "site/public/images"
    downloaded = 0
    
    for i, url in enumerate(image_urls):
        timestamp = int(time.time() * 1000) + i
        safe_query = re.sub(r'[^a-z0-9-]', '-', query.lower())
        filename = f"{output_dir}/pinterest-{safe_query}-{timestamp}.jpg"
        
        if download_image(url, filename):
            downloaded += 1
        
        # Pause entre téléchargements
        time.sleep(random.uniform(1, 3))
    
    print()
    print(f"🎉 Scraping terminé: {downloaded}/{len(image_urls)} images téléchargées")
    print(f"📁 Dossier: {output_dir}")

if __name__ == "__main__":
    asyncio.run(main())