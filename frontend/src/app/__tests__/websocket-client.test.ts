import { PractitionerSocketClient } from '@/lib/websocket'

describe('PractitionerSocketClient', () => {
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
})
