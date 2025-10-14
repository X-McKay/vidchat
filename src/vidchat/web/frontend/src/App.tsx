import { useState } from 'react'
import { Chat } from './components/Chat'
import { Avatar } from './components/Avatar'

export default function App() {
  const [currentFrame, setCurrentFrame] = useState<string | null>(null)
  const [currentVideo, setCurrentVideo] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4 h-screen flex flex-col">
        <header className="mb-6">
          <h1 className="text-4xl font-bold text-foreground">VidChat</h1>
          <p className="text-muted-foreground mt-2">
            AI chat agent with avatar video and audio responses
          </p>
        </header>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-hidden">
          <Avatar
            currentFrame={currentFrame}
            currentVideo={currentVideo}
            isProcessing={isProcessing}
            className="h-full"
          />
          <Chat
            onFrameUpdate={setCurrentFrame}
            onVideoUpdate={setCurrentVideo}
            onProcessingChange={setIsProcessing}
            className="h-full"
          />
        </div>
      </div>
    </div>
  )
}
