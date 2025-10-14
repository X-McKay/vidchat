# VidChat Web Interface Guide

Complete guide for the modern web interface with React, TypeScript, and shadcn/ui.

## Overview

The web interface provides:
- **Modern UI** with shadcn/ui components (Radix UI + Tailwind CSS)
- **Real-time chat** via WebSocket
- **Avatar video streaming** with synchronized audio
- **Responsive design** for desktop and mobile
- **TypeScript** for type safety

## Architecture

```
Frontend (React + TypeScript)
    ↕ WebSocket
Backend (FastAPI + Python)
    ↕
VidChat Core (AI + TTS + Avatar)
```

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- WebSocket for real-time communication
- Base64 encoding for media streaming

**Frontend:**
- React 19 with TypeScript
- Vite (build tool)
- shadcn/ui (UI components)
- Tailwind CSS (styling)
- Lucide React (icons)

## Quick Start

### 1. Install Backend Dependencies

```bash
# Add web server dependencies
cd /path/to/vidchat
pip install fastapi uvicorn python-multipart websockets
# Or add to pyproject.toml
```

### 2. Install Frontend Dependencies

```bash
cd src/vidchat/web/frontend
npm install
```

### 3. Build Frontend

```bash
npm run build
```

### 4. Start Server

```bash
# From project root
python -m uvicorn vidchat.web.server:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access Interface

Open browser to: http://localhost:8000

## File Structure

```
src/vidchat/web/
├── __init__.py
├── server.py              # FastAPI backend
└── frontend/
    ├── package.json       # Dependencies
    ├── tsconfig.json      # TypeScript config
    ├── vite.config.ts     # Vite config
    ├── tailwind.config.js # Tailwind config
    ├── postcss.config.js  # PostCSS config
    ├── index.html         # HTML entry point
    └── src/
        ├── main.tsx       # React entry point
        ├── App.tsx        # Main app component
        ├── index.css      # Global styles
        ├── lib/
        │   └── utils.ts   # Utility functions
        ├── components/
        │   ├── ui/        # shadcn/ui components
        │   │   ├── button.tsx
        │   │   ├── card.tsx
        │   │   ├── input.tsx
        │   │   ├── scroll-area.tsx
        │   │   └── ...
        │   ├── Chat.tsx   # Chat interface
        │   ├── Avatar.tsx # Avatar display
        │   └── MessageList.tsx # Message history
        └── hooks/
            └── useWebSocket.ts # WebSocket hook
```

## Backend API

### REST Endpoints

#### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "agent_initialized": true
}
```

#### POST /api/chat
Simple chat endpoint (non-streaming).

**Request:**
```json
{
  "message": "Hello, how are you?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "I'm doing well, thank you!",
  "audio_url": null,
  "avatar_frame_url": null
}
```

#### GET /api/avatar/frame
Get a single avatar frame.

**Query Parameters:**
- `text` (string): Text to display
- `mouth_openness` (float): 0.0 to 1.0

**Response:** JPEG image

#### GET /api/config
Get current VidChat configuration.

**Response:**
```json
{
  "avatar": {
    "type": "image",
    "width": 800,
    "height": 600,
    "fps": 30
  },
  "ai": {
    "model": "llama3.2"
  },
  "tts": {
    "provider": "piper",
    "sample_rate": 22050
  }
}
```

### WebSocket API

#### WS /ws/chat
Real-time chat with avatar streaming.

**Client → Server:**
```json
{
  "type": "message",
  "content": "user message"
}
```

**Server → Client (Text Response):**
```json
{
  "type": "text",
  "content": "AI response text"
}
```

**Server → Client (Audio Data):**
```json
{
  "type": "audio",
  "data": "base64_encoded_wav_audio",
  "format": "wav"
}
```

**Server → Client (Video Frame):**
```json
{
  "type": "frame",
  "data": "base64_encoded_jpeg_image",
  "mouth_openness": 0.5,
  "frame_index": 42,
  "total_frames": 150
}
```

