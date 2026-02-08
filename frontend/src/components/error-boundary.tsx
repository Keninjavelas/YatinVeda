'use client'

import React, { ReactNode, useState } from 'react'
import { AlertTriangle, RotateCw } from 'lucide-react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-8">
              <div className="flex justify-center mb-4">
                <div className="bg-red-100 p-4 rounded-full">
                  <AlertTriangle className="w-8 h-8 text-red-600" />
                </div>
              </div>

              <h1 className="text-2xl font-bold text-gray-900 text-center mb-2">
                Something went wrong
              </h1>

              <p className="text-gray-600 text-center mb-4">
                We're sorry for the inconvenience. An unexpected error occurred.
              </p>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                  <p className="text-sm font-mono text-red-700 overflow-auto max-h-48">
                    {this.state.error.message}
                  </p>
                </div>
              )}

              <div className="space-y-3">
                <button
                  onClick={this.handleReset}
                  className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
                >
                  <RotateCw size={20} />
                  Try again
                </button>

                <button
                  onClick={() => window.location.href = '/'}
                  className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  Go home
                </button>
              </div>

              <p className="text-xs text-gray-500 text-center mt-4">
                If the problem persists, please contact support.
              </p>
            </div>
          </div>
        )
      )
    }

    return this.props.children
  }
}
