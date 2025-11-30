import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { WebSocketClient } from './WebSocketClient'

describe('WebSocketClient', () => {
    let client: WebSocketClient
    let mockWs: any

    beforeEach(() => {
        // Mock WebSocket
        mockWs = {
            send: vi.fn(),
            close: vi.fn(),
            onopen: null,
            onmessage: null,
            onclose: null,
            onerror: null,
            readyState: WebSocket.OPEN
        }

        global.WebSocket = vi.fn(function () { return mockWs }) as any


        client = new WebSocketClient('ws://test')
    })

    afterEach(() => {
        vi.clearAllMocks()
    })

    it('should connect to the correct URL', () => {
        client.connect()
        expect(global.WebSocket).toHaveBeenCalledWith('ws://test')
    })

    it('should send messages', () => {
        client.connect()
        // Simulate open
        if (mockWs.onopen) mockWs.onopen({} as any)

        client.send('test message')
        expect(mockWs.send).toHaveBeenCalledWith('test message')
    })

    it('should handle incoming messages', () => {
        const onMessage = vi.fn()
        client.on('message', onMessage)
        client.connect()

        // Simulate message
        const data = JSON.stringify({ gesture: 'POINTING' })
        if (mockWs.onmessage) mockWs.onmessage({ data } as any)

        expect(onMessage).toHaveBeenCalledWith({ gesture: 'POINTING' })
    })

    it('should handle disconnection', () => {
        const onClose = vi.fn()
        client.on('close', onClose)
        client.connect()

        if (mockWs.onclose) mockWs.onclose({} as any)

        expect(onClose).toHaveBeenCalled()
    })
})
