#!/usr/bin/env python3
"""
Pinterest Image Scraper - Cristallina
Scrape d'images déco haute qualité depuis Pinterest
Sans rate limit, images originales HD !
"""

import requests
import json
import re
import time
import random
from urllib.parse import quote_plus, urlparse
from pathlib import Path
import argparse

class PinterestScraper:
    def __init__(self):
        self.session = requests.Session()
        # Headers réalistes pour éviter la détection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def search_pins(self, query, count=10):
        """Cherche des épingles via l'API Pinterest interne"""
        encoded_query = quote_plus(query)
        
        # URL de l'API interne Pinterest (endpoint découvert via reverse engineering)
        api_url = f"https://www.pinterest.fr/resource/BaseSearchResource/get/"
        
        params = {
            "source_url": f"/search/pins/?q={encoded_query}",
            "data": json.dumps({
                "options": {
                    "query": query,
                    "scope": "pins",
                    "no_fetch_context_on_resource": False
                },
                "context": {}
            })
        }
        
        try:
            response = self.session.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                pins = self._extract_pins_from_api_response(data)
                return pins[:count]
        except Exception as e:
            print(f"❌ API Pinterest failed: {e}")
            
        # Fallback : Scraping direct
        return self._scrape_search_page(query, count)
    
    def _extract_pins_from_api_response(self, data):
        """Extrait les données des épingles depuis la réponse API"""
        pins = []
        
        try:
            results = data.get('resource_response', {}).get('data', {}).get('results', [])
            for pin in results:
                if pin.get('type') == 'pin':
                    pin_data = {
                        'id': pin.get('id'),
                        'url': pin.get('link', ''),
                        'title': pin.get('grid_title', ''),
                        'description': pin.get('description', ''),
                        'image_url': self._get_original_image_url(pin),
                        'pin_url': f"https://www.pinterest.fr/pin/{pin.get('id')}/"
                    }
                    if pin_data['image_url']:
                        pins.append(pin_data)
        except Exception as e:
            print(f"⚠️ Parse error: {e}")
            
        return pins
    
    def _get_original_image_url(self, pin):
        """Récupère l'URL de l'image originale haute résolution"""
        images = pin.get('images', {})
        
        # Ordre de préférence : orig > 736x > 564x > autres
        for size in ['orig', '736x', '564x']:
            if size in images and images[size].get('url'):
                return images[size]['url']
                
        # Fallback sur la première image disponible
        for img in images.values():
            if isinstance(img, dict) and img.get('url'):
                return img['url']
                
        return None
    
    def _scrape_search_page(self, query, count):
        """Fallback : scrape la page de recherche directement"""
        encoded_query = quote_plus(query)
        search_url = f"https://www.pinterest.fr/search/pins/?q={encoded_query}"
        
        try:
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return []
                
            # Extraction des données JSON embarquées
            pattern = r'<script id="__PWS_DATA__" type="application/json">(.+?)</script>'
            match = re.search(pattern, response.text)
            
            if match:
                json_data = json.loads(match.group(1))
                return self._extract_pins_from_page_data(json_data, count)
                
        except Exception as e:
            print(f"❌ Page scraping failed: {e}")
            
        return []
    
    def _extract_pins_from_page_data(self, data, count):
        """Extrait les épingles des données JSON de la page"""
        pins = []
        
        try:
            # Navigation dans la structure complexe des données Pinterest
            props = data.get('props', {})
            initial_redux_state = props.get('initialReduxState', {})
            pins_data = initial_redux_state.get('pins', {})
            
            for pin_id, pin_info in pins_data.items():
                if len(pins) >= count:
                    break
                    
                pin_data = {
                    'id': pin_id,
                    'url': pin_info.get('link', ''),
                    'title': pin_info.get('grid_title', ''),
                    'description': pin_info.get('description', ''),
                    'image_url': self._get_original_image_url(pin_info),
                    'pin_url': f"https://www.pinterest.fr/pin/{pin_id}/"
                }
                
                if pin_data['image_url']:
                    pins.append(pin_data)
                    
        except Exception as e:
            print(f"⚠️ Data extraction error: {e}")
            
        return pins
    
    def download_image(self, image_url, filename, output_dir="./images"):
        """Télécharge une image depuis Pinterest"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        file_path = output_path / filename
        
        try:
            # Headers spécifiques pour le téléchargement d'images
            headers = {
                'Referer': 'https://www.pinterest.fr/',
                'User-Agent': self.session.headers['User-Agent']
            }
            
            response = self.session.get(image_url, headers=headers, timeout=15, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"✅ Downloaded: {filename}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Download failed for {filename}: {e}")
            return None
    
    def search_and_download(self, query, count=5, output_dir="./images", prefix="pinterest"):
        """Recherche et télécharge des images pour une requête"""
        print(f"🔍 Searching Pinterest for: {query}")
        
        pins = self.search_pins(query, count)
        print(f"📌 Found {len(pins)} pins")
        
        downloaded_files = []
        
        for i, pin in enumerate(pins):
            # Filename avec timestamp unique
            timestamp = int(time.time() * 1000) + i
            ext = self._get_image_extension(pin['image_url'])
            filename = f"{prefix}-{query.replace(' ', '-').lower()}-{timestamp}.{ext}"
            
            downloaded_file = self.download_image(pin['image_url'], filename, output_dir)
            
            if downloaded_file:
                downloaded_files.append({
                    'file': downloaded_file,
                    'pin_url': pin['pin_url'],
                    'title': pin['title'],
                    'description': pin['description']
                })
                
            # Pause aléatoire pour éviter la détection
            time.sleep(random.uniform(0.5, 2.0))
            
        print(f"✅ Downloaded {len(downloaded_files)}/{count} images")
        return downloaded_files
    
    def _get_image_extension(self, url):
        """Détermine l'extension du fichier image"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if '.jpg' in path or '.jpeg' in path:
            return 'jpg'
        elif '.png' in path:
            return 'png'
        elif '.webp' in path:
            return 'webp'
        else:
            return 'jpg'  # Default

def main():
    parser = argparse.ArgumentParser(description='Pinterest Image Scraper pour Cristallina')
    parser.add_argument('query', help='Requête de recherche (ex: "salon moderne déco")')
    parser.add_argument('-c', '--count', type=int, default=5, help='Nombre d\'images (défaut: 5)')
    parser.add_argument('-o', '--output', default='./images', help='Dossier de sortie')
    parser.add_argument('-p', '--prefix', default='pinterest', help='Préfixe des fichiers')
    
    args = parser.parse_args()
    
    scraper = PinterestScraper()
    results = scraper.search_and_download(
        query=args.query,
        count=args.count,
        output_dir=args.output,
        prefix=args.prefix
    )
    
    print(f"\n🎉 Scraping terminé ! {len(results)} images téléchargées")
    
    # Affichage des résultats
    for result in results:
        print(f"📁 {result['file']}")
        print(f"📌 {result['pin_url']}")
        print(f"📝 {result['title'][:50]}...")
        print("-" * 50)

if __name__ == "__main__":
    main()