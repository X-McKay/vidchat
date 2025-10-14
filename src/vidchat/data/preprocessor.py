"""
Audio preprocessing for voice training data.
"""
import logging
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
import soundfile as sf

from .config import DataPrepConfig


logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """
    Preprocess audio files for voice training.

    Features:
    - Noise reduction
    - Normalization
    - Silence removal and segmentation
    - Resampling
    """

    def __init__(self, config: DataPrepConfig):
        """
        Initialize preprocessor.

        Args:
            config: Data preparation configuration
        """
        self.config = config
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if required libraries are available."""
        try:
            import librosa
            self.librosa = librosa
        except ImportError:
            logger.warning("librosa not installed. Install with: pip install librosa")
            self.librosa = None

        try:
            import noisereduce as nr
            self.nr = nr
        except ImportError:
            logger.warning("noisereduce not installed. Install with: pip install noisereduce")
            self.nr = None

        try:
            from pydub import AudioSegment
            from pydub.silence import split_on_silence
            from pydub.effects import normalize
            self.AudioSegment = AudioSegment
            self.split_on_silence = split_on_silence
            self.normalize = normalize
        except ImportError:
            logger.warning("pydub not installed. Install with: pip install pydub")
            self.AudioSegment = None

    def clean_audio(
        self,
        input_path: Path,
        output_path: Path,
        apply_noise_reduction: bool = True,
        normalize: bool = True
    ) -> Path:
        """
        Clean a single audio file.

        Args:
            input_path: Input audio file path
            output_path: Output audio file path
            apply_noise_reduction: Whether to apply noise reduction
            normalize: Whether to normalize volume

        Returns:
            Path to cleaned audio file
        """
        if self.config.verbose:
            logger.info(f"Cleaning: {input_path.name}")

        # Load audio
        audio, sr = sf.read(input_path)

        # Normalize volume
        if normalize:
            audio = audio / np.max(np.abs(audio)) * 0.95

        # Apply noise reduction
        if apply_noise_reduction and self.nr is not None:
            audio = self.nr.reduce_noise(
                y=audio,
                sr=sr,
                prop_decrease=self.config.noise_reduction_strength
            )

        # Save cleaned audio
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, audio, sr)

        return output_path

    def clean_all(
        self,
        input_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Clean all audio files in a directory.

        Args:
            input_dir: Input directory (uses config.raw_audio_path if None)
            output_dir: Output directory (uses config.clean_audio_path if None)

        Returns:
            List of cleaned audio file paths
        """
        if input_dir is None:
            input_dir = self.config.raw_audio_path
        if output_dir is None:
            output_dir = self.config.clean_audio_path

        output_dir.mkdir(parents=True, exist_ok=True)

        # Find all audio files
        audio_files = list(input_dir.glob("*.wav")) + list(input_dir.glob("*.mp3"))

        logger.info(f"Cleaning {len(audio_files)} audio files...")

        cleaned_files = []
        for audio_file in audio_files:
            output_file = output_dir / f"{audio_file.stem}.wav"

            if self.config.skip_existing and output_file.exists():
                logger.debug(f"Skipping existing: {output_file.name}")
                cleaned_files.append(output_file)
                continue

            try:
                cleaned = self.clean_audio(
                    audio_file,
                    output_file,
                    apply_noise_reduction=self.config.apply_noise_reduction,
                    normalize=self.config.normalize_audio
                )
                cleaned_files.append(cleaned)
            except Exception as e:
                logger.error(f"Error cleaning {audio_file.name}: {e}")

        logger.info(f"✓ Cleaned {len(cleaned_files)} files")
        return cleaned_files

    def segment_audio(
        self,
        input_path: Path,
        output_dir: Path
    ) -> List[Path]:
        """
        Split audio file into segments based on silence.

        Args:
            input_path: Input audio file
            output_dir: Directory for output segments

        Returns:
            List of segment file paths
        """
        if self.AudioSegment is None:
            logger.error("pydub not available for segmentation")
            return []

        if self.config.verbose:
            logger.info(f"Segmenting: {input_path.name}")

        # Load audio
        audio = self.AudioSegment.from_wav(input_path)

        # Split on silence
        chunks = self.split_on_silence(
            audio,
            min_silence_len=self.config.min_silence_len,
            silence_thresh=self.config.silence_thresh,
            keep_silence=self.config.keep_silence
        )

        # Export segments of appropriate length
        output_dir.mkdir(parents=True, exist_ok=True)
        segment_paths = []

        base_name = input_path.stem
        for i, chunk in enumerate(chunks):
            chunk_len = len(chunk)

            # Skip segments that are too short or too long
            if chunk_len < self.config.min_segment_length:
                continue
            if chunk_len > self.config.max_segment_length:
                # Could split further, but skip for now
                continue

            segment_path = output_dir / f"{base_name}_seg{i:04d}.wav"
            chunk.export(segment_path, format="wav")
            segment_paths.append(segment_path)

        return segment_paths

    def segment_all(
        self,
        input_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Segment all audio files in a directory.

        Args:
            input_dir: Input directory (uses config.clean_audio_path if None)
            output_dir: Output directory (uses config.segments_path if None)

        Returns:
            List of all segment file paths
        """
        if input_dir is None:
            input_dir = self.config.clean_audio_path
        if output_dir is None:
            output_dir = self.config.segments_path

        audio_files = list(input_dir.glob("*.wav"))

        logger.info(f"Segmenting {len(audio_files)} audio files...")

        all_segments = []
        for audio_file in audio_files:
            try:
                segments = self.segment_audio(audio_file, output_dir)
                all_segments.extend(segments)
            except Exception as e:
                logger.error(f"Error segmenting {audio_file.name}: {e}")

        logger.info(f"✓ Created {len(all_segments)} segments from {len(audio_files)} files")
        return all_segments

    def resample_audio(
        self,
        input_path: Path,
        output_path: Path,
        target_sr: Optional[int] = None
    ) -> Path:
        """
        Resample audio to target sample rate.

        Args:
            input_path: Input audio file
            output_path: Output audio file
            target_sr: Target sample rate (uses config.target_sample_rate if None)

        Returns:
            Path to resampled audio file
        """
        if target_sr is None:
            target_sr = self.config.target_sample_rate

        if self.librosa is None:
            logger.error("librosa not available for resampling")
            return input_path

        # Load audio
        audio, sr = self.librosa.load(input_path, sr=None)

        # Resample if necessary
        if sr != target_sr:
            audio = self.librosa.resample(audio, orig_sr=sr, target_sr=target_sr)

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(output_path, audio, target_sr)

        return output_path

    def resample_all(
        self,
        input_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> List[Path]:
        """
        Resample all audio files in a directory.

        Args:
            input_dir: Input directory (uses config.segments_path if None)
            output_dir: Output directory (uses config.processed_path if None)

        Returns:
            List of resampled audio file paths
        """
        if input_dir is None:
            input_dir = self.config.segments_path
        if output_dir is None:
            output_dir = self.config.processed_path

        output_dir.mkdir(parents=True, exist_ok=True)

        audio_files = list(input_dir.glob("*.wav"))

        logger.info(f"Resampling {len(audio_files)} files to {self.config.target_sample_rate}Hz...")

        resampled_files = []
        for audio_file in audio_files:
            output_file = output_dir / audio_file.name

            if self.config.skip_existing and output_file.exists():
                logger.debug(f"Skipping existing: {output_file.name}")
                resampled_files.append(output_file)
                continue

            try:
                resampled = self.resample_audio(audio_file, output_file)
                resampled_files.append(resampled)
            except Exception as e:
                logger.error(f"Error resampling {audio_file.name}: {e}")

        logger.info(f"✓ Resampled {len(resampled_files)} files")
        return resampled_files

    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get duration of audio file in seconds.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds
        """
        info = sf.info(audio_path)
        return info.duration

    def get_total_duration(self, audio_dir: Path) -> Tuple[float, int]:
        """
        Get total duration of all audio files in a directory.

        Args:
            audio_dir: Directory containing audio files

        Returns:
            Tuple of (total_duration_seconds, file_count)
        """
        audio_files = list(audio_dir.glob("*.wav"))
        total_duration = sum(self.get_audio_duration(f) for f in audio_files)
        return total_duration, len(audio_files)
