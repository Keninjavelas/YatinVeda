'use client'

import { FormEvent, useState } from 'react'
import Link from 'next/link'
import { AlertCircle, ArrowLeft, CheckCircle, Mail } from 'lucide-react'
import { useToast } from '@/lib/toast-context'

export default function ForgotPasswordPage() {
  const { showToast } = useToast()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const data = await response.json().catch(() => ({ detail: 'Failed to process request' }))
        const message = data.detail || data.message || 'Failed to process request'
        setError(message)
        showToast(message, 'error')
        return
      }

      setSuccess(true)
      showToast('Password reset link sent. Check your email.', 'success')
      setEmail('')
    } catch (err) {
      const message = err instanceof Error && err.name === 'AbortError'
        ? 'Request timed out. Please try again.'
        : 'Failed to process request. Please try again.'
      setError(message)
      showToast(message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-500 rounded-full flex items-center justify-center">
              <span className="text-xl">🔐</span>
            </div>
            <h1 className="text-3xl font-bold text-white">YatinVeda</h1>
          </div>
          <p className="text-slate-400">Reset your password</p>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 shadow-2xl backdrop-blur-sm">
          {error && (
            <div className="mb-6 flex items-start space-x-3 rounded-lg bg-red-500/10 border border-red-500/30 p-4">
              <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-6 flex items-start space-x-3 rounded-lg bg-green-500/10 border border-green-500/30 p-4">
              <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-green-200">Check your email!</p>
                <p className="text-sm text-green-200/80 mt-1">
                  We sent a password reset link to the email you provided.
                </p>
              </div>
            </div>
          )}

          {!success ? (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                    placeholder="your@email.com"
                    disabled={loading}
                    autoComplete="email"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:from-slate-600 disabled:to-slate-700 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-200 shadow-lg shadow-purple-500/30 hover:shadow-purple-500/50"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Sending...
                  </span>
                ) : (
                  '🔗 Send Reset Link'
                )}
              </button>
            </form>
          ) : (
            <div className="text-center py-6">
              <p className="text-slate-300 mb-4">Didn\'t receive the email?</p>
              <button
                onClick={() => {
                  setSuccess(false)
                  setEmail('')
                }}
                className="text-purple-400 hover:text-purple-300 font-medium transition"
              >
                Try another email
              </button>
            </div>
          )}

          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-slate-400 hover:text-purple-400 font-medium transition"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to sign in
            </Link>
          </div>
        </div>

        <div className="mt-8 text-center text-slate-500 text-sm">
          Remember your password?
          <Link href="/login" className="text-purple-400 hover:text-purple-300 ml-1 font-medium">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
