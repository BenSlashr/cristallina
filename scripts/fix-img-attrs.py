#!/usr/bin/env python3
"""
Add width, height, loading, decoding attributes to <img> tags in .astro article pages.
Hero images (first image) get loading="eager", others get loading="lazy".
"""
import os
import re
import sys

PAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'site', 'src', 'pages')

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


def fix_img_tag(match, is_first):
    tag = match.group(0)

    # Skip if already has width/height
    if 'width=' in tag and 'height=' in tag:
        # Still ensure loading/decoding
        if 'loading=' not in tag:
            loading = 'eager' if is_first else 'lazy'
            tag = tag.replace('/>', f' loading="{loading}" />')
            tag = tag.replace('>', f' loading="{loading}" >', 1) if '/>' not in tag else tag
        if 'decoding=' not in tag:
            tag = tag.replace('/>', ' decoding="async" />')
            tag = tag.replace('>', ' decoding="async" >', 1) if '/>' not in tag else tag
        return tag

    # Add width and height (1200x675 for 16:9 landscape images)
    loading = 'eager' if is_first else 'lazy'

    # Remove existing loading attr if present
    tag = re.sub(r'\s+loading="[^"]*"', '', tag)

    # Add attributes before closing /> or >
    attrs = f' width="1200" height="675" loading="{loading}" decoding="async"'

    if '/>' in tag:
        tag = tag.replace('/>', f'{attrs} />')
    else:
        # For tags like <img ...>
        tag = re.sub(r'(\s*)>$', f'{attrs}>', tag)

    return tag


def process_file(filepath, filename):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    img_count = [0]  # mutable counter for closure

    def replace_img(match):
        img_count[0] += 1
        is_first = img_count[0] == 1
        return fix_img_tag(match, is_first)

    new_content = re.sub(r'<img\s[^>]*?/?>', replace_img, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'  OK ({img_count[0]} images): {filename}')
        return True
    else:
        print(f'  SKIP (no changes): {filename}')
        return False


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

    print(f'\nUpdated {count}/{total} files')


if __name__ == '__main__':
    main()
