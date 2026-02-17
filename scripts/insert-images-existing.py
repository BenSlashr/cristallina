#!/usr/bin/env python3
"""
Insert Pinterest/Unsplash images into existing .astro articles that have < 5 images.

Usage:
    python3 scripts/insert-images-existing.py [--dry-run]
"""

import os
import re
import sys
import random

PAGES_DIR = "site/src/pages"
IMAGES_DIR = "site/public/images"
MIN_IMAGE_SIZE = 30 * 1024  # 30KB minimum to avoid thumbnails
TARGET_IMAGES = 6  # Target total images per article

# Manual mapping: slug keywords -> Pinterest/Unsplash image prefixes
SLUG_IMAGE_MAP = {
    "balcon": [
        "pinterest-d-coration-scandinave",
        "pinterest-d-coration-minimaliste",
        "pinterest-appartement-moderne",
    ],
    "chambre-ado": [
        "pinterest-chambre-coucher-2026",
        "pinterest-rangement-chambre",
        "pinterest-chambre-jungle",
    ],
    "chambre-parentale": [
        "pinterest-chambre-coucher-2026",
        "pinterest-chambre-adulte-deux-couleurs",
        "unsplash-cozy-bedroom",
    ],
    "cuisine-vintage": [
        "pinterest-cuisine-verte-bois",
        "pinterest-d-coration-fran-aise",
        "pinterest-maison-rustique-moderne",
    ],
    "couloir": [
        "pinterest-d-coration-minimaliste",
        "pinterest-d-coration-fran-aise",
        "pinterest-appartement-moderne",
    ],
    "decoration-recup": [
        "pinterest-d-coration-shabby-chic",
        "pinterest-maison-rustique-moderne",
    ],
    "decoration-vintage": [
        "pinterest-d-coration-shabby-chic",
        "pinterest-d-coration-fran-aise",
    ],
    "dressing": [
        "pinterest-rangement-chambre",
        "pinterest-rangement-salle-bain",
    ],
    "eclairage-ambiance": [
        "pinterest-salon-moderne",
        "pinterest-salle-bain-moderne",
        "unsplash-modern-led-lighting",
    ],
    "entree-maison": [
        "pinterest-d-coration-minimaliste",
        "pinterest-appartement-moderne",
        "pinterest-d-coration-scandinave",
    ],
    "home-office": [
        "pinterest-d-coration-scandinave",
        "pinterest-d-coration-minimaliste",
        "unsplash-modern-office-workspace",
    ],
    "salle-manger": [
        "pinterest-salle-manger-couleur",
        "pinterest-d-coration-fran-aise",
    ],
    "salon-cocooning": [
        "pinterest-salon-cosy-hygge",
        "pinterest-salon-d-coration-naturel-chic",
    ],
    "studio-etudiant": [
        "pinterest-petite-cuisine-moderne",
        "pinterest-rangement-chambre",
        "unsplash-small-space-design",
    ],
    "couleurs-apaisantes": [
        "pinterest-couleur-salon-2026",
        "pinterest-d-coration-minimaliste",
        "unsplash-calming-colors-zen",
    ],
    "textiles-maison": [
        "pinterest-salon-cosy-hygge",
        "pinterest-salon-d-coration-naturel-chic",
        "unsplash-cozy-textiles-home",
    ],
}

