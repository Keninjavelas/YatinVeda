/**
 * @jest-environment jsdom
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import SignUpPage from '../page'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'

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

jest.mock('next/image', () => ({
  __esModule: true,
  default: ({ src, alt, fill, priority, ...props }: any) => (
    <img 
      src={src} 
      alt={alt} 
      {...props}
      // Don't pass fill and priority to DOM img element
    />
  ),
}))

// Mock fetch
global.fetch = jest.fn()

const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
}

const mockAuth = {
  isAuthenticated: false,
}

const mockToast = {
  showToast: jest.fn(),
}

describe('SignUpPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue(mockRouter)
    ;(useAuth as jest.Mock).mockReturnValue(mockAuth)
    ;(useToast as jest.Mock).mockReturnValue(mockToast)
    ;(global.fetch as jest.Mock).mockClear()
  })

  it('renders role selection by default', () => {
    render(<SignUpPage />)
    
    expect(screen.getByText('Choose Your Account Type')).toBeInTheDocument()
    expect(screen.getByText('Regular User')).toBeInTheDocument()
    expect(screen.getByText('Practitioner')).toBeInTheDocument()
  })

  it('shows basic information form', () => {
    render(<SignUpPage />)
    
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
  })

  it('allows role selection between user and practitioner', () => {
    render(<SignUpPage />)
    
    const userButton = screen.getByText('Regular User').closest('button')
    const practitionerButton = screen.getByText('Practitioner').closest('button')
    
    expect(userButton).toBeInTheDocument()
    expect(practitionerButton).toBeInTheDocument()
    
    // Click practitioner role
    fireEvent.click(practitionerButton!)
    
    // Should show step indicator for practitioners
    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
  })

  it('validates password requirements', async () => {
    render(<SignUpPage />)
    
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    // Fill in form with weak password
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'weak' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'weak' } })
    
    // For regular users, there's no Next button - they submit directly
    const submitButton = screen.getByText('🚀 Create Account')
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/password must be at least 8 characters/i)).toBeInTheDocument()
    })
  })

  it('validates password confirmation match', async () => {
    render(<SignUpPage />)
    
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    // Fill in form with mismatched passwords
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'DifferentPassword123' } })
    
    // For regular users, there's no Next button - they submit directly
    const submitButton = screen.getByText('🚀 Create Account')
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('shows practitioner-specific fields when practitioner role is selected', async () => {
    render(<SignUpPage />)
    
    // Select practitioner role
    const practitionerButton = screen.getByText('Practitioner').closest('button')
    fireEvent.click(practitionerButton!)
    
    // Fill basic info
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    fireEvent.change(nameInput, { target: { value: 'Test Practitioner' } })
    fireEvent.change(emailInput, { target: { value: 'practitioner@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'ValidPassword123' } })
    
    // Go to next step
    const nextButton = screen.getByText('Next')
    fireEvent.click(nextButton)
    
    await waitFor(() => {
      expect(screen.getByText('Professional Information')).toBeInTheDocument()
      expect(screen.getByLabelText(/professional title/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/professional bio/i)).toBeInTheDocument()
      expect(screen.getByText(/specializations/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/experience.*years/i)).toBeInTheDocument()
    })
  })

  it('validates practitioner bio minimum length', async () => {
    render(<SignUpPage />)
    
    // Select practitioner role and fill basic info
    const practitionerButton = screen.getByText('Practitioner').closest('button')
    fireEvent.click(practitionerButton!)
    
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    fireEvent.change(nameInput, { target: { value: 'Test Practitioner' } })
    fireEvent.change(emailInput, { target: { value: 'practitioner@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'ValidPassword123' } })
    
    // Go to professional info step
    fireEvent.click(screen.getByText('Next'))
    
    await waitFor(() => {
      expect(screen.getByText('Professional Information')).toBeInTheDocument()
    })
    
    // Fill professional info with short bio but complete other required fields
    const titleInput = screen.getByLabelText(/professional title/i)
    const bioInput = screen.getByLabelText(/professional bio/i)
    const experienceInput = screen.getByLabelText(/experience.*years/i)
    
    fireEvent.change(titleInput, { target: { value: 'Vedic Astrologer' } })
    fireEvent.change(bioInput, { target: { value: 'Short bio' } }) // Less than 50 characters
    fireEvent.change(experienceInput, { target: { value: '5' } })
    
    // Select a specialization (required)
    const vedicAstrologyButton = screen.getByText('Vedic Astrology')
    fireEvent.click(vedicAstrologyButton)
    
    // The Next button should be disabled because bio is too short
    const nextButton = screen.getByText('Next')
    expect(nextButton).toBeDisabled()
    
    // Character counter should show the current length
    expect(screen.getByText(/9\/50 characters minimum/)).toBeInTheDocument()
  })

  it('allows specialization selection', async () => {
    render(<SignUpPage />)
    
    // Navigate to practitioner professional info
    const practitionerButton = screen.getByText('Practitioner').closest('button')
    fireEvent.click(practitionerButton!)
    
    // Fill basic info and proceed
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    fireEvent.change(nameInput, { target: { value: 'Test Practitioner' } })
    fireEvent.change(emailInput, { target: { value: 'practitioner@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'ValidPassword123' } })
    
    fireEvent.click(screen.getByText('Next'))
    
    await waitFor(() => {
      expect(screen.getByText('Professional Information')).toBeInTheDocument()
    })
    
    // Check that specializations are available
    expect(screen.getByText('Vedic Astrology')).toBeInTheDocument()
    expect(screen.getByText('Tarot Reading')).toBeInTheDocument()
    expect(screen.getByText('Numerology')).toBeInTheDocument()
    
    // Select a specialization
    const vedicAstrologyButton = screen.getByText('Vedic Astrology')
    fireEvent.click(vedicAstrologyButton)
    
    // Button should be selected (have different styling)
    expect(vedicAstrologyButton.closest('button')).toHaveClass('border-purple-500')
  })

  it('submits user registration successfully', async () => {
    const mockResponse = {
      ok: true,
      json: async () => ({
        message: 'User registered successfully',
        access_token: 'mock-token',
        user_id: 1,
        role: 'user'
      })
    }
    ;(global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse)
    
    render(<SignUpPage />)
    
    // Fill form for regular user
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'ValidPassword123' } })
    
    // Submit form
    const createButton = screen.getByText('🚀 Create Account')
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/register',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('"role":"user"')
        })
      )
    })
    
    await waitFor(() => {
      expect(screen.getByText('Account created! Redirecting to login...')).toBeInTheDocument()
    })
  })

  it('handles registration errors gracefully', async () => {
    const mockResponse = {
      ok: false,
      status: 400,
      json: async () => ({
        detail: 'Email already registered'
      })
    }
    ;(global.fetch as jest.Mock).mockResolvedValueOnce(mockResponse)
    
    render(<SignUpPage />)
    
    // Fill form
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    fireEvent.change(emailInput, { target: { value: 'existing@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'ValidPassword123' } })
    
    // Submit form
    const createButton = screen.getByText('🚀 Create Account')
    fireEvent.click(createButton)
    
    await waitFor(() => {
      expect(screen.getByText(/email already registered/i)).toBeInTheDocument()
    })
  })

  it('redirects authenticated users to dashboard', () => {
    ;(useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
    })
    
    render(<SignUpPage />)
    
    expect(mockRouter.replace).toHaveBeenCalledWith('/dashboard')
  })

  it('shows password visibility toggle', () => {
    render(<SignUpPage />)
    
    const passwordInput = screen.getByLabelText(/^password/i)
    const toggleButton = passwordInput.parentElement?.querySelector('button')
    
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    // Click toggle
    fireEvent.click(toggleButton!)
    
    expect(passwordInput).toHaveAttribute('type', 'text')
  })

  it('validates required fields before allowing form submission', () => {
    render(<SignUpPage />)
    
    const createButton = screen.getByText('🚀 Create Account')
    
    // Button should be disabled when fields are empty
    expect(createButton).toBeDisabled()
    
    // Fill required fields
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email address/i)
    const passwordInput = screen.getByLabelText(/^password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    
    fireEvent.change(nameInput, { target: { value: 'Test User' } })
    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'ValidPassword123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'ValidPassword123' } })
    
    // Button should now be enabled
    expect(createButton).not.toBeDisabled()
  })
})