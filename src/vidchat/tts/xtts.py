"""XTTS v2 Text-to-Speech engine with voice cloning.

Coqui XTTS v2 provides high-quality voice cloning with just 6 seconds of reference audio.
Supports 17 languages and zero-shot voice cloning (no training needed).
"""

import os
from pathlib import Path
from typing import Optional

try:
    from TTS.api import TTS
    XTTS_AVAILABLE = True
except ImportError:
    XTTS_AVAILABLE = False

from vidchat.tts.base import BaseTTS


class XTTSTTS(BaseTTS):
    """XTTS v2 TTS engine with voice cloning capability."""

    def __init__(
        self,
        reference_audio: str | Path,
        language: str = "en",
        device: Optional[str] = None,
    ):
        """Initialize XTTS TTS engine.

        Args:
            reference_audio: Path to reference audio file (6+ seconds) for voice cloning.
                           XTTS v2 requires a speaker reference for synthesis.
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, hu, ko, ja, hi)
            device: Device to use ("cuda" or "cpu"). Auto-detects if None.

        Raises:
            ImportError: If coqui-tts is not installed.
            FileNotFoundError: If reference_audio doesn't exist.
        """
        if not XTTS_AVAILABLE:
            raise ImportError(
                "coqui-tts is not installed. Install with: uv sync --extra voice-cloning"
            )

        self.reference_audio = Path(reference_audio)
        self.language = language

        # Validate reference audio
        if not self.reference_audio.exists():
            raise FileNotFoundError(f"Reference audio not found: {self.reference_audio}")

        # Auto-detect device
        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        # Initialize XTTS v2 model
        print(f"Loading XTTS v2 model on {self.device}...")
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False)
        self.tts.to(self.device)
        print("✓ XTTS v2 loaded")

    def synthesize(self, text: str, output_path: str | Path) -> str:
        """Synthesize speech from text using voice cloning.

        Args:
            text: Text to synthesize
            output_path: Path to save the generated audio

        Returns:
            Path to the generated audio file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Voice cloning with reference audio
        wav = self.tts.tts(
            text=text,
            speaker_wav=str(self.reference_audio),
            language=self.language,
        )

        # Save audio
        self.tts.synthesizer.save_wav(wav, str(output_path))
        return str(output_path)

    def is_available(self) -> bool:
        """Check if XTTS is available."""
        return XTTS_AVAILABLE

    def get_sample_rate(self) -> int:
        """Get the sample rate of generated audio."""
        return 24000  # XTTS v2 uses 24kHz

    @staticmethod
    def get_supported_languages() -> list[str]:
        """Get list of supported language codes."""
        return [
            "en",  # English
            "es",  # Spanish
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "pl",  # Polish
            "tr",  # Turkish
            "ru",  # Russian
            "nl",  # Dutch
            "cs",  # Czech
            "ar",  # Arabic
            "zh-cn",  # Chinese
            "hu",  # Hungarian
            "ko",  # Korean
            "ja",  # Japanese
            "hi",  # Hindi
        ]


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python xtts.py <reference_audio.wav>")
        print("\nXTTS v2 requires a reference audio file (6+ seconds) for voice cloning.")
        print(f"Supported languages: {XTTSTTS.get_supported_languages()}")
        sys.exit(1)

    ref_audio = sys.argv[1]
    print(f"Testing XTTS v2 voice cloning with: {ref_audio}")

    tts = XTTSTTS(reference_audio=ref_audio)
    output = tts.synthesize(
        "Hello! This is XTTS version two with voice cloning. The quick brown fox jumps over the lazy dog.",
        "/tmp/xtts_clone.wav"
    )
    print(f"Generated: {output}")
    print(f"Sample rate: {tts.get_sample_rate()}Hz")
    print(f"\nSupported languages: {XTTSTTS.get_supported_languages()}")
