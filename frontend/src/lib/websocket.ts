const WS_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000').replace('http://', 'ws://').replace('https://', 'wss://')

export type SocketEventHandler = (event: MessageEvent) => void

export class PractitionerSocketClient {
  private socket: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private readonly token: string
  private readonly onMessage: SocketEventHandler

  constructor(token: string, onMessage: SocketEventHandler) {
    this.token = token
    this.onMessage = onMessage
  }

  connect() {
    const url = `${WS_BASE_URL}/api/v1/ws/connect?token=${encodeURIComponent(this.token)}`
    this.socket = new WebSocket(url)

    this.socket.onmessage = this.onMessage
    this.socket.onclose = () => {
      this.reconnectTimer = setTimeout(() => this.connect(), 3000)
    }
  }

  send(message: string) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(message)
    }
  }

  close() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.socket?.close()
    this.socket = null
  }
}
