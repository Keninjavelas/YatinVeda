import type { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/api/', '/admin/', '/dashboard/', '/profile/', '/wallet/', '/prescriptions/', '/video-consult/', '/practitioner-portal/'],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
  }
}
