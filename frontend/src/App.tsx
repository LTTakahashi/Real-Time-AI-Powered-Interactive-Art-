import React, { useEffect, useRef, useState } from 'react'
import WebcamFeed from './components/WebcamFeed'
import DrawingCanvas, { type DrawingCanvasRef } from './components/DrawingCanvas'
import StatusPill, { type SystemStatus } from './components/StatusPill'
import StyleSelector, { type StyleOption } from './components/StyleSelector'
import { WebSocketClient } from './services/WebSocketClient'
import { Wand2, RefreshCw, Download } from 'lucide-react'

const STYLES: StyleOption[] = [
  { id: 'neon', name: 'Neon', color: 'bg-cyan-500' },
  { id: 'sketch', name: 'Sketch', color: 'bg-gray-500' },
  { id: 'oil', name: 'Oil Paint', color: 'bg-yellow-600' },
  { id: 'watercolor', name: 'Watercolor', color: 'bg-blue-400' },
  { id: 'pixel', name: 'Pixel Art', color: 'bg-purple-500' },
]

function App() {
  const [status, setStatus] = useState<SystemStatus>('disconnected')
  const [selectedStyle, setSelectedStyle] = useState('neon')
  const [generatedImage, setGeneratedImage] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const wsRef = useRef<WebSocketClient | null>(null)
  const canvasRef = useRef<DrawingCanvasRef>(null)
  const lastFrameTime = useRef(0)

  useEffect(() => {
    // Initialize WebSocket
    const ws = new WebSocketClient('ws://localhost:8000/ws/tracking')
    wsRef.current = ws

    ws.on('open', () => setStatus('idle'))
    ws.on('close', () => setStatus('disconnected'))
    ws.on('error', () => setStatus('disconnected'))

    ws.on('message', (data) => {
      // Handle Drawing Commands
      if (canvasRef.current) {
        const { action, points } = data

        if (action === 'start_stroke' && points) {
          canvasRef.current.startStroke(points[0], points[1])
          setStatus('drawing')
        } else if (action === 'draw' && points) {
          canvasRef.current.drawPoint(points[0], points[1])
          setStatus('drawing')
        } else if (action === 'end_stroke') {
          canvasRef.current.endStroke()
          setStatus('idle')
        } else if (action === 'clear') {
          canvasRef.current.clear()
        } else if (action === 'undo') {
          // Canvas component doesn't support undo yet (it's visual only)
          // But backend handles logic. We might need to redraw everything?
          // For now, simple clear or flash.
          // Ideally, backend sends full stroke list on undo.
          // For Phase 3 MVP, we'll ignore undo visual update or just clear.
          canvasRef.current.clear() // Temporary: Undo clears all (limit of simple canvas)
        }
      }

      // Update Status based on Gesture
      if (data.gesture === 'POINTING') {
        // Handled above
      } else if (data.gesture === 'OPEN_PALM') {
        setStatus('hovering')
      } else if (data.gesture === 'CLOSED_FIST') {
        // Maybe trigger generation?
      }
    })

    ws.connect()

    return () => ws.disconnect()
  }, [])

  const handleFrame = (canvas: HTMLCanvasElement) => {
    // Limit FPS to 30 to save bandwidth
    const now = Date.now()
    if (now - lastFrameTime.current < 33) return
    lastFrameTime.current = now

    if (wsRef.current) {
      const base64 = canvas.toDataURL('image/jpeg', 0.7)
      // Remove header
      const data = base64.split(',')[1]
      wsRef.current.send(data)
    }
  }

  const handleGenerate = async () => {
    if (isGenerating) return
    setIsGenerating(true)
    setStatus('processing')

    try {
      const response = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          style: selectedStyle,
          image: '' // Backend uses its own canvas state
        })
      })

      const data = await response.json()
      const requestId = data.request_id

      // Poll for result
      const pollInterval = setInterval(async () => {
        const res = await fetch(`http://localhost:8000/result/${requestId}`)
        const result = await res.json()

        if (result.status === 'complete') {
          clearInterval(pollInterval)
          setGeneratedImage(`data:image/jpeg;base64,${result.image}`)
          setIsGenerating(false)
          setStatus('idle')
        } else if (result.status === 'failed') {
          clearInterval(pollInterval)
          setIsGenerating(false)
          setStatus('idle')
          alert('Generation failed')
        }
      }, 1000)

    } catch (e) {
      console.error(e)
      setIsGenerating(false)
      setStatus('idle')
    }
  }

  return (
    <div className="relative w-screen h-screen bg-black overflow-hidden font-sans text-white">
      {/* Webcam Layer */}
      <div className="absolute inset-0 z-0">
        <WebcamFeed onFrame={handleFrame} />
      </div>

      {/* Drawing Layer */}
      <div className="absolute inset-0 z-10">
        <DrawingCanvas ref={canvasRef} width={640} height={480} />
      </div>

      {/* HUD Layer */}
      <div className="absolute inset-0 z-20 pointer-events-none flex flex-col justify-between p-8">
        {/* Top Bar */}
        <div className="flex justify-between items-start">
          <div className="flex flex-col gap-2">
            <h1 className="text-4xl font-bold tracking-tighter bg-gradient-to-r from-pink-500 to-violet-500 bg-clip-text text-transparent drop-shadow-lg">
              GestureCanvas
            </h1>
            <StatusPill status={status} />
          </div>

          {/* Generated Image Overlay */}
          {generatedImage && (
            <div className="pointer-events-auto relative group">
              <img
                src={generatedImage}
                alt="Generated"
                className="w-64 h-auto rounded-xl border-2 border-white/20 shadow-2xl transition-transform hover:scale-105"
              />
              <button
                onClick={() => setGeneratedImage(null)}
                className="absolute -top-2 -right-2 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <RefreshCw size={16} />
              </button>
            </div>
          )}
        </div>

        {/* Bottom Bar */}
        <div className="flex items-end justify-center gap-8 pointer-events-auto">
          <StyleSelector
            styles={STYLES}
            selected={selectedStyle}
            onSelect={setSelectedStyle}
          />

          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="h-24 w-24 rounded-full bg-gradient-to-br from-pink-500 to-violet-600 flex flex-col items-center justify-center gap-1 shadow-lg shadow-pink-500/30 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:grayscale"
          >
            {isGenerating ? (
              <RefreshCw className="animate-spin w-8 h-8" />
            ) : (
              <Wand2 className="w-8 h-8" />
            )}
            <span className="text-xs font-bold">GENERATE</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
