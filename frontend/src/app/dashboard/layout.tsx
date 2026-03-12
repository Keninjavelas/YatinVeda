import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Your personalised YatinVeda dashboard — charts, upcoming consultations, and astrology insights.',
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return children
}