**Server → Client (Completion):**
```json
{
  "type": "done"
}
```

**Server → Client (Error):**
```json
{
  "type": "error",
  "content": "Error message"
}
```

## Frontend Components

### Main App Component

```typescript
// src/App.tsx
import { useState, useEffect } from 'react'
import { Chat } from './components/Chat'
import { Avatar } from './components/Avatar'
import { cn } from './lib/utils'

function App() {
  const [avatarFrame, setAvatarFrame] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  return (
    <div className="h-screen bg-background flex">
      {/* Avatar Panel */}
      <div className="w-1/2 border-r flex items-center justify-center bg-muted/20">
        <Avatar frame={avatarFrame} />
      </div>

      {/* Chat Panel */}
      <div className="w-1/2 flex flex-col">
        <Chat
          onFrameUpdate={setAvatarFrame}
          onConnectionChange={setIsConnected}
        />
      </div>
    </div>
  )
}
```

### Chat Component

Uses WebSocket for real-time communication:

```typescript
// src/components/Chat.tsx
import { useState, useRef, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { ScrollArea } from './ui/scroll-area'
import { Send, Loader2 } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export function Chat({ onFrameUpdate, onConnectionChange }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Connect to WebSocket
    ws.current = new WebSocket('ws://localhost:8000/ws/chat')

    ws.current.onopen = () => {
      onConnectionChange(true)
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'text') {
        // Add assistant message
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: data.content,
          timestamp: new Date()
        }])
      } else if (data.type === 'frame') {
        // Update avatar frame
        onFrameUpdate(`data:image/jpeg;base64,${data.data}`)
      } else if (data.type === 'audio') {
        // Play audio
        const audio = new Audio(`data:audio/wav;base64,${data.data}`)
        audio.play()
      } else if (data.type === 'done') {
        setIsLoading(false)
      }
    }

    return () => {
      ws.current?.close()
    }
  }, [])

  const sendMessage = () => {
    if (!input.trim() || !ws.current) return

    // Add user message
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }])

    // Send to server
    ws.current.send(JSON.stringify({
      type: 'message',
      content: input
    }))

    setInput('')
    setIsLoading(true)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <h1 className="text-2xl font-bold">VidChat</h1>
        <p className="text-sm text-muted-foreground">
          AI Assistant with Avatar
        </p>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={cn(
              "mb-4 p-3 rounded-lg",
              msg.role === 'user'
                ? "bg-primary text-primary-foreground ml-12"
                : "bg-muted mr-12"
            )}
          >
            <p>{msg.content}</p>
            <span className="text-xs opacity-70">
              {msg.timestamp.toLocaleTimeString()}
            </span>
          </div>
        ))}
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type your message..."
          disabled={isLoading}
        />
        <Button
          onClick={sendMessage}
          disabled={isLoading}
        >
          {isLoading ? <Loader2 className="animate-spin" /> : <Send />}
        </Button>
      </div>
    </div>
  )
}
```

### Avatar Component

```typescript
// src/components/Avatar.tsx
import { useEffect, useState } from 'react'
import { Card } from './ui/card'

interface AvatarProps {
  frame: string | null
}

export function Avatar({ frame }: AvatarProps) {
  const [displayFrame, setDisplayFrame] = useState<string | null>(null)

  useEffect(() => {
    if (frame) {
      setDisplayFrame(frame)
    }
  }, [frame])

  return (
    <Card className="overflow-hidden w-[800px] h-[600px] flex items-center justify-center">
      {displayFrame ? (
        <img
          src={displayFrame}
          alt="Avatar"
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="text-center text-muted-foreground">
          <p>Avatar will appear here</p>
          <p className="text-sm">Start chatting to see the avatar!</p>
        </div>
      )}
    </Card>
  )
}
```

## Styling with shadcn/ui

### Global Styles

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 212.7 26.8% 83.9%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

## Building and Deployment

### Development Mode

