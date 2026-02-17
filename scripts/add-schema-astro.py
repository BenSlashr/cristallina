#!/usr/bin/env python3
"""
Batch add schema.org JSON-LD, breadcrumbs, and ogImage to .astro article pages.
"""
import os
import re
import sys

PAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'site', 'src', 'pages')

# Pages to skip (not articles)
SKIP = {
    'index.astro',
    '[slug].astro',
    'contact.astro',
    'mentions-legales.astro',
    'politique-confidentialite.astro',
    '404.astro',
    'a-propos.astro',
    'guides.astro',
}

# Category mapping from the homepage data
CATEGORY_MAP = {
    'eclairage-ambiance-techniques-sublimer': 'Eclairage',
    'balcon-amenagement-petit-espace-optimise': 'Exterieur',
    'entree-maison-idees-decoration-accueil': 'Entree',
    'dressing-optimise-solutions-rangement-garde-robe': 'Rangement',
    'salon-cocooning-hiver-ambiance-ultra-cosy': 'Salon',
    'home-office-zen-bureau-apaisant-productif': 'Bureau',
    'chambre-ado-moderne-idees-decoration-tendance': 'Chambre',
    'salle-manger-conviviale-decoration-chaleureuse': 'Salle a manger',
    'couloir-decoration-idees-transformation-espace': 'Couloir',
    'decoration-recup-upcycling-maison-unique': 'DIY',
    'sous-sol-amenage-espace-vie-cosy': 'Amenagement',
    'decoration-vintage-moderne-mixer-epoques-style': 'Style',
    'chambre-parentale-spa-cocon-bien-etre': 'Chambre',
    'cuisine-vintage-campagne-charme-authentique': 'Cuisine',
    'studio-etudiant-astuces-decoration-petit-espace': 'Petit espace',
    'terrasse-design-amenagements-exterieurs-tendance': 'Exterieur',
    'deco-murale-idees-habiller-murs-style': 'Decoration',
    'jardin-hiver-verandas-vegetales-inspirantes': 'Plantes',
    'bureau-moderne-amenagements-productifs-2026': 'Bureau',
    'salon-boheme-deco-chic-coloree': 'Salon',
    'chambre-moderne-design-minimaliste': 'Chambre',
    'salle-de-bain-zen-spa-maison': 'Salle de bain',
    'cuisine-moderne-2026-amenagements-innovants': 'Cuisine',
    'carrelage-moderne-tendances-2026': 'Revetements',
    'mobilier-scandinave-design-nordique': 'Mobilier',
    'textiles-maison-cosy': 'Textiles',
    'couleurs-apaisantes-zen': 'Couleurs',
    'rangement-creatif-optimisation': 'Organisation',
    'eclairage-moderne-tendances': 'Eclairage',
    'plantes-interieur-deco': 'Plantes',
    'amenagement-feng-shui': 'Feng Shui',
    'tendances-deco-2026': 'Tendances',
    'style-industriel-moderne': 'Style',
    'agrandir-petit-espace-astuces': 'Amenagement',
    'cuisine-ouverte-optimiser-espace': 'Cuisine',
    'amenager-chambre-cocooning': 'Chambre',
    'decoration-salon-naturel-chic': 'Decoration',
    'salle-de-bain-cosy': 'Salle de bain',
    'comment-fabriquer-soi-meme-un-bar-en-palettes': 'DIY',
}


def get_slug(filename):
    return filename.replace('.astro', '')


def process_file(filepath, filename):
    slug = get_slug(filename)
    category = CATEGORY_MAP.get(slug, 'Decoration')

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already processed
    if 'articleSchema' in content or 'breadcrumbSchema' in content:
        print(f'  SKIP (already has schema): {filename}')
        return False

    # Split frontmatter and template
    parts = content.split('---', 2)
    if len(parts) < 3:
        print(f'  SKIP (no frontmatter): {filename}')
        return False

    frontmatter = parts[1]
    template = parts[2]

    # Add import if not present
    if "import { articleSchema, breadcrumbSchema }" not in frontmatter:
        # Add after last import line
        import_line = "import { articleSchema, breadcrumbSchema } from '@/utils/schema';\n"
        # Find the last import
        lines = frontmatter.split('\n')
        last_import_idx = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('import '):
                last_import_idx = i
        if last_import_idx >= 0:
            lines.insert(last_import_idx + 1, import_line.rstrip())
        frontmatter = '\n'.join(lines)

    # Add schema variables before the closing ---
    # Find where the const declarations end
    schema_code = f"""
const pageSlug = '{slug}';
const schemaArticle = articleSchema({{
  title,
  description,
  url: '/{slug}/',
}});
const schemaBreadcrumb = breadcrumbSchema([
  {{ name: 'Accueil', url: '/' }},
  {{ name: '{category}', url: '/guides/decoration' }},
  {{ name: title, url: '/{slug}/' }},
]);
"""
    frontmatter = frontmatter.rstrip() + '\n' + schema_code + '\n'

    # Fix BaseLayout tag to add jsonLd and ogImage
    # Pattern: <BaseLayout {title} {description} canonical="...">
    template = re.sub(
        r'<BaseLayout\s+\{title\}\s+\{description\}\s+canonical="[^"]*"\s*>',
        '<BaseLayout {title} {description}\n  jsonLd={[schemaArticle, schemaBreadcrumb]}\n>',
        template
    )

    # Also handle variant: <BaseLayout title={title} description={description} ...>
    template = re.sub(
        r'<BaseLayout\s+title=\{title\}\s+description=\{description\}\s+canonical="[^"]*"\s*>',
        '<BaseLayout title={title} description={description}\n  jsonLd={[schemaArticle, schemaBreadcrumb]}\n>',
        template
    )

    # Add breadcrumb HTML nav after <main...> <article...> <header...> block
    # We'll add it right before the <header class="mb-8"> tag
    breadcrumb_html = '''
      <!-- Breadcrumb -->
      <nav class="flex items-center gap-2 text-sm mb-6" style="color: #B5B5B5;" aria-label="Fil d'ariane">
        <a href="/" class="hover:text-rose-400 transition-colors">Accueil</a>
        <span>/</span>
        <a href="/guides/decoration" class="hover:text-rose-400 transition-colors">''' + category + '''</a>
        <span>/</span>
        <span style="color: #8B8B8B;">{title}</span>
      </nav>

'''
    # Insert before <header class="mb-8">
    if '<nav class="flex items-center' not in template and 'aria-label="Fil d\'ariane"' not in template:
        template = template.replace(
            '<header class="mb-8">',
            breadcrumb_html + '      <header class="mb-8">'
        )

    new_content = '---' + frontmatter + '---' + template
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'  OK: {filename}')
    return True


def main():
    pages_dir = os.path.abspath(PAGES_DIR)
    count = 0
    total = 0

    for filename in sorted(os.listdir(pages_dir)):
        if not filename.endswith('.astro'):
            continue
        if filename in SKIP:
            continue

        filepath = os.path.join(pages_dir, filename)
        if not os.path.isfile(filepath):
            continue

        total += 1
        if process_file(filepath, filename):
            count += 1

    print(f'\nProcessed {count}/{total} files')


if __name__ == '__main__':
    main()
