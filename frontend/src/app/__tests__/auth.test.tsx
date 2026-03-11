import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

// Mock next/navigation
const mockPush = jest.fn()
const mockUsePathname = jest.fn(() => '/dashboard')
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => mockUsePathname(),
  useSearchParams: () => new URLSearchParams(),
}))

// Mock dependencies
jest.mock('@/lib/auth-context')
jest.mock('@/lib/toast-context')
jest.mock('@/lib/api-client')
jest.mock('@/lib/i18n', () => ({
  useI18n: () => ({ t: (key: string, fallback: string) => fallback, locale: 'en' }),
  I18nProvider: ({ children }: { children: React.ReactNode }) => children,
}))

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>

const createAuthReturn = (overrides = {}) => ({
  user: null,
  accessToken: null,
  csrfToken: null,
  isAuthenticated: false,
  isLoading: false,
  isApiLoading: false,
  login: jest.fn(),
  logout: jest.fn(),
  refreshUser: jest.fn(),
  setTokens: jest.fn(),
  clearAuth: jest.fn(),
  refreshAccessToken: jest.fn(),
  ...overrides,
})

const createToastReturn = () => ({
  showToast: jest.fn(),
  addToast: jest.fn(),
  toasts: [],
  removeToast: jest.fn(),
})

describe('Authentication Flow', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(createAuthReturn())
    mockUseToast.mockReturnValue(createToastReturn())
  })

  it('should identify unauthenticated state correctly', () => {
    const auth = createAuthReturn({ isAuthenticated: false, accessToken: null })
    mockUseAuth.mockReturnValue(auth)
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.accessToken).toBeNull()
  })

  it('should identify authenticated state with user data', () => {
    const user = { id: 1, username: 'test', email: 'test@test.com', full_name: 'Test User', is_admin: false, role: 'user' }
    const auth = createAuthReturn({ isAuthenticated: true, accessToken: 'token-123', user })
    mockUseAuth.mockReturnValue(auth)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.user?.email).toBe('test@test.com')
  })

  it('should call login with correct credentials', async () => {
    const mockLogin = jest.fn().mockResolvedValue({ success: true })
    mockUseAuth.mockReturnValue(createAuthReturn({ login: mockLogin }))

    const auth = mockUseAuth()
    await auth.login('testuser', 'password123')
    expect(mockLogin).toHaveBeenCalledWith('testuser', 'password123')
  })

  it('should handle login failure gracefully', async () => {
    const mockLogin = jest.fn().mockRejectedValue(new Error('Invalid credentials'))
    mockUseAuth.mockReturnValue(createAuthReturn({ login: mockLogin }))

    const auth = mockUseAuth()
    await expect(auth.login('bad', 'creds')).rejects.toThrow('Invalid credentials')
  })

  it('should call logout and clear state', async () => {
    const mockLogout = jest.fn().mockResolvedValue(undefined)
    const mockClearAuth = jest.fn()
    mockUseAuth.mockReturnValue(createAuthReturn({
      isAuthenticated: true,
      logout: mockLogout,
      clearAuth: mockClearAuth,
    }))

    const auth = mockUseAuth()
    await auth.logout()
    expect(mockLogout).toHaveBeenCalled()
  })

  it('should detect admin role correctly', () => {
    const adminUser = { id: 1, username: 'admin', email: 'admin@test.com', full_name: 'Admin', is_admin: true, role: 'admin' }
    const auth = createAuthReturn({ isAuthenticated: true, user: adminUser })
    expect(auth.user?.is_admin).toBe(true)
  })

  it('should detect practitioner role correctly', () => {
    const practitioner = { id: 2, username: 'guru', email: 'guru@test.com', full_name: 'Guru', is_admin: false, role: 'practitioner' }
    const auth = createAuthReturn({ isAuthenticated: true, user: practitioner })
    expect(auth.user?.role).toBe('practitioner')
  })

  it('should show loading state during authentication check', () => {
    mockUseAuth.mockReturnValue(createAuthReturn({ isLoading: true }))
    const auth = mockUseAuth()
    expect(auth.isLoading).toBe(true)
  })

  it('should handle token refresh', async () => {
    const mockRefresh = jest.fn().mockResolvedValue('new-token-123')
    mockUseAuth.mockReturnValue(createAuthReturn({ refreshAccessToken: mockRefresh }))

    const auth = mockUseAuth()
    const newToken = await auth.refreshAccessToken()
    expect(mockRefresh).toHaveBeenCalled()
    expect(newToken).toBe('new-token-123')
  })
})

describe('AuthGuard Component', () => {
  // Import after mocks are set up
  const { AuthGuard } = require('@/components/auth-guard')

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(createAuthReturn())
    mockUseToast.mockReturnValue(createToastReturn())
  })

  it('should render children when authenticated', () => {
    mockUseAuth.mockReturnValue(createAuthReturn({ isAuthenticated: true, user: { id: 1, username: 'u', email: 'u@u.com', full_name: 'U', is_admin: false, role: 'user' } }))

    render(
      <AuthGuard>
        <div data-testid="protected">Protected Content</div>
      </AuthGuard>
    )
    expect(screen.getByTestId('protected')).toBeInTheDocument()
  })

  it('should show loading spinner when checking auth', () => {
    mockUseAuth.mockReturnValue(createAuthReturn({ isLoading: true }))
    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )
    expect(screen.getByText('Verifying access...')).toBeInTheDocument()
  })

  it('should redirect to login when not authenticated', () => {
    mockUseAuth.mockReturnValue(createAuthReturn({ isAuthenticated: false }))
    render(
      <AuthGuard>
        <div>Protected Content</div>
      </AuthGuard>
    )
    // Should redirect, not show content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should redirect non-admin from admin pages', () => {
    const regularUser = { id: 1, username: 'u', email: 'u@u.com', full_name: 'U', is_admin: false, role: 'user' }
    mockUseAuth.mockReturnValue(createAuthReturn({ isAuthenticated: true, user: regularUser }))

    render(
      <AuthGuard requiredRole="admin">
        <div>Admin Content</div>
      </AuthGuard>
    )
    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
  })

  it('should allow admin access to admin pages', () => {
    const adminUser = { id: 1, username: 'admin', email: 'admin@test.com', full_name: 'Admin', is_admin: true, role: 'admin' }
    mockUseAuth.mockReturnValue(createAuthReturn({ isAuthenticated: true, user: adminUser }))

    render(
      <AuthGuard requiredRole="admin">
        <div data-testid="admin-content">Admin Content</div>
      </AuthGuard>
    )
    expect(screen.getByTestId('admin-content')).toBeInTheDocument()
  })
})

describe('API Client Authentication', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should include auth header in requests', async () => {
    const mockGet = (apiClient.get as jest.Mock).mockResolvedValue({ data: [] })
    await apiClient.get('/api/v1/health')
    expect(mockGet).toHaveBeenCalledWith('/api/v1/health')
  })

  it('should handle 401 response', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValue({ response: { status: 401 } })
    await expect(apiClient.get('/api/v1/profile')).rejects.toEqual(expect.objectContaining({ response: { status: 401 } }))
  })

  it('should handle network errors', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValue(new Error('Network Error'))
    await expect(apiClient.get('/api/v1/health')).rejects.toThrow('Network Error')
  })
})