```bash
# Terminal 1: Frontend dev server
cd src/vidchat/web/frontend
npm run dev

# Terminal 2: Backend server
cd /path/to/vidchat
python -m uvicorn vidchat.web.server:app --reload
```

Access at:
- Frontend dev server: http://localhost:5173
- Backend API: http://localhost:8000

### Production Build

```bash
# Build frontend
cd src/vidchat/web/frontend
npm run build

# Start production server
cd /path/to/vidchat
python -m uvicorn vidchat.web.server:app --host 0.0.0.0 --port 8000
```

Access at: http://localhost:8000

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install -e .[web]

# Install Node.js
RUN apt-get update && apt-get install -y nodejs npm

# Build frontend
COPY src/vidchat/web/frontend ./src/vidchat/web/frontend
WORKDIR /app/src/vidchat/web/frontend
RUN npm install && npm run build

# Back to app directory
WORKDIR /app

# Copy source code
COPY src ./src

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "vidchat.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t vidchat-web .
docker run -p 8000:8000 vidchat-web
```

## Configuration

### Environment Variables

```bash
# .env
VIDCHAT_HOST=0.0.0.0
VIDCHAT_PORT=8000
VIDCHAT_OLLAMA_URL=http://localhost:11434/v1
VIDCHAT_MODEL=llama3.2
VIDCHAT_AVATAR_TYPE=image
```

### Custom Configuration

```python
# custom_web_config.py
from vidchat.config import AppConfig, AvatarConfig, AIAgentConfig
from vidchat.web.server import start_server
import os

config = AppConfig(
    avatar=AvatarConfig(
        renderer_type=os.getenv("VIDCHAT_AVATAR_TYPE", "image"),
        width=800,
        height=600,
    ),
    ai=AIAgentConfig(
        model_name=os.getenv("VIDCHAT_MODEL", "llama3.2"),
        ollama_base_url=os.getenv("VIDCHAT_OLLAMA_URL"),
    )
)

# Pass config to agent initialization in server.py
```

## Troubleshooting

### "WebSocket connection failed"

**Solution:** Ensure backend is running and accessible
```bash
# Check backend
curl http://localhost:8000/health

# Check WebSocket
wscat -c ws://localhost:8000/ws/chat
```

### "Avatar not displaying"

**Solution:** Check browser console for errors
- Verify base64 image data is valid
- Check CORS settings
- Ensure avatar renderer is initialized

### "No audio playback"

**Solution:**
- Check browser audio permissions
- Verify audio data format (WAV)
- Check base64 encoding is correct

### Build errors

```bash
# Clear caches
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run build
```

## Performance Optimization

### Frame Streaming

- Buffer frames on client
- Sync with audio playback
- Skip frames if falling behind

### WebSocket Optimization

- Compress large messages
- Use binary frames for media
- Implement reconnection logic

### Avatar Rendering

- Use JPEG for smaller size (vs PNG)
- Adjust JPEG quality (85 is good balance)
- Consider WebP for better compression

## Next Steps

1. **Add Authentication**
   - JWT tokens
   - User sessions
   - Protected routes

2. **Enhanced Features**
   - Voice input (speech-to-text)
   - Chat history persistence
   - Multiple avatar selection
   - Dark mode toggle

3. **Mobile Optimization**
   - Responsive layout
   - Touch-friendly controls
   - PWA support

4. **Advanced UI**
   - Typing indicators
   - Read receipts
   - Emoji support
   - File uploads

## Resources

- **shadcn/ui:** https://ui.shadcn.com/
- **Radix UI:** https://www.radix-ui.com/
- **Tailwind CSS:** https://tailwindcss.com/
- **FastAPI:** https://fastapi.tiangolo.com/
- **WebSocket API:** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

## Summary

The web interface provides a modern, professional UI for VidChat with:
- ✅ Real-time chat via WebSocket
- ✅ Avatar video streaming
- ✅ Audio playback
- ✅ shadcn/ui components
- ✅ TypeScript type safety
- ✅ Responsive design
- ✅ Production-ready architecture

Ready to deploy and extend with additional features!
