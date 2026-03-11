import { apiClient } from '@/lib/api-client'

jest.mock('@/lib/api-client')

describe('Search API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should perform global search', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      results: [
        { type: 'user', id: 1, title: 'Test User', snippet: 'Vedic astrologer' },
        { type: 'post', id: 5, title: 'Mars Transit', snippet: 'Mars in Aries...' },
      ],
      total: 2,
    })

    const result = await apiClient.get('/api/v1/search/global?q=vedic')
    expect(result.results).toHaveLength(2)
    expect(result.total).toBe(2)
  })

  it('should handle search autocomplete', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      suggestions: ['vedic astrology', 'vedic chart', 'vedic remedies'],
    })

    const result = await apiClient.get('/api/v1/search/autocomplete?q=vedi')
    expect(result.suggestions).toHaveLength(3)
    expect(result.suggestions[0]).toContain('vedic')
  })

  it('should handle empty search results', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue({ results: [], total: 0 })

    const result = await apiClient.get('/api/v1/search/global?q=nonexistent')
    expect(result.results).toHaveLength(0)
    expect(result.total).toBe(0)
  })
})

describe('Calculations API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should generate birth chart', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      ascendant: { sign: 'Aries', degree: 15.5 },
      planets: [
        { name: 'Sun', sign: 'Leo', degree: 22.3, house: 5, nakshatra: 'Magha' },
        { name: 'Moon', sign: 'Cancer', degree: 10.1, house: 4, nakshatra: 'Pushya' },
      ],
      houses: Array.from({ length: 12 }, (_, i) => ({ house: i + 1, sign: 'Aries' })),
    })

    const chart = await apiClient.post('/api/v1/calculations/chart', {
      date: '1990-05-15',
      time: '14:30',
      latitude: 28.6139,
      longitude: 77.2090,
    })

    expect(chart.ascendant.sign).toBe('Aries')
    expect(chart.planets).toHaveLength(2)
    expect(chart.houses).toHaveLength(12)
  })

  it('should calculate compatibility', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      total_score: 28,
      max_score: 36,
      compatibility_percentage: 77.8,
      aspects: [
        { name: 'Varna', score: 1, max: 1 },
        { name: 'Vashya', score: 2, max: 2 },
        { name: 'Nadi', score: 8, max: 8 },
      ],
    })

    const result = await apiClient.post('/api/v1/calculations/compatibility', {
      person1: { date: '1990-05-15', time: '14:30', lat: 28.6, lon: 77.2 },
      person2: { date: '1992-08-20', time: '09:00', lat: 19.0, lon: 72.8 },
    })

    expect(result.total_score).toBe(28)
    expect(result.compatibility_percentage).toBeGreaterThan(70)
  })

  it('should calculate dasha periods', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      maha_dasha: 'Venus',
      antar_dasha: 'Jupiter',
      periods: [
        { planet: 'Venus', start: '2020-01-01', end: '2040-01-01', years: 20 },
        { planet: 'Sun', start: '2040-01-01', end: '2046-01-01', years: 6 },
      ],
    })

    const result = await apiClient.post('/api/v1/calculations/dasha', {
      moon_nakshatra: 'Rohini',
      birth_date: '1990-05-15',
    })

    expect(result.maha_dasha).toBe('Venus')
    expect(result.periods).toHaveLength(2)
  })
})

describe('Remedies API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should fetch remedy recommendations', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      remedies: [
        { planet: 'Saturn', type: 'gemstone', name: 'Blue Sapphire', description: 'Wear on middle finger' },
        { planet: 'Rahu', type: 'mantra', name: 'Rahu Mantra', description: 'Chant 108 times' },
      ],
    })

    const result = await apiClient.post('/api/v1/remedies/recommend', {
      chart_data: { ascendant: 'Aries', planets: [] },
      concerns: ['career', 'health'],
    })

    expect(result.remedies).toHaveLength(2)
    expect(result.remedies[0].type).toBe('gemstone')
  })

  it('should fetch remedy categories', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      categories: ['gemstone', 'mantra', 'yantra', 'ritual', 'charity', 'lifestyle'],
    })

    const result = await apiClient.get('/api/v1/remedies/categories')
    expect(result.categories).toContain('gemstone')
    expect(result.categories).toContain('mantra')
  })

  it('should create tracking plan', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      plan_id: 'plan-123',
      remedies: [{ id: 1, name: 'Sun Mantra', frequency: 'daily', target_days: 40 }],
    })

    const result = await apiClient.post('/api/v1/remedies/tracking-plan', {
      remedy_ids: [1, 2, 3],
    })

    expect(result.plan_id).toBe('plan-123')
  })
})

describe('Stripe Payments API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should create checkout session', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      checkout_url: 'https://checkout.stripe.com/session_123',
      session_id: 'session_123',
    })

    const result = await apiClient.post('/api/v1/stripe/checkout', {
      amount: 1500,
      currency: 'inr',
      description: 'Guru consultation',
    })

    expect(result.checkout_url).toContain('stripe.com')
    expect(result.session_id).toBeTruthy()
  })

  it('should create payment intent', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      client_secret: 'pi_secret_123',
      payment_intent_id: 'pi_123',
    })

    const result = await apiClient.post('/api/v1/stripe/payment-intent', {
      amount: 2000,
      currency: 'inr',
    })

    expect(result.client_secret).toBeTruthy()
  })

  it('should handle payment failure', async () => {
    ;(apiClient.post as jest.Mock).mockRejectedValue({
      response: { status: 402, data: { detail: 'Card declined' } },
    })

    await expect(
      apiClient.post('/api/v1/stripe/checkout', { amount: 1500 })
    ).rejects.toEqual(expect.objectContaining({
      response: expect.objectContaining({ status: 402 }),
    }))
  })
})

describe('Social Sharing API', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should generate share data', async () => {
    ;(apiClient.post as jest.Mock).mockResolvedValue({
      share_text: 'Check out my Vedic chart on YatinVeda!',
      share_url: 'https://yatinveda.com/share/abc123',
      platforms: {
        twitter: 'https://twitter.com/intent/tweet?text=...',
        whatsapp: 'https://wa.me/?text=...',
      },
    })

    const result = await apiClient.post('/api/v1/share/generate', {
      content_type: 'chart',
      content_id: 1,
    })

    expect(result.share_url).toContain('yatinveda')
    expect(result.platforms).toHaveProperty('twitter')
    expect(result.platforms).toHaveProperty('whatsapp')
  })

  it('should list available platforms', async () => {
    ;(apiClient.get as jest.Mock).mockResolvedValue({
      platforms: ['twitter', 'facebook', 'whatsapp', 'linkedin', 'email'],
    })

    const result = await apiClient.get('/api/v1/share/platforms')
    expect(result.platforms).toContain('whatsapp')
    expect(result.platforms.length).toBeGreaterThanOrEqual(3)
  })
})
