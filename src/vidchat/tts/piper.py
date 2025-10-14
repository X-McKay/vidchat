"""
Piper TTS engine implementation.
"""
import subprocess
import tempfile
from pathlib import Path
from .base import BaseTTS
from ..config import TTSConfig


class PiperTTS(BaseTTS):
    """Piper TTS engine for high-quality speech synthesis."""

    def __init__(self, config: TTSConfig | None = None):
        """
        Initialize Piper TTS engine.

        Args:
            config: TTS configuration
        """
        from ..config import default_config
        self.config = config or default_config.tts
        self.model_path = Path(self.config.piper_model)

    def synthesize(self, text: str, output_path: str | Path) -> str:
        """
        Synthesize speech from text using Piper.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file

        Returns:
            Path to generated audio file
        """
        output_path = Path(output_path)

        cmd = [
            "piper",
            "--model", str(self.model_path),
            "--output_file", str(output_path)
        ]

        result = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Piper TTS failed: {result.stderr}")

        if not output_path.exists():
            raise RuntimeError(f"Piper TTS did not create output file: {output_path}")

        return str(output_path)

    def get_sample_rate(self) -> int:
        """Get the sample rate of generated audio."""
        return self.config.sample_rate

    def is_available(self) -> bool:
        """Check if Piper TTS is available."""
        try:
            result = subprocess.run(
                ["piper", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def list_available_voices(self) -> list[str]:
        """
        List available voice models.

        Returns:
            List of voice model paths
        """
        models_dir = self.model_path.parent
        if not models_dir.exists():
            return []

        return [
            str(f) for f in models_dir.glob("*.onnx")
        ]
