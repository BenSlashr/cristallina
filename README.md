# Cristallina — Blog déco/lifestyle féminin

Stack complete pour creer un site de contenu editorial avec :
- Astro 5 + React islands + Tailwind 4
- Pipeline de redaction IA (preprocessing + verification)
- Publication planifiee automatique
- Markdown enrichi (callouts, Mermaid, tooltips glossaire)
- SEO complet (Schema.org, OG, RSS, sitemap, canonical)
- Composants interactifs (quiz, arbre de decision, comparateur)
- Newsletter Mailchimp
- Deploiement VPS + Caddy

## Quick Start

```bash
# 1. Copier le starter pack
cp -r starter-pack/ mon-nouveau-site/
cd mon-nouveau-site/site/

# 2. Installer les dependances
npm install

# 3. Installer Playwright (pour Mermaid)
npx playwright install chromium
sudo npx playwright install-deps chromium

# 4. Configurer l'environnement
cp .env.example .env
# Remplir FAL_KEY et TAVILY_API_KEY

# 5. Lancer en dev
npm run dev
```

## Structure du projet

```
starter-pack/
├── CLAUDE.md                          # Instructions IA pour la redaction
├── README.md                          # Ce fichier
├── scripts/
│   ├── preprocess-article.sh          # Pipeline preprocessing (Tavily + Slashr + fal.ai)
│   └── verify-articles.sh            # Verification qualite des articles
├── infra/
│   ├── Caddyfile                      # Config reverse proxy
│   ├── rebuild-sites.sh              # Script de rebuild
│   ├── rebuild-sites.service          # Systemd service
│   └── rebuild-sites.timer           # Systemd timer (6h)
└── site/
    ├── package.json
    ├── astro.config.mjs               # Astro + plugins markdown
    ├── tsconfig.json
    ├── .env.example
    ├── .gitignore
    ├── public/
    │   ├── favicon.svg
    │   ├── images/                    # Images des articles
    │   └── data/                      # Fichiers JSON (cartes, etc.)
    └── src/
        ├── content.config.ts          # 3 collections : blog, guides, glossary
        ├── styles/
        │   └── global.css             # Design system complet (dark theme)
        ├── layouts/
        │   └── BaseLayout.astro       # SEO, OG, Twitter, fonts, RSS
        ├── plugins/
        │   └── rehype-glossary-tooltip.ts  # Tooltips build-time
        ├── data/
        │   └── glossary-terms.ts      # Termes du glossaire
        ├── components/
        │   ├── Logo.astro
        │   ├── Navbar.astro           # Nav fixe + mobile menu
        │   ├── Footer.astro           # Footer multi-colonnes
        │   ├── ScrollToTop.astro
        │   ├── CrossLinks.astro       # Maillage inter-silos
        │   ├── NewsletterForm.tsx      # Mailchimp JSONP (React)
        │   ├── NewsletterCTA.astro
        │   └── tools/
        │       ├── QuizEngine.tsx      # Quiz a choix multiples
        │       ├── DecisionTreeEngine.tsx  # Arbre de decision
        │       └── ComparisonWidget.tsx    # Tableau comparatif
        ├── pages/
        │   ├── index.astro            # Homepage
        │   ├── [slug].astro           # Articles blog
        │   ├── rss.xml.ts             # Feed RSS
        │   ├── guides/
        │   │   └── [...slug].astro    # Guides hierarchiques (hub + guide)
        │   └── glossaire/
        │       ├── index.astro        # Index du glossaire
        │       └── [slug].astro       # Pages de termes
        └── content/
            ├── blog/
            │   └── example-post.md
            ├── guides/
            │   └── getting-started/
            │       ├── index.md       # Hub (page de branche)
            │       └── first-steps.md # Guide (article)
            └── glossaire/
                └── seo.md
```

## Checklist de personnalisation

### Obligatoire (avant le premier build)

- [ ] `astro.config.mjs` : remplacer `site` par votre domaine
- [ ] `site/.env` : renseigner vos cles API (FAL_KEY, TAVILY_API_KEY)
- [ ] `content.config.ts` : adapter les branches de guides a votre domaine
- [ ] `glossary-terms.ts` : remplacer par vos termes de glossaire
- [ ] `BaseLayout.astro` : modifier la description par defaut et le titre RSS
- [ ] `Navbar.astro` : modifier les liens de navigation
- [ ] `Footer.astro` : modifier les liens et la description
- [ ] `Logo.astro` : remplacer le SVG et le nom du site
- [ ] `NewsletterForm.tsx` : configurer vos identifiants Mailchimp

### Recommande

- [ ] `global.css` : personnaliser les couleurs d'accent et les fonts
- [ ] `CLAUDE.md` : adapter les instructions pour votre domaine
- [ ] `verify-articles.sh` : ajuster la liste de mots interdits
- [ ] `preprocess-article.sh` : adapter le prompt d'image
- [ ] `infra/Caddyfile` : configurer votre domaine
- [ ] Ajouter vos pages legales : CGU, confidentialite, contact

## Fonctionnalites cles

### Publication planifiee
Mettez `pubDate: 2026-03-15` dans le frontmatter. L'article ne sera pas
genere au build tant que la date n'est pas passee. Le timer systemd
rebuild toutes les 6h.

### Pipeline de redaction
```bash
# 1. Preprocessing (recherche + SEO brief + image)
./scripts/preprocess-article.sh mon-article "mot cle seo" branch parent 1

# 2. Rediger en lisant /tmp/preprocess-mon-article/prompt-data.md

# 3. Verifier la qualite
./scripts/verify-articles.sh mon-article

# 4. Build
cd site && npm run build
```

### Markdown enrichi
- **Callouts** : `> [!TIP]`, `> [!NOTE]`, `> [!WARNING]`, `> [!CAUTION]`, `> [!IMPORTANT]`
- **Mermaid** : diagrammes rendus en SVG au build (strategy `img-svg`)
- **Tooltips** : termes du glossaire detectes automatiquement et enrichis

### Composants interactifs (React islands)
```astro
<!-- Quiz -->
<QuizEngine client:visible title="Quiz" questions={myQuestions} />

<!-- Arbre de decision -->
<DecisionTreeEngine client:visible config={myConfig} />

<!-- Comparateur -->
<ComparisonWidget client:visible title="Comparatif" items={myItems} />
```

### Deploiement VPS
```bash
# Installer Caddy
sudo apt install caddy

# Copier la config
sudo cp infra/Caddyfile /etc/caddy/Caddyfile
sudo cp infra/rebuild-sites.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/rebuild-sites.sh

# Installer le timer de rebuild
sudo cp infra/rebuild-sites.service /etc/systemd/system/
sudo cp infra/rebuild-sites.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rebuild-sites.timer

# Verifier
sudo systemctl list-timers rebuild-sites.timer
```

## Notes techniques

### rehype-mermaid : TOUJOURS utiliser `strategy: 'img-svg'`
La strategie `inline-svg` entre en conflit avec le plugin `rehype-raw`
integre d'Astro, ce qui cause des corps d'articles vides (pas d'erreur
dans la console). Utiliser `img-svg` resout le probleme.

### Playwright requis pour Mermaid
```bash
npx playwright install chromium
sudo npx playwright install-deps chromium
```

### Tailwind 4
Utilise la nouvelle syntaxe `@theme` dans `global.css` et le plugin
Vite `@tailwindcss/vite` (pas de `tailwind.config.js`).
