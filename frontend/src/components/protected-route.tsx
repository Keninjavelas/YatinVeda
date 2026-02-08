'use client'

import React, { ReactNode } from 'react'
import { useAuth } from '@/lib/auth-context'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'user' | 'admin'
}

/**
 * Wrapper component that protects routes from unauthenticated access.
 * Shows loading state while auth is being verified.
 * Redirects to login if user is not authenticated (handled by useAuth hook).
 */
export function ProtectedRoute({ children, requiredRole = 'user' }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-slate-300">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null // Redirect handled by useAuth
  }

  if (requiredRole === 'admin' && !user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-500 mb-4">Access Denied</h1>
          <p className="text-slate-300">You do not have permission to access this page.</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
