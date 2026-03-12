import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Dasha Periods',
  description: 'Explore your Vimshottari Dasha periods — understand planetary time cycles and their effects on your life.',
}

export default function DashaLayout({ children }: { children: React.ReactNode }) {
  return children
}
