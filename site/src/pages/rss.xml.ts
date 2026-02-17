import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

const FALLBACK_DATE = new Date('2025-01-01');

export async function GET(context: APIContext) {
  const now = new Date();

  // Guides (published only)
  const guidePages = await getCollection('guides', ({ data }) =>
    data.type === 'guide' && (!data.pubDate || data.pubDate.valueOf() <= now.valueOf())
  );

  // Blog articles
  const blogPosts = await getCollection('blog', ({ data }) =>
    data.pubDate.valueOf() <= now.valueOf()
  );

  // Merge and sort by date (newest first)
  const allItems = [
    ...guidePages.map((p) => ({
      title: p.data.title,
      description: p.data.description,
      pubDate: p.data.pubDate ?? FALLBACK_DATE,
      link: `/guides/${p.id}`,
    })),
    ...blogPosts.map((p) => ({
      title: p.data.title,
      description: p.data.description,
      pubDate: p.data.pubDate,
      link: `/${p.id}`,
    })),
  ].sort((a, b) => b.pubDate.valueOf() - a.pubDate.valueOf());

  return rss({
    title: 'Cristallina - RSS Feed',
    description: 'Inspiration deco et lifestyle - guides et articles recents.',
    site: context.site!.toString(),
    items: allItems.slice(0, 30),
    customData: '<language>fr</language>',
  });
}
