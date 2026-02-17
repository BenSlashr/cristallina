#!/usr/bin/env python3
"""
Insert Pinterest/Unsplash images into generated .md articles after H2 headings.

Usage:
    python3 scripts/insert-images-md.py [--dry-run] [--slug SLUG] [--all]

    --all       Process all .md files in site/src/content/guides/
    --slug SLUG Process a specific article slug
    --dry-run   Show changes without writing
"""

import os
import re
import sys
import random

GUIDES_DIR = "site/src/content/guides"
IMAGES_DIR = "site/public/images"
MIN_IMAGE_SIZE = 30 * 1024  # 30KB minimum
TARGET_IMAGES = 5  # Target images per article

# Mapping from slug keywords to image prefixes
# More generic than the .astro version - covers broad topics
KEYWORD_IMAGE_MAP = {
    "salon": [
        "pinterest-salon-moderne",
        "pinterest-salon-cosy-hygge",
        "pinterest-salon-d-coration-naturel-chic",
    ],
    "cuisine": [
        "pinterest-cuisine-moderne-d-co",
        "pinterest-cuisine-verte-bois",
        "pinterest-petite-cuisine-moderne",
        "pinterest-cuisine-couleur-olive",
    ],
    "chambre": [
        "pinterest-chambre-coucher-2026",
        "pinterest-chambre-adulte-deux-couleurs",
        "pinterest-chambre-jungle",
    ],
    "salle-de-bain": [
        "pinterest-am-nagement-salle-bain-2026",
        "pinterest-salle-bain-moderne",
        "pinterest-salle-bain-cosy",
        "pinterest-salle-bain-industrielle",
    ],
    "bain": [
        "pinterest-am-nagement-salle-bain-2026",
        "pinterest-salle-bain-moderne",
        "pinterest-baignoire-scandinave",
    ],
    "douche": [
        "pinterest-am-nagement-salle-bain-2026",
        "pinterest-salle-bain-moderne",
    ],
    "baignoire": [
        "pinterest-baignoire-scandinave",
        "pinterest-am-nagement-salle-bain-2026",
    ],
    "jardin": [
        "pinterest-maison-rustique-moderne",
        "pinterest-maison-moderne-2026",
        "unsplash-modern-terrace-design",
    ],
    "terrasse": [
        "unsplash-modern-terrace-design",
        "pinterest-maison-moderne-2026",
    ],
    "exterieur": [
        "pinterest-fa-ade-maison-moderne",
        "pinterest-fa-ade-maison-couleur",
        "pinterest-maison-moderne-2026",
    ],
    "facade": [
        "pinterest-fa-ade-maison-moderne",
        "pinterest-fa-ade-maison-couleur",
    ],
    "couleur": [
        "pinterest-couleur-salon-2026",
        "pinterest-couleur-ocre-terre-cuite",
        "pinterest-couleur-violet",
        "pinterest-d-coration-orange",
    ],
    "peinture": [
        "pinterest-couleur-salon-2026",
        "pinterest-fa-ade-maison-couleur",
    ],
    "rangement": [
        "pinterest-rangement-chambre",
        "pinterest-rangement-salle-bain",
    ],
    "ikea": [
        "pinterest-d-coration-scandinave",
        "pinterest-d-coration-minimaliste",
        "pinterest-rangement-chambre",
    ],
    "scandinave": [
        "pinterest-d-coration-scandinave",
        "unsplash-scandinavian-furniture",
        "unsplash-scandinavian-living-room",
    ],
    "industriel": [
        "pinterest-salle-bain-industrielle",
        "unsplash-industrial-loft",
    ],
    "minimaliste": [
        "pinterest-d-coration-minimaliste",
    ],
    "vintage": [
        "pinterest-d-coration-shabby-chic",
        "pinterest-d-coration-fran-aise",
    ],
    "shabby": [
        "pinterest-d-coration-shabby-chic",
    ],
    "marocain": [
        "pinterest-d-coration-marocaine",
    ],
    "rustique": [
        "pinterest-maison-rustique-moderne",
    ],
    "moderne": [
        "pinterest-salon-moderne",
        "pinterest-appartement-moderne",
        "pinterest-maison-moderne-2026",
    ],
    "appartement": [
        "pinterest-appartement-moderne",
        "pinterest-appartement-traversant",
    ],
    "meuble": [
        "pinterest-d-coration-scandinave",
        "pinterest-salon-moderne",
    ],
    "eclairage": [
        "unsplash-modern-led-lighting",
        "pinterest-salon-moderne",
    ],
    "plantes": [
        "pinterest-plantes-salle-bain",
        "unsplash-indoor-plants-air-purifying",
    ],
    "deco": [
        "pinterest-d-coration-fran-aise",
        "pinterest-d-coration-minimaliste",
        "pinterest-d-coration-scandinave",
    ],
    "decoration": [
        "pinterest-d-coration-fran-aise",
        "pinterest-d-coration-minimaliste",
        "pinterest-d-coration-scandinave",
    ],
    "maison": [
        "pinterest-maison-moderne-2026",
        "pinterest-maison-rustique-moderne",
        "pinterest-d-coration-fran-aise",
    ],
    "mur": [
        "unsplash-wall-decoration-stylish",
        "pinterest-d-coration-minimaliste",
    ],
    "carrelage": [
        "pinterest-am-nagement-salle-bain-2026",
        "unsplash-modern-tile-kitchen-bathroom",
    ],
    "bureau": [
        "unsplash-modern-office-workspace",
        "pinterest-d-coration-scandinave",
    ],
    "diy": [
        "pinterest-d-coration-shabby-chic",
        "pinterest-maison-rustique-moderne",
        "unsplash-wooden-pallet-bar-diy",
    ],
    "adobe": [
        "pinterest-maison-adobe-moderne",
    ],
    "salle-manger": [
        "pinterest-salle-manger-couleur",
        "pinterest-d-coration-fran-aise",
    ],
}

