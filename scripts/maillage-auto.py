#!/usr/bin/env python3
"""
Maillage interne automatique pour cristallina.fr
Ajoute des liens internes pour atteindre un minimum de 5 liens sortants par article.
"""

import os
import re
import glob
import json
from collections import defaultdict

GUIDES_DIR = "/Users/benoit/cristallina/site/src/content/guides"
MIN_LINKS = 5

# Stopwords francais pour le matching semantique
STOPWORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'en', 'a', 'au',
    'aux', 'pour', 'par', 'sur', 'avec', 'dans', 'que', 'qui', 'ce', 'cette',
    'ces', 'son', 'sa', 'ses', 'mon', 'ma', 'mes', 'ton', 'ta', 'tes',
    'il', 'elle', 'on', 'nous', 'vous', 'ils', 'elles', 'est', 'sont',
    'pas', 'ne', 'plus', 'ou', 'se', 'si', 'tout', 'tous', 'toutes',
    'comment', 'faire', 'bien', 'tres', 'peut', 'avoir', 'etre',
    'votre', 'notre', 'leur', 'leurs', 'quand', 'dont', 'car',
    'd', 'l', 'n', 's', 'y', 'c', 'j', 'qu', 'lorsque',
    'idees', 'photos', 'images', 'conseils', 'guide', 'astuces',
    'modernes', 'moderne', '2026', 'decoration', 'deco', 'ikea',
    'maison', 'interieur', 'design', 'style', 'meilleures', 'meilleur',
    'nouveau', 'nouvelle', 'nouveaux', 'nouvelles', 'fort', 'frappe',
    'prix', 'moins', 'euros', 'chez', 'avec', 'cette', 'entre',
    'cet', 'aussi', 'comme', 'mais'
}

