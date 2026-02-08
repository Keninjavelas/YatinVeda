/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import AdminPage from '../page'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

// Mock the dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

jest.mock('@/lib/auth-context', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/lib/toast-context', () => ({
  useToast: jest.fn(),
}))

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
  },
}))

jest.mock('@/components/auth-guard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
}

const mockAuth = {
  accessToken: 'mock-token',
}

const mockToast = {
  showToast: jest.fn(),
}

const mockStats = {
  total_users: 100,
  active_users: 85,
  admin_users: 5,
  total_charts: 250,
  total_learning_records: 150,
  completed_lessons: 120,
  total_chat_messages: 500,
  completion_rate: 80.0,
}

const mockVerificationStats = {
  total_practitioners: 25,
  pending_verification: 5,
  verified: 18,
  rejected: 2,
  recent_verifications_30_days: 3,
  verification_rate: 72.0,
}

const mockPendingPractitioners = [
  {
    guru_id: 1,
    user_id: 10,
    username: 'practitioner1',
    email: 'practitioner1@example.com',
    full_name: 'John Practitioner',
    professional_title: 'Vedic Astrologer',
    bio: 'Experienced astrologer with 10 years of practice in Vedic astrology and horoscope reading.',
    specializations: ['vedic_astrology', 'horoscope_matching'],
    experience_years: 10,
    certification_details: {
      certification_type: 'diploma',
      issuing_authority: 'Indian Astrology Institute',
    },
    languages: ['english', 'hindi'],
    price_per_hour: 2000,
    created_at: '2024-01-15T10:00:00Z',
    verification_status: 'pending_verification',
    is_ready_for_verification: true,
  },
  {
    guru_id: 2,
    user_id: 11,
    username: 'practitioner2',
    email: 'practitioner2@example.com',
    full_name: 'Jane Practitioner',
    professional_title: 'Tarot Reader',
    bio: 'Short bio',
    specializations: [],
    experience_years: 5,
    certification_details: {
      certification_type: 'certificate',
      issuing_authority: 'Tarot Academy',
    },
    languages: ['english'],
    price_per_hour: 1500,
    created_at: '2024-01-20T10:00:00Z',
    verification_status: 'pending_verification',
    is_ready_for_verification: false,
  },
]

