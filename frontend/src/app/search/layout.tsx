import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Search',
  description: 'Search YatinVeda for practitioners, community posts, charts, and Vedic astrology resources.',
}

export default function SearchLayout({ children }: { children: React.ReactNode }) {
  return children
}
