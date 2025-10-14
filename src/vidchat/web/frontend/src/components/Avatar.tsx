import { useEffect, useRef } from 'react'
import { Card, CardContent } from './ui/card'
import { cn } from '@/lib/utils'

interface AvatarProps {
  currentFrame: string | null
  currentVideo: string | null
  isProcessing: boolean
  className?: string
}

export function Avatar({ currentFrame, currentVideo, isProcessing, className }: AvatarProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)

  // Handle frame-based rendering (for image/geometric renderer)
  useEffect(() => {
    if (!currentFrame || !canvasRef.current || currentVideo) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const img = new Image()
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
    }
    img.src = currentFrame
  }, [currentFrame, currentVideo])

  // Handle video-based rendering (for SadTalker)
  useEffect(() => {
    if (!currentVideo || !videoRef.current) return

    const video = videoRef.current
    video.src = currentVideo
    video.play().catch(err => console.error('Error playing video:', err))
  }, [currentVideo])

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardContent className="p-0 relative">
        {/* Video element for SadTalker video playback */}
        <video
          ref={videoRef}
          className={cn(
            "w-full h-auto",
            !currentVideo && "hidden"
          )}
          controls={false}
          autoPlay
          loop={false}
        />

        {/* Canvas element for frame-based rendering */}
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          className={cn(
            "w-full h-auto",
            currentVideo && "hidden"
          )}
        />

        {isProcessing && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <div className="flex flex-col items-center gap-2 text-white">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white" />
              <span className="text-sm font-medium">
                {currentVideo ? 'Generating video...' : 'Processing...'}
              </span>
            </div>
          </div>
        )}
        {!currentFrame && !currentVideo && !isProcessing && (
          <div className="absolute inset-0 flex items-center justify-center bg-muted">
            <p className="text-muted-foreground">Avatar will appear here</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
