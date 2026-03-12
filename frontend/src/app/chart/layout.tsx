import type { Metadata } from 'next'
import { AstrologyServiceJsonLd, BreadcrumbJsonLd } from '@/components/structured-data'

export const metadata: Metadata = {
  title: 'Birth Chart',
  description: 'Generate and analyse your Vedic astrology birth chart (Kundli) with AI-powered planetary insights.',
}

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'

export default function ChartLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AstrologyServiceJsonLd />
      <BreadcrumbJsonLd items={[
        { name: 'Home', url: SITE_URL },
        { name: 'Birth Chart', url: `${SITE_URL}/chart` },
      ]} />
      {children}
    </>
  )
}
