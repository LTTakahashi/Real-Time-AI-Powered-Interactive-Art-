import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

// Mock sub-components to avoid complex setup
vi.mock('./components/WebcamFeed', () => ({
    default: () => <div data-testid="mock-webcam">Webcam</div>
}))
vi.mock('./components/DrawingCanvas', () => ({
    default: () => <div data-testid="mock-canvas">Canvas</div>
}))
// Mock WebSocketClient
vi.mock('./services/WebSocketClient', () => ({
    WebSocketClient: vi.fn(function () {
        return {
            connect: vi.fn(),
            disconnect: vi.fn(),
            on: vi.fn(),
            send: vi.fn()
        }
    })
}))

describe('App', () => {
    beforeEach(() => {
        // Mock fetch for generate
        global.fetch = vi.fn()
    })

    it('should render main UI elements', () => {
        render(<App />)
        expect(screen.getByText('GestureCanvas')).toBeInTheDocument()
        expect(screen.getByText('GENERATE')).toBeInTheDocument()
        expect(screen.getByTestId('mock-webcam')).toBeInTheDocument()
    })
})