# Alt text templates based on slug themes
ALT_TEXT_MAP = {
    "balcon": [
        "Amenagement de balcon avec mobilier compact et plantes vertes",
        "Petit balcon decore avec des elements scandinaves",
        "Balcon optimise avec rangements et vegetalisation verticale",
        "Decoration de balcon minimaliste et fonctionnelle",
        "Balcon cosy avec eclairage tamisé et plantes suspendues",
    ],
    "chambre-ado": [
        "Chambre d'adolescent avec decoration moderne et rangements",
        "Amenagement chambre ado tendance 2026",
        "Decoration chambre jeune avec couleurs vives et mobilier design",
        "Espace de travail et detente dans une chambre ado",
        "Rangement optimise pour chambre d'adolescent",
    ],
    "chambre-parentale": [
        "Chambre parentale avec ambiance spa et couleurs douces",
        "Suite parentale cocooning avec textiles naturels",
        "Chambre adulte bicolore elegante et apaisante",
        "Decoration chambre parentale style contemporain",
        "Amenagement chambre parentale avec coin bien-etre",
    ],
    "cuisine-vintage": [
        "Cuisine vintage avec elements en bois et touches retro",
        "Decoration cuisine campagne chic avec meubles anciens",
        "Cuisine rustique moderne avec credence en carrelage metro",
        "Ambiance cuisine vintage avec accessoires d'epoque",
        "Cuisine style campagne francaise avec poutres apparentes",
    ],
    "couloir": [
        "Couloir decore avec miroirs et eclairage indirect",
        "Amenagement couloir minimaliste et lumineux",
        "Decoration couloir avec galerie de cadres et console",
        "Couloir transforme en espace de rangement elegant",
        "Entree et couloir avec touches decoratives francaises",
    ],
    "decoration-recup": [
        "Meuble recycle transforme en piece unique decorative",
        "Decoration upcycling avec palettes et objets recuperes",
        "Interieur shabby chic avec elements de recup",
        "Etagere DIY avec materiaux recuperes et plantes",
        "Salon decore avec des objets chines et recycles",
    ],
    "decoration-vintage": [
        "Salon avec melange de meubles vintage et modernes",
        "Decoration vintage chic avec patine et dorures",
        "Interieur mix and match epoques et styles",
        "Coin lecture vintage avec fauteuil retro et lampe ancienne",
        "Decoration shabby chic avec couleurs pastel et brocante",
    ],
    "dressing": [
        "Dressing organise avec systeme de rangement modulable",
        "Amenagement de placard optimise avec separateurs",
        "Dressing ouvert avec rangements par categories",
        "Organisation garde-robe avec accessoires de rangement",
        "Dressing fonctionnel avec eclairage integre",
    ],
    "eclairage-ambiance": [
        "Eclairage d'ambiance avec luminaires design modernes",
        "Salon avec eclairage indirect et bougies decoratives",
        "Techniques d'eclairage pour creer une ambiance chaleureuse",
        "Luminaires suspendus modernes dans un interieur contemporain",
        "Eclairage de salle de bain moderne avec spots et LED",
    ],
    "entree-maison": [
        "Entree de maison avec console et miroir decoratif",
        "Amenagement entree minimaliste avec rangement malin",
        "Decoration d'entree accueillante avec plantes et patere",
        "Hall d'entree moderne avec banc et rangement chaussures",
        "Entree style scandinave epuree et fonctionnelle",
    ],
    "home-office": [
        "Bureau a domicile zen avec plantes et lumiere naturelle",
        "Espace de travail minimaliste et productif a la maison",
        "Home office scandinave avec bureau en bois clair",
        "Bureau apaisant avec decoration epuree et rangements",
        "Coin bureau zen avec eclairage naturel et vegetation",
    ],
    "salle-manger": [
        "Salle a manger conviviale avec grande table en bois",
        "Decoration salle a manger chaleureuse avec suspension",
        "Coin repas avec couleurs chaudes et mobilier confortable",
        "Salle a manger style campagne francaise avec buffet",
        "Table dressee dans une salle a manger lumineuse",
    ],
    "salon-cocooning": [
        "Salon cocooning hivernal avec plaids et coussins moelleux",
        "Ambiance hygge dans un salon aux tons chauds",
        "Salon cosy avec tapis epais et eclairage tamisé",
        "Coin lecture douillet avec fauteuil et couverture",
        "Decoration salon naturel chic avec materiaux bruts",
    ],
    "studio-etudiant": [
        "Studio etudiant optimise avec meubles multifonctions",
        "Amenagement petit espace etudiant avec rangement vertical",
        "Decoration studio compact avec astuces gain de place",
        "Cuisine compacte de studio avec rangements malins",
        "Coin nuit et bureau dans un studio bien agence",
    ],
    "couleurs-apaisantes": [
        "Palette de couleurs zen dans un interieur lumineux",
        "Salon aux tons pastel et naturels pour une ambiance sereine",
        "Decoration minimaliste avec couleurs douces et apaisantes",
        "Interieur aux couleurs neutres et chaleureuses",
        "Chambre aux teintes bleu-gris pour un effet zen",
    ],
    "textiles-maison": [
        "Assortiment de textiles cosy dans un salon chaleureux",
        "Coussins et plaids en lin naturel sur canape",
        "Decoration textile avec rideaux et coussins assortis",
        "Textiles maison en fibres naturelles et couleurs douces",
        "Ambiance cocooning avec tapis berbere et coussins",
    ],
}


def get_available_images(prefix):
    """Get all images matching a prefix, filtered by minimum size."""
    images = []
    for f in os.listdir(IMAGES_DIR):
        if f.startswith(prefix) and f.endswith(".jpg"):
            path = os.path.join(IMAGES_DIR, f)
            size = os.path.getsize(path)
            if size >= MIN_IMAGE_SIZE:
                images.append(f)
    return sorted(images)


def find_matching_slug_key(slug):
    """Find which SLUG_IMAGE_MAP key matches this article slug."""
    for key in SLUG_IMAGE_MAP:
        if key in slug:
            return key
    return None


def count_images(content):
    """Count <img tags in content."""
    return len(re.findall(r"<img\s", content))


def find_h2_h3_positions(content):
    """Find positions right after the closing > of <h2> and <h3> section tags.
    Returns list of (line_index, tag_type) for insertion points.
    Skip the 'Sommaire' h2 and the table of contents h2."""
    lines = content.split("\n")
    positions = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Skip Sommaire / table of contents headings
        if "sommaire" in line_lower or "dans cet article" in line_lower:
            continue
        # Match any h2 tag (with or without id attribute)
        if re.search(r"<h2[\s>]", line):
            positions.append((i, "h2"))
        # Match h3 tags (subsection headings)
        elif re.search(r"<h3[\s>]", line):
            positions.append((i, "h3"))
    return positions


