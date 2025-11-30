import React, { useEffect, useRef } from 'react'

interface WebcamFeedProps {
    onFrame: (canvas: HTMLCanvasElement) => void
}

const WebcamFeed: React.FC<WebcamFeedProps> = ({ onFrame }) => {
    const videoRef = useRef<HTMLVideoElement>(null)
    const canvasRef = useRef<HTMLCanvasElement>(null)

    useEffect(() => {
        const startCamera = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480 }
                })

                if (videoRef.current) {
                    videoRef.current.srcObject = stream
                    videoRef.current.play()
                }
            } catch (err) {
                console.error("Error accessing webcam:", err)
            }
        }

        startCamera()

        return () => {
            // Cleanup tracks
            if (videoRef.current && videoRef.current.srcObject) {
                const stream = videoRef.current.srcObject as MediaStream
                stream.getTracks().forEach(track => track.stop())
            }
        }
    }, [])

    // Frame loop
    useEffect(() => {
        let animationId: number

        const processFrame = () => {
            if (videoRef.current && canvasRef.current) {
                const video = videoRef.current
                const canvas = canvasRef.current
                const ctx = canvas.getContext('2d')

                if (ctx && video.readyState === video.HAVE_ENOUGH_DATA) {
                    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
                    onFrame(canvas)
                }
            }
            animationId = requestAnimationFrame(processFrame)
        }

        animationId = requestAnimationFrame(processFrame)

        return () => cancelAnimationFrame(animationId)
    }, [onFrame])

    return (
        <div className="relative">
            <video
                ref={videoRef}
                data-testid="webcam-video"
                className="transform -scale-x-100" // Mirror
                playsInline
                muted
            />
            <canvas
                ref={canvasRef}
                width={640}
                height={480}
                className="hidden" // Hidden canvas for processing
            />
        </div>
    )
}

export default WebcamFeed
