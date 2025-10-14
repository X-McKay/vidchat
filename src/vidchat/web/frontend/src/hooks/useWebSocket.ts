import { useEffect, useRef, useState, useCallback } from 'react'

export interface WebSocketMessage {
  type: 'text' | 'audio' | 'video' | 'frame' | 'done' | 'error'
  content?: string
  data?: string
  format?: string
  mouth_openness?: number
  error?: string
}

interface UseWebSocketOptions {
  url: string
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  autoConnect?: boolean
}

export function useWebSocket({
  url,
  onMessage,
  onOpen,
  onClose,
  onError,
  autoConnect = true
}: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)

  // Store callbacks in refs to avoid recreating connect function
  const onMessageRef = useRef(onMessage)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    onMessageRef.current = onMessage
    onOpenRef.current = onOpen
    onCloseRef.current = onClose
    onErrorRef.current = onError
  }, [onMessage, onOpen, onClose, onError])

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return
    }

    setIsConnecting(true)
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      setIsConnected(true)
      setIsConnecting(false)
      onOpenRef.current?.()
    }

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage
        onMessageRef.current?.(data)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.current.onclose = () => {
      setIsConnected(false)
      setIsConnecting(false)
      onCloseRef.current?.()
    }

    ws.current.onerror = (error) => {
      setIsConnected(false)
      setIsConnecting(false)
      onErrorRef.current?.(error)
    }
  }, [url])

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close()
      ws.current = null
    }
  }, [])

  const sendMessage = useCallback((message: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [autoConnect, connect, disconnect])

  return {
    isConnected,
    isConnecting,
    connect,
    disconnect,
    sendMessage
  }
}
