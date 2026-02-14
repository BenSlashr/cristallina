# Guide de personnalisation du pipeline

Ce document liste tous les éléments à adapter quand on crée un nouveau site à partir du starter-pack.

---

## 1. Template global du site

Avant de toucher aux scripts, il faut adapter le site Astro lui-même au thème choisi.

### Fichiers à modifier

| Fichier | Quoi changer |
|---------|-------------|
| `site/src/styles/global.css` | Palette de couleurs (primary, secondary, accent, background), fonts, espacements |
| `site/src/layouts/BaseLayout.astro` | Titre du site, meta description par défaut, favicon, OG image |
| `site/src/components/layout/Header.astro` | Logo/nom du site, liens de navigation, catégories dans le menu |
| `site/src/components/layout/Footer.astro` | Nom du site, liens légaux, réseaux sociaux |
| `site/src/pages/index.astro` | Sections homepage, hero, textes d'accroche |
| `site/src/pages/a-propos.astro` | Bio du persona, histoire du site |
| `site/astro.config.mjs` | Domaine (`site:`), intégrations, redirects |
| `site/tailwind.config.*` | Tokens Tailwind custom si utilisés hors CSS |
| `CLAUDE.md` | Domaine, catégories, structure du contenu, frontmatter, palette Mermaid |

### Checklist thème

- [ ] Choisir une palette de 3-4 couleurs cohérente (primary, secondary, accent, fond)
- [ ] Adapter les couleurs CSS dans `global.css`
- [ ] Remplacer le nom du site dans Header, Footer, BaseLayout
- [ ] Mettre à jour les catégories de contenu (nav, footer, routing)
- [ ] Adapter la homepage (hero, textes, sections)
- [ ] Créer la page à propos avec le persona du site
- [ ] Configurer le domaine dans `astro.config.mjs`
- [ ] Mettre à jour le `CLAUDE.md` avec toutes les infos du nouveau site

---

## 2. benchmark-redaction.sh

Le script principal du pipeline. Chercher les commentaires `<!-- PERSONNALISER -->` dans le fichier.

| Élément | Ligne | Quoi changer |
|---------|-------|-------------|
| Bannière ASCII | haut du fichier | Remplacer `[PROJECT_NAME]` par le nom du site |
| `SITE_DIR` | config | Adapter si le site n'est pas dans `site/` (ex: racine du projet) |
| `CONTENT_EXT` | config | `.mdx` ou `.md` selon le projet |
| `QUIZ_JSON_PATH` | config | Chemin vers le fichier JSON des quiz (ex: `src/data/quizzes.json`) |
| Seuils de mots | Phase 3 | `MIN_WORDS` et `MAX_WORDS` selon la cible du site |
| Format CSV | Phase 1 | 5 champs (slug,keyword,branch,parent,order) ou 3 champs (slug,keyword,category) |

### Architecture CSV

**Hub/Guide (5 champs)** - pour les sites avec arborescence hiérarchique :
```
slug,keyword,branch,parent,order
mon-article,mot cle,branche,article-parent,1
```

**Catégories plates (3 champs)** - pour les sites avec catégories simples :
```
slug,keyword,category
mon-article,mot cle,categorie
```

Si vous changez l'architecture CSV, il faut adapter :
- La lecture du CSV (boucle `while IFS=','`)
- Les tableaux déclarés (`BRANCHES`, `PARENTS`, `ORDERS` vs `CATEGORIES`)
- L'appel à `preprocess-article.sh` (5 args vs 3 args)
- L'appel à l'API de rédaction (variables passées dans le prompt)

---

## 3. redaction-system-prompt.md

Le prompt système envoyé au LLM pour la rédaction des articles.

| Élément | Quoi changer |
|---------|-------------|
| Persona | Nom, âge, métier, traits de personnalité, ton |
| Palette Mermaid | 4 couleurs de nœuds adaptées au design system du site |
| Budget de mots | Fourchette cible (ex: 1500-2000, 2000-2800) |
| Maillage interne | Liste des articles et outils existants du site |
| Exemples de style | Phrases exemples dans le ton du persona |
| Règles spécifiques | Contraintes propres au sujet (ex: sources obligatoires pour la crypto) |

### Palette Mermaid

Dériver 4 couleurs du design system CSS du site :
```
Nœud principal : fond très clair de primary, stroke primary
Nœud secondaire : fond très clair de secondary, stroke secondary
Nœud accent : fond très clair d'accent, stroke accent
Nœud info : fond neutre clair, stroke neutre
```

### Maillage interne

Lister TOUS les articles et outils publiés du site. Format :
```markdown
- [Titre de l'article](/chemin/vers/article/) - description courte
```

Mettre à jour cette liste à chaque nouvel article publié.

---

## 4. quiz-system-prompt.md

| Élément | Quoi changer |
|---------|-------------|
| `[SUJET]` | Thématique du site (ex: "la couture", "les animaux de compagnie") |
| `[PROJECT_NAME]` | Nom du site (ex: "Coudemail", "Titiranol Box") |
| Types de faits | Adapter selon le domaine (chiffres, dates, techniques, etc.) |

---

## 5. preprocess-article.sh

| Élément | Quoi changer |
|---------|-------------|
| Nombre de paramètres | 3 (slug, keyword, category) ou 5 (slug, keyword, branch, parent, order) |
| Prompts d'image fal.ai | Adapter les scènes par catégorie (atelier couture vs aquarium vs bureau crypto) |
| Palette couleurs fal.ai | `colors` JSON avec les 3 couleurs du design system |
| Style/sous-style | `digital_illustration` + sous-style adapté au sujet |
| Frontmatter template | Adapter les champs (articleType, category, etc.) |

### Prompts d'image par catégorie

Chaque catégorie du site doit avoir son propre prompt d'image. Exemple :
```bash
case "$CATEGORY" in
    categorie1)
        IMAGE_STYLE="digital_illustration"
        IMAGE_SUBSTYLE="hand_drawn"
        IMAGE_PROMPT="scène concrète décrivant le sujet..."
        ;;
esac
```

### Palette fal.ai

Extraire les 3 couleurs principales du CSS du site :
```json
"colors": [
    {"r": R1, "g": G1, "b": B1},
    {"r": R2, "g": G2, "b": B2},
    {"r": R3, "g": G3, "b": B3}
]
```

---

## 6. verify-articles.sh

| Élément | Quoi changer |
|---------|-------------|
| `CONTENT_DIR` | Chemin vers le dossier des articles |
| `CONTENT_EXT` | `.mdx` ou `.md` |
| Seuils de mots | `WARN_WORDS` et `MAX_WORDS` cohérents avec benchmark |
| Seuils d'accents | Minimum de caractères accentués attendus |
| Seuils de callouts | Min/max callouts par article |

---

## 7. Fichier JSON des quiz

Créer un fichier JSON vide `{}` à l'emplacement défini dans `QUIZ_JSON_PATH`.

Si le site utilise TypeScript pour importer les quiz, créer aussi un wrapper TS :
```typescript
import quizzes from './quizzes.json';

export interface QuizQuestion {
  question: string;
  options: string[];
  correctIndex: number;
  explanation: string;
}

export interface QuizData {
  title: string;
  questions: QuizQuestion[];
}

const QUIZZES: Record<string, QuizData> = quizzes as Record<string, QuizData>;

export function getQuizForSlug(slug: string): QuizData | null {
  return QUIZZES[slug] ?? null;
}

export { QUIZZES };
```

---

## Checklist de démarrage

1. [ ] Adapter le template global du site (CSS, layouts, pages, CLAUDE.md)
2. [ ] Choisir l'architecture CSV (3 ou 5 champs)
3. [ ] Personnaliser `benchmark-redaction.sh` (bannière, chemins, seuils)
4. [ ] Écrire `redaction-system-prompt.md` (persona, palette, maillage)
5. [ ] Personnaliser `quiz-system-prompt.md` (sujet, nom du site)
6. [ ] Adapter `preprocess-article.sh` (params, prompts image, palette)
7. [ ] Vérifier `verify-articles.sh` (chemins, seuils)
8. [ ] Créer le fichier JSON quiz vide
9. [ ] Tester avec un article : `./scripts/benchmark-redaction.sh test.csv`