# Fallback image prefixes for unmatched slugs
FALLBACK_PREFIXES = [
    "pinterest-d-coration-fran-aise",
    "pinterest-d-coration-minimaliste",
    "pinterest-d-coration-scandinave",
    "pinterest-salon-moderne",
    "pinterest-appartement-moderne",
]


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


def find_image_prefixes_for_slug(slug):
    """Find matching image prefixes based on slug keywords."""
    prefixes = set()
    slug_lower = slug.lower()
    for keyword, prefix_list in KEYWORD_IMAGE_MAP.items():
        if keyword in slug_lower:
            prefixes.update(prefix_list)
    if not prefixes:
        prefixes.update(FALLBACK_PREFIXES)
    return list(prefixes)


def count_images_in_md(content):
    """Count existing images in markdown content."""
    return len(re.findall(r"<img\s|!\[", content))


def find_h2_positions(content):
    """Find line indices of ## headings (H2) in markdown."""
    lines = content.split("\n")
    positions = []
    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        # Match ## headings but skip sommaire
        if line.strip().startswith("## "):
            heading_text = line.strip().lower()
            if "sommaire" not in heading_text:
                positions.append(i)
    return positions


def build_image_html(filename, alt_text):
    """Build image HTML block for markdown files."""
    return f"""
<div class="my-8">
  <img src="/images/{filename}" alt="{alt_text}" class="w-full rounded-lg shadow-sm" loading="lazy" />
</div>
"""


def generate_alt_text(slug, index):
    """Generate a contextual alt text from the slug."""
    readable = slug.replace("-", " ")
    suffixes = [
        "inspiration decoration",
        "amenagement et design",
        "idees et tendances",
        "style et ambiance",
        "decoration interieure",
    ]
    return f"{readable.capitalize()} - {suffixes[index % len(suffixes)]}"


def insert_images_into_md(filepath, dry_run=False):
    """Insert images into a single .md article."""
    slug = os.path.basename(filepath).replace(".md", "")
    if slug == "index":
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    current_count = count_images_in_md(content)
    if current_count >= TARGET_IMAGES:
        return None

    needed = TARGET_IMAGES - current_count

    # Find matching images
    prefixes = find_image_prefixes_for_slug(slug)
    candidates = []
    for prefix in prefixes:
        candidates.extend(get_available_images(prefix))

    if not candidates:
        print(f"  WARNING: No images found for {slug}")
        return None

    # Deduplicate and select
    candidates = list(dict.fromkeys(candidates))
    random.seed(slug)
    random.shuffle(candidates)

    step = max(1, len(candidates) // (needed + 1))
    selected = []
    for i in range(needed):
        idx = (i * step) % len(candidates)
        if candidates[idx] not in selected:
            selected.append(candidates[idx])
    for c in candidates:
        if len(selected) >= needed:
            break
        if c not in selected:
            selected.append(c)
    selected = selected[:needed]

    # Find H2 positions
    positions = find_h2_positions(content)
    if not positions:
        print(f"  WARNING: No H2 headings found in {slug}")
        return None

    # Distribute images across H2 positions
    lines = content.split("\n")
    insertion_map = []
    for i, img_file in enumerate(selected):
        if i < len(positions):
            pos = positions[i]
        else:
            # Distribute remaining among existing positions
            pos = positions[i % len(positions)]
        alt = generate_alt_text(slug, i)
        insertion_map.append((pos, img_file, alt))

    # Sort by position descending (insert bottom-up)
    insertion_map.sort(key=lambda x: x[0], reverse=True)

    for line_idx, img_file, alt in insertion_map:
        img_html = build_image_html(img_file, alt)
        # Insert after the paragraph following the H2
        insert_at = line_idx + 1
        # Skip empty lines
        while insert_at < len(lines) and lines[insert_at].strip() == "":
            insert_at += 1
        # Skip one paragraph (until next empty line or heading)
        while insert_at < len(lines):
            if lines[insert_at].strip() == "" or lines[insert_at].strip().startswith("#"):
                break
            insert_at += 1

        lines.insert(insert_at, img_html)

    new_content = "\n".join(lines)
    new_count = count_images_in_md(new_content)

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
    process_all = "--all" in sys.argv
    target_slug = None

    for i, arg in enumerate(sys.argv):
        if arg == "--slug" and i + 1 < len(sys.argv):
            target_slug = sys.argv[i + 1]

    if dry_run:
        print("=== DRY RUN MODE ===\n")

    print("Scanning .md articles for image enrichment...\n")

    results = []

    if target_slug:
        # Find the specific file
        for root, dirs, files in os.walk(GUIDES_DIR):
            for f in files:
                if f == f"{target_slug}.md":
                    filepath = os.path.join(root, f)
                    result = insert_images_into_md(filepath, dry_run)
                    if result:
                        results.append(result)
    elif process_all:
        for root, dirs, files in os.walk(GUIDES_DIR):
            for f in sorted(files):
                if f.endswith(".md"):
                    filepath = os.path.join(root, f)
                    result = insert_images_into_md(filepath, dry_run)
                    if result:
                        results.append(result)
    else:
        print("Usage: python3 scripts/insert-images-md.py [--dry-run] [--slug SLUG | --all]")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"Total articles enriched: {len(results)}")
    total_added = sum(r["added"] for r in results)
    print(f"Total images added: {total_added}")

    if dry_run:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
