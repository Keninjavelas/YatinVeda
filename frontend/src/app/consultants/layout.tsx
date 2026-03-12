import type { Metadata } from 'next'
import { ConsultantDirectoryJsonLd, BreadcrumbJsonLd } from '@/components/structured-data'

export const metadata: Metadata = {
  title: 'Consultants',
  description: 'Browse verified Vedic astrology practitioners — read reviews, check availability, and book consultations.',
}

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'

export default function ConsultantsLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <ConsultantDirectoryJsonLd />
      <BreadcrumbJsonLd items={[
        { name: 'Home', url: SITE_URL },
        { name: 'Consultants', url: `${SITE_URL}/consultants` },
      ]} />
      {children}
    </>
  )
}
