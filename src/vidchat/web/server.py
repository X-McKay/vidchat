"""
FastAPI web server for VidChat with WebSocket support.

Handles text chat, audio streaming, and avatar frame streaming.
"""
import asyncio
import base64
import io
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from ..core.agent import VidChatAgent
from ..config import default_config
from ..utils import setup_logger


logger = setup_logger("vidchat.web")


# API Models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    audio_url: Optional[str] = None


# FastAPI app
app = FastAPI(
    title="VidChat Web API",
    description="Web interface for VidChat AI assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance (consider session management for multi-user)
vidchat_agent: Optional[VidChatAgent] = None


@app.on_event("startup")
async def startup_event():
    """Initialize VidChat agent on startup."""
    global vidchat_agent
    logger.info("Initializing VidChat agent...")
    try:
        vidchat_agent = VidChatAgent(config=default_config)
        logger.info("✓ VidChat agent initialized")
    except Exception as e:
        logger.error(f"Failed to initialize VidChat agent: {e}")
        vidchat_agent = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global vidchat_agent
    logger.info("Shutting down VidChat web server")


@app.get("/")
async def read_root():
    """Serve the React frontend."""
    frontend_path = Path(__file__).parent / "frontend" / "dist" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "VidChat Web API", "status": "running", "frontend": "not built"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agent_initialized": vidchat_agent is not None
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Send a message to VidChat and get response.

    Note: This is a simpler REST endpoint. For real-time streaming,
    use the WebSocket endpoint instead.
    """
    if not vidchat_agent:
        raise HTTPException(status_code=503, detail="VidChat agent not initialized")

    try:
        # Get AI response
        response_text = await vidchat_agent.chat(message.message)

        return ChatResponse(
            response=response_text,
            audio_url=None  # Could generate and store audio file
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat with audio streaming.

    Protocol:
    - Client sends: {"type": "message", "content": "user message"}
    - Server sends: {"type": "text", "content": "AI response"}
    - Server sends: {"type": "audio", "data": "base64_audio", "format": "wav"}
    - Server sends: {"type": "done"}
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") == "message":
                user_message = data.get("content", "")
                logger.info(f"Received message: {user_message[:50]}...")

                if not vidchat_agent:
                    await websocket.send_json({
                        "type": "error",
                        "content": "VidChat agent not initialized"
                    })
                    continue

                try:
                    # Get AI response
                    response_text = await vidchat_agent.chat(user_message)

                    # Send text response
                    await websocket.send_json({
                        "type": "text",
                        "content": response_text
                    })

                    # Generate and send video with SadTalker
                    await _handle_sadtalker_response(websocket, vidchat_agent, response_text)

                    # Send completion signal
                    await websocket.send_json({"type": "done"})

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "content": f"Error: {str(e)}"
                    })

            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)


async def _handle_sadtalker_response(websocket: WebSocket, agent: VidChatAgent, text: str):
    """
    Handle response using SadTalker video generation.

    Workflow:
    1. Generate audio from text
    2. Use SadTalker to generate video (image + audio → video)
    3. Send video to client
    """
    import os

    try:
        # Generate speech audio
        logger.info("Generating speech audio...")
        audio_path = agent.generate_speech(text)

        # Generate video using SadTalker
        logger.info("Generating SadTalker video (this takes ~30-60 seconds)...")
        video_path = agent.avatar.generate_video(audio_path)

        # Read and encode video
        with open(video_path, 'rb') as f:
            video_data = f.read()
            video_base64 = base64.b64encode(video_data).decode('utf-8')

            # Send video to client
            await websocket.send_json({
                "type": "video",
                "data": video_base64,
                "format": "mp4"
            })

        logger.info("Video sent to client")

        # Cleanup
        try:
            os.unlink(audio_path)
            os.unlink(video_path)
        except:
            pass

    except Exception as e:
        logger.error(f"Error in SadTalker workflow: {e}", exc_info=True)
        raise


@app.get("/api/config")
async def get_config():
    """Get current VidChat configuration."""
    if not vidchat_agent:
        raise HTTPException(status_code=503, detail="VidChat agent not initialized")

    return {
        "ai": {
            "model": vidchat_agent.config.ai.model_name,
        },
        "tts": {
            "provider": vidchat_agent.config.tts.provider,
            "sample_rate": vidchat_agent.config.tts.sample_rate,
        }
    }


# Mount static files (frontend build)
frontend_dist = Path(__file__).parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
    """
    import uvicorn

    logger.info(f"Starting VidChat web server on {host}:{port}")
    uvicorn.run(
        "vidchat.web.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server(reload=True)
