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

    constructor(url: string) {
        this.url = url
    }

    connect() {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = (event) => {
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
        }

        this.ws.onerror = (event) => {
            this.handlers.error.forEach(h => h(event))
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
        if (this.ws) {
            this.ws.close()
            this.ws = null
        }
    }
}
