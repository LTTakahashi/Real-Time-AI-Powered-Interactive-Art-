type WebSocketEvent = 'message' | 'open' | 'close' | 'error'
type EventHandler = (data: any) => void

export class WebSocketClient {
    private url: string
    private ws: WebSocket | null = null
    private handlers: Record<WebSocketEvent, EventHandler[]> = {
        message: [],
        open: [],
        close: [],
        error: []
    }
    private reconnectAttempts = 0
    private maxReconnectAttempts = 5
    private reconnectTimeout: number | null = null
    private intentionallyClosed = false

    constructor(url: string) {
        this.url = url
    }

    connect() {
        // Clear any pending reconnection
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout)
            this.reconnectTimeout = null
        }

        try {
            this.ws = new WebSocket(this.url)

            this.ws.onopen = (event) => {
                this.reconnectAttempts = 0 // Reset on successful connection
                this.handlers.open.forEach(h => h(event))
            }

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    this.handlers.message.forEach(h => h(data))
                } catch (e) {
                    console.error('Failed to parse WebSocket message', e)
                }
            }

            this.ws.onclose = (event) => {
                this.handlers.close.forEach(h => h(event))

                // Auto-reconnect if not intentionally closed
                if (!this.intentionallyClosed && this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.min(1000 * (2 ** this.reconnectAttempts), 10000)
                    console.log(`WebSocket disconnected. Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`)

                    this.reconnectTimeout = window.setTimeout(() => {
                        this.reconnectAttempts++
                        this.connect()
                    }, delay)
                }
            }

            this.ws.onerror = (event) => {
                console.error('WebSocket error:', event)
                this.handlers.error.forEach(h => h(event))
            }
        } catch (error) {
            console.error('Failed to create WebSocket:', error)
            this.handlers.error.forEach(h => h(error))
        }
    }

    send(data: string) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data)
        } else {
            console.warn('WebSocket not connected')
        }
    }

    on(event: WebSocketEvent, handler: EventHandler) {
        this.handlers[event].push(handler)
    }

    off(event: WebSocketEvent, handler: EventHandler) {
        this.handlers[event] = this.handlers[event].filter(h => h !== handler)
    }

    disconnect() {
        this.intentionallyClosed = true

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout)
            this.reconnectTimeout = null
        }

        if (this.ws) {
            this.ws.close()
            this.ws = null
        }

        this.reconnectAttempts = 0
    }
}
