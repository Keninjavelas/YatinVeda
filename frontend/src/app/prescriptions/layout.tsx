import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Prescriptions',
  description: 'View your personalised Vedic astrology prescriptions — gemstones, mantras, rituals, and lifestyle guidance.',
}

export default function PrescriptionsLayout({ children }: { children: React.ReactNode }) {
  return children
}