# Clusters semantiques manuels - articles qui DOIVENT se lier entre eux
SEMANTIC_CLUSTERS = {
    "douche-italienne": [
        "salle-de-bain/douche-italienne",
        "salle-de-bain/douches-italiennes-idees",
        "salle-de-bain/quel-receveur-pour-douche-italienne",
        "salle-de-bain/carrelage-douche-italienne",
        "salle-de-bain/douche-1-euro",
    ],
    "peinture-carrelage": [
        "couleurs/la-peinture-sur-carrelage-une-methode-pour-renover-votre-interieur",
        "salle-de-bain/peinture-pour-carrelage-douche",
        "salle-de-bain/peinture-pour-carrelage-salle-de-bain-les-choses-a-eviter",
        "cuisine/peinture-pour-carrelage-cuisine",
        "exterieur/peinture-pour-carrelage-exterieur-terrasse",
    ],
    "couleurs-deco": [
        "couleurs/couleurs-dinterieur-de-mur-et-de-peinture-a-la-mode-2026",
        "couleurs/couleurs-compatibles-avec-lorange-pour-les-murs-et-la-decoration",
        "couleurs/des-couleurs-pour-donner-de-la-profondeur-a-un-mur-ou-a-une-piece",
        "couleurs/couleurs-ocres-pour-les-murs-et-la-decoration",
        "couleurs/couleur-taupe",
        "couleurs/quelles-sont-les-couleurs-qui-se-marient-bien-avec-le-violet-en-decoration",
        "couleurs/couleurs-pour-la-salle-a-manger-a-peindre-et-a-decorer",
        "couleurs/peinture-luxens",
        "couleurs/avis-peinture-spectrum",
    ],
    "cuisine-amenagement": [
        "cuisine/cuisine",
        "cuisine/cuisines-modernes-2026-designs-modeles",
        "cuisine/cuisine-americaine-2026-dessins-et-modeles",
        "cuisine/cuisines-avec-ilot-2026-designs-et-tendances",
        "cuisine/petites-cuisines-modernes-2026-designs-et-modeles",
        "cuisine/la-cuisine-verte-et-bois-une-teinte-elegante-et-moderne",
        "cuisine/cuisine-olive",
        "cuisine/couleurs-de-cuisine-2026",
        "cuisine/decoration-cuisine",
        "cuisine/organisation-armoire-cuisine",
        "cuisine/cuisine-haut-gamme-77-ai-concept",
        "cuisine/le-charme-de-la-cuisine-rustique-un-look-retro-chic-incontournable",
        "cuisine/changer-portes-cuisines-ikea-faktum",
    ],
    "chambre-deco": [
        "chambre/decoration-de-la-chambre-a-coucher-2026-tendances-et-photos",
        "chambre/deco-terracotta-chambre",
        "chambre/les-meilleures-options-de-couleurs-pour-une-chambre-dadulte-a-deux-teintes",
        "chambre/ranger-chambre",
        "chambre/deco-chambre-harry-potter",
        "chambre/decorer-la-chambre-a-coucher-avec-peu-dargent",
        "chambre/decorer-une-chambre-dans-un-style-jungle",
        "chambre/chambre-sans-fenetre",
        "chambre/decorer-chambre-coucher-location",
        "chambre/guide-pour-une-deco-pop-dans-la-chambre-a-coucher",
        "chambre/le-feng-shui-dans-la-chambre-a-coucher",
    ],
    "salon-styles": [
        "decoration/salons-modernes-et-elegants-2026",
        "decoration/couleurs-du-salon-2026-palettes-de-murs-et-de-decors",
        "decoration/decoration-minimaliste-idees-et-photos-faciles",
        "decoration/decoration-petit-salon",
        "decoration/salons-bruns-idees-et-images",
        "decoration/salons-modernes-tendances-2026",
        "decoration/salon-plus-chaleureux",
        "decoration/bleu-salon",
        "decoration/chaise-salon",
    ],
    "styles-monde": [
        "decoration/decoration-marocaine-moderne-ou-classique",
        "decoration/decoration-francaise-idees-et-photos-romantiques",
        "decoration/decoration-africaine-50-photos-et-idees",
        "decoration/decoration-japonaise-20-images-et-idees",
        "decoration/decoration-maritime-50-photos-et-idees-modernes",
        "decoration/decoration-shabby-chic-idees-et-photos-de-style-et-de-decoration",
        "decoration/decoration-classique-20-images-et-idees-contemporaines",
        "decoration/decoration-vintage-50-images-et-idees-pour-linspiration",
        "decoration/50-idees-de-decoration-art-deco",
        "decoration/comment-combiner-le-style-industriel-et-scandinave",
    ],
    "sdb-amenagement": [
        "salle-de-bain/amenager-une-salle-de-bain-en-2026-styles-et-conseils",
        "salle-de-bain/salles-de-bains-modernes-2026-modeles-designs-decoration",
        "salle-de-bain/meuble-salle-de-bain-beton-cire",
        "salle-de-bain/salle-de-bain-industrielle",
        "salle-de-bain/couleurs-tendance-pour-les-salles-de-bains-modernes-2026",
        "salle-de-bain/plantes-salle-de-bains",
        "salle-de-bain/idees-de-rangement-et-de-placards-pour-la-salle-de-bains",
        "salle-de-bain/les-points-importants-a-renover-dans-une-salle-de-bain",
        "salle-de-bain/salles-de-bains-rustiques-decoration-et-design-modernes",
        "salle-de-bain/baignoire-japonaise",
        "salle-de-bain/baignoire-scandinave",
        "salle-de-bain/carrelage-metro-salle-de-bain",
        "salle-de-bain/comment-entretenir-un-bain-nordique",
    ],
    "exterieur-terrasse": [
        "exterieur/la-pergola-bioclimatique-lalliance-parfaite-entre-esthetique-et-confort",
        "exterieur/ombrager-terrasse",
        "exterieur/renovez-votre-terrasse-pour-la-securite",
        "exterieur/difference-pergola-tonnelle",
        "exterieur/comment-profiter-de-votre-exterieur-meme-lors-des-fortes-chaleurs-dete",
        "exterieur/le-guide-ultime-des-parasols-de-terrasse-pour-cafes-hotels-et-restaurants",
        "exterieur/peinture-pour-carrelage-exterieur-terrasse",
        "exterieur/papier-peint-dexterieur",
    ],
    "exterieur-jardin": [
        "exterieur/comment-creer-un-jardin-zen-en-7-etapes",
        "exterieur/jardins-verticaux-de-40-photos-dinspiration-verte",
        "exterieur/jardins-et-cours-mexicains-images-et-idees-pour-linspiration",
        "exterieur/jardins-interieurs-modernes-photos-et-conseils-de-conception",
        "exterieur/6-idees-pour-fabriquer-des-jardinieres-suspendues-maison",
        "exterieur/diy-jardiniere",
        "exterieur/poser-bordure-jardin-sans-beton",
        "exterieur/installer-serre-tunnel",
        "exterieur/comment-transformer-votre-jardin-avec-un-conteneur-maritime",
    ],
    "exterieur-maison": [
        "exterieur/couleurs-pour-les-exterieurs-et-les-facades-de-maisons-2026",
        "exterieur/maisons-modernes-2026-images-dexterieur-et-dinterieur",
        "exterieur/maisons-modernes-en-adobe-images-dinterieurs-et-dexterieurs",
        "exterieur/construire-pool-house",
        "exterieur/couleurs-des-portes-exterieures-comment-choisir-la-couleur",
        "decoration/facades-de-maisons-modernes-2026",
    ],
    "tableaux-murs": [
        "decoration/bien-accrocher-tableau-mural",
        "decoration/choisir-tableau-mural",
        "decoration/choisir-cadre-tableau-mural-vegetal",
        "decoration/choisir-tableau-lumineux",
        "decoration/choisir-tableau-planning-pense-bete",
        "decoration/choisir-tableau-velleda",
        "decoration/choisir-tableau-noir-ardoise",
        "decoration/choisir-tableau-enfant",
        "decoration/decoration-doree-sur-les-murs-les-meubles-ou-les-accessoires",
    ],
    "shopping-ikea": [
        "shopping/cohue-chez-ikea-avec-ce-plateau-multifonction-de-la-saison",
        "shopping/cohue-chez-ikea-avec-cette-lampe-articulee-super-design-a-moins-de-5-euros",
        "shopping/cohue-chez-ikea-avec-letagere-murale-prisee-a-prix-imbattable",
        "shopping/ikea-cartonne-avec-son-armoire-dangle",
        "shopping/ikea-cet-indispensable-pour-secher-son-linge-meme-en-automne-a-moins-de-6-euros",
        "shopping/ikea-frappe-fort-avec-cette-etagere-design-et-tres-pratique-qui-saccroche-au-mur-tres-facilement",
        "shopping/ikea-frappe-fort-avec-le-produit-indispensable-pour-le-bricolage-a-moins-de-13-euros",
        "shopping/ikea-frappe-fort-sa-nouvelle-table-de-nuit-a-9-e-en-edition-limitee",
        "shopping/ikea-lance-son-nouveau-support-pour-casque-design-a-un-prix-totalement-fou",
        "couleurs/ikea-frappe-tres-fort-avec-sa-table-ronde-minimaliste-en-deux-couleurs",
        "decoration/ikea-frappe-fort-avec-son-nouveau-canape-2-places-parfait-pour-les-petits-salons",
        "cuisine/changer-portes-cuisines-ikea-faktum",
        "rangement/ikea-cartonne-avec-ce-rangement-bureau-decouverte-du-must-have-de-la-saison",
    ],
    "bricolage-murs": [
        "decoration/comment-enduir-un-mur-en-parpaing",
        "decoration/recouvrir-parpaings",
        "decoration/crepir-un-mur-interieur",
        "decoration/peindre-sans-poncer",
        "decoration/peindre-lino",
        "decoration/pistolet-a-calfeutrer",
        "decoration/isolation-dune-dalle-en-beton-techniques-options-disolation-et-cout",
    ],
    "tapis-textiles": [
        "decoration/choisir-tapis-fibre-naturelle",
        "decoration/choisir-tapis-imprime",
        "decoration/choisir-tapis-logo-personnalise",
        "decoration/coussins-decoratifs-pour-les-salons-les-fauteuils-et-les-sols",
        "decoration/rotin-osier",
    ],
    "plantes-interieur": [
        "decoration/la-peperomia-hope",
        "decoration/entretenir-du-scindapsus-pictus-la-plante-robuste-qui-a-tout-pour-plaire",
        "decoration/pots-de-fleurs-decoratifs-70-photos-et-idees",
        "salle-de-bain/plantes-salle-de-bains",
        "exterieur/jardins-verticaux-de-40-photos-dinspiration-verte",
    ],
    "diy-creatif": [
        "decoration/artisanat-avec-des-materiaux-recycles-pour-la-maison",
        "decoration/creez-votre-table-basse-au-design-original-avec-ces-astuces-diy",
        "decoration/comment-realiser-des-fleurs-en-tissu-ou-en-papier-etape-par-etape",
        "decoration/fabriquer-un-bureau-avec-des-caissons",
        "decoration/fabriquer-four-a-pizza",
        "decoration/pneus-recycles-pour-la-decoration",
    ],
}

