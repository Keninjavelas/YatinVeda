import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { ToastProvider } from '@/lib/toast-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { GlobalLoadingBar } from '@/components/loading-indicator'
import Navbar from '@/components/navbar'
import { Toaster } from 'sonner'
import { I18nProvider } from '@/lib/i18n'

export const metadata: Metadata = {
  title: 'YatinVeda - Vedic Astrology Platform',
  description: 'AI-assisted Vedic Astrology Intelligence Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <ErrorBoundary>
          <ToastProvider>
            <I18nProvider>
              <AuthProvider>
                <GlobalLoadingBar />
                <Navbar />
                {children}
                <Toaster position="top-right" />
              </AuthProvider>
            </I18nProvider>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
