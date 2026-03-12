/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from '@testing-library/react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

// Mock dependencies
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => '/profile',
  useSearchParams: () => new URLSearchParams(),
}))

jest.mock('@/lib/auth-context')
jest.mock('@/lib/toast-context')
jest.mock('@/lib/api-client')
jest.mock('@/lib/i18n', () => ({
  useI18n: () => ({ t: (_key: string, fallback: string) => fallback, locale: 'en' }),
  I18nProvider: ({ children }: { children: React.ReactNode }) => children,
}))

// Stub BackButton to avoid Link-related issues
jest.mock('@/components/BackButton', () => {
  return function MockBackButton() { return <button>Back</button> }
})

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>

const authUser = {
  user: { id: 1, username: 'testuser', email: 'test@example.com', full_name: 'Test User', is_admin: false, role: 'user' as const },
  accessToken: 'test-token',
  csrfToken: 'csrf-token',
  isAuthenticated: true,
  isLoading: false,
  isApiLoading: false,
  login: jest.fn(),
  logout: jest.fn(),
  refreshUser: jest.fn(),
  setTokens: jest.fn(),
  clearAuth: jest.fn(),
  refreshAccessToken: jest.fn(),
}

const toastMock = { showToast: jest.fn(), addToast: jest.fn(), toasts: [], removeToast: jest.fn() }

// Import the page component once
import ProfilePage from '@/app/profile/page'

describe('Profile Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(authUser)
    mockUseToast.mockReturnValue(toastMock)
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      charts_saved: 5,
      chat_messages: 12,
      lessons_completed: 3,
      account_age_days: 30,
      member_since: '2024-01-01',
    })
  })

  it('renders profile heading for authenticated user', async () => {
    render(<ProfilePage />)
    await waitFor(() => {
      expect(screen.getByText(/Profile/i)).toBeInTheDocument()
    })
  })

  it('displays user name and email', async () => {
    render(<ProfilePage />)
    await waitFor(() => {
      expect(screen.getAllByText('Test User').length).toBeGreaterThan(0)
      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })
  })

  it('fetches profile stats on mount', async () => {
    render(<ProfilePage />)
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/profile/stats')
    })
  })

  it('shows loading state when auth is loading', () => {
    mockUseAuth.mockReturnValue({ ...authUser, isLoading: true, isAuthenticated: false })
    render(<ProfilePage />)
    expect(screen.getByText(/Verifying access/i)).toBeInTheDocument()
  })

  it('redirects when unauthenticated', () => {
    mockUseAuth.mockReturnValue({ ...authUser, isAuthenticated: false, isLoading: false, user: null })
    render(<ProfilePage />)
    // AuthGuard redirects via router.push
    expect(mockPush).toHaveBeenCalled()
  })
})
