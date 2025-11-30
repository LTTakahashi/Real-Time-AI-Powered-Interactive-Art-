import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import DrawingCanvas, { DrawingCanvasRef } from './DrawingCanvas'
import React from 'react'

describe('DrawingCanvas', () => {
    let mockContext: any

    beforeEach(() => {
        mockContext = {
            beginPath: vi.fn(),
            moveTo: vi.fn(),
            lineTo: vi.fn(),
            stroke: vi.fn(),
            clearRect: vi.fn(),
            lineWidth: 0,
            lineCap: '',
            lineJoin: '',
            strokeStyle: ''
        }

        // Mock getContext
        HTMLCanvasElement.prototype.getContext = vi.fn(() => mockContext) as any
    })

    it('should render canvas element', () => {
        render(<DrawingCanvas width={640} height={480} />)
        const canvas = screen.getByTestId('drawing-canvas')
        expect(canvas).toBeInTheDocument()
        expect(canvas).toHaveAttribute('width', '640')
    })

    it('should expose drawing methods via ref', () => {
        const ref = React.createRef<DrawingCanvasRef>()
        render(<DrawingCanvas width={640} height={480} ref={ref} />)

        expect(ref.current).toHaveProperty('startStroke')
        expect(ref.current).toHaveProperty('drawPoint')
        expect(ref.current).toHaveProperty('endStroke')
        expect(ref.current).toHaveProperty('clear')
    })

    it('should draw a line when methods are called', () => {
        const ref = React.createRef<DrawingCanvasRef>()
        render(<DrawingCanvas width={640} height={480} ref={ref} />)

        ref.current?.startStroke(10, 10)
        expect(mockContext.beginPath).toHaveBeenCalled()
        expect(mockContext.moveTo).toHaveBeenCalledWith(10, 10)

        ref.current?.drawPoint(20, 20)
        expect(mockContext.lineTo).toHaveBeenCalledWith(20, 20)
        expect(mockContext.stroke).toHaveBeenCalled()
    })
})
