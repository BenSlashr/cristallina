#!/usr/bin/env python3
"""
Mass Pinterest Scraper - Cristallina
Scrape ciblé avec requêtes longue traîne pour chaque sujet
"""

import re
import sys
import asyncio
import subprocess
import random
from pathlib import Path

# Mapping intelligent : URL → Requête Pinterest spécifique (longue traîne)
PINTEREST_QUERIES = {
    # Décoration & Style
    "decoration-salon-naturel-chic": "salon décoration naturel chic lin beige plantes",
    "meuble-salle-de-bain-beton-cire": "meuble salle bain béton ciré vasque design moderne",
    "decoration-de-la-chambre-a-coucher-2026-tendances-et-photos": "chambre coucher 2026 tendances décoration moderne",
    "couleurs-pour-les-exterieurs-et-les-facades-de-maisons-2026": "façade maison couleur extérieur 2026 tendance peinture",
    "couleurs-compatibles-avec-lorange-pour-les-murs-et-la-decoration": "décoration orange mur couleur assortiment design",
    "maisons-modernes-2026-images-dexterieur-et-dinterieur": "maison moderne 2026 architecture design intérieur extérieur",
    "cuisine-olive": "cuisine couleur olive vert sauge décoration moderne",
    "appartement-traversant": "appartement traversant lumière aménagement design",
    "decoration-marocaine-moderne-ou-classique": "décoration marocaine moderne zellige tapis berbère",
    "salle-de-bain-cosy": "salle bain cosy chaleureuse bois naturel spa",
    "la-cuisine-verte-et-bois-une-teinte-elegante-et-moderne": "cuisine verte bois sauge eucalyptus moderne design",
    "salons-modernes-et-elegants-2026": "salon moderne élégant 2026 canapé design déco",
    "decorer-une-chambre-dans-un-style-jungle": "chambre jungle tropical plantes vertes papier peint",
    "baignoire-scandinave": "baignoire scandinave bois îlot design nordique",
    "ranger-chambre": "rangement chambre organisation dressing optimisé",
    "maisons-modernes-en-adobe-images-dinterieurs-et-dexterieurs": "maison adobe moderne terre architecture écologique",
    "amenager-une-salle-de-bain-en-2026-styles-et-conseils": "aménagement salle bain 2026 moderne design tendance",
    "maisons-rustiques-modernes-idees-et-photos-de-decoration": "maison rustique moderne pierre bois authentique",
    "les-meilleures-options-de-couleurs-pour-une-chambre-dadulte-a-deux-teintes": "chambre adulte deux couleurs peinture bicolore",
    "douches-italiennes-idees": "douche italienne carrelage receveur moderne design",
    "carrelage-douche-italienne": "carrelage douche italienne grand format pierre",
    "facades-de-maisons-modernes-2026": "façade maison moderne 2026 enduit bardage design",
    "salle-de-bain-industrielle": "salle bain industrielle métal carrelage metro noir",
    "couleurs-du-salon-2026-palettes-de-murs-et-de-decors": "couleur salon 2026 peinture tendance palette déco",
    "decoration-shabby-chic-idees-et-photos-de-style-et-de-decoration": "décoration shabby chic pastel vintage romantique",
    "salles-de-bains-modernes-2026-modeles-designs-decoration": "salle bain moderne 2026 design luxe contemporain",
    "couleurs-ocres-pour-les-murs-et-la-decoration": "couleur ocre terre cuite mur décoration chaude",
    "quelles-sont-les-couleurs-qui-se-marient-bien-avec-le-violet-en-decoration": "couleur violet décoration assortiment mauve prune",
    "appartements-modernes-60-photos-et-conseils-de-decoration": "appartement moderne décoration design contemporain",
    "decoration-francaise-idees-et-photos-romantiques": "décoration française romantique campagne chic authentique",
    "couleurs-pour-la-salle-a-manger-a-peindre-et-a-decorer": "salle manger couleur peinture décoration conviviale",
    "decoration-minimaliste-idees-et-photos-faciles": "décoration minimaliste épuré scandinave simple blanc",
    "petites-cuisines-modernes-2026-designs-et-modeles": "petite cuisine moderne 2026 compact optimisée",
    "idees-de-rangement-et-de-placards-pour-la-salle-de-bains": "rangement salle bain placard organisation optimisé",
    "plantes-salle-de-bains": "plantes salle bain humidité fougère bambou déco",
    "douche-italienne": "douche italienne moderne receveur carrelage design",
    "peinture-pour-carrelage-cuisine": "peinture carrelage cuisine rénovation relooking",
    "des-couleurs-pour-donner-de-la-profondeur-a-un-mur-ou-a-une-piece": "couleur profondeur mur pièce perspective design",
    "decoration-doree-sur-les-murs-les-meubles-ou-les-accessoires": "décoration dorée or laiton accessoires luxe",
    "couleurs-dinterieur-de-mur-et-de-peinture-a-la-mode-2026": "couleur intérieur 2026 tendance peinture mode",
    "decorations-de-larbre-de-noel-pour-2026": "décoration sapin noel 2026 boules guirlandes moderne",
    "decorer-avec-terracota": "décoration terracotta terre cuite ocre chaleureux",
    "decoration-africaine-50-photos-et-idees": "décoration africaine ethnique wax masques artisanat",
    "couleurs-des-portes-exterieures-comment-choisir-la-couleur": "porte entrée couleur extérieur façade assortiment",
    "jardins-verticaux-de-40-photos-dinspiration-verte": "jardin vertical mur végétalisé plantes grimpantes",
    "couleur-canape-choisir": "canapé couleur choix salon décoration assortiment",
    "le-mobilier-metallique-une-tendance-deco-sure": "mobilier métal industriel acier design moderne",
    "pots-de-fleurs-decoratifs-70-photos-et-idees": "pot fleur décoratif jardinière design céramique",
    "decoration-maritime-50-photos-et-idees-modernes": "décoration maritime mer bleu blanc corde",
    "salons-bruns-idees-et-images": "salon marron brun taupe chocolat décoration",
    "le-charme-de-la-cuisine-rustique-un-look-retro-chic-incontournable": "cuisine rustique campagne bois authentique vintage",
    "carrelage-metro-salle-de-bain": "carrelage métro salle bain blanc biseauté rétro",
    "50-idees-de-decoration-art-deco": "décoration art déco années 20 géométrique doré",
    "couleurs-tendance-pour-les-salles-de-bains-modernes-2026": "couleur salle bain 2026 tendance moderne design",
    "decoration-petit-salon": "petit salon décoration optimisation espace compact",
    "jardins-interieurs-modernes-photos-et-conseils-de-conception": "jardin intérieur moderne plantes design végétal",
    "decoration-classique-20-images-et-idees-contemporaines": "décoration classique intemporel élégant raffiné",
    "cuisines-avec-ilot-2026-designs-et-tendances": "cuisine ilot 2026 design moderne central",
    "decoration-vintage-50-images-et-idees-pour-linspiration": "décoration vintage rétro années 50 60 authentique",
    "salle-de-jeux-pour-enfants": "salle jeu enfant playroom rangement coloré",
    "couleurs-de-cuisine-2026": "couleur cuisine 2026 tendance peinture moderne",
    "le-feng-shui-dans-la-chambre-a-coucher": "feng shui chambre zen harmonie équilibre",
    "decorer-la-chambre-a-coucher-avec-peu-dargent": "décoration chambre petit budget DIY économique",
    "cuisines-modernes-2026-designs-modeles": "cuisine moderne 2026 design contemporain tendance",
    "salles-de-bains-rustiques-decoration-et-design-modernes": "salle bain rustique moderne bois pierre",
    "salons-modernes-tendances-2026": "salon moderne 2026 tendance décoration design",
    "comment-combiner-le-style-industriel-et-scandinave": "style industriel scandinave mix métal bois",
    "decoration-japonaise-20-images-et-idees": "décoration japonaise zen minimaliste tatami",
    "decoration-cuisine": "décoration cuisine moderne design accessoires",
    "coussins-decoratifs-pour-les-salons-les-fauteuils-et-les-sols": "coussin décoratif salon canapé textile design",
    "bleu-salon": "salon bleu marine pétrole canard décoration",
    "salon-plus-chaleureux": "salon chaleureux cosy ambiance chaude déco",
    "cuisine-americaine-2026-dessins-et-modeles": "cuisine américaine 2026 ouverte bar design",
    "le-lustre-style-baroque": "lustre baroque cristal doré pampilles classique",
    "patio-moderne-de-maisons-simples-et-belles": "patio moderne design extérieur terrasse",
    "couleur-taupe": "couleur taupe décoration neutre élégant",
    
    # Bricolage & DIY
    "recouvrir-parpaings": "recouvrir parpaing enduit crépi façade extérieur",
    "poser-bordure-jardin-sans-beton": "bordure jardin pose sans béton flexible",
    "comment-verouiller-porte-interieur": "verrouiller porte intérieur serrure sécurité",
    "peinture-luxens": "peinture luxens avis couleur nuancier qualité",
    "peindre-lino": "peindre lino sol rénovation peinture adhérence",
    "parquet-tache": "parquet taché réparation ponçage rénovation",
    "comment-isoler-une-montee-descalier": "isolation escalier montée phonique thermique",
    "escaliers-silencieux": "escalier silencieux grincement réparation bruit",
    "crepir-un-mur-interieur": "crépir mur intérieur enduit technique application",
    "comment-nettoyer-une-table-en-ceramique": "nettoyer table céramique entretien produit",
    "comment-peindre-des-bocaux-ou-des-bouteilles-en-verre": "peindre bocal verre DIY peinture technique",
    "fabriquer-un-bureau-avec-des-caissons": "fabriquer bureau caisson DIY plan construction",
    "comment-realiser-des-fleurs-en-tissu-ou-en-papier-etape-par-etape": "fleur tissu papier DIY tutorial étape",
    "comment-se-debarrasser-de-la-cochenille-sur-un-citronnier": "cochenille citronnier traitement naturel lutte",
    "tuile-transparente-cout-et-usage": "tuile transparente polycarbonate toit véranda",
    "fabriquer-four-a-pizza": "fabriquer four pizza DIY construction brique",
    "astuce-de-grand-mere-nettoyer-un-canape-en-cuir-encrasse": "nettoyer canapé cuir encrassé astuce grand-mère",
    "5-astuces-de-deco-massif-avec-galets": "massif galets décoration jardin aménagement",
    "comment-peut-on-semer-du-gazon-sans-rouleau": "semer gazon sans rouleau technique semis",
    "comment-enduir-un-mur-en-parpaing": "enduire mur parpaing ciment technique",
    "quel-receveur-pour-douche-italienne": "receveur douche italienne choix matériau",
    "la-peinture-sur-carrelage-une-methode-pour-renover-votre-interieur": "peinture carrelage rénovation technique produit",
    "comment-creer-une-station-de-gaming": "station gaming setup bureau éclairage",
    "comment-se-debarrasser-des-fourmis-dans-le-jardin": "fourmis jardin élimination naturel répulsif",
    "comment-creer-un-jardin-zen-en-7-etapes": "jardin zen création étapes bambou sable",
    "la-pergola-bioclimatique-lalliance-parfaite-entre-esthetique-et-confort": "pergola bioclimatique lames orientables design",
    "comment-transformer-votre-jardin-avec-un-conteneur-maritime": "conteneur maritime jardin transformation aménagement",
    "quel-est-le-meilleur-moyen-de-se-debarrasser-dun-nid-de-guepes-dans-un-mur": "nid guêpes mur élimination sécurité",
    "recuperation-eau-piscine": "récupération eau piscine écologique système",
    "peindre-sans-poncer": "peindre sans poncer adhérence primaire technique",
    "renovez-votre-terrasse-pour-la-securite": "rénovation terrasse sécurité antidérapant",
    "bien-accrocher-tableau-mural": "accrocher tableau mur fixation solide",
    "peinture-pour-carrelage-douche": "peinture carrelage douche étanche technique",
    "comment-entretenir-un-bain-nordique": "bain nordique entretien spa bois",
    "choisir-cadre-tableau-mural-vegetal": "cadre tableau végétal mur plantes",
    "diy-jardiniere": "jardinière DIY fabrication bois palettes",
    "erreurs-rideaux": "erreurs rideaux pose longueur choix",
    "les-points-importants-a-renover-dans-une-salle-de-bain": "rénovation salle bain points importants étapes",
    "installer-serre-tunnel": "serre tunnel installation jardin protection",
    "volets-en-bois": "volets bois entretien rénovation peinture",
    "toiture-shingle-les-caracteristiques-le-cout-et-le-devis": "toiture shingle bardeaux asphalte pose",
    "construire-pool-house": "pool house construction plan permission",
    "les-portes-coulissantes-disponible-chez-leroy-merlin": "porte coulissante leroy merlin choix installation",
    "piece-trop-chaude": "pièce chaude refroidir ventilation isolation",
    "couleurs-tendances-automne-hiver-2021": "couleur tendance automne hiver déco",
    "peinture-pour-carrelage-salle-de-bain-les-choses-a-eviter": "peinture carrelage salle bain erreurs éviter",
    "choisir-tableau-noir-ardoise": "tableau noir ardoise cuisine bureau",
    "peinture-pour-carrelage-exterieur-terrasse": "peinture carrelage extérieur terrasse sol",
    "pistolet-a-calfeutrer": "pistolet calfeutrer silicone étanchéité",
    "isolation-dune-dalle-en-beton-techniques-options-disolation-et-cout": "isolation dalle béton technique matériau",
    "ombrager-terrasse": "ombrager terrasse voile parasol pergola",
    "6-idees-pour-fabriquer-des-jardinieres-suspendues-maison": "jardinière suspendue DIY fabrication maison",
    "papier-peint-dexterieur": "papier peint extérieur façade résistant",
    "artisanat-avec-des-materiaux-recycles-pour-la-maison": "artisanat recyclage matériaux DIY maison",
    "conseils-pour-leclairage-dune-cave-a-vin": "éclairage cave vin LED température",
    "remplacer-roulette-veranda": "roulette véranda remplacement réparation",
    "organisation-armoire-cuisine": "organisation armoire cuisine rangement optimisation",
    "decirer-un-meuble-en-bois-les-astuces-pratiques": "décirer meuble bois cire technique",
    "rangement-soutien-gorge": "rangement soutien-gorge tiroir organisation",
    "etiquette-linge": "étiquette linge marquage nom enfant",
    "changer-portes-cuisines-ikea-faktum": "changer porte cuisine ikea faktum",
    "installer-eclairage-exterieur-sans-fil": "éclairage extérieur sans fil solaire",
    "comment-profiter-de-votre-exterieur-meme-lors-des-fortes-chaleurs-dete": "extérieur chaleur été ombrage rafraîchissement",
    "chambre-sans-fenetre": "chambre sans fenêtre éclairage aération",
    
    # Objets & Mobilier spécifiques
    "poele-a-granules-suspendu": "poêle granulés suspendu design moderne",
    "comment-fabriquer-soi-meme-un-bar-en-palettes": "bar palettes DIY fabrication bois récup",
    "table-basse-aquarium-idee-pour-decorer-votre-salle": "table basse aquarium design salon original",
    "baignoire-japonaise": "baignoire japonaise ofuro bois profonde",
    "douche-1-euro": "douche 1 euro aide rénovation subvention",
    "table-basse-japonaise-kotatsu": "table kotatsu japonaise chauffante tatami",
    "combien-de-temps-avant-dutiliser-le-matelas-emma": "matelas emma déballage attente utilisation",
    "maison-container": "maison container maritime transformation habitation",
    "choisir-aquarium-mural": "aquarium mural design intégré décoration",
    "percale-coton": "percale coton linge lit qualité",
    "satin-coton": "satin coton textile linge qualité",
    "rotin-osier": "rotin osier mobilier naturel tressé",
    "album-photo": "album photo souvenir livre personnalisé",
    "chaise-salon": "chaise salon design confortable moderne",
    "choisir-tableau-planning-pense-bete": "tableau planning pense-bête organisation",
    "choisir-tableau-mural": "tableau mural décoration art choix",
    "choisir-tableau-velleda": "tableau velleda effaçable bureau école",
    "creez-votre-table-basse-au-design-original-avec-ces-astuces-diy": "table basse DIY design original fabrication",
    "choisir-tapis-imprime": "tapis imprimé motif salon décoration",
    "choisir-tapis-fibre-naturelle": "tapis fibre naturelle jute sisal",
    "choisir-tableau-lumineux": "tableau lumineux LED décoratif",
    "difference-pergola-tonnelle": "pergola tonnelle différence choix jardin",
    "tiny-house-container": "tiny house container petit maison",
    "installation-et-usage-dune-tuile-chatiere": "tuile chatière ventilation toiture installation",
    "ascenseur-maison-etna-france": "ascenseur maison particulier etna installation",
    "le-guide-ultime-des-parasols-de-terrasse-pour-cafes-hotels-et-restaurants": "parasol terrasse professionnel café restaurant",
    
    # Problèmes & Nuisibles
    "pupes-de-mouche": "pupes mouche élimination insectes nuisibles",
    "blattes-forestieres-ambrees": "blatte forestière ambrée identification traitement",
    "dans-un-aquarium-comment-se-debarrasser-des-algues-noires": "algues noires aquarium traitement élimination",
    "heure-taupes-sortent-dehors": "taupe jardin sortie heure piégeage",
    "invasion-mouches": "invasion mouches maison élimination répulsif",
    "comment-se-debarrasser-des-algues-noires-dans-un-aquarium": "algues noires aquarium élimination traitement",
    
    # Plantes & Jardinage
    "la-peperomia-hope": "peperomia hope plante verte entretien",
    "plantes-salle-de-bains": "plantes salle bain humidité tropicales",
    "entretenir-du-scindapsus-pictus-la-plante-robuste-qui-a-tout-pour-plaire": "scindapsus pictus plante entretien pothos",
    "jardins-et-cours-mexicains-images-et-idees-pour-linspiration": "jardin mexicain cour cactus design",
    
    # Noël & Fêtes
    "decoration-anniversaire-sur-le-theme-de-fort-boyard": "anniversaire fort boyard décoration thème",
    "noel-2021": "noel 2021 décoration sapin tendance",
    
    # Avis & Tests
    "avis-peinture-spectrum": "peinture spectrum avis test qualité",
    "avis-poster-store": "poster store avis qualité impression",
    
    # Ikea spécifique
    "ikea-frappe-fort-avec-son-nouveau-canape-2-places-parfait-pour-les-petits-salons": "ikea canapé 2 places petit salon",
    "cohue-chez-ikea-avec-ce-plateau-multifonction-de-la-saison": "ikea plateau multifonction design tendance",
    "cohue-chez-ikea-avec-cette-lampe-articulee-super-design-a-moins-de-5-euros": "ikea lampe articulée design pas cher",
    "ikea-cartonne-avec-son-armoire-dangle": "ikea armoire angle rangement optimisé",
    "ikea-cartonne-avec-ce-rangement-bureau-decouverte-du-must-have-de-la-saison": "ikea rangement bureau organisation",
    "ikea-lance-son-nouveau-support-pour-casque-design-a-un-prix-totalement-fou": "ikea support casque gaming bureau",
    
    # Immobilier & Finance
    "bureau-de-jardin-de-5m2-un-mauvais-concept-qui-etait-cense-etre-sympa": "bureau jardin 5m2 télétravail extérieur",
    "action-logement": "action logement aide financement travaux",
    "deco-et-equipement-b2b": "déco équipement professionnel b2b",
    "cuisine": "cuisine aménagement design moderne tendance"
}

