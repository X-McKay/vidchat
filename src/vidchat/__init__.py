"""
VidChat - AI Chat Agent with Voice Cloning (Web-Only)

A modular framework for creating AI chat experiences with XTTS voice cloning.
Web interface only - OpenCV desktop UI removed for simplicity.
"""

__version__ = "0.3.0"
__author__ = "VidChat Team"

from .core.agent import VidChatAgent
from .tts.piper import PiperTTS
from .tts.xtts import XTTSTTS
from .audio.analyzer import AudioAnalyzer

__all__ = [
    "VidChatAgent",
    "PiperTTS",
    "XTTSTTS",
    "AudioAnalyzer",
]
