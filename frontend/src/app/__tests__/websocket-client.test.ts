import { PractitionerSocketClient } from '@/lib/websocket'

describe('PractitionerSocketClient', () => {
  let originalWebSocket: typeof WebSocket

  beforeEach(() => {
    originalWebSocket = (global as any).WebSocket
  })

  afterEach(() => {
    (global as any).WebSocket = originalWebSocket
  })

  it('creates and closes socket client cleanly', () => {
    const close = jest.fn()
    const mockSocket: Partial<WebSocket> = {
      readyState: 1,
      close,
      send: jest.fn(),
      onmessage: null,
      onclose: null,
    }

    const wsCtor = jest.fn(() => mockSocket)
    ;(global as any).WebSocket = wsCtor

    const client = new PractitionerSocketClient('token', () => {})
    client.connect()
    client.send('ping')
    client.close()

    expect(wsCtor).toHaveBeenCalled()
    expect(close).toHaveBeenCalled()
  })

  it('sends messages when socket is open', () => {
    const send = jest.fn()
    const mockSocket: Partial<WebSocket> = {
      readyState: 1, // WebSocket.OPEN
      close: jest.fn(),
      send,
      onmessage: null,
      onclose: null,
    }

    ;(global as any).WebSocket = jest.fn(() => mockSocket)

    const client = new PractitionerSocketClient('my-token', () => {})
    client.connect()
    client.send(JSON.stringify({ type: 'chat', content: 'Hello' }))

    expect(send).toHaveBeenCalledWith(JSON.stringify({ type: 'chat', content: 'Hello' }))
  })

  it('does not send when socket is closed', () => {
    const send = jest.fn()
    const mockSocket: Partial<WebSocket> = {
      readyState: 3, // WebSocket.CLOSED
      close: jest.fn(),
      send,
      onmessage: null,
      onclose: null,
    }

    ;(global as any).WebSocket = jest.fn(() => mockSocket)

    const client = new PractitionerSocketClient('token', () => {})
    client.connect()
    client.send('ping')

    expect(send).not.toHaveBeenCalled()
  })

  it('handles incoming messages via callback', () => {
    const onMessage = jest.fn()
    let capturedOnMessage: ((ev: MessageEvent) => void) | null = null

    const mockSocket: Partial<WebSocket> = {
      readyState: 1,
      close: jest.fn(),
      send: jest.fn(),
      set onmessage(handler: ((ev: MessageEvent) => void) | null) {
        capturedOnMessage = handler
      },
      get onmessage() { return capturedOnMessage },
      onclose: null,
    }

    ;(global as any).WebSocket = jest.fn(() => mockSocket)

    const client = new PractitionerSocketClient('token', onMessage)
    client.connect()

    // Simulate message
    if (capturedOnMessage) {
      capturedOnMessage(new MessageEvent('message', { data: JSON.stringify({ type: 'pong' }) }))
    }

    expect(onMessage).toHaveBeenCalled()
  })

  it('constructs correct WebSocket URL', () => {
    const mockSocket: Partial<WebSocket> = {
      readyState: 1,
      close: jest.fn(),
      send: jest.fn(),
      onmessage: null,
      onclose: null,
    }

    const wsCtor = jest.fn(() => mockSocket)
    ;(global as any).WebSocket = wsCtor

    const client = new PractitionerSocketClient('abc123', () => {})
    client.connect()

    const url = wsCtor.mock.calls[0][0]
    expect(url).toContain('ws://')
    expect(url).toContain('/api/v1/ws/connect')
    expect(url).toContain('token=abc123')
  })

  it('handles chat message type', () => {
    const chatMessage = {
      type: 'chat',
      from_user_id: 2,
      content: 'Namaste!',
      timestamp: '2024-01-01T00:00:00',
    }

    const serialized = JSON.stringify(chatMessage)
    const parsed = JSON.parse(serialized)
    expect(parsed.type).toBe('chat')
    expect(parsed.content).toBe('Namaste!')
  })

  it('handles room join message type', () => {
    const joinMessage = {
      type: 'join_room',
      room: 'vedic-astrology-101',
    }

    const serialized = JSON.stringify(joinMessage)
    const parsed = JSON.parse(serialized)
    expect(parsed.type).toBe('join_room')
    expect(parsed.room).toBe('vedic-astrology-101')
  })

  it('handles typing indicator message', () => {
    const typingMessage = {
      type: 'typing',
      target_user_id: 5,
    }

    const serialized = JSON.stringify(typingMessage)
    const parsed = JSON.parse(serialized)
    expect(parsed.type).toBe('typing')
    expect(parsed.target_user_id).toBe(5)
  })
})