async def scrape_pinterest_for_topic(topic_slug, pinterest_query, count=5):
    """Scrape Pinterest pour un sujet spécifique"""
    print(f"🎯 {topic_slug}")
    print(f"🔍 Query: {pinterest_query}")
    
    try:
        # Exécuter le scraper Playwright
        process = await asyncio.create_subprocess_exec(
            'python3', 'scripts/pinterest-playwright.py', 
            pinterest_query, str(count),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print(f"✅ {topic_slug}: {count} images récupérées")
            return True
        else:
            print(f"❌ {topic_slug}: Échec scraping")
            print(f"Error: {stderr.decode()[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {topic_slug}: Exception {e}")
        return False

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mass-pinterest-scraper.py [nombre_sujets] [images_par_sujet]")
        print("Exemple: python3 mass-pinterest-scraper.py 20 5")
        sys.exit(1)
    
    max_topics = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    images_per_topic = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    print("🎨 MASS PINTEREST SCRAPER - CRISTALLINA")
    print("🎯 Scraping ciblé avec longue traîne")
    print(f"📊 {max_topics} sujets × {images_per_topic} images = {max_topics * images_per_topic} images total")
    print()
    
    # Prendre les N premiers sujets
    topics_to_scrape = list(PINTEREST_QUERIES.items())[:max_topics]
    
    successful = 0
    failed = 0
    
    # Scraping avec gestion intelligente des pauses anti-ban
    for i, (topic_slug, pinterest_query) in enumerate(topics_to_scrape, 1):
        print(f"\n[{i}/{max_topics}] ", end="")
        
        success = await scrape_pinterest_for_topic(topic_slug, pinterest_query, images_per_topic)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Pauses anti-ban intelligentes
        if i < len(topics_to_scrape):
            if i % 10 == 0:
                # Pause longue tous les 10 sujets
                print(f"\n⏸️  Pause longue anti-ban (60s) après {i} sujets...")
                await asyncio.sleep(60)
            elif i % 5 == 0:
                # Pause moyenne tous les 5 sujets
                print(f"\n⏸️  Pause moyenne (30s) après {i} sujets...")
                await asyncio.sleep(30)
            else:
                # Pause courte aléatoire entre chaque requête
                pause = random.uniform(2, 8)
                print(f" (pause {pause:.1f}s)")
                await asyncio.sleep(pause)
    
    print("\n" + "="*60)
    print(f"🎉 SCRAPING MASSIF TERMINÉ")
    print(f"✅ Succès: {successful}/{max_topics}")
    print(f"❌ Échecs: {failed}/{max_topics}")
    print(f"📸 Images estimées: {successful * images_per_topic}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())