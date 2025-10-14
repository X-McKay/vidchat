# VidChat Web Interface

A modern web interface for VidChat built with FastAPI backend and React + TypeScript + shadcn/ui frontend.

## Architecture

- **Backend**: FastAPI with WebSocket support
- **Frontend**: React 19 + TypeScript + Vite
- **UI Components**: shadcn/ui (Radix UI + Tailwind CSS)
- **Communication**: WebSocket for real-time avatar streaming and audio

## Quick Start

### 1. Install Dependencies

```bash
# Install Python web dependencies
uv sync --extra web

# Install frontend dependencies
cd src/vidchat/web/frontend
npm install --legacy-peer-deps
```

### 2. Build Frontend

```bash
cd src/vidchat/web/frontend
npm run build
```

### 3. Start Server

```bash
# From project root
python start_web_server.py

# Or with custom host/port
python start_web_server.py --host 0.0.0.0 --port 8080

# With auto-reload for development
python start_web_server.py --reload
```

### 4. Access the Interface

Open your browser and navigate to:
- http://localhost:8000

## Development

### Frontend Development

For faster development with hot module replacement:

```bash
cd src/vidchat/web/frontend

# Start Vite dev server
npm run dev

# In another terminal, start the backend
python start_web_server.py
```

Then access:
- Frontend: http://localhost:5173 (Vite dev server)
- Backend: http://localhost:8000 (FastAPI server)

**Note**: Update the WebSocket URL in `src/components/Chat.tsx` to point to `ws://localhost:8000/ws/chat` when using the Vite dev server.

### Backend Development

The FastAPI backend is located in `src/vidchat/web/server.py`.

Key endpoints:
- `GET /` - Serves the React frontend
- `GET /health` - Health check
- `POST /api/chat` - REST API for chat (simple endpoint)
- `WebSocket /ws/chat` - WebSocket endpoint for real-time chat with avatar streaming

### Frontend Architecture

```
src/vidchat/web/frontend/src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── scroll-area.tsx
│   ├── Avatar.tsx             # Avatar display component
│   └── Chat.tsx               # Chat interface with WebSocket
├── hooks/
│   └── useWebSocket.ts        # WebSocket custom hook
├── lib/
│   └── utils.ts               # Utility functions
├── App.tsx                    # Main application component
├── main.tsx                   # Application entry point
└── index.css                  # Global styles with shadcn/ui theme

```

## WebSocket Protocol

### Message Types

#### From Client to Server:
```json
{
  "type": "message",
  "content": "Your message here"
}
```

#### From Server to Client:

**Text Response:**
```json
{
  "type": "text",
  "content": "AI response text"
}
```

**Audio Data:**
```json
{
  "type": "audio",
  "data": "base64_encoded_audio_data"
}
```

**Avatar Frame:**
```json
{
  "type": "frame",
  "data": "base64_encoded_jpeg_frame",
  "mouth_openness": 0.5
}
```

**Done:**
```json
{
  "type": "done"
}
```

**Error:**
```json
{
  "type": "error",
  "error": "Error message"
}
```

## Customization

### Styling

The interface uses Tailwind CSS with shadcn/ui theme system. Customize colors and styles in:
- `src/vidchat/web/frontend/src/index.css` - CSS variables for light/dark themes
- `src/vidchat/web/frontend/tailwind.config.js` - Tailwind configuration

### Avatar Renderer

The avatar renderer can be configured in `src/vidchat/config/settings.py`:

```python
avatar = AvatarConfig(
    renderer_type="image",  # Options: "geometric", "image", "sadtalker"
    avatar_image="assets/avatars/default_avatar.png",
    width=800,
    height=600
)
```

## Troubleshooting

### Frontend Build Issues

**Issue**: npm install fails with peer dependency errors

**Solution**: Use `--legacy-peer-deps` flag:
```bash
npm install --legacy-peer-deps
```

### WebSocket Connection Issues

**Issue**: WebSocket fails to connect

**Solutions**:
1. Ensure backend is running on the correct port
2. Check CORS settings in `src/vidchat/web/server.py`
3. Verify firewall settings allow WebSocket connections
4. Check browser console for specific error messages

### Avatar Not Displaying

**Issue**: Avatar frames not showing

**Solutions**:
1. Verify avatar renderer is initialized in backend logs
2. Check if avatar images exist in `assets/avatars/`
3. Ensure OpenCV is properly installed: `uv sync`
4. Check browser console for image loading errors

### Audio Not Playing

**Issue**: Audio responses not playing

**Solutions**:
1. Verify browser allows audio autoplay
2. Check if TTS engine is properly initialized
3. Test audio format compatibility with browser
4. Check browser console for audio loading errors

## Production Deployment

### Build for Production

```bash
# Build frontend
cd src/vidchat/web/frontend
npm run build

# The built files will be in dist/
```

### Serve with Production Server

Use a production ASGI server like Gunicorn with Uvicorn workers:

```bash
gunicorn vidchat.web.server:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y nodejs npm

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install uv
RUN uv sync --extra web

# Build frontend
WORKDIR /app/src/vidchat/web/frontend
RUN npm install --legacy-peer-deps
RUN npm run build

# Return to app directory
WORKDIR /app

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "start_web_server.py", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t vidchat-web .
docker run -p 8000:8000 vidchat-web
```

## Environment Variables

Configure the following environment variables for production:

- `VIDCHAT_HOST` - Server host (default: 127.0.0.1)
- `VIDCHAT_PORT` - Server port (default: 8000)
- `VIDCHAT_LOG_LEVEL` - Logging level (default: info)
- `OLLAMA_HOST` - Ollama server URL if using remote instance

## Security Considerations

1. **CORS**: Update `allow_origins` in `server.py` to restrict allowed origins in production
2. **Authentication**: Add authentication middleware for multi-user deployments
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **HTTPS**: Use reverse proxy (nginx/caddy) with SSL certificates
5. **WebSocket Security**: Implement WebSocket authentication tokens

## Performance Tips

1. **Avatar Rendering**: The image renderer provides 400+ FPS. Use it for production.
2. **Caching**: Enable browser caching for static assets
3. **CDN**: Serve static assets from CDN in production
4. **Connection Pool**: Configure appropriate worker count based on expected load
5. **GPU Acceleration**: Use GPU for SadTalker renderer if available

## License

See the main project LICENSE file.
