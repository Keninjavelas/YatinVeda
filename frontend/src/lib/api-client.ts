/**
 * Enhanced API Client with automatic token refresh and cookie-based authentication
 * 
 * Features:
 * - Automatic token refresh on 401 responses
 * - Cookie-based refresh token handling
 * - CSRF token management
 * - Comprehensive error handling
 * - Request retry logic
 * - Loading state management
 * 
 * Usage:
 *   import { apiClient } from '@/lib/api-client'
 *   const data = await apiClient.get('/api/v1/charts')
 *   const result = await apiClient.post('/api/v1/bookings', { ... })
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// Global loading state for API requests
let activeRequests = 0
const loadingCallbacks: Array<(loading: boolean) => void> = []

export function onLoadingChange(callback: (loading: boolean) => void) {
  loadingCallbacks.push(callback)
  return () => {
    const index = loadingCallbacks.indexOf(callback)
    if (index > -1) loadingCallbacks.splice(index, 1)
  }
}

function setLoading(loading: boolean) {
  if (loading) {
    activeRequests++
  } else {
    activeRequests = Math.max(0, activeRequests - 1)
  }
  const isLoading = activeRequests > 0
  loadingCallbacks.forEach(callback => callback(isLoading))
}

interface TokenStorage {
  accessToken: string | null
  refreshToken: string | null  // Only used for fallback; prefer httpOnly cookie
  csrfToken: string | null
}

interface ApiError extends Error {
  status?: number
  code?: string
  details?: any
}

class ApiClientError extends Error implements ApiError {
  status?: number
  code?: string
  details?: any

  constructor(message: string, status?: number, code?: string, details?: any) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.code = code
    this.details = details
  }
}

// In-memory token storage (refresh token in httpOnly cookie, CSRF in memory)
let tokens: TokenStorage = {
  accessToken: null,
  refreshToken: null,  // Cookie-based auth uses httpOnly cookie instead
  csrfToken: null
}

// Track refresh attempts to prevent infinite loops
let isRefreshing = false
let refreshPromise: Promise<boolean> | null = null

export function setTokens(access: string, refresh?: string, csrf?: string) {
  tokens.accessToken = access
  // Only store refresh token if explicitly provided (fallback for non-cookie auth)
  if (refresh) tokens.refreshToken = refresh
  if (csrf) tokens.csrfToken = csrf
  
  // Persist to sessionStorage for page refresh
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.setItem('access_token', access)
      // Only store refresh token in sessionStorage if provided (not recommended for security)
      if (refresh) sessionStorage.setItem('refresh_token', refresh)
      if (csrf) sessionStorage.setItem('csrf_token', csrf)
    } catch (error) {
      console.warn('Failed to store tokens in sessionStorage:', error)
    }
  }
}

export function getTokens(): TokenStorage {
  // Restore from sessionStorage if in-memory tokens are missing
  if (typeof window !== 'undefined') {
    try {
      if (!tokens.accessToken) {
        tokens.accessToken = sessionStorage.getItem('access_token')
      }
      if (!tokens.refreshToken) {
        tokens.refreshToken = sessionStorage.getItem('refresh_token')
      }
      if (!tokens.csrfToken) {
        tokens.csrfToken = sessionStorage.getItem('csrf_token')
      }
    } catch (error) {
      console.warn('Failed to retrieve tokens from sessionStorage:', error)
    }
  }
  return tokens
}

export function clearTokens() {
  tokens.accessToken = null
  tokens.refreshToken = null
  tokens.csrfToken = null
  
  if (typeof window !== 'undefined') {
    try {
      sessionStorage.removeItem('access_token')
      sessionStorage.removeItem('refresh_token')
      sessionStorage.removeItem('csrf_token')
    } catch (error) {
      console.warn('Failed to clear tokens from sessionStorage:', error)
    }
  }
}

async function refreshAccessToken(): Promise<boolean> {
  // Prevent multiple simultaneous refresh attempts
  if (isRefreshing && refreshPromise) {
    return refreshPromise
  }

  isRefreshing = true
  const { refreshToken, csrfToken } = getTokens()

  refreshPromise = (async () => {
    try {
      // Prefer cookie-based refresh (httpOnly cookie sent automatically)
      // Include CSRF token header when using cookie-based auth
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (csrfToken) {
        headers['x-csrf-token'] = csrfToken
      }

      const requestBody = refreshToken ? { refresh_token: refreshToken } : undefined

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers,
        credentials: 'include',  // Include httpOnly cookies
        body: requestBody ? JSON.stringify(requestBody) : undefined
      })

      if (!response.ok) {
        clearTokens()
        // Redirect to login on auth failure
        if (typeof window !== 'undefined') {
          window.location.href = '/login?reason=session_expired'
        }
        return false
      }

      const data = await response.json()
      if (data.access_token) {
        // Extract new CSRF token from response headers (refresh may rotate CSRF)
        const newCsrfToken = response.headers.get('x-csrf-token')
        // Don't store refresh token from response body; it's in httpOnly cookie
        setTokens(data.access_token, undefined, newCsrfToken || csrfToken || undefined)
        return true
      }
      return false
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearTokens()
      if (typeof window !== 'undefined') {
        window.location.href = '/login?reason=refresh_failed'
      }
      return false
    } finally {
      isRefreshing = false
      refreshPromise = null
    }
  })()

  return refreshPromise
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
  skipLoading?: boolean
  retries?: number
  timeout?: number
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { 
    skipAuth, 
    skipLoading, 
    retries = 1, 
    timeout = 30000,
    ...fetchOptions 
  } = options
  
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`
  
  // Set loading state
  if (!skipLoading) {
    setLoading(true)
  }

  try {
    return await requestWithRetry<T>(url, fetchOptions, {
      skipAuth,
      retries,
      timeout
    })
  } finally {
    if (!skipLoading) {
      setLoading(false)
    }
  }
}

async function requestWithRetry<T>(
  url: string,
  fetchOptions: RequestInit,
  options: {
    skipAuth?: boolean
    retries: number
    timeout: number
  }
): Promise<T> {
  const { skipAuth, retries, timeout } = options
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeout)

      const headersRecord: Record<string, string> = {
        'Content-Type': 'application/json',
        ...((fetchOptions.headers as Record<string, string>) || {})
      }

      // Add access token if available and not skipped
      if (!skipAuth) {
        const { accessToken, csrfToken } = getTokens()
        if (accessToken) {
          headersRecord['Authorization'] = `Bearer ${accessToken}`
        }
        // Include CSRF token for mutation operations (httpOnly cookie protection)
        if (csrfToken && (fetchOptions.method === 'POST' || fetchOptions.method === 'PATCH' || fetchOptions.method === 'PUT' || fetchOptions.method === 'DELETE')) {
          headersRecord['x-csrf-token'] = csrfToken
        }
      }

      // Always include credentials to send/receive httpOnly cookies
      let response = await fetch(url, { 
        ...fetchOptions, 
        headers: headersRecord as HeadersInit,
        credentials: 'include',
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      // If 401 and refresh token available, attempt refresh and retry once
      if (response.status === 401 && !skipAuth && attempt === 0) {
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          const { accessToken } = getTokens()
          if (accessToken) {
            headersRecord['Authorization'] = `Bearer ${accessToken}`
          }
          
          const retryController = new AbortController()
          const retryTimeoutId = setTimeout(() => retryController.abort(), timeout)
          
          response = await fetch(url, { 
            ...fetchOptions, 
            headers: headersRecord as HeadersInit,
            credentials: 'include',
            signal: retryController.signal
          })
          
          clearTimeout(retryTimeoutId)
        } else {
          // Refresh failed; redirect to login
          if (typeof window !== 'undefined') {
            window.location.href = '/login?reason=auth_required'
          }
          throw new ApiClientError('Authentication required', 401, 'AUTH_REQUIRED')
        }
      }

      if (!response.ok) {
        let errorMessage = `API Error: ${response.status}`
        let errorDetails: any = null
        
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
          errorDetails = errorData
        } catch {
          errorMessage = await response.text() || errorMessage
        }
        
        throw new ApiClientError(errorMessage, response.status, 'API_ERROR', errorDetails)
      }

      // Extract and cache CSRF token from response headers if present
      const csrfFromResponse = response.headers.get('x-csrf-token')
      if (csrfFromResponse) {
        const { accessToken } = getTokens()
        // Update CSRF token while preserving access token
        if (accessToken) {
          setTokens(accessToken, undefined, csrfFromResponse)
        }
      }

      // Handle different response types
      const contentType = response.headers.get('content-type')
      if (contentType?.includes('application/json')) {
        return response.json()
      } else if (contentType?.includes('text/')) {
        return response.text() as unknown as T
      } else {
        return response.blob() as unknown as T
      }

    } catch (error) {
      lastError = error as Error
      
      // Don't retry on certain errors
      if (error instanceof ApiClientError) {
        if (error.status === 401 || error.status === 403 || error.status === 404) {
          throw error
        }
      }
      
      // Don't retry on abort errors (timeout)
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ApiClientError('Request timeout', 408, 'TIMEOUT')
      }
      
      // If this is the last attempt, throw the error
      if (attempt === retries) {
        throw error
      }
      
      // Wait before retrying (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000))
    }
  }

  throw lastError || new ApiClientError('Request failed after retries', 500, 'RETRY_FAILED')
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),
  
  post: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    }),
  
  put: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    }),
  
  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),

  patch: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined
    }),

  // Utility methods for common operations
  upload: async <T>(endpoint: string, formData: FormData, options?: RequestOptions): Promise<T> => {
    const { skipAuth, skipLoading, ...fetchOptions } = options || {}
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`
    
    if (!skipLoading) {
      setLoading(true)
    }

    try {
      const headersRecord: Record<string, string> = {
        // Don't set Content-Type for FormData, let browser set it with boundary
        ...((fetchOptions.headers as Record<string, string>) || {})
      }

      if (!skipAuth) {
        const { accessToken, csrfToken } = getTokens()
        if (accessToken) {
          headersRecord['Authorization'] = `Bearer ${accessToken}`
        }
        if (csrfToken) {
          headersRecord['x-csrf-token'] = csrfToken
        }
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: headersRecord as HeadersInit,
        credentials: 'include',
        body: formData,
        ...fetchOptions
      })

      if (!response.ok) {
        let errorMessage = `Upload failed: ${response.status}`
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch {
          errorMessage = await response.text() || errorMessage
        }
        throw new ApiClientError(errorMessage, response.status, 'UPLOAD_ERROR')
      }

      return response.json()
    } finally {
      if (!skipLoading) {
        setLoading(false)
      }
    }
  },

  // Download method for files
  download: async (endpoint: string, filename?: string, options?: RequestOptions): Promise<void> => {
    const response = await request<Blob>(endpoint, { 
      ...options, 
      skipLoading: false 
    })
    
    if (typeof window !== 'undefined') {
      const url = window.URL.createObjectURL(response)
      const a = document.createElement('a')
      a.href = url
      a.download = filename || 'download'
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    }
  }
}

/**
 * Enhanced login helper: sets tokens (including CSRF from response header) and returns user profile
 * Refresh token is stored in httpOnly cookie by backend, not in JavaScript
 */