# Ancres suggerees par cluster (generiques, seront adaptees)
ANCHOR_TEMPLATES = {
    "douche-italienne": "douche italienne",
    "peinture-carrelage": "peinture pour carrelage",
    "couleurs-deco": "couleurs de decoration",
    "cuisine-amenagement": "amenagement cuisine",
    "chambre-deco": "decoration de chambre",
    "salon-styles": "decoration de salon",
    "styles-monde": "styles de decoration",
    "sdb-amenagement": "salle de bain",
    "exterieur-terrasse": "terrasse et exterieur",
    "exterieur-jardin": "jardin",
    "exterieur-maison": "facade et exterieur",
    "tableaux-murs": "tableaux et decoration murale",
    "shopping-ikea": "bons plans IKEA",
    "bricolage-murs": "bricolage et renovation",
    "tapis-textiles": "tapis et textiles",
    "plantes-interieur": "plantes d'interieur",
    "diy-creatif": "DIY et creation",
}


def load_articles():
    """Load all articles with metadata."""
    articles = {}
    files = glob.glob(f"{GUIDES_DIR}/**/*.md", recursive=True)

    for f in files:
        if f.endswith("index.md"):
            continue

        slug = os.path.splitext(os.path.basename(f))[0]
        rel_path = os.path.relpath(f, GUIDES_DIR)
        branch_slug = rel_path.replace(os.sep, '/').rsplit('.md', 1)[0]  # e.g. "decoration/brise-vue"
        branch = branch_slug.split('/')[0]

        with open(f, 'r') as fh:
            content = fh.read()

        # Extract title from frontmatter
        title_match = re.search(r'^title:\s*"(.+?)"', content, re.MULTILINE)
        title = title_match.group(1) if title_match else slug

        # Count existing outgoing links to /guides/
        existing_links = re.findall(r'\]\(/guides/([^)]+)\)', content)
        existing_targets = set()
        for link in existing_links:
            link_clean = link.rstrip('/')
            existing_targets.add(link_clean)

        # Extract keywords from title
        title_words = set()
        for w in re.findall(r'[a-zA-ZàâäéèêëïîôùûüçÀÂÄÉÈÊËÏÎÔÙÛÜÇ]+', title.lower()):
            if w not in STOPWORDS and len(w) > 2:
                title_words.add(w)

        articles[branch_slug] = {
            'file': f,
            'slug': slug,
            'branch_slug': branch_slug,
            'branch': branch,
            'title': title,
            'title_words': title_words,
            'content': content,
            'existing_targets': existing_targets,
            'outgoing_count': len(existing_targets),
        }

    return articles


