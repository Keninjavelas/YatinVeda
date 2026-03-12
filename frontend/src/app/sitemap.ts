import type { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'

  return [
    { url: baseUrl, lastModified: new Date(), changeFrequency: 'weekly', priority: 1.0 },
    { url: `${baseUrl}/login`, changeFrequency: 'monthly', priority: 0.5 },
    { url: `${baseUrl}/signup`, changeFrequency: 'monthly', priority: 0.5 },
    { url: `${baseUrl}/chart`, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${baseUrl}/compatibility`, changeFrequency: 'weekly', priority: 0.8 },
    { url: `${baseUrl}/dasha`, changeFrequency: 'weekly', priority: 0.7 },
    { url: `${baseUrl}/remedies`, changeFrequency: 'weekly', priority: 0.8 },
    { url: `${baseUrl}/consultants`, changeFrequency: 'daily', priority: 0.8 },
    { url: `${baseUrl}/book-appointment-new`, changeFrequency: 'daily', priority: 0.7 },
    { url: `${baseUrl}/community`, changeFrequency: 'daily', priority: 0.7 },
    { url: `${baseUrl}/library`, changeFrequency: 'weekly', priority: 0.6 },
    { url: `${baseUrl}/search`, changeFrequency: 'weekly', priority: 0.5 },
  ]
}
