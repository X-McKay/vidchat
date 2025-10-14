"""
Audio analysis module for lip-sync and voice processing.
"""
import wave
import numpy as np
from typing import List, Tuple
from ..config import AudioConfig


class AudioAnalyzer:
    """Analyzes audio files for amplitude, pitch, and other features."""

    def __init__(self, config: AudioConfig | None = None):
        """Initialize audio analyzer with configuration."""
        from ..config import default_config
        self.config = config or default_config.audio

    def analyze_amplitude(self, audio_path: str, target_fps: int = 30) -> List[float]:
        """
        Analyze audio file to extract amplitude data for lip-sync.

        Args:
            audio_path: Path to WAV audio file
            target_fps: Target frames per second for video

        Returns:
            List of amplitude values (0.0 to 1.0) for each video frame
        """
        with wave.open(audio_path, 'rb') as wav:
            sample_rate = wav.getframerate()
            n_frames = wav.getnframes()
            audio_data = wav.readframes(n_frames)

            # Convert bytes to numpy array
            samples = np.frombuffer(audio_data, dtype=np.int16)

            # Calculate amplitude envelope
            samples_per_frame = int(sample_rate / target_fps)
            n_video_frames = len(samples) // samples_per_frame

            amplitudes = []
            for i in range(n_video_frames):
                start = i * samples_per_frame
                end = start + samples_per_frame
                frame_samples = samples[start:end]

                # Calculate RMS (root mean square) amplitude
                rms = np.sqrt(np.mean(frame_samples.astype(float) ** 2))

                # Normalize to 0-1 range
                normalized = min(rms / self.config.amplitude_max, 1.0)

                # Apply threshold
                if normalized < self.config.amplitude_threshold:
                    normalized = 0.0

                amplitudes.append(normalized)

            return amplitudes

    def smooth_amplitude(self, amplitudes: List[float], window_size: int | None = None) -> List[float]:
        """
        Apply smoothing to amplitude data for more natural movement.

        Args:
            amplitudes: Raw amplitude values
            window_size: Size of smoothing window (default from config)

        Returns:
            Smoothed amplitude values
        """
        if window_size is None:
            window_size = self.config.smoothing_window

        if window_size <= 1:
            return amplitudes

        smoothed = []
        for i in range(len(amplitudes)):
            start = max(0, i - window_size // 2)
            end = min(len(amplitudes), i + window_size // 2 + 1)
            window = amplitudes[start:end]
            smoothed.append(sum(window) / len(window))

        return smoothed

    def get_audio_info(self, audio_path: str) -> dict:
        """
        Get audio file information.

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio information
        """
        with wave.open(audio_path, 'rb') as wav:
            return {
                'sample_rate': wav.getframerate(),
                'n_frames': wav.getnframes(),
                'n_channels': wav.getnchannels(),
                'sample_width': wav.getsampwidth(),
                'duration': wav.getnframes() / wav.getframerate()
            }

    def detect_silence(self, audio_path: str, threshold: float = 0.05) -> List[Tuple[float, float]]:
        """
        Detect silent regions in audio.

        Args:
            audio_path: Path to audio file
            threshold: Amplitude threshold for silence

        Returns:
            List of (start_time, end_time) tuples for silent regions
        """
        amplitudes = self.analyze_amplitude(audio_path)
        info = self.get_audio_info(audio_path)
        fps = 30
        frame_duration = 1.0 / fps

        silent_regions = []
        in_silence = False
        silence_start = 0.0

        for i, amp in enumerate(amplitudes):
            time = i * frame_duration

            if amp < threshold and not in_silence:
                # Start of silence
                in_silence = True
                silence_start = time
            elif amp >= threshold and in_silence:
                # End of silence
                in_silence = False
                silent_regions.append((silence_start, time))

        # Handle case where audio ends in silence
        if in_silence:
            silent_regions.append((silence_start, info['duration']))

        return silent_regions
