import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { ToastProvider } from '@/lib/toast-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { GlobalLoadingBar } from '@/components/loading-indicator'
import Navbar from '@/components/navbar'
import { Toaster } from 'sonner'
import { I18nProvider } from '@/lib/i18n'
import { OrganizationJsonLd } from '@/components/structured-data'

export const metadata: Metadata = {
  title: {
    default: 'YatinVeda - Vedic Astrology Platform',
    template: '%s | YatinVeda',
  },
  description: 'AI-assisted Vedic Astrology Intelligence Platform — birth chart analysis, consultations, remedies, and community.',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://yatinveda.com'),
  manifest: '/manifest.json',
  themeColor: '#0f172a',
  openGraph: {
    type: 'website',
    siteName: 'YatinVeda',
    title: 'YatinVeda - Vedic Astrology Platform',
    description: 'AI-assisted Vedic Astrology Intelligence Platform — birth chart analysis, consultations, remedies, and community.',
  },
  twitter: {
    card: 'summary_large_image',
  },
  robots: {
    index: true,
    follow: true,
  },
  appleWebApp: {
    capable: true,
    title: 'YatinVeda',
    statusBarStyle: 'black-translucent',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <OrganizationJsonLd />
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[9999] focus:bg-white focus:text-black focus:px-4 focus:py-2 focus:rounded focus:shadow-lg"
        >
          Skip to main content
        </a>
        <ErrorBoundary>
          <ToastProvider>
            <I18nProvider>
              <AuthProvider>
                <GlobalLoadingBar />
                <Navbar />
                <main id="main-content">
                  {children}
                </main>
                <Toaster position="top-right" />
              </AuthProvider>
            </I18nProvider>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
