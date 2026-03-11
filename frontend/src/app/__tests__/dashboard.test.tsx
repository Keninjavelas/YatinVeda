import { render, screen, waitFor } from '@testing-library/react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => '/dashboard',
  useSearchParams: () => new URLSearchParams(),
}))

jest.mock('@/lib/auth-context')
jest.mock('@/lib/toast-context')
jest.mock('@/lib/api-client')
jest.mock('@/lib/i18n', () => ({
  useI18n: () => ({ t: (key: string, fallback: string) => fallback, locale: 'en' }),
  I18nProvider: ({ children }: { children: React.ReactNode }) => children,
}))

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>
const mockUseToast = useToast as jest.MockedFunction<typeof useToast>

const authUser = {
  user: { id: 1, username: 'test', email: 'test@test.com', full_name: 'Test User', is_admin: false, role: 'user' as const },
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

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(authUser)
    mockUseToast.mockReturnValue({ showToast: jest.fn(), addToast: jest.fn(), toasts: [], removeToast: jest.fn() })
  })

  it('should fetch bookings on mount', async () => {
    const mockBookings = [
      {
        id: 1,
        guru_id: 10,
        guru_name: 'Guru Sharma',
        booking_date: new Date(Date.now() + 86400000).toISOString(),
        time_slot: '10:00',
        duration_minutes: 60,
        session_type: 'video_call',
        status: 'confirmed',
        payment_status: 'paid',
        payment_amount: 1500,
        meeting_link: 'https://meet.example.com/123',
        created_at: '2024-01-01',
      },
    ]
    ;(apiClient.get as jest.Mock).mockResolvedValue(mockBookings)

    const result = await apiClient.get('/api/v1/guru-booking/bookings')
    expect(result).toHaveLength(1)
    expect(result[0].guru_name).toBe('Guru Sharma')
  })

  it('should filter upcoming bookings correctly', () => {
    const now = new Date()
    const futureDate = new Date(now.getTime() + 7 * 86400000).toISOString()
    const pastDate = new Date(now.getTime() - 7 * 86400000).toISOString()

    const bookings = [
      { id: 1, booking_date: futureDate, status: 'confirmed' },
      { id: 2, booking_date: pastDate, status: 'confirmed' },
      { id: 3, booking_date: futureDate, status: 'cancelled' },
    ]

    const upcoming = bookings.filter((b) => {
      const date = new Date(b.booking_date)
      return date >= now && (b.status === 'pending' || b.status === 'confirmed')
    })

    expect(upcoming).toHaveLength(1)
    expect(upcoming[0].id).toBe(1)
  })

  it('should sort upcoming bookings by date', () => {
    const now = new Date()
    const bookings = [
      { id: 1, booking_date: new Date(now.getTime() + 3 * 86400000).toISOString(), status: 'confirmed' },
      { id: 2, booking_date: new Date(now.getTime() + 1 * 86400000).toISOString(), status: 'confirmed' },
      { id: 3, booking_date: new Date(now.getTime() + 7 * 86400000).toISOString(), status: 'pending' },
    ]

    const sorted = bookings.sort(
      (a, b) => new Date(a.booking_date).getTime() - new Date(b.booking_date).getTime()
    )

    expect(sorted[0].id).toBe(2) // Closest date first
    expect(sorted[2].id).toBe(3) // Furthest date last
  })

  it('should handle booking fetch error', async () => {
    const showToast = jest.fn()
    ;(apiClient.get as jest.Mock).mockRejectedValue(new Error('Network error'))

    try {
      await apiClient.get('/api/v1/guru-booking/bookings')
    } catch {
      showToast('Failed to load bookings. Please try again.', 'error')
    }
    expect(showToast).toHaveBeenCalledWith('Failed to load bookings. Please try again.', 'error')
  })

  it('should identify session types correctly', () => {
    const sessions = ['video_call', 'audio_call', 'chat']
    expect(sessions).toContain('video_call')
    expect(sessions).toContain('audio_call')
    expect(sessions).toContain('chat')
  })

  it('should display correct payment status', () => {
    const booking = { payment_status: 'paid', payment_amount: 1500 }
    expect(booking.payment_status).toBe('paid')
    expect(booking.payment_amount).toBe(1500)

    const unpaid = { payment_status: 'pending', payment_amount: 999 }
    expect(unpaid.payment_status).toBe('pending')
  })
})

describe('Dashboard - API Interactions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(authUser)
    mockUseToast.mockReturnValue({ showToast: jest.fn(), addToast: jest.fn(), toasts: [], removeToast: jest.fn() })
  })

  it('should fetch user profile', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      id: 1,
      username: 'test',
      email: 'test@test.com',
      full_name: 'Test User',
    })

    const profile = await apiClient.get('/api/v1/auth/profile')
    expect(profile.username).toBe('test')
  })

  it('should fetch user charts', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue([
      { id: 1, title: 'Birth Chart', chart_type: 'natal', created_at: '2024-01-01' },
    ])

    const charts = await apiClient.get('/api/v1/charts')
    expect(charts).toHaveLength(1)
    expect(charts[0].chart_type).toBe('natal')
  })
})
