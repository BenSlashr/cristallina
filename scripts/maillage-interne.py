#!/usr/bin/env python3
"""
Système de Maillage Interne Intelligent - Cristallina
Analyse les articles existants et crée des liens contextuels
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

class MaillageInterne:
    def __init__(self):
        self.articles = {}
        self.themes = defaultdict(list)
        self.keywords = defaultdict(list)
        
    def analyser_articles(self):
        """Analyse tous les articles .astro pour extraire métadonnées et contenu"""
        pages_dir = Path("site/src/pages")
        
        print("🔍 Analyse des articles existants...")
        
        for astro_file in pages_dir.glob("*.astro"):
            if astro_file.name == "index.astro":
                continue
                
            slug = astro_file.stem
            article_data = self.extraire_donnees_article(astro_file)
            
            if article_data:
                self.articles[slug] = article_data
                self.categoriser_article(slug, article_data)
        
        print(f"✅ {len(self.articles)} articles analysés")
        return len(self.articles)
    
    def extraire_donnees_article(self, fichier):
        """Extrait titre, description et mots-clés d'un fichier .astro"""
        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                contenu = f.read()
            
            # Extraire le frontmatter
            frontmatter_match = re.search(r'^---\s*\n(.*?)\n---', contenu, re.DOTALL)
            if not frontmatter_match:
                return None
            
            frontmatter = frontmatter_match.group(1)
            
            # Extraire titre et description
            title_match = re.search(r'title:\s*["\'](.+?)["\']', frontmatter)
            desc_match = re.search(r'description:\s*["\'](.+?)["\']', frontmatter)
            
            if not title_match:
                return None
            
            titre = title_match.group(1)
            description = desc_match.group(1) if desc_match else ""
            
            # Extraire le contenu principal pour analyse des mots-clés
            contenu_principal = re.sub(r'<[^>]+>', ' ', contenu)  # Nettoyer HTML
            mots_cles = self.extraire_mots_cles(titre + " " + description + " " + contenu_principal[:1000])
            
            return {
                "titre": titre,
                "description": description,
                "mots_cles": mots_cles,
                "path": str(fichier)
            }
            
        except Exception as e:
            print(f"❌ Erreur lecture {fichier}: {e}")
            return None
    
    def extraire_mots_cles(self, texte):
        """Extrait les mots-clés pertinents pour le maillage"""
        # Mots-clés déco importants
        keywords_deco = [
            "salon", "cuisine", "chambre", "salle de bain", "bureau", "terrasse", "balcon",
            "decoration", "amenagement", "design", "moderne", "scandinave", "industriel", "vintage",
            "couleurs", "peinture", "mobilier", "meubles", "rangement", "organisation",
            "plantes", "eclairage", "textiles", "cosy", "zen", "naturel", "chic", "tendance",
            "diy", "budget", "astuces", "conseils", "idees", "inspiration", "style"
        ]
        
        texte_lower = texte.lower()
        mots_trouves = []
        
        for keyword in keywords_deco:
            if keyword in texte_lower:
                mots_trouves.append(keyword)
        
        return mots_trouves
    
    def categoriser_article(self, slug, data):
        """Catégorise l'article par thème et mots-clés"""
        titre_lower = data["titre"].lower()
        
        # Classification thématique
        if any(word in titre_lower for word in ["salon", "living"]):
            self.themes["salon"].append(slug)
        elif any(word in titre_lower for word in ["cuisine", "kitchen"]):
            self.themes["cuisine"].append(slug)
        elif any(word in titre_lower for word in ["chambre", "bedroom"]):
            self.themes["chambre"].append(slug)
        elif any(word in titre_lower for word in ["salle de bain", "bathroom"]):
            self.themes["salle-de-bain"].append(slug)
        elif any(word in titre_lower for word in ["bureau", "office"]):
            self.themes["bureau"].append(slug)
        elif any(word in titre_lower for word in ["exterieur", "terrasse", "balcon", "jardin"]):
            self.themes["exterieur"].append(slug)
        else:
            self.themes["general"].append(slug)
        
        # Indexation par mots-clés
        for mot_cle in data["mots_cles"]:
            self.keywords[mot_cle].append(slug)
    
    def generer_liens_intelligents(self):
        """Génère des suggestions de liens entre articles"""
        suggestions = defaultdict(list)
        
        print("🔗 Génération des liens intelligents...")
        
        for slug, article in self.articles.items():
            liens_suggeres = set()
            
            # 1. Liens thématiques (même pièce)
            for theme, articles in self.themes.items():
                if slug in articles:
                    for autre_slug in articles:
                        if autre_slug != slug:
                            liens_suggeres.add(autre_slug)
            
            # 2. Liens par mots-clés communs
            for mot_cle in article["mots_cles"]:
                for autre_slug in self.keywords[mot_cle]:
                    if autre_slug != slug:
                        liens_suggeres.add(autre_slug)
            
            # Limiter à 5-8 liens pertinents par article
            suggestions[slug] = list(liens_suggeres)[:8]
        
        return suggestions
    
    def creer_fichier_maillage(self, suggestions):
        """Crée un fichier JSON avec toutes les suggestions de maillage"""
        
        # Enrichir avec les données des articles liés
        maillage_complet = {}
        
        for slug, liens in suggestions.items():
            if slug in self.articles:
                liens_enrichis = []
                
                for lien_slug in liens:
                    if lien_slug in self.articles:
                        liens_enrichis.append({
                            "slug": lien_slug,
                            "titre": self.articles[lien_slug]["titre"],
                            "description": self.articles[lien_slug]["description"]
                        })
                
                maillage_complet[slug] = {
                    "article": {
                        "titre": self.articles[slug]["titre"],
                        "description": self.articles[slug]["description"]
                    },
                    "liens_suggeres": liens_enrichis
                }
        
        # Sauvegarder
        with open("site/src/data/maillage-interne.json", "w", encoding="utf-8") as f:
            json.dump(maillage_complet, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Fichier de maillage créé: site/src/data/maillage-interne.json")
        return maillage_complet
    
    def generer_rapport(self, suggestions):
        """Génère un rapport détaillé du maillage"""
        print("\n" + "="*60)
        print("📊 RAPPORT MAILLAGE INTERNE")
        print("="*60)
        print(f"📄 Articles analysés: {len(self.articles)}")
        print(f"🏷️  Thèmes identifiés: {len(self.themes)}")
        print(f"🔑 Mots-clés uniques: {len(self.keywords)}")
        print()
        
        print("🏠 Répartition par thèmes:")
        for theme, articles in self.themes.items():
            print(f"   {theme}: {len(articles)} articles")
        
        print()
        print("🔗 Top 10 mots-clés les plus connectés:")
        top_keywords = sorted(self.keywords.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        for keyword, articles in top_keywords:
            print(f"   {keyword}: {len(articles)} articles")
        
        print()
        print("💡 Suggestions moyennes par article: {:.1f}".format(
            sum(len(liens) for liens in suggestions.values()) / len(suggestions)
        ))

def main():
    print("🔗 SYSTÈME DE MAILLAGE INTERNE INTELLIGENT")
    print("🎯 Analyse et génération de liens contextuels")
    print()
    
    maillage = MaillageInterne()
    
    # Étape 1: Analyser tous les articles
    nb_articles = maillage.analyser_articles()
    if nb_articles == 0:
        print("❌ Aucun article trouvé")
        return
    
    # Étape 2: Générer les liens intelligents
    suggestions = maillage.generer_liens_intelligents()
    
    # Étape 3: Créer le fichier de maillage
    maillage_complet = maillage.creer_fichier_maillage(suggestions)
    
    # Étape 4: Rapport final
    maillage.generer_rapport(suggestions)
    
    print()
    print("🎉 Maillage interne généré avec succès !")
    print("📁 Fichier: site/src/data/maillage-interne.json")

if __name__ == "__main__":
    main()