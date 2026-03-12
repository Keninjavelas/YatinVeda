import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Community',
  description: 'Join the YatinVeda community — ask questions, share insights, and discuss Vedic astrology with fellow enthusiasts.',
}

export default function CommunityLayout({ children }: { children: React.ReactNode }) {
  return children
}
