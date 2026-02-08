/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter, useSearchParams } from 'next/navigation'
import LoginPage from '../page'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'

// Mock the dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}))

jest.mock('@/lib/auth-context', () => ({
  useAuth: jest.fn(),
}))

jest.mock('@/lib/toast-context', () => ({
  useToast: jest.fn(),
}))

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
}

const mockSearchParams = {
  get: jest.fn(),
}

const mockAuth = {
  login: jest.fn(),
  isAuthenticated: false,
  user: null,
}

const mockToast = {
  addToast: jest.fn(),
}

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useSearchParams as jest.Mock).mockReturnValue(mockSearchParams)
    ;(useAuth as jest.Mock).mockReturnValue(mockAuth)
    ;(useToast as jest.Mock).mockReturnValue(mockToast)
    mockSearchParams.get.mockReturnValue('/dashboard')
  })

  it('renders login form', () => {
    render(<LoginPage />)
    
    expect(screen.getByLabelText(/email or username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('handles form submission', async () => {
    mockAuth.login.mockResolvedValueOnce(undefined)
    
    render(<LoginPage />)
    
    const emailInput = screen.getByLabelText(/email or username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(mockAuth.login).toHaveBeenCalledWith('test@example.com', 'password123')
    })
  })

  it('displays error message on login failure', async () => {
    const errorMessage = 'Invalid credentials'
    mockAuth.login.mockRejectedValueOnce(new Error(errorMessage))
    
    render(<LoginPage />)
    
    const emailInput = screen.getByLabelText(/email or username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
      expect(mockToast.addToast).toHaveBeenCalledWith(errorMessage, 'error', 4000)
    })
  })

  it('redirects admin users to admin dashboard', () => {
    const adminUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      full_name: 'Admin User',
      is_admin: true,
      role: 'user',
      verification_status: 'active'
    }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      ...mockAuth,
      isAuthenticated: true,
      user: adminUser,
    })
    
    render(<LoginPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/admin')
  })

  it('redirects regular users to dashboard', () => {
    const regularUser = {
      id: 1,
      username: 'user',
      email: 'user@example.com',
      full_name: 'Regular User',
      is_admin: false,
      role: 'user',
      verification_status: 'active'
    }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      ...mockAuth,
      isAuthenticated: true,
      user: regularUser,
    })
    
    render(<LoginPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/dashboard')
  })

  it('redirects verified practitioners to dashboard', () => {
    const verifiedPractitioner = {
      id: 1,
      username: 'practitioner',
      email: 'practitioner@example.com',
      full_name: 'Verified Practitioner',
      is_admin: false,
      role: 'practitioner',
      verification_status: 'verified'
    }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      ...mockAuth,
      isAuthenticated: true,
      user: verifiedPractitioner,
    })
    
    render(<LoginPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/dashboard')
  })

  it('redirects pending practitioners to profile with verification message', () => {
    const pendingPractitioner = {
      id: 1,
      username: 'practitioner',
      email: 'practitioner@example.com',
      full_name: 'Pending Practitioner',
      is_admin: false,
      role: 'practitioner',
      verification_status: 'pending_verification'
    }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      ...mockAuth,
      isAuthenticated: true,
      user: pendingPractitioner,
    })
    
    render(<LoginPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/profile?tab=verification')
    expect(mockToast.addToast).toHaveBeenCalledWith(
      'Your account is pending verification. Please complete your profile.',
      'info',
      5000
    )
  })

  it('redirects rejected practitioners to profile with warning message', () => {
    const rejectedPractitioner = {
      id: 1,
      username: 'practitioner',
      email: 'practitioner@example.com',
      full_name: 'Rejected Practitioner',
      is_admin: false,
      role: 'practitioner',
      verification_status: 'rejected'
    }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      ...mockAuth,
      isAuthenticated: true,
      user: rejectedPractitioner,
    })
    
    render(<LoginPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/profile?tab=verification')
    expect(mockToast.addToast).toHaveBeenCalledWith(
      'Your verification was rejected. Please update your information and resubmit.',
      'warning',
      5000
    )
  })

  it('shows password visibility toggle', () => {
    render(<LoginPage />)
    
    const passwordInput = screen.getByLabelText(/password/i)
    const toggleButton = passwordInput.parentElement?.querySelector('button')
    
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    // Click toggle
    fireEvent.click(toggleButton!)
    
    expect(passwordInput).toHaveAttribute('type', 'text')
  })

  it('disables form during submission', async () => {
    mockAuth.login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)))
    
    render(<LoginPage />)
    
    const emailInput = screen.getByLabelText(/email or username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)
    
    // Form should be disabled during submission
    expect(submitButton).toBeDisabled()
    expect(emailInput).toBeDisabled()
    expect(passwordInput).toBeDisabled()
    expect(screen.getByText(/signing in/i)).toBeInTheDocument()
    
    await waitFor(() => {
      expect(mockAuth.login).toHaveBeenCalled()
    })
  })

  it('uses callback URL for regular users when provided', () => {
    mockSearchParams.get.mockImplementation((key) => {
      if (key === 'callbackUrl') return '/custom-redirect'
      return null
    })
    
    const regularUser = {
      id: 1,
      username: 'user',
      email: 'user@example.com',
      full_name: 'Regular User',
      is_admin: false,
      role: 'user',
      verification_status: 'active'
    }
    
    ;(useAuth as jest.Mock).mockReturnValue({
      ...mockAuth,
      isAuthenticated: true,
      user: regularUser,
    })
    
    render(<LoginPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/custom-redirect')
  })

  it('has links to signup and forgot password', () => {
    render(<LoginPage />)
    
    expect(screen.getByRole('link', { name: /create one/i })).toHaveAttribute('href', '/signup')
    expect(screen.getByRole('link', { name: /forgot password/i })).toHaveAttribute('href', '/forgot-password')
  })
})