import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign Up',
  description: 'Create your free YatinVeda account to explore Vedic astrology birth charts, book consultations, and join the community.',
}

export default function SignupLayout({ children }: { children: React.ReactNode }) {
  return children
}
