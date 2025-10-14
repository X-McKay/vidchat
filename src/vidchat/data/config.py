"""
Configuration for voice data preparation pipeline.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class DataPrepConfig:
    """Configuration for voice data preparation pipeline."""

    # YouTube URLs
    youtube_urls: List[str] = field(default_factory=list)
    youtube_urls_file: str | Path | None = None  # Path to file with URLs (one per line)

    # Directory structure
    output_dir: Path = Path("voice_data")
    raw_audio_dir: str = "01_raw_audio"
    clean_audio_dir: str = "02_clean_audio"
    segments_dir: str = "03_segments"
    processed_dir: str = "04_processed"
    final_dir: str = "voice_dataset"

    # YouTube download settings
    audio_format: str = "wav"
    audio_quality: str = "0"  # Best quality

    # Audio preprocessing
    target_sample_rate: int = 22050
    normalize_audio: bool = True
    apply_noise_reduction: bool = True
    noise_reduction_strength: float = 0.5

    # Segmentation settings
    min_silence_len: int = 500  # milliseconds
    silence_thresh: int = -40  # dBFS
    keep_silence: int = 200  # milliseconds at edges
    min_segment_length: int = 2000  # milliseconds (2 seconds)
    max_segment_length: int = 10000  # milliseconds (10 seconds)

    # Transcription settings
    whisper_model: str = "medium"  # tiny, base, small, medium, large
    whisper_language: str = "en"
    whisper_fp16: bool = True  # Use FP16 if GPU available

    # Quality control
    min_total_duration_minutes: int = 30
    max_total_duration_minutes: int = 180  # 3 hours
    min_transcription_confidence: float = 0.8

    # Processing options
    skip_existing: bool = True
    verbose: bool = True
    parallel_downloads: int = 3
    parallel_transcription: int = 1  # GPU bottleneck

    def __post_init__(self):
        """Ensure output_dir is a Path object."""
        if not isinstance(self.output_dir, Path):
            self.output_dir = Path(self.output_dir)

        # Load URLs from file if specified
        if self.youtube_urls_file:
            urls_file = Path(self.youtube_urls_file)
            if urls_file.exists():
                with open(urls_file, 'r') as f:
                    file_urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    self.youtube_urls.extend(file_urls)

    def get_path(self, subdir: str) -> Path:
        """Get full path for a subdirectory."""
        return self.output_dir / subdir

    @property
    def raw_audio_path(self) -> Path:
        return self.get_path(self.raw_audio_dir)

    @property
    def clean_audio_path(self) -> Path:
        return self.get_path(self.clean_audio_dir)

    @property
    def segments_path(self) -> Path:
        return self.get_path(self.segments_dir)

    @property
    def processed_path(self) -> Path:
        return self.get_path(self.processed_dir)

    @property
    def final_path(self) -> Path:
        return self.get_path(self.final_dir)

    def create_directories(self):
        """Create all necessary directories."""
        for path in [
            self.raw_audio_path,
            self.clean_audio_path,
            self.segments_path,
            self.processed_path,
            self.final_path / "wavs",
        ]:
            path.mkdir(parents=True, exist_ok=True)


def load_config_from_python_file(file_path: str | Path) -> DataPrepConfig:
    """
    Load configuration from a Python file that defines youtube_videos list.

    Args:
        file_path: Path to Python file containing youtube_videos list

    Returns:
        DataPrepConfig with loaded URLs
    """
    file_path = Path(file_path)

    # Read and exec the file
    namespace = {}
    with open(file_path, 'r') as f:
        exec(f.read(), namespace)

    # Extract youtube_videos list
    youtube_urls = namespace.get('youtube_videos', [])

    return DataPrepConfig(youtube_urls=youtube_urls)


# Default configuration
default_config = DataPrepConfig()
