import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Library',
  description: 'Browse the YatinVeda knowledge library — articles, guides, and resources on Vedic astrology concepts.',
}

export default function LibraryLayout({ children }: { children: React.ReactNode }) {
  return children
}
