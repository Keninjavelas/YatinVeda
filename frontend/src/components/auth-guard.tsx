'use client'

import { ReactNode, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

interface AuthGuardProps {
  children: ReactNode
  requiredRole?: 'user' | 'admin'
}

/**
 * Client-side route guard that redirects to login if not authenticated.
 * Place this at the top level of protected pages.
 */
export function AuthGuard({ children, requiredRole = 'user' }: AuthGuardProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        // Redirect to login with callback URL
        router.push(`/login?callbackUrl=${encodeURIComponent(window.location.pathname)}`)
      } else if (requiredRole === 'admin' && !user?.is_admin) {
        // Redirect to home if trying to access admin-only page
        router.push('/')
      }
    }
  }, [isLoading, isAuthenticated, user, requiredRole, router])

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-slate-300">Verifying access...</p>
        </div>
      </div>
    )
  }

  // Return null while redirecting
  if (!isAuthenticated || (requiredRole === 'admin' && !user?.is_admin)) {
    return null
  }

  return <>{children}</>
}
