import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Glossary — terminology definitions with tooltips
 * TODO: Adjust categories to match your domain
 */
const glossary = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/glossaire' }),
  schema: z.object({
    title: z.string(),
    slug: z.string(),
    shortDefinition: z.string(),
    category: z.enum(['general', 'technique', 'finance', 'legal']),
    relatedTerms: z.array(z.string()).default([]),
    difficulty: z.enum(['debutant', 'intermediaire', 'avance']).default('debutant'),
  }),
});

/**
 * Blog — general articles with publication dates
 * Supports scheduled publishing via pubDate filtering
 */
const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    category: z.string(),
    author: z.string(),
    readingTime: z.string().optional(),
    image: z.string().optional(),
  }),
});

/**
 * Guides — hierarchical content with hub/guide structure
 * Hubs are branch index pages, guides are individual articles
 * TODO: Adjust branch names to match your topic areas
 */
const guides = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/guides' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    type: z.enum(['hub', 'guide']),
    branch: z.enum([
      'getting-started', 'advanced', 'tools', 'best-practices',
      'decoration', 'cuisine', 'chambre', 'salle-de-bain',
      'exterieur', 'couleurs', 'rangement', 'shopping',
    ]),
    parent: z.string().nullable().default(null),
    order: z.number().default(0),
    image: z.string().optional(),
    pubDate: z.coerce.date().optional(),
    readingTime: z.string().optional(),
    faqSchema: z.boolean().default(false),
  }),
});

export const collections = { glossary, blog, guides };
