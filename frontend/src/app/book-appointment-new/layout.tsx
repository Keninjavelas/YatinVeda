import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Book Consultation',
  description: 'Book a personalised Vedic astrology consultation with verified practitioners on YatinVeda.',
}

export default function BookAppointmentLayout({ children }: { children: React.ReactNode }) {
  return children
}
