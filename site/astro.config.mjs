// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { remarkAlert } from 'remark-github-blockquote-alert';
import rehypeMermaid from 'rehype-mermaid';
import rehypeGlossaryTooltip from './src/plugins/rehype-glossary-tooltip.ts';

export default defineConfig({
  site: 'https://www.cristallina.fr',
  output: 'static',
  markdown: {
    syntaxHighlight: {
      type: 'shiki',
      excludeLangs: ['mermaid'],
    },
    remarkPlugins: [remarkAlert],
    rehypePlugins: [
      // CRITICAL: Use 'img-svg' strategy, NOT 'inline-svg'
      // inline-svg conflicts with Astro's built-in rehype-raw and causes silent empty article bodies
      [rehypeMermaid, {
        strategy: 'img-svg',
        dark: true,
        mermaidConfig: {
          theme: 'dark',
          themeVariables: {
            // Cristallina - rose/mauve doux
            primaryColor: '#FFF0F5',
            primaryTextColor: '#701A75',
            primaryBorderColor: '#E879F9',
            lineColor: '#8B5CF6',
            secondaryColor: '#F3F4F6',
            tertiaryColor: '#FEF3F2',
            noteBkgColor: '#FFF0F5',
            noteTextColor: '#581C87',
            noteBorderColor: '#E879F9',
          },
        },
      }],
      rehypeGlossaryTooltip,
    ],
  },
  integrations: [
    react(),
    mdx(),
    sitemap(),
  ],
  vite: {
    plugins: [tailwindcss()],
  },
});
