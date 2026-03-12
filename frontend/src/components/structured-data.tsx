import Script from 'next/script'

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'

/** Organization + WebSite structured data for the root layout. */
export function OrganizationJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Organization',
        '@id': `${SITE_URL}/#organization`,
        name: 'YatinVeda',
        url: SITE_URL,
        description:
          'AI-assisted Vedic Astrology Intelligence Platform — birth chart analysis, consultations, remedies, and community.',
        sameAs: [],
        contactPoint: {
          '@type': 'ContactPoint',
          contactType: 'customer service',
          availableLanguage: ['English', 'Hindi'],
        },
      },
      {
        '@type': 'WebSite',
        '@id': `${SITE_URL}/#website`,
        url: SITE_URL,
        name: 'YatinVeda',
        publisher: { '@id': `${SITE_URL}/#organization` },
        potentialAction: {
          '@type': 'SearchAction',
          target: {
            '@type': 'EntryPoint',
            urlTemplate: `${SITE_URL}/search?q={search_term_string}`,
          },
          'query-input': 'required name=search_term_string',
        },
      },
    ],
  }

  return (
    <Script
      id="org-jsonld"
      type="application/ld+json"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}

/** Service structured data for the chart generation page. */
export function AstrologyServiceJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'Service',
    name: 'Vedic Birth Chart Analysis',
    provider: { '@id': `${SITE_URL}/#organization` },
    description:
      'AI-powered Vedic astrology birth chart generation with planetary positions, house placements, dasha periods, and personalized interpretations.',
    serviceType: 'Astrology Consultation',
    areaServed: 'Worldwide',
    availableChannel: {
      '@type': 'ServiceChannel',
      serviceUrl: `${SITE_URL}/chart`,
      availableLanguage: ['English', 'Hindi'],
    },
  }

  return (
    <Script
      id="service-jsonld"
      type="application/ld+json"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}

/** FAQ structured data — accepts an array of question/answer pairs. */
export function FAQJsonLd({
  items,
}: {
  items: { question: string; answer: string }[]
}) {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: items.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  }

  return (
    <Script
      id="faq-jsonld"
      type="application/ld+json"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}

/** BreadcrumbList — pass an array of {name, url} items. */
export function BreadcrumbJsonLd({
  items,
}: {
  items: { name: string; url: string }[]
}) {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: item.name,
      item: item.url,
    })),
  }

  return (
    <Script
      id="breadcrumb-jsonld"
      type="application/ld+json"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}

/** ProfessionalService for the consultants directory. */
export function ConsultantDirectoryJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'ProfessionalService',
    name: 'YatinVeda Astrology Consultations',
    provider: { '@id': `${SITE_URL}/#organization` },
    description:
      'Connect with verified Vedic astrology practitioners for personalized consultations via video, audio or chat.',
    serviceType: 'Astrology Consultation',
    areaServed: 'Worldwide',
    url: `${SITE_URL}/consultants`,
  }

  return (
    <Script
      id="consultant-jsonld"
      type="application/ld+json"
      strategy="afterInteractive"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}
