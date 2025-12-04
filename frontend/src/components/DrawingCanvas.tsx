import { useRef, useImperativeHandle, forwardRef } from 'react'

export interface DrawingCanvasRef {
    startStroke: (x: number, y: number) => void
    drawPoint: (x: number, y: number) => void
    endStroke: () => void
    clear: () => void
    getDataURL: () => string | null
}

interface DrawingCanvasProps {
    width: number
    height: number
}

const DrawingCanvas = forwardRef<DrawingCanvasRef, DrawingCanvasProps>(({ width, height }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)

    useImperativeHandle(ref, () => ({
        startStroke: (x, y) => {
            const ctx = canvasRef.current?.getContext('2d')
            if (ctx) {
                ctx.beginPath()
                ctx.moveTo(x, y)
                ctx.lineWidth = 5
                ctx.lineCap = 'round'
                ctx.lineJoin = 'round'
                ctx.strokeStyle = '#00FF00' // Green default
            }
        },
        drawPoint: (x, y) => {
            const ctx = canvasRef.current?.getContext('2d')
            if (ctx) {
                ctx.lineTo(x, y)
                ctx.stroke()
            }
        },
        endStroke: () => {
            // Nothing needed for basic canvas, but could close path
        },
        clear: () => {
            const ctx = canvasRef.current?.getContext('2d')
            if (ctx) {
                ctx.clearRect(0, 0, width, height)
            }
        },
        getDataURL: () => {
            return canvasRef.current ? canvasRef.current.toDataURL('image/jpeg', 0.8) : null
        }
    }))

    return (
        <canvas
            ref={canvasRef}
            width={width}
            height={height}
            className="absolute top-0 left-0 pointer-events-none" // Overlay
            data-testid="drawing-canvas"
        />
    )
})

export default DrawingCanvas
