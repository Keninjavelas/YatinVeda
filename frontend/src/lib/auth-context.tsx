'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { apiClient, login as apiLogin, logout as apiLogout, onLoadingChange, getAuthStatus } from './api-client'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  is_admin: boolean
  role: string
  verification_status: string
  practitioner_profile?: {
    guru_id: number
    professional_title: string
    bio: string
    specializations: string[]
    experience_years: number
    certification_details: any
    languages: string[]
    price_per_hour: number
    availability_schedule: any
    verified_at: string | null
    rating: number
    total_sessions: number
  } | null
}

interface AuthContextType {
  user: User | null
  accessToken: string | null
  csrfToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  isApiLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setTokens: (access: string, refresh?: string, csrf?: string) => void
  clearAuth: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [csrfToken, setCsrfToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isApiLoading, setIsApiLoading] = useState(false)
  const router = useRouter()

  // Subscribe to API loading state
  useEffect(() => {
    const unsubscribe = onLoadingChange(setIsApiLoading)
    return unsubscribe
  }, [])

  // Initialize auth state from sessionStorage
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = typeof window !== 'undefined' ? sessionStorage.getItem('access_token') : null
      const storedCsrf = typeof window !== 'undefined' ? sessionStorage.getItem('csrf_token') : null
      
      if (storedToken) {
        setAccessToken(storedToken)
        setCsrfToken(storedCsrf)
        // Fetch user profile
        await fetchUserProfile(storedToken)
      } else {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const fetchUserProfile = async (token?: string) => {
    try {
      const userData = await apiClient.get<User>('/api/v1/auth/profile', {
        skipLoading: true // Don't show global loading for profile fetch
      })
      setUser(userData)
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      // If profile fetch fails, clear auth and redirect to login
      clearAuth()
      router.push('/login?reason=profile_fetch_failed')
    } finally {
      setIsLoading(false)
    }
  }

  const refreshUser = async () => {
    if (accessToken) {
      await fetchUserProfile(accessToken)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const data = await apiLogin(email, password)
      const newAccessToken = data.access_token
      
      // Get auth status to extract CSRF token
      const authStatus = getAuthStatus()
      
      setAccessToken(newAccessToken)
      setCsrfToken(authStatus.hasCsrfToken ? sessionStorage.getItem('csrf_token') : null)

      // Fetch user profile
      await fetchUserProfile(newAccessToken)
      
      // Handle role-based navigation after profile is loaded
      // This will be handled by the login page component based on user role
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const logout = async () => {
    try {
      await apiLogout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
      router.push('/login?reason=logged_out')
    }
  }

  const setTokensHandler = (access: string, refresh?: string, csrf?: string) => {
    setAccessToken(access)
    if (csrf) {
      setCsrfToken(csrf)
    }
    // The API client handles sessionStorage persistence
  }

  const clearAuth = () => {
    setUser(null)
    setAccessToken(null)
    setCsrfToken(null)
    // Clear sessionStorage is handled by API client
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        csrfToken,
        isLoading,
        isAuthenticated: !!user,
        isApiLoading,
        login,
        logout,
        refreshUser,
        setTokens: setTokensHandler,
        clearAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
