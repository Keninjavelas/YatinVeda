'use client'

import React from 'react'
import { useAuth } from '@/lib/auth-context'

interface LoadingIndicatorProps {
  show?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function LoadingIndicator({ 
  show, 
  size = 'md', 
  className = '' 
}: LoadingIndicatorProps) {
  const { isApiLoading } = useAuth()
  const shouldShow = show !== undefined ? show : isApiLoading

  if (!shouldShow) return null

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  }

  return (
    <div className={`inline-flex items-center justify-center ${className}`}>
      <svg 
        className={`animate-spin ${sizeClasses[size]} text-purple-500`} 
        xmlns="http://www.w3.org/2000/svg" 
        fill="none" 
        viewBox="0 0 24 24"
      >
        <circle 
          className="opacity-25" 
          cx="12" 
          cy="12" 
          r="10" 
          stroke="currentColor" 
          strokeWidth="4"
        />
        <path 
          className="opacity-75" 
          fill="currentColor" 
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  )
}

// Global loading bar component for top of page
export function GlobalLoadingBar() {
  const { isApiLoading } = useAuth()

  if (!isApiLoading) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      <div className="h-1 bg-gradient-to-r from-purple-500 to-pink-500 animate-pulse" />
      <div className="h-1 bg-gradient-to-r from-purple-500 to-pink-500 animate-pulse opacity-50" 
           style={{ 
             animation: 'loading-bar 2s ease-in-out infinite',
             transformOrigin: 'left'
           }} 
      />
      <style jsx>{`
        @keyframes loading-bar {
          0% { transform: scaleX(0); }
          50% { transform: scaleX(0.7); }
          100% { transform: scaleX(1); }
        }
      `}</style>
    </div>
  )
}

// Skeleton loading component for content
interface SkeletonProps {
  width?: string
  height?: string
  className?: string
  lines?: number
}

export function Skeleton({ 
  width = '100%', 
  height = '1rem', 
  className = '',
  lines = 1 
}: SkeletonProps) {
  if (lines > 1) {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse bg-slate-700 rounded"
            style={{ 
              width: i === lines - 1 ? '75%' : width, 
              height 
            }}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      className={`animate-pulse bg-slate-700 rounded ${className}`}
      style={{ width, height }}
    />
  )
}

// Loading overlay for forms and modals
interface LoadingOverlayProps {
  show: boolean
  message?: string
  children: React.ReactNode
}

export function LoadingOverlay({ 
  show, 
  message = 'Loading...', 
  children 
}: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {show && (
        <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-10 rounded-lg">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 flex items-center space-x-3">
            <LoadingIndicator show={true} size="md" />
            <span className="text-white font-medium">{message}</span>
          </div>
        </div>
      )}
    </div>
  )
}