"""
Base TTS interface for text-to-speech engines.
"""
from abc import ABC, abstractmethod
from pathlib import Path


class BaseTTS(ABC):
    """Abstract base class for TTS engines."""

    @abstractmethod
    def synthesize(self, text: str, output_path: str | Path) -> str:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file

        Returns:
            Path to generated audio file
        """
        pass

    @abstractmethod
    def get_sample_rate(self) -> int:
        """Get the sample rate of generated audio."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if TTS engine is available and properly configured."""
        pass
