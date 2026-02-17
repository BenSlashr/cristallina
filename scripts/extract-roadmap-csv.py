#!/usr/bin/env python3
"""
Extract slugs from ROADMAP_CONTENU.md, filter existing articles,
assign branches and generate batch CSV files of 10 articles each.

Usage:
    python3 scripts/extract-roadmap-csv.py [--output-dir batches]
"""

import os
import re
import sys
import glob

ROADMAP_FILE = "ROADMAP_CONTENU.md"
PAGES_DIR = "site/src/pages"
GUIDES_DIR = "site/src/content/guides"
DEFAULT_OUTPUT_DIR = "batches"

# Branch assignment heuristics
BRANCH_RULES = [
    (["salon", "sejour"], "decoration"),
    (["cuisine"], "cuisine"),
    (["chambre", "coucher", "lit"], "chambre"),
    (["salle-de-bain", "bain", "douche", "baignoire"], "salle-de-bain"),
    (["jardin", "terrasse", "exterieur", "ext-rieur", "patio", "balcon", "pergola", "piscine", "pool", "serre"], "exterieur"),
    (["couleur", "peinture", "teinte", "palette", "ocre", "violet", "orange", "taupe", "bleu"], "couleurs"),
    (["rangement", "placard", "dressing", "organisation"], "rangement"),
    (["ikea"], "shopping"),
]


def extract_slugs_from_roadmap(filepath):
    """Parse ROADMAP_CONTENU.md and extract slugs from cristallina.fr/SLUG/ lines."""
    slugs = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Match lines like: cristallina.fr/some-slug/
            match = re.match(r"^cristallina\.fr/([^/]+)/?$", line)
            if match:
                slugs.append(match.group(1))
    return slugs


def get_existing_slugs():
    """Get set of slugs that already exist as .astro pages or .md guides."""
    existing = set()

    # Check .astro pages
    for f in os.listdir(PAGES_DIR):
        if f.endswith(".astro"):
            slug = f.replace(".astro", "")
            existing.add(slug)

    # Check .md guides
    for f in glob.glob(os.path.join(GUIDES_DIR, "**/*.md"), recursive=True):
        basename = os.path.basename(f).replace(".md", "")
        if basename != "index":
            existing.add(basename)

    return existing


def assign_branch(slug):
    """Assign a branch category based on slug keywords."""
    slug_lower = slug.lower()
    for keywords, branch in BRANCH_RULES:
        for kw in keywords:
            if kw in slug_lower:
                return branch
    return "decoration"  # fallback


def slug_to_keyword(slug):
    """Convert slug to a search keyword (replace hyphens with spaces)."""
    return slug.replace("-", " ")


def main():
    output_dir = DEFAULT_OUTPUT_DIR
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--output-dir" and i + 2 < len(sys.argv):
            output_dir = sys.argv[i + 2]

    # Extract all slugs from roadmap
    all_slugs = extract_slugs_from_roadmap(ROADMAP_FILE)
    print(f"Total slugs in roadmap: {len(all_slugs)}")

    # Filter existing articles
    existing = get_existing_slugs()
    print(f"Existing articles: {len(existing)}")

    new_slugs = [s for s in all_slugs if s not in existing]
    print(f"New articles to create: {len(new_slugs)}")

    # Filter out non-decoration slugs that don't fit the site
    # (e.g., pest control, aquarium, etc.)
    skip_keywords = [
        "mouche", "guepe", "fourmi", "taupes", "algues", "cochenille",
        "blattes", "aquarium", "pupes", "invasion",
        "action-logement", "ascenseur", "avis-poster",
        "album-photo", "etiquette-linge", "noel-2021",
        "couleurs-tendances-automne-hiver-2021",
        "satin-coton", "percale-coton",
    ]

    filtered_slugs = []
    skipped = []
    for s in new_slugs:
        should_skip = False
        for kw in skip_keywords:
            if kw in s:
                should_skip = True
                break
        if should_skip:
            skipped.append(s)
        else:
            filtered_slugs.append(s)

    if skipped:
        print(f"Skipped {len(skipped)} non-decoration slugs:")
        for s in skipped:
            print(f"  - {s}")

    print(f"\nArticles to batch: {len(filtered_slugs)}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate CSV batches of 10
    batch_size = 10
    batch_num = 0
    order_in_batch = 0

    for i, slug in enumerate(filtered_slugs):
        if i % batch_size == 0:
            batch_num += 1
            order_in_batch = 0
            batch_file = os.path.join(output_dir, f"batch-{batch_num:02d}.csv")
            f = open(batch_file, "w", encoding="utf-8")
            f.write("slug,keyword,branch,parent,order\n")

        order_in_batch += 1
        branch = assign_branch(slug)
        keyword = slug_to_keyword(slug)
        parent = branch  # parent hub = branch name

        f.write(f"{slug},{keyword},{branch},{parent},{order_in_batch}\n")

        if (i + 1) % batch_size == 0 or i == len(filtered_slugs) - 1:
            f.close()
            print(f"  Created {batch_file} ({order_in_batch} articles)")

    print(f"\nTotal batches: {batch_num}")
    print(f"Files in: {output_dir}/")

    # Print branch distribution
    branch_counts = {}
    for slug in filtered_slugs:
        branch = assign_branch(slug)
        branch_counts[branch] = branch_counts.get(branch, 0) + 1

    print(f"\nBranch distribution:")
    for branch, count in sorted(branch_counts.items(), key=lambda x: -x[1]):
        print(f"  {branch}: {count} articles")


if __name__ == "__main__":
    main()
