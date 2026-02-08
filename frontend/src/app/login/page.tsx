'use client'

import { useState, FormEvent, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'
import { User, Lock, AlertCircle, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { LoadingIndicator } from '@/components/loading-indicator'

export const dynamic = 'force-dynamic'

function LoginContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { login, isAuthenticated, user, isApiLoading } = useAuth()
  const { addToast } = useToast()
  const callbackUrl = searchParams.get('callbackUrl') || '/dashboard'
  const reason = searchParams.get('reason')

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Show appropriate message based on redirect reason
  useEffect(() => {
    if (reason) {
      const messages = {
        session_expired: 'Your session has expired. Please log in again.',
        auth_required: 'Authentication required. Please log in.',
        refresh_failed: 'Session refresh failed. Please log in again.',
        logged_out: 'You have been logged out successfully.',
        profile_fetch_failed: 'Failed to load profile. Please log in again.'
      }
      const message = messages[reason as keyof typeof messages]
      if (message) {
        addToast(message, reason === 'logged_out' ? 'success' : 'info', 4000)
      }
    }
  }, [reason, addToast])

  // Redirect if already logged in
  useEffect(() => {
    if (isAuthenticated && user) {
      let redirectUrl = callbackUrl
      
      // Role-based navigation
      if (user.is_admin) {
        redirectUrl = '/admin'
      } else if (user.role === 'practitioner') {
        // Check verification status for practitioners
        if (user.verification_status === 'pending_verification') {
          redirectUrl = '/profile?tab=verification'
          addToast('Your account is pending verification. Please complete your profile.', 'info', 5000)
        } else if (user.verification_status === 'rejected') {
          redirectUrl = '/profile?tab=verification'
          addToast('Your verification was rejected. Please update your information and resubmit.', 'warning', 5000)
        } else if (user.verification_status === 'verified') {
          redirectUrl = '/dashboard'
        } else {
          redirectUrl = '/dashboard'
        }
      } else {
        // Regular users use callback URL or default to dashboard
        redirectUrl = callbackUrl
      }
      
      router.replace(redirectUrl)
    }
  }, [isAuthenticated, user, router, callbackUrl, addToast])

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(email, password)
      
      // Success message will be shown after redirect based on user role
      // The redirect logic is handled in the useEffect above
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Login failed. Please try again.'
      setError(errorMsg)
      addToast(errorMsg, 'error', 4000)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full flex items-center justify-center">
              <span className="text-xl">✨</span>
            </div>
            <h1 className="text-3xl font-bold text-white">YatinVeda</h1>
          </div>
          <p className="text-slate-400">Sign in to access your Vedic Astrology Dashboard</p>
        </div>

        {/* Form Card */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
          {error && (
            <div className="mb-6 flex items-start space-x-3 rounded-lg bg-red-500/10 border border-red-500/30 p-4 animate-in fade-in">
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email or Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  id="email"
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  placeholder="your@email.com or username"
                  disabled={loading}
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-slate-300">
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-sm text-purple-400 hover:text-purple-300 transition"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-11 pr-11 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  placeholder="••••••••"
                  disabled={loading}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-300 transition"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || isApiLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-[1.02]"
            >
              {loading || isApiLoading ? (
                <span className="flex items-center justify-center">
                  <LoadingIndicator show={true} size="sm" className="mr-3" />
                  Signing in...
                </span>
              ) : (
                '✨ Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Don&apos;t have an account?{' '}
              <Link
                href="/signup"
                className="text-purple-400 hover:text-purple-300 font-medium transition hover:underline"
              >
                Create one
              </Link>
            </p>
          </div>
        </div>

        <div className="mt-8 text-center text-slate-500 text-sm">
          🔒 Secure authentication • Your personal astrology dashboard awaits
        </div>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen">Loading...</div>}>
      <LoginContent />
    </Suspense>
  )
}
