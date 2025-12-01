import { useEffect, useRef, useState } from 'react'
import WebcamFeed from './components/WebcamFeed'
import DrawingCanvas, { type DrawingCanvasRef } from './components/DrawingCanvas'
import StatusPill, { type SystemStatus } from './components/StatusPill'
import StyleSelector, { type StyleOption } from './components/StyleSelector'
import { WebSocketClient } from './services/WebSocketClient'
import { Wand2, RefreshCw } from 'lucide-react'

const STYLES: StyleOption[] = [
  { id: 'photorealistic', name: 'Photo', color: 'bg-blue-500' },
  { id: 'anime', name: 'Anime', color: 'bg-pink-500' },
  { id: 'oil_painting', name: 'Oil Paint', color: 'bg-yellow-600' },
  { id: 'watercolor', name: 'Watercolor', color: 'bg-blue-400' },
  { id: 'sketch', name: 'Sketch', color: 'bg-gray-500' },
]

function App() {
  const [status, setStatus] = useState<SystemStatus>('disconnected')
  const [selectedStyle, setSelectedStyle] = useState('photorealistic')
  const [generatedImage, setGeneratedImage] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [demoMode, setDemoMode] = useState(false)

  const wsRef = useRef<WebSocketClient | null>(null)
  const canvasRef = useRef<DrawingCanvasRef>(null)
  const lastFrameTime = useRef(0)
  const pollIntervalRef = useRef<number | null>(null)

  useEffect(() => {
    // Cleanup polling interval on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

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

      // Poll for result with timeout
      let pollCount = 0
      const maxPolls = 60  // 60 seconds timeout

      pollIntervalRef.current = setInterval(async () => {
        if (pollCount++ > maxPolls) {
          if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
          setIsGenerating(false)
          setStatus('idle')
          alert('Generation timed out. Please try again.')
          return
        }

        try {
          const res = await fetch(`http://localhost:8000/result/${requestId}`)
          const result = await res.json()

          if (result.status === 'complete') {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
            setGeneratedImage(`data:image/jpeg;base64,${result.image}`)
            setIsGenerating(false)
            setStatus('idle')
          } else if (result.status === 'failed') {
            if (pollIntervalRef.current) clearInterval(pollIntervalRef.current)
            setIsGenerating(false)
            setStatus('idle')
            alert('Generation failed: ' + (result.error || 'Unknown error'))
          }
        } catch (pollError) {
          console.error('Polling error:', pollError)
        }
      }, 1000)

    } catch (e) {
      console.error(e)
      setIsGenerating(false)
      setStatus('idle')
      alert('Failed to start generation: ' + (e as Error).message)
    }
  }

  return (
    <div className="relative w-screen h-screen bg-neutral-950 text-white overflow-hidden selection:bg-purple-500/30 font-sans">

      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-50 p-6 flex justify-between items-start bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
        <div className="pointer-events-auto flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tighter bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent drop-shadow-lg">
            GestureCanvas
          </h1>
          <StatusPill status={status} />
        </div>

        <div className="pointer-events-auto">
          <button
            onClick={() => setDemoMode(!demoMode)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all border ${demoMode
                ? 'bg-purple-500/20 border-purple-500 text-purple-300 shadow-[0_0_10px_rgba(168,85,247,0.3)]'
                : 'bg-white/5 border-white/10 text-white/50 hover:bg-white/10'
              }`}
          >
            {demoMode ? '● DEMO MODE' : '○ WEBCAM'}
          </button>
        </div>
      </div>

      {/* Webcam Layer */}
      <div className="absolute inset-0 z-0 opacity-60">
        <WebcamFeed onFrame={handleFrame} demoMode={demoMode} />
      </div>

      {/* Drawing Layer */}
      <div className="absolute inset-0 z-10">
        <DrawingCanvas ref={canvasRef} width={640} height={480} />
      </div>

      {/* Generated Image Overlay */}
      {generatedImage && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black/60 backdrop-blur-sm p-12 animate-in fade-in duration-300">
          <div className="relative group">
            <img
              src={generatedImage}
              alt="Generated Art"
              className="max-w-full max-h-[80vh] rounded-xl border-2 border-white/20 shadow-2xl transition-transform hover:scale-[1.02]"
            />
            <button
              onClick={() => setGeneratedImage(null)}
              className="absolute -top-4 -right-4 bg-white text-black p-2 rounded-full shadow-lg hover:bg-gray-200 transition-colors pointer-events-auto"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        </div>
      )}

      {/* Bottom Controls */}
      <div className="absolute bottom-0 left-0 right-0 p-8 z-20 pointer-events-none flex justify-center items-end gap-8 bg-gradient-to-t from-black/90 to-transparent">
        <div className="pointer-events-auto">
          <StyleSelector
            styles={STYLES}
            selected={selectedStyle}
            onSelect={setSelectedStyle}
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="pointer-events-auto h-20 w-20 rounded-full bg-gradient-to-br from-pink-500 to-violet-600 flex flex-col items-center justify-center gap-1 shadow-lg shadow-pink-500/30 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:grayscale"
        >
          {isGenerating ? (
            <RefreshCw className="animate-spin w-6 h-6" />
          ) : (
            <Wand2 className="w-6 h-6" />
          )}
          <span className="text-[10px] font-bold tracking-wider">GENERATE</span>
        </button>
      </div>
    </div>
  )
}

export default App
