import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth-context'
import { ToastProvider } from '@/lib/toast-context'
import { ErrorBoundary } from '@/components/error-boundary'
import { GlobalLoadingBar } from '@/components/loading-indicator'
import Navbar from '@/components/navbar'
import { Toaster } from 'sonner'

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
            <AuthProvider>
              <GlobalLoadingBar />
              <Navbar />
              {children}
              <Toaster position="top-right" />
            </AuthProvider>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}
