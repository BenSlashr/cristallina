# Cristallina - Instructions projet

## Stack
- Astro 5 + React islands + Tailwind 4
- Dossier projet : `site/`
- Build : `cd site && npm run build`
- Hebergement : VPS, Caddy en reverse proxy, fichiers statiques
- Domaine : `https://www.cristallina.fr` (version canonique avec www)
- TOUJOURS utiliser `https://www.cristallina.fr` dans les liens internes et le maillage

## Publication planifiee

Les articles avec un `pubDate` dans le futur ne sont pas generes au build.
Un timer systemd rebuild le site toutes les 6h (0h, 6h, 12h, 18h UTC).

Pour planifier un article, mettre une date future dans le frontmatter :
```yaml
pubDate: 2026-03-15
```

L'article apparaitra au premier rebuild apres cette date.

## Guidelines de redaction de contenu

### Workflow obligatoire pour chaque article

**Etape 1 : Preprocessing (script bash)**

```bash
./scripts/preprocess-article.sh <slug> <keyword> <branch> <parent> <order>
```

Le script genere `/tmp/preprocess-{slug}/prompt-data.md` contenant :
- Brief SEO Slashr (mots-cles, plan de contenu, nombre de mots)
- Recherche factuelle Tavily (synthese, sources, chiffres)
- Frontmatter suggere
- Contenu du hub parent (pour eviter les repetitions)

Plusieurs articles peuvent etre preprocesses en parallele :
```bash
./scripts/preprocess-article.sh slug1 kw1 branch1 parent1 1 &
./scripts/preprocess-article.sh slug2 kw2 branch2 parent2 2 &
wait
```

**Structure des fichiers et frontmatter**

Chemin : `site/src/content/guides/{branch-slug}/{article-slug}.md`
Images : `site/public/images/guides/{article-slug}.webp`

Frontmatter obligatoire :
```yaml
---
title: "Titre SEO de l'article"
description: "Meta description 150-160 caracteres"
type: guide
branch: getting-started
parent: getting-started
order: 3
image: "/images/guides/{slug}.webp"
readingTime: "12 min"
faqSchema: true
---
```

**Etape 2 : Rediger en lisant les donnees preprocessees**

Lire `/tmp/preprocess-{slug}/prompt-data.md` puis rediger l'article.

**Nombre de mots cible : 2000 a 2800 mots.**

**REGLE CRITIQUE : TOUJOURS ecrire avec les accents francais** (e, e, e, a, u, c, i, o, u).

**Etape 3 : Ajouter des callouts (blocs enrichis)**

Chaque article doit contenir 3 a 5 callouts :

```markdown
> [!TIP]
> Texte du conseil ici.
```

Types : `[!TIP]` (or), `[!NOTE]` (bleu), `[!WARNING]` (orange), `[!CAUTION]` (rouge), `[!IMPORTANT]` (violet)

Regles : 3 a 5 par article, mixer au moins 2 types, 1 a 3 phrases max par callout.

**Etape 3b : Ajouter des diagrammes Mermaid**

1 a 3 diagrammes par article. Palette obligatoire :
```
style NODE fill:#141D30,stroke:#F59E0B,color:#F1F5F9   (principal)
style NODE fill:#141D30,stroke:#8B5CF6,color:#F1F5F9   (secondaire)
```

### Patterns anti-detection IA

#### Caracteres typographiques bannis
- Tiret cadratin/demi-cadratin (— –) -> tiret simple (-)
- Apostrophe typographique (') -> apostrophe droite (')
- Guillemets typographiques (" ") -> guillemets droits (")

#### Mots interdits (~100)
de plus, en outre, par consequent, neanmoins, toutefois, dorenavant, des lors, il convient de,
crucial/e/aux, fondamental/e/aux, primordial/e/aux, incontournable/s,
captivant/e/s, fascinant/e/s, revolutionnaire/s, novateur/trice/s,
epoustouflant/e/s, majestueux/se, remarquable/s, exceptionnel/le/s,
indeniablement, assurement, indubitablement, incontestablement,
veritablement, considerablement, substantiellement, plethore, myriade,
subsequent/e/s, tapisserie, pierre angulaire, fer de lance,
exacerber, apprehender, corroborer, eluder, entraver, preconiser, proner,
stipuler, soulignons, notons, mentionnons

#### Connecteurs limites (max 1 par article)
de plus, en outre, par consequent, neanmoins, toutefois, cependant, ainsi, en effet

#### Patterns de remplissage a eviter
- "voyons maintenant", "passons a", "interessons-nous a", "examinons"
- "comme nous l'avons mentionne precedemment"
- "dans cette section/partie/chapitre"
- "il est a noter que", "il faut savoir/noter/souligner que"

#### Alternatives recommandees
- de plus -> aussi, et puis, en plus
- par consequent -> donc, du coup, resultat
- neanmoins/toutefois -> mais, pourtant
- crucial -> important, cle, central
- preconiser -> recommander, conseiller, suggerer
- plethore/myriade -> beaucoup, quantite, masse

### Etape 4 : Verification qualite

```bash
./scripts/verify-articles.sh <slug1> [slug2]
./scripts/verify-articles.sh --all
./scripts/verify-articles.sh --all --build
```

Le script verifie : accents, mots interdits, caracteres typo, callouts, longueur, frontmatter, build.

### Pipeline automatise (benchmark-redaction.sh)

Le script `scripts/benchmark-redaction.sh` automatise le workflow complet en une seule commande : preprocessing, redaction via API LLM, quiz, verification, et deploiement.

**Usage :**
```bash
# Lancer le pipeline complet
./scripts/benchmark-redaction.sh --model sonnet --articles articles.csv

# Avec options
./scripts/benchmark-redaction.sh --model haiku --articles articles.csv --parallel 5 --no-deploy
```

**Format CSV (5 champs, avec header) :**
```csv
slug,keyword,branch,parent,order
mon-article,mot cle seo,branche,hub-parent,1
```

**Modeles supportes :**
- Anthropic : `opus`, `sonnet`, `haiku`
- OpenAI : `nano` (gpt-5-nano), `mini` (gpt-5-mini)

**Options :**
| Option | Description |
|--------|-------------|
| `--model <id>` | Modele LLM (defaut: sonnet) |
| `--articles <csv>` | Fichier CSV des articles (requis) |
| `--parallel <n>` | Nombre d'articles en parallele (defaut: 3) |
| `--cooldown <s>` | Pause entre articles en secondes (auto: 30s Anthropic, 0s OpenAI) |
| `--skip-preprocess` | Sauter la Phase 1 si les donnees existent deja |
| `--no-deploy` | Ne pas copier les articles valides dans le projet |
| `--max-tokens <n>` | Limite de tokens en sortie (defaut: 8192) |

**Les 6 phases :**

| Phase | Action | Detail |
|-------|--------|--------|
| 1. Preprocessing | `preprocess-article.sh` en parallele | Recherche Tavily + brief SEO Slashr + image fal.ai |
| 2. Redaction | Appel API LLM | Article complet genere avec le system prompt du persona |
| 2b. Quiz | Appel API LLM | 3 questions quiz par article |
| 3. Verification | Inline | Mots interdits, accents, typo, callouts, Mermaid, longueur |
| 4. Rapport | Inline | Tokens, cout, temps, taux de succes |
| 5. Merge quiz | `jq` | Fusionne les quiz dans `site/src/data/quizzes.json` |
| 6. Deploiement | `cp` | Copie les articles OK dans `site/src/content/guides/{branch}/` |

**Fichiers du pipeline :**
- `scripts/benchmark-redaction.sh` - Script principal (6 phases)
- `scripts/preprocess-article.sh` - Preprocessing (Tavily + Slashr + fal.ai)
- `scripts/verify-articles.sh` - Verification qualite standalone
- `scripts/redaction-system-prompt.md` - Prompt persona (a personnaliser, voir PERSONNALISATION.md)
- `scripts/quiz-system-prompt.md` - Prompt generation quiz (a personnaliser)
- `scripts/PERSONNALISATION.md` - Guide complet de personnalisation du pipeline
- `site/src/data/quizzes.json` - Stockage des quiz generes

**Cles API requises** (dans `site/.env`) :
- `ANTHROPIC_API_KEY` ou `OPENAI_API_KEY` (selon le modele)
- `TAVILY_API_KEY` (recherche factuelle)
- `FAL_KEY` (generation d'images)

**Personnalisation :** Voir `scripts/PERSONNALISATION.md` pour la liste complete des elements a adapter quand on cree un nouveau site (persona, palette, maillage, prompts image, seuils de mots, etc.).

## Generation d'images - Recraft V3 via fal.ai

```bash
source site/.env && curl -s -X POST "https://fal.run/fal-ai/recraft-20b" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "no text, no letters. Description ici.",
    "image_size": "landscape_16_9",
    "style": "digital_illustration",
    "colors": [{"r": 4, "g": 6, "b": 12}, {"r": 245, "g": 158, "b": 11}, {"r": 139, "g": 92, "b": 246}]
  }' | jq '.images[0].url'
```

Regles : JAMAIS de texte sur les images, palette sombre coherente, pas de photos realistes de personnes.