def get_clusters_for_article(branch_slug):
    """Find which clusters an article belongs to."""
    clusters = []
    for cluster_name, members in SEMANTIC_CLUSTERS.items():
        if branch_slug in members:
            clusters.append(cluster_name)
    return clusters


def compute_relevance(source, target, articles):
    """Compute relevance score between two articles."""
    score = 0

    # Same branch bonus
    if source['branch'] == target['branch']:
        score += 3

    # Shared title keywords
    shared = source['title_words'] & target['title_words']
    score += len(shared) * 2

    # Same cluster bonus (big)
    src_clusters = get_clusters_for_article(source['branch_slug'])
    tgt_clusters = get_clusters_for_article(target['branch_slug'])
    shared_clusters = set(src_clusters) & set(tgt_clusters)
    if shared_clusters:
        score += 5

    # Cross-cluster adjacency (both in related themes)
    adjacent_clusters = {
        'salon-styles': ['couleurs-deco', 'styles-monde', 'tapis-textiles'],
        'couleurs-deco': ['salon-styles', 'chambre-deco', 'sdb-amenagement'],
        'cuisine-amenagement': ['couleurs-deco', 'shopping-ikea'],
        'chambre-deco': ['couleurs-deco', 'salon-styles', 'plantes-interieur'],
        'sdb-amenagement': ['douche-italienne', 'peinture-carrelage', 'couleurs-deco'],
        'douche-italienne': ['sdb-amenagement', 'peinture-carrelage'],
        'peinture-carrelage': ['sdb-amenagement', 'douche-italienne', 'bricolage-murs'],
        'exterieur-terrasse': ['exterieur-jardin', 'exterieur-maison'],
        'exterieur-jardin': ['exterieur-terrasse', 'plantes-interieur'],
        'exterieur-maison': ['exterieur-terrasse', 'couleurs-deco'],
        'bricolage-murs': ['peinture-carrelage', 'diy-creatif'],
        'diy-creatif': ['bricolage-murs', 'tapis-textiles'],
        'tableaux-murs': ['salon-styles', 'chambre-deco'],
        'shopping-ikea': ['cuisine-amenagement', 'salon-styles', 'chambre-deco'],
        'tapis-textiles': ['salon-styles', 'chambre-deco'],
        'plantes-interieur': ['exterieur-jardin', 'chambre-deco', 'sdb-amenagement'],
    }

    for sc in src_clusters:
        for tc in tgt_clusters:
            if tc in adjacent_clusters.get(sc, []):
                score += 2

    return score