describe('AdminPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useAuth as jest.Mock).mockReturnValue(mockAuth)
    ;(useToast as jest.Mock).mockReturnValue(mockToast)
    
    // Mock API responses
    ;(apiClient.get as jest.Mock).mockImplementation((url: string) => {
      if (url === '/api/v1/auth/profile') {
        return Promise.resolve({ is_admin: true })
      }
      if (url === '/api/v1/admin/stats') {
        return Promise.resolve(mockStats)
      }
      if (url === '/api/v1/admin/users') {
        return Promise.resolve([])
      }
      if (url === '/api/v1/admin/pending-verifications') {
        return Promise.resolve(mockPendingPractitioners)
      }
      if (url === '/api/v1/admin/verification-stats') {
        return Promise.resolve(mockVerificationStats)
      }
      return Promise.reject(new Error('Unknown endpoint'))
    })
  })

  it('renders admin dashboard with tabs', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Users')).toBeInTheDocument()
    expect(screen.getByText('Verification')).toBeInTheDocument()
  })

  it('displays user stats when users tab is active', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Total Users')).toBeInTheDocument()
    })
    
    expect(screen.getByText('100')).toBeInTheDocument() // total_users
    expect(screen.getByText('250')).toBeInTheDocument() // total_charts
    expect(screen.getByText('120')).toBeInTheDocument() // completed_lessons
    expect(screen.getByText('500')).toBeInTheDocument() // total_chat_messages
  })

  it('switches to verification tab and displays verification stats', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Click verification tab
    const verificationTab = screen.getByText('Verification')
    fireEvent.click(verificationTab)
    
    await waitFor(() => {
      expect(screen.getByText('Total Practitioners')).toBeInTheDocument()
    })
    
    expect(screen.getByText('25')).toBeInTheDocument() // total_practitioners
    expect(screen.getByText('5')).toBeInTheDocument() // pending_verification
    expect(screen.getByText('18')).toBeInTheDocument() // verified
    expect(screen.getAllByText('2')).toHaveLength(2) // rejected count appears in badge and stat
  })

  it('displays pending practitioners in verification queue', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Switch to verification tab
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('John Practitioner')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Vedic Astrologer')).toBeInTheDocument()
    expect(screen.getByText('10 years')).toBeInTheDocument()
    expect(screen.getByText('Jane Practitioner')).toBeInTheDocument()
    expect(screen.getByText('Tarot Reader')).toBeInTheDocument()
  })

  it('shows ready status for complete practitioners', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Switch to verification tab
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      const readyElements = screen.getAllByText('Ready')
      expect(readyElements.length).toBeGreaterThan(0)
    })
    
    expect(screen.getByText('Incomplete')).toBeInTheDocument()
  })

  it('opens practitioner verification modal when review is clicked', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Switch to verification tab
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('John Practitioner')).toBeInTheDocument()
    })
    
    // Click review button
    const reviewButtons = screen.getAllByText('Review')
    fireEvent.click(reviewButtons[0])
    
    await waitFor(() => {
      expect(screen.getByText('Practitioner Verification')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Basic Information')).toBeInTheDocument()
    expect(screen.getByText('Professional Bio')).toBeInTheDocument()
    expect(screen.getAllByText('Specializations')).toHaveLength(2) // One in table, one in modal
    expect(screen.getByText('Certification Details')).toBeInTheDocument()
  })

  it('shows approve and reject buttons for ready practitioners', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Switch to verification tab and open modal
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('John Practitioner')).toBeInTheDocument()
    })
    
    const reviewButtons = screen.getAllByText('Review')
    fireEvent.click(reviewButtons[0])
    
    await waitFor(() => {
      expect(screen.getByText('Approve')).toBeInTheDocument()
    })
    
    expect(screen.getByText('Reject')).toBeInTheDocument()
  })

  it('shows incomplete profile warning for unready practitioners', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Switch to verification tab and open modal for incomplete practitioner
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('Jane Practitioner')).toBeInTheDocument()
    })
    
    const reviewButtons = screen.getAllByText('Review')
    fireEvent.click(reviewButtons[1]) // Second practitioner (incomplete)
    
    await waitFor(() => {
      expect(screen.getByText('Profile Incomplete')).toBeInTheDocument()
    })
    
    expect(screen.getByText(/profile is not complete/i)).toBeInTheDocument()
  })

  it('handles practitioner approval', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValueOnce({
      success: true,
      message: 'Practitioner approved successfully',
    })
    
    // Mock window.prompt
    window.prompt = jest.fn().mockReturnValue('Great profile!')
    
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Navigate to verification and open modal
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('John Practitioner')).toBeInTheDocument()
    })
    
    const reviewButtons = screen.getAllByText('Review')
    fireEvent.click(reviewButtons[0])
    
    await waitFor(() => {
      expect(screen.getByText('Approve')).toBeInTheDocument()
    })
    
    // Click approve
    fireEvent.click(screen.getByText('Approve'))
    
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/admin/verify/1', {
        notes: 'Great profile!',
      })
    })
    
    expect(mockToast.showToast).toHaveBeenCalledWith(
      'Practitioner verified successfully',
      'success'
    )
  })

  it('handles practitioner rejection', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValueOnce({
      success: true,
      message: 'Practitioner rejected',
    })
    
    // Mock window.prompt for reason and notes
    window.prompt = jest.fn()
      .mockReturnValueOnce('Insufficient experience documentation')
      .mockReturnValueOnce('Please provide more details')
    
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Navigate to verification and open modal
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('John Practitioner')).toBeInTheDocument()
    })
    
    const reviewButtons = screen.getAllByText('Review')
    fireEvent.click(reviewButtons[0])
    
    await waitFor(() => {
      expect(screen.getByText('Reject')).toBeInTheDocument()
    })
    
    // Click reject
    fireEvent.click(screen.getByText('Reject'))
    
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/admin/reject/1', {
        reason: 'Insufficient experience documentation',
        notes: 'Please provide more details',
      })
    })
    
    expect(mockToast.showToast).toHaveBeenCalledWith('Practitioner rejected', 'success')
  })

  it('displays notification badge for pending verifications', async () => {
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Should show badge with pending count
    const badge = screen.getByText('2') // 2 pending practitioners
    expect(badge).toBeInTheDocument()
    expect(badge.closest('span')).toHaveClass('bg-red-500')
  })

  it('shows empty state when no practitioners are pending', async () => {
    ;(apiClient.get as jest.Mock).mockImplementation((url: string) => {
      if (url === '/api/v1/auth/profile') {
        return Promise.resolve({ is_admin: true })
      }
      if (url === '/api/v1/admin/stats') {
        return Promise.resolve(mockStats)
      }
      if (url === '/api/v1/admin/users') {
        return Promise.resolve([])
      }
      if (url === '/api/v1/admin/pending-verifications') {
        return Promise.resolve([]) // Empty array
      }
      if (url === '/api/v1/admin/verification-stats') {
        return Promise.resolve(mockVerificationStats)
      }
      return Promise.reject(new Error('Unknown endpoint'))
    })
    
    render(<AdminPage />)
    
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    })
    
    // Switch to verification tab
    fireEvent.click(screen.getByText('Verification'))
    
    await waitFor(() => {
      expect(screen.getByText('All caught up!')).toBeInTheDocument()
    })
    
    expect(screen.getByText(/no practitioners pending verification/i)).toBeInTheDocument()
  })
})