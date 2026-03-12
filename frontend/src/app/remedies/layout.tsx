import type { Metadata } from 'next'
import { FAQJsonLd, BreadcrumbJsonLd } from '@/components/structured-data'

export const metadata: Metadata = {
  title: 'Remedies',
  description: 'Explore personalised Vedic astrology remedies — gemstones, mantras, and rituals based on your birth chart.',
}

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'

const remedyFAQ = [
  { question: 'What are Vedic astrology remedies?', answer: 'Vedic astrology remedies include gemstones, mantras, rituals, and lifestyle changes prescribed based on planetary positions in your birth chart to mitigate negative influences and enhance positive ones.' },
  { question: 'How are remedies personalised?', answer: 'Each remedy is tailored to your unique birth chart (Kundli). Our AI analyses planetary positions, dasha periods, and house placements to suggest the most effective remedies.' },
  { question: 'Are gemstone recommendations safe?', answer: 'All gemstone recommendations follow traditional Vedic guidelines and are suggested only after thorough chart analysis by verified practitioners.' },
]

export default function RemediesLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <FAQJsonLd items={remedyFAQ} />
      <BreadcrumbJsonLd items={[
        { name: 'Home', url: SITE_URL },
        { name: 'Remedies', url: `${SITE_URL}/remedies` },
      ]} />
      {children}
    </>
  )
}