def generate_anchor(source, target):
    """Generate a natural anchor text for the link."""
    title = target['title']

    # Try to extract a short, natural anchor from the title
    # Remove ":" and what follows if title is long
    if ':' in title and len(title) > 50:
        title = title.split(':')[0].strip()

    # Clean up common prefixes
    for prefix in ['Comment ', 'Pourquoi ', "L'", 'Le ', 'La ', 'Les ']:
        if title.startswith(prefix) and len(title) > 40:
            pass  # Keep it for now

    # Shorten very long titles
    if len(title) > 60:
        # Try to find a natural break
        words = title.split()
        short = []
        for w in words:
            short.append(w)
            if len(' '.join(short)) > 40:
                break
        title = ' '.join(short)

    return title.lower().rstrip('.')


def find_insertion_point(content):
    """Find the best place to insert a 'Pour aller plus loin' section."""
    # Insert before FAQ if present
    faq_match = re.search(r'^## .*FAQ|^## .*[Qq]uestions?\s', content, re.MULTILINE)
    if faq_match:
        return faq_match.start()

    # Insert before last heading that looks like conclusion
    conclusion_patterns = [
        r'^## .*[Cc]onclusion',
        r'^## .*[Ss]ynth[eè]se',
        r'^## .*[Rr][eé]sum[eé]',
        r'^## .*[Mm]ot de la fin',
        r'^## .*[Vv]erdict',
        r'^## .*[Bb]ilan',
        r'^## .*[Ee]n r[eé]sum[eé]',
    ]

    last_match = None
    for pattern in conclusion_patterns:
        m = re.search(pattern, content, re.MULTILINE)
        if m:
            last_match = m

    if last_match:
        return last_match.start()

    # Fallback: insert before the very last ## heading
    headings = list(re.finditer(r'^## ', content, re.MULTILINE))
    if len(headings) >= 2:
        return headings[-1].start()

    # Last resort: end of file
    return len(content)


def inject_links(articles):
    """Main function: inject links to reach minimum 5 per article."""
    stats = {'total_links_added': 0, 'articles_modified': 0}

    for branch_slug, article in articles.items():
        needed = MIN_LINKS - article['outgoing_count']
        if needed <= 0:
            continue

        # Find best candidates
        candidates = []
        for other_slug, other in articles.items():
            if other_slug == branch_slug:
                continue
            if other_slug in article['existing_targets']:
                continue
            # Also skip if the slug (without branch) is already targeted
            if any(other['slug'] in t for t in article['existing_targets']):
                continue

            relevance = compute_relevance(article, other, articles)
            if relevance > 0:
                candidates.append((relevance, other_slug, other))

        # Sort by relevance (highest first)
        candidates.sort(key=lambda x: -x[0])

        # Take top candidates (need + 2 extra for safety)
        selected = candidates[:needed + 2][:max(needed, 3)]

        if not selected:
            # Fallback: pick from same branch
            for other_slug, other in articles.items():
                if other_slug == branch_slug:
                    continue
                if other['branch'] == article['branch'] and other_slug not in article['existing_targets']:
                    selected.append((1, other_slug, other))
                    if len(selected) >= needed:
                        break

        if not selected:
            print(f"  SKIP {branch_slug}: no candidates found")
            continue

        # Build the links section
        links_md = "\n## Sur le meme theme\n\n"
        links_added = 0

        for _, target_slug, target in selected[:needed]:
            anchor = generate_anchor(article, target)
            link = f"- [{anchor}](/guides/{target_slug}/)\n"
            links_md += link
            links_added += 1

        links_md += "\n"

        if links_added == 0:
            continue

        # Find insertion point
        content = article['content']
        insert_pos = find_insertion_point(content)

        # Insert
        new_content = content[:insert_pos] + links_md + content[insert_pos:]

        # Write back
        with open(article['file'], 'w') as fh:
            fh.write(new_content)

        stats['total_links_added'] += links_added
        stats['articles_modified'] += 1
        print(f"  {branch_slug}: +{links_added} liens (total: {article['outgoing_count'] + links_added})")

    return stats


def main():
    print("=== Chargement des articles ===")
    articles = load_articles()
    print(f"  {len(articles)} articles charges")

    # Stats before
    below_min = sum(1 for a in articles.values() if a['outgoing_count'] < MIN_LINKS)
    print(f"  {below_min} articles sous le minimum de {MIN_LINKS} liens sortants")

    print("\n=== Injection des liens ===")
    stats = inject_links(articles)

    print(f"\n=== Resultat ===")
    print(f"  Articles modifies: {stats['articles_modified']}")
    print(f"  Liens ajoutes: {stats['total_links_added']}")

    # Verify
    print("\n=== Verification post-injection ===")
    articles_after = load_articles()
    still_below = sum(1 for a in articles_after.values() if a['outgoing_count'] < MIN_LINKS)
    print(f"  Articles encore sous {MIN_LINKS} liens: {still_below}")

    if still_below > 0:
        for bs, a in articles_after.items():
            if a['outgoing_count'] < MIN_LINKS:
                print(f"    {bs}: {a['outgoing_count']} liens")


if __name__ == "__main__":
    main()
