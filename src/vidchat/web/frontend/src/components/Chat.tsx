import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { ScrollArea } from './ui/scroll-area'
import { cn } from '@/lib/utils'
import { useWebSocket, type WebSocketMessage } from '@/hooks/useWebSocket'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatProps {
  onFrameUpdate: (frame: string) => void
  onVideoUpdate: (video: string) => void
  onProcessingChange: (isProcessing: boolean) => void
  className?: string
}

export function Chat({ onFrameUpdate, onVideoUpdate, onProcessingChange, className }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const handleMessage = (data: WebSocketMessage) => {
    if (data.type === 'text') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content || ''
      }])
    } else if (data.type === 'video') {
      // Handle video response (SadTalker)
      onVideoUpdate(`data:video/mp4;base64,${data.data}`)
      // Note: SadTalker videos include audio, so no separate audio playback needed
    } else if (data.type === 'audio') {
      // Play audio response (for frame-based rendering)
      if (audioRef.current) {
        audioRef.current.pause()
      }
      audioRef.current = new Audio(`data:audio/wav;base64,${data.data}`)
      audioRef.current.play().catch(err =>
        console.error('Error playing audio:', err)
      )
    } else if (data.type === 'frame') {
      // Handle frame response (image/geometric renderer)
      onFrameUpdate(`data:image/jpeg;base64,${data.data}`)
    } else if (data.type === 'done') {
      setIsProcessing(false)
      onProcessingChange(false)
    } else if (data.type === 'error') {
      console.error('WebSocket error:', data.error)
      setIsProcessing(false)
      onProcessingChange(false)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${data.error}`
      }])
    }
  }

  const { isConnected, isConnecting, sendMessage } = useWebSocket({
    url: 'ws://localhost:8000/ws/chat',
    onMessage: handleMessage,
    onOpen: () => console.log('WebSocket connected'),
    onClose: () => console.log('WebSocket disconnected'),
    onError: (error) => console.error('WebSocket error:', error)
  })

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = () => {
    if (!inputValue.trim() || !isConnected || isProcessing) return

    const userMessage: Message = {
      role: 'user',
      content: inputValue
    }

    setMessages(prev => [...prev, userMessage])
    setIsProcessing(true)
    onProcessingChange(true)

    sendMessage({
      type: 'message',
      content: inputValue
    })

    setInputValue('')
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Card className={cn("flex flex-col", className)}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Chat</span>
          <div className="flex items-center gap-2 text-sm font-normal">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isConnected ? "bg-green-500" : isConnecting ? "bg-yellow-500" : "bg-red-500"
            )} />
            <span className="text-muted-foreground">
              {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}
            </span>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 flex-1 overflow-hidden p-0">
        <ScrollArea className="flex-1 px-6">
          <div className="space-y-4 pb-4">
            {messages.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                <p>Start a conversation with the AI avatar</p>
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex",
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] rounded-lg px-4 py-2",
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>
        <div className="px-6 pb-6">
          <div className="flex gap-2">
            <Input
              placeholder="Type your message..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={!isConnected || isProcessing}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!isConnected || isProcessing || !inputValue.trim()}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