export async function login(username: string, password: string) {
  setLoading(true)
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      credentials: 'include'  // Allow setting httpOnly cookies
    })

    if (!response.ok) {
      let errorMessage = 'Login failed'
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorMessage
      } catch {
        errorMessage = `Login failed: ${response.status}`
      }
      throw new ApiClientError(errorMessage, response.status, 'LOGIN_FAILED')
    }

    const data = await response.json()
    
    if (data.access_token) {
      // Extract CSRF token from response headers (required for cookie-based refresh)
      const csrfToken = response.headers.get('x-csrf-token')
      // Don't store refresh_token in JavaScript; it's in httpOnly cookie for security
      setTokens(data.access_token, undefined, csrfToken || undefined)
    }
    
    return data
  } finally {
    setLoading(false)
  }
}

/**
 * Enhanced logout helper: revokes refresh token (from httpOnly cookie) and clears storage
 */
export async function logout() {
  setLoading(true)
  
  try {
    // Backend reads refresh token from httpOnly cookie, no body needed
    await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'  // Send httpOnly cookie with refresh token
    })
  } catch (error) {
    console.warn('Logout request failed:', error)
  } finally {
    clearTokens()
    setLoading(false)
    if (typeof window !== 'undefined') {
      window.location.href = '/login?reason=logged_out'
    }
  }
}

/**
 * Check if user is authenticated (has valid access token)
 */
export function isAuthenticated(): boolean {
  const { accessToken } = getTokens()
  return !!accessToken
}

/**
 * Get current authentication status
 */
export function getAuthStatus() {
  const { accessToken, csrfToken } = getTokens()
  return {
    isAuthenticated: !!accessToken,
    hasAccessToken: !!accessToken,
    hasCsrfToken: !!csrfToken,
    isRefreshing
  }
}
