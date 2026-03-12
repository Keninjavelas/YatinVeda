/**
 * @jest-environment jsdom
 */

import { render, screen, waitFor } from '@testing-library/react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => '/wallet',
  useSearchParams: () => new URLSearchParams(),
}))

jest.mock('@/lib/auth-context')
jest.mock('@/lib/toast-context')
jest.mock('@/lib/api-client')
jest.mock('@/lib/i18n', () => ({
  useI18n: () => ({ t: (_key: string, fallback: string) => fallback, locale: 'en' }),
  I18nProvider: ({ children }: { children: React.ReactNode }) => children,
}))

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

import WalletPage from '@/app/wallet/page'

describe('Wallet Page', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(authUser)
    mockUseToast.mockReturnValue(toastMock)
    ;(apiClient.get as jest.Mock).mockImplementation((url: string) => {
      if (url.includes('balance')) {
        return Promise.resolve({ balance: 25000, currency: 'INR' })
      }
      if (url.includes('transactions')) {
        return Promise.resolve({
          items: [
            { id: 1, amount: 10000, transaction_type: 'credit', description: 'Wallet top-up', created_at: '2024-06-01T10:00:00Z', balance_after: 25000 },
          ],
        })
      }
      return Promise.resolve({})
    })
  })

  it('renders wallet heading', async () => {
    render(<WalletPage />)
    await waitFor(() => {
      expect(screen.getByText(/My Wallet/i)).toBeInTheDocument()
    })
  })

  it('fetches wallet balance on mount', async () => {
    render(<WalletPage />)
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/payments/wallet/balance'),
        expect.anything()
      )
    })
  })

  it('fetches transactions on mount', async () => {
    render(<WalletPage />)
    await waitFor(() => {
      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/payments/wallet/transactions'),
        expect.anything()
      )
    })
  })

  it('shows loading state when auth is loading', () => {
    mockUseAuth.mockReturnValue({ ...authUser, isLoading: true, isAuthenticated: false })
    render(<WalletPage />)
    expect(screen.getByText(/Verifying access/i)).toBeInTheDocument()
  })

  it('redirects when unauthenticated', () => {
    mockUseAuth.mockReturnValue({ ...authUser, isAuthenticated: false, isLoading: false, user: null })
    render(<WalletPage />)
    expect(mockPush).toHaveBeenCalled()
  })
})
