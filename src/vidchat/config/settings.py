"""
Configuration settings for VidChat application.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path


# Project paths
# __file__ is src/vidchat/config/settings.py
# Go up to src/vidchat, then src, then project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


@dataclass
class TTSConfig:
    """Text-to-Speech configuration."""
    provider: str = "piper"  # Options: piper, xtts, rvc, piper+rvc
    piper_model: str = str(MODELS_DIR / "en_US-lessac-medium.onnx")
    rvc_model: str | None = None  # Path to RVC model (for voice conversion)
    sample_rate: int = 22050

    # XTTS voice cloning settings
    xtts_reference_audio: str | None = None  # Path to reference audio (6+ seconds)
    xtts_language: str = "en"  # Language code for XTTS


@dataclass
class AvatarConfig:
    """Avatar rendering configuration."""
    # Renderer type: "geometric", "image", or "sadtalker"
    renderer_type: str = "sadtalker"

    # Avatar image path (for image and sadtalker modes)
    avatar_image: str | None = str(PROJECT_ROOT / "assets" / "avatars" / "default_avatar.png")

    # Display settings
    width: int = 800
    height: int = 600
    fps: int = 30

    # Colors (BGR format for OpenCV)
    bg_color: tuple[int, int, int] = (25, 25, 35)
    avatar_idle_color: tuple[int, int, int] = (100, 180, 220)
    avatar_speaking_color: tuple[int, int, int] = (120, 220, 140)
    text_color: tuple[int, int, int] = (255, 255, 255)

    # Animation settings
    enable_blink: bool = True
    blink_interval: float = 3.0  # seconds
    enable_head_movement: bool = False
    head_movement_amplitude: float = 5.0  # pixels

    # SadTalker specific settings
    sadtalker_path: str | None = str(Path.home() / "SadTalker")  # Path to SadTalker installation
    sadtalker_use_enhancer: bool = False  # Use GFPGAN enhancer (disabled - not compatible with Python 3.13+)
    sadtalker_still_mode: bool = False  # Less head movement
    sadtalker_preprocess: str = "crop"  # crop or full


@dataclass
class AIAgentConfig:
    """AI agent configuration."""
    model_name: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434/v1"
    system_prompt: str = (
        "You are a friendly AI assistant. Keep your responses conversational "
        "and concise (2-3 sentences max)."
    )
    temperature: float = 0.7
    max_tokens: int | None = None


@dataclass
class AudioConfig:
    """Audio processing configuration."""
    sample_rate: int = 22050
    amplitude_threshold: float = 0.05
    amplitude_max: float = 8000.0
    smoothing_window: int = 3  # frames


@dataclass
class RVCConfig:
    """RVC (Retrieval-based Voice Conversion) configuration."""
    enabled: bool = False
    model_path: str | None = None
    index_path: str | None = None

    # RVC training settings
    training_data_dir: str = str(DATA_DIR / "rvc_training")
    output_model_dir: str = str(MODELS_DIR / "rvc")

    # Training hyperparameters
    epochs: int = 500
    batch_size: int = 8
    learning_rate: float = 0.0001


@dataclass
class AppConfig:
    """Main application configuration."""
    window_name: str = "VidChat - AI Assistant"

    # Sub-configurations
    tts: TTSConfig = field(default_factory=TTSConfig)
    avatar: AvatarConfig = field(default_factory=AvatarConfig)
    ai: AIAgentConfig = field(default_factory=AIAgentConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    rvc: RVCConfig = field(default_factory=RVCConfig)

    # Feature flags
    enable_audio_sync: bool = True
    enable_emotion_detection: bool = False
    enable_gesture_generation: bool = False

    # Debug settings
    debug: bool = False
    log_level: str = "INFO"


# Default configuration instance
default_config = AppConfig()
