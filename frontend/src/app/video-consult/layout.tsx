import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Video Consultation',
  description: 'Join a live video astrology consultation with a verified Vedic practitioner on YatinVeda.',
}

export default function VideoConsultLayout({ children }: { children: React.ReactNode }) {
  return children
}
