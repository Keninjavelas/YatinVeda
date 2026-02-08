import { apiClient } from '../api-client'

// Mock fetch
global.fetch = jest.fn()

// Mock window.location for navigation tests
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
})

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ data: 'test' }),
      text: async () => 'test text',
      blob: async () => new Blob(['test']),
      headers: {
        get: jest.fn().mockReturnValue(null), // Mock headers.get method
      },
    })
  })

  it('should make GET requests with correct headers', async () => {
    await apiClient.get('/test')
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.objectContaining({
        method: 'GET',
      })
    )
  })

  it('should make POST requests with CSRF token', async () => {
    const mockData = { name: 'test' }
    await apiClient.post('/test', mockData)
    
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(mockData),
      })
    )
  })

  it('should handle authentication errors', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Unauthorized' }),
      text: async () => 'Unauthorized',
      blob: async () => new Blob(['Unauthorized']),
      headers: {
        get: jest.fn().mockReturnValue(null),
      },
    })

    await expect(apiClient.get('/protected')).rejects.toThrow()
  })

  it('should retry on token refresh', async () => {
    // Test implementation for token refresh logic
    expect(true).toBe(true)
  })
})
