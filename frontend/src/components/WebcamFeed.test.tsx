import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import WebcamFeed from './WebcamFeed'

describe('WebcamFeed', () => {
    beforeEach(() => {
        // Mock getUserMedia
        Object.defineProperty(global.navigator, 'mediaDevices', {
            value: {
                getUserMedia: vi.fn().mockResolvedValue({
                    getTracks: () => [{ stop: vi.fn() }]
                })
            },
            writable: true
        })

        // Mock HTMLMediaElement.play
        window.HTMLMediaElement.prototype.play = vi.fn()
    })

    afterEach(() => {
        vi.clearAllMocks()
    })

    it('should render video element', () => {
        render(<WebcamFeed onFrame={() => { }} />)
        const video = screen.getByTestId('webcam-video')
        expect(video).toBeInTheDocument()
    })

    it('should request camera access', () => {
        render(<WebcamFeed onFrame={() => { }} />)
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
            video: { width: 640, height: 480 }
        })
    })
})
