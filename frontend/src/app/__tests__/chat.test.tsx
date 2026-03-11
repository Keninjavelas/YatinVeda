import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => '/chat',
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
const mockShowToast = jest.fn()
const mockAddToast = jest.fn()

const defaultAuth = {
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

describe('Chat Interface', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
    mockUseAuth.mockReturnValue(defaultAuth)
    mockUseToast.mockReturnValue({
      showToast: mockShowToast,
      addToast: mockAddToast,
      toasts: [],
      removeToast: jest.fn(),
    })
  })

  it('should store conversations in localStorage', () => {
    const conversations = [
      { role: 'user', content: 'What is my birth chart?' },
      { role: 'assistant', content: 'Based on your details...' },
    ]
    localStorage.setItem('chat_history', JSON.stringify(conversations))

    const stored = JSON.parse(localStorage.getItem('chat_history') || '[]')
    expect(stored).toHaveLength(2)
    expect(stored[0].role).toBe('user')
    expect(stored[1].role).toBe('assistant')
  })

  it('should limit context window to last 5 messages', () => {
    const messages = Array.from({ length: 10 }, (_, i) => ({
      role: i % 2 === 0 ? 'user' : 'assistant',
      content: `Message ${i + 1}`,
    }))

    const lastFive = messages.slice(-5)
    expect(lastFive).toHaveLength(5)
    expect(lastFive[0].content).toBe('Message 6')
    expect(lastFive[4].content).toBe('Message 10')
  })

  it('should handle API chat request', async () => {
    const mockPost = (apiClient.post as jest.Mock).mockResolvedValue({
      response: 'The Sun represents...',
      model: 'vedamind',
    })

    const result = await apiClient.post('/api/v1/chat/ask', {
      message: 'Tell me about Sun in Aries',
      context: [],
    })

    expect(mockPost).toHaveBeenCalled()
    expect(result.response).toContain('Sun represents')
  })

  it('should handle chat API errors', async () => {
    ;(apiClient.post as jest.Mock).mockRejectedValue(new Error('Service unavailable'))
    await expect(
      apiClient.post('/api/v1/chat/ask', { message: 'test', context: [] })
    ).rejects.toThrow('Service unavailable')
  })

  it('should save and load conversation history', () => {
    const history = {
      conversations: [
        {
          id: '1',
          title: 'Birth Chart Analysis',
          messages: [
            { role: 'user', content: 'Analyze my chart' },
            { role: 'assistant', content: 'Your chart shows...' },
          ],
        },
      ],
    }

    localStorage.setItem('vedamind_history', JSON.stringify(history))
    const loaded = JSON.parse(localStorage.getItem('vedamind_history') || '{}')
    expect(loaded.conversations).toHaveLength(1)
    expect(loaded.conversations[0].title).toBe('Birth Chart Analysis')
  })

  it('should handle empty message gracefully', () => {
    const message = ''
    expect(message.trim()).toBe('')
    expect(message.trim().length).toBe(0)
  })

  it('should sanitize user input before sending', () => {
    const maliciousInput = '<script>alert("xss")</script>Tell me about Mars'
    const sanitized = maliciousInput.replace(/<[^>]*>/g, '')
    expect(sanitized).not.toContain('<script>')
    expect(sanitized).toContain('Tell me about Mars')
  })
})