def build_image_html(filename, alt_text):
    """Build the image HTML block."""
    return f'''
        <div class="my-8">
          <img src="/images/{filename}" alt="{alt_text}" class="w-full rounded-lg shadow-sm" loading="lazy" />
        </div>
'''


def insert_images_into_article(filepath, dry_run=False):
    """Insert images into a single .astro article."""
    slug = os.path.basename(filepath).replace(".astro", "")
    slug_key = find_matching_slug_key(slug)

    if slug_key is None:
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    current_count = count_images(content)
    if current_count >= 5:
        return None

    needed = TARGET_IMAGES - current_count

    # Collect candidate images from all matching prefixes
    candidates = []
    for prefix in SLUG_IMAGE_MAP[slug_key]:
        candidates.extend(get_available_images(prefix))

    if not candidates:
        print(f"  WARNING: No images found for {slug} (prefixes: {SLUG_IMAGE_MAP[slug_key]})")
        return None

    # Remove duplicates and shuffle, then pick evenly spaced ones
    candidates = list(dict.fromkeys(candidates))  # dedupe preserving order
    random.seed(slug)  # deterministic per slug
    random.shuffle(candidates)

    # Pick images spaced out in the list
    step = max(1, len(candidates) // (needed + 1))
    selected = []
    for i in range(needed):
        idx = (i * step) % len(candidates)
        if candidates[idx] not in selected:
            selected.append(candidates[idx])
    # Fill remaining if needed
    for c in candidates:
        if len(selected) >= needed:
            break
        if c not in selected:
            selected.append(c)
    selected = selected[:needed]

    # Get alt texts
    alt_texts = ALT_TEXT_MAP.get(slug_key, [f"Image decoration {slug}"] * needed)

    # Find insertion points (h2 with id= and h3 tags)
    positions = find_h2_h3_positions(content)

    if not positions:
        print(f"  WARNING: No h2/h3 insertion points found in {slug}")
        return None

    # Distribute images across insertion points
    # Prefer after h2 first, then h3 if we have extras
    h2_positions = [(pos, tag) for pos, tag in positions if tag == "h2"]
    h3_positions = [(pos, tag) for pos, tag in positions if tag == "h3"]

    # Assign: first to h2s (max 1 per h2), then spread remaining on h3s
    insertion_map = []
    img_idx = 0

    for pos, tag in h2_positions:
        if img_idx >= len(selected):
            break
        insertion_map.append((pos, selected[img_idx], alt_texts[img_idx % len(alt_texts)]))
        img_idx += 1

    # Spread remaining images across h3 positions (skip every other to avoid overload)
    h3_step = max(1, len(h3_positions) // max(1, len(selected) - img_idx))
    h3_idx = 0
    while img_idx < len(selected) and h3_idx < len(h3_positions):
        pos, tag = h3_positions[h3_idx]
        insertion_map.append((pos, selected[img_idx], alt_texts[img_idx % len(alt_texts)]))
        img_idx += 1
        h3_idx += h3_step

    if not insertion_map:
        return None

    # Sort by position (descending) to insert from bottom up (preserves line numbers)
    insertion_map.sort(key=lambda x: x[0], reverse=True)

    lines = content.split("\n")
    for line_idx, img_file, alt in insertion_map:
        img_html = build_image_html(img_file, alt)
        # Find the end of the heading block (next line after the heading)
        insert_at = line_idx + 1
        # Skip past closing tags on the same line or the next few lines
        while insert_at < len(lines) and lines[insert_at].strip() in ("", "</h2>", "</h3>"):
            insert_at += 1
        # Also skip one paragraph if present (insert after first paragraph under heading)
        p_count = 0
        while insert_at < len(lines) and p_count < 1:
            if "</p>" in lines[insert_at]:
                p_count += 1
                insert_at += 1
                break
            insert_at += 1

        lines.insert(insert_at, img_html)

    new_content = "\n".join(lines)
    new_count = count_images(new_content)

    if dry_run:
        print(f"  {slug}: {current_count} -> {new_count} images (+{new_count - current_count})")
        for _, img_file, alt in insertion_map:
            print(f"    + {img_file}")
    else:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  {slug}: {current_count} -> {new_count} images (+{new_count - current_count})")

    return {
        "slug": slug,
        "before": current_count,
        "after": new_count,
        "added": new_count - current_count,
    }


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE ===\n")

    print("Scanning .astro articles for image enrichment...\n")

    results = []
    for filename in sorted(os.listdir(PAGES_DIR)):
        if not filename.endswith(".astro"):
            continue
        filepath = os.path.join(PAGES_DIR, filename)
        result = insert_images_into_article(filepath, dry_run)
        if result:
            results.append(result)

    print(f"\n{'='*50}")
    print(f"Total articles enriched: {len(results)}")
    total_added = sum(r["added"] for r in results)
    print(f"Total images added: {total_added}")

    if dry_run:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
