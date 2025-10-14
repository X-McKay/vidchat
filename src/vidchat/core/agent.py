"""
Core VidChat agent with avatar rendering support.

This agent integrates AI chat, TTS, and avatar rendering for the web interface.
"""
import asyncio
import tempfile
import os
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider

from ..config import AppConfig, default_config
from ..tts import PiperTTS, HybridTTS, RVCTTS, XTTSTTS
from ..avatar import SadTalkerRenderer
from ..utils import get_logger


class VidChatAgent:
    """Main VidChat agent for AI chat, TTS, and avatar rendering."""

    def __init__(self, config: AppConfig | None = None):
        """
        Initialize VidChat agent.

        Args:
            config: Application configuration
        """
        self.config = config or default_config

        # Initialize AI agent
        self._init_ai_agent()

        # Initialize TTS engine
        self._init_tts()

        # Initialize avatar renderer (SadTalker)
        self._init_avatar()

        # Logger
        self.logger = get_logger("vidchat.agent")

    def _init_avatar(self):
        """Initialize SadTalker avatar renderer."""
        self.avatar = SadTalkerRenderer(self.config.avatar)

    def _init_ai_agent(self):
        """Initialize PydanticAI agent with Ollama."""
        ollama_provider = OllamaProvider(
            base_url=self.config.ai.ollama_base_url
        )

        model = OpenAIChatModel(
            model_name=self.config.ai.model_name,
            provider=ollama_provider
        )

        self.ai_agent = Agent(
            model=model,
            system_prompt=self.config.ai.system_prompt
        )

    def _init_tts(self):
        """Initialize TTS engine based on provider."""
        provider = self.config.tts.provider.lower()

        if provider == "xtts":
            # XTTS voice cloning
            if not self.config.tts.xtts_reference_audio:
                raise ValueError("XTTS provider requires xtts_reference_audio in config")
            self.tts = XTTSTTS(
                reference_audio=self.config.tts.xtts_reference_audio,
                language=self.config.tts.xtts_language,
            )
        elif provider == "piper":
            # Standard Piper TTS
            self.tts = PiperTTS(self.config.tts)
        elif provider in ("piper+rvc", "hybrid"):
            # Hybrid: Piper + RVC voice conversion
            base_tts = PiperTTS(self.config.tts)
            if self.config.rvc.enabled:
                rvc = RVCTTS(self.config.rvc)
                self.tts = HybridTTS(base_tts, rvc)
            else:
                self.tts = base_tts
        else:
            # Fallback to Piper
            self.logger.warning(f"Unknown TTS provider '{provider}', using Piper")
            self.tts = PiperTTS(self.config.tts)

    async def chat(self, user_input: str) -> str:
        """
        Process user input and get AI response.

        Args:
            user_input: User's message

        Returns:
            AI response text
        """
        print(f"\n[You]: {user_input}")

        result = await self.ai_agent.run(user_input)
        response_obj = result.response

        # Extract text from response
        if hasattr(response_obj, 'parts') and len(response_obj.parts) > 0:
            response_text = response_obj.parts[0].content
        else:
            response_text = str(response_obj)

        return response_text

    def generate_speech(self, text: str, output_path: str | None = None) -> str:
        """
        Generate speech audio from text.

        Args:
            text: Text to synthesize
            output_path: Optional output path (temp file if not provided)

        Returns:
            Path to generated audio file
        """
        if output_path is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file.close()
            output_path = temp_file.name

        self.tts.synthesize(text, output_path)
        return output_path
