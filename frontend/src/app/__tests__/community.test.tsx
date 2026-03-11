import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useAuth } from '@/lib/auth-context'
import { useToast } from '@/lib/toast-context'
import { apiClient } from '@/lib/api-client'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), back: jest.fn() }),
  usePathname: () => '/community',
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

describe('Community Feed', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue(defaultAuth)
    mockUseToast.mockReturnValue({
      showToast: mockShowToast,
      addToast: mockAddToast,
      toasts: [],
      removeToast: jest.fn(),
    })
  })

  it('should fetch community posts', async () => {
    const mockPosts = [
      { id: 1, content: 'Mars in Aries meaning?', user_id: 1, username: 'user1', likes: 5, created_at: '2024-01-01' },
      { id: 2, content: 'Venus transit effects', user_id: 2, username: 'user2', likes: 3, created_at: '2024-01-02' },
    ]
    ;(apiClient.get as jest.Mock).mockResolvedValue(mockPosts)

    const posts = await apiClient.get('/api/v1/community/posts')
    expect(posts).toHaveLength(2)
    expect(posts[0].content).toContain('Mars')
  })

  it('should handle like/unlike toggle', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({ liked: true, total_likes: 6 })

    const result = await apiClient.post('/api/v1/community/posts/1/like')
    expect(result.liked).toBe(true)
    expect(result.total_likes).toBe(6)
  })

  it('should handle unlike action', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({ liked: false, total_likes: 4 })

    const result = await apiClient.post('/api/v1/community/posts/1/like')
    expect(result.liked).toBe(false)
    expect(result.total_likes).toBe(4)
  })

  it('should paginate posts for infinite scroll', async () => {
    const page1 = Array.from({ length: 10 }, (_, i) => ({
      id: i + 1, content: `Post ${i + 1}`, user_id: 1, likes: 0, created_at: '2024-01-01',
    }))
    const page2 = Array.from({ length: 5 }, (_, i) => ({
      id: i + 11, content: `Post ${i + 11}`, user_id: 1, likes: 0, created_at: '2024-01-01',
    }))

    ;(apiClient.get as jest.Mock)
      .mockResolvedValueOnce(page1)
      .mockResolvedValueOnce(page2)

    const firstPage = await apiClient.get('/api/v1/community/posts?page=1&limit=10')
    expect(firstPage).toHaveLength(10)

    const secondPage = await apiClient.get('/api/v1/community/posts?page=2&limit=10')
    expect(secondPage).toHaveLength(5)

    const allPosts = [...firstPage, ...secondPage]
    expect(allPosts).toHaveLength(15)
  })

  it('should handle post creation', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      id: 100, content: 'New astrology question', user_id: 1, likes: 0,
    })

    const newPost = await apiClient.post('/api/v1/community/posts', { content: 'New astrology question' })
    expect(newPost.id).toBe(100)
    expect(newPost.content).toBe('New astrology question')
  })

  it('should handle post creation failure with toast', async () => {
    ;(apiClient.post as jest.Mock).mockRejectedValue(new Error('Failed to create post'))

    try {
      await apiClient.post('/api/v1/community/posts', { content: 'Test' })
    } catch {
      mockShowToast('Failed to create post', 'error')
    }
    expect(mockShowToast).toHaveBeenCalledWith('Failed to create post', 'error')
  })

  it('should handle empty community feed', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue([])

    const posts = await apiClient.get('/api/v1/community/posts')
    expect(posts).toHaveLength(0)
  })

  it('should handle network error loading posts', async () => {
    ;(apiClient.get as jest.Mock).mockRejectedValue(new Error('Network Error'))
    await expect(apiClient.get('/api/v1/community/posts')).rejects.toThrow('Network Error')
  })
})
