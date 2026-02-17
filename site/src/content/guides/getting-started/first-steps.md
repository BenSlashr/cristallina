---
title: "Premiers pas : le guide complet"
description: "Un guide pas a pas pour vos premiers pas. Installation, configuration et premier projet."
type: guide
branch: getting-started
parent: getting-started
order: 1
readingTime: "8 min"
faqSchema: true
---

Ce guide vous accompagne dans vos premiers pas. Suivez les etapes ci-dessous pour une mise en route rapide.

## Etape 1 : Installation

Commencez par installer les outils necessaires. Vous aurez besoin de Node.js (v18+) et d'un editeur de code.

> [!TIP]
> Utilisez VS Code avec l'extension Astro pour une meilleure experience de developpement.

## Etape 2 : Configuration

Creez un fichier `.env` a partir du template fourni et renseignez vos cles API.

```mermaid
graph LR
    A["Cloner le repo"] --> B["Installer les deps"]
    B --> C["Configurer .env"]
    C --> D["Lancer npm run dev"]
    style A fill:#141D30,stroke:#F59E0B,color:#F1F5F9
    style B fill:#141D30,stroke:#8B5CF6,color:#F1F5F9
    style C fill:#141D30,stroke:#F59E0B,color:#F1F5F9
    style D fill:#141D30,stroke:#8B5CF6,color:#F1F5F9
```

> [!WARNING]
> Ne committez jamais votre fichier `.env` dans le depot Git. Ajoutez-le a `.gitignore`.

## Etape 3 : Premier contenu

Creez votre premier article dans `src/content/blog/` en suivant le schema du frontmatter.

> [!NOTE]
> Les articles avec une date `pubDate` dans le futur ne seront pas generes au build. Ils apparaitront automatiquement au prochain rebuild apres leur date de publication.


## Sur le meme theme

- [enduire un mur en parpaing](/guides/decoration/comment-enduir-un-mur-en-parpaing/)
- [comment nettoyer une table en céramique](/guides/decoration/comment-nettoyer-une-table-en-ceramique/)
- [bien accrocher un tableau mural](/guides/decoration/bien-accrocher-tableau-mural/)
- [tiny house container](/guides/decoration/tiny-house-container/)
- [crépir un mur intérieur](/guides/decoration/crepir-un-mur-interieur/)

## Questions frequentes

### Comment planifier un article ?

Mettez une date future dans le champ `pubDate` du frontmatter. Le systeme de rebuild automatique (toutes les 6h) publiera l'article au bon moment.

### Comment ajouter un terme au glossaire ?

Ajoutez une entree dans `src/data/glossary-terms.ts` et creez le fichier markdown correspondant dans `src/content/glossaire/`.

> [!IMPORTANT]
> Lancez toujours le script de verification apres avoir ecrit un article : `./scripts/verify-articles.sh mon-slug`
