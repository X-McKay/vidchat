"""
Complete voice data preparation pipeline.
"""
import logging
import shutil
import csv
from pathlib import Path
from typing import Dict, List

from .config import DataPrepConfig
from .downloader import YouTubeDownloader
from .preprocessor import AudioPreprocessor
from .transcriber import WhisperTranscriber


logger = logging.getLogger(__name__)


class VoiceDataPipeline:
    """
    Complete pipeline for preparing voice training data from YouTube videos.

    Pipeline stages:
    1. Download audio from YouTube URLs
    2. Clean and normalize audio
    3. Segment audio based on silence
    4. Resample to target sample rate
    5. Transcribe with Whisper
    6. Create final dataset structure
    """

    def __init__(self, config: DataPrepConfig):
        """
        Initialize pipeline.

        Args:
            config: Data preparation configuration
        """
        self.config = config
        self.downloader = YouTubeDownloader(config)
        self.preprocessor = AudioPreprocessor(config)
        self.transcriber = WhisperTranscriber(config)

        # Statistics
        self.stats = {
            'downloaded': 0,
            'cleaned': 0,
            'segments': 0,
            'processed': 0,
            'transcribed': 0,
            'duration_seconds': 0,
        }

    def run(self, skip_download: bool = False, skip_transcription: bool = False) -> Dict:
        """
        Run the complete pipeline.

        Args:
            skip_download: Skip downloading (use existing raw audio)
            skip_transcription: Skip transcription (use existing segments)

        Returns:
            Dictionary with pipeline statistics
        """
        logger.info("=" * 60)
        logger.info("VidChat Voice Data Preparation Pipeline")
        logger.info("=" * 60)

        # Create directories
        self.config.create_directories()

        # Stage 1: Download
        if not skip_download:
            logger.info("\n[Stage 1/6] Downloading audio from YouTube...")
            downloaded = self.downloader.download_all()
            self.stats['downloaded'] = len(downloaded)
        else:
            logger.info("\n[Stage 1/6] Skipping download (using existing files)")
            downloaded = list(self.config.raw_audio_path.glob("*.wav"))
            self.stats['downloaded'] = len(downloaded)

        if self.stats['downloaded'] == 0:
            logger.error("No audio files to process. Exiting.")
            return self.stats

        # Stage 2: Clean audio
        logger.info("\n[Stage 2/6] Cleaning and normalizing audio...")
        cleaned = self.preprocessor.clean_all()
        self.stats['cleaned'] = len(cleaned)

        if self.stats['cleaned'] == 0:
            logger.error("No audio files cleaned. Exiting.")
            return self.stats

        # Stage 3: Segment audio
        logger.info("\n[Stage 3/6] Segmenting audio...")
        segments = self.preprocessor.segment_all()
        self.stats['segments'] = len(segments)

        if self.stats['segments'] == 0:
            logger.error("No segments created. Exiting.")
            return self.stats

        # Stage 4: Resample
        logger.info("\n[Stage 4/6] Resampling to target sample rate...")
        processed = self.preprocessor.resample_all()
        self.stats['processed'] = len(processed)

        # Calculate duration
        duration, _ = self.preprocessor.get_total_duration(self.config.processed_path)
        self.stats['duration_seconds'] = duration
        duration_minutes = duration / 60

        logger.info(f"✓ Total audio duration: {duration_minutes:.1f} minutes")

        # Check if we have enough data
        if duration_minutes < self.config.min_total_duration_minutes:
            logger.warning(
                f"Warning: Only {duration_minutes:.1f} minutes of audio. "
                f"Recommended minimum: {self.config.min_total_duration_minutes} minutes"
            )

        # Stage 5: Transcribe
        if not skip_transcription:
            logger.info("\n[Stage 5/6] Transcribing with Whisper...")
            transcriptions = self.transcriber.transcribe_all()
            self.stats['transcribed'] = len(transcriptions)

            # Filter low confidence
            filtered = self.transcriber.filter_low_confidence(transcriptions)
            logger.info(f"Kept {len(filtered)}/{len(transcriptions)} high-confidence transcriptions")
        else:
            logger.info("\n[Stage 5/6] Skipping transcription (using existing metadata)")
            metadata_path = self.config.final_path / "metadata.csv"
            if metadata_path.exists():
                transcriptions = self.transcriber.load_metadata(metadata_path)
                self.stats['transcribed'] = len(transcriptions)
            else:
                logger.error("No metadata file found to skip transcription")
                return self.stats

        # Stage 6: Finalize dataset
        logger.info("\n[Stage 6/6] Creating final dataset structure...")
        self._finalize_dataset()

        # Print final statistics
        self._print_statistics()

        return self.stats

    def _finalize_dataset(self):
        """Create final dataset structure."""
        final_wavs = self.config.final_path / "wavs"
        final_wavs.mkdir(parents=True, exist_ok=True)

        # Copy processed audio files to final dataset
        processed_files = list(self.config.processed_path.glob("*.wav"))

        logger.info(f"Copying {len(processed_files)} audio files to final dataset...")

        for audio_file in processed_files:
            dest = final_wavs / audio_file.name
            if not dest.exists() or not self.config.skip_existing:
                shutil.copy2(audio_file, dest)

        logger.info("✓ Final dataset created")

    def _print_statistics(self):
        """Print pipeline statistics."""
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline Complete! Statistics:")
        logger.info("=" * 60)

        duration_minutes = self.stats['duration_seconds'] / 60

        stats_lines = [
            f"Downloaded videos: {self.stats['downloaded']}",
            f"Cleaned files: {self.stats['cleaned']}",
            f"Audio segments: {self.stats['segments']}",
            f"Processed files: {self.stats['processed']}",
            f"Transcriptions: {self.stats['transcribed']}",
            f"Total duration: {duration_minutes:.1f} minutes ({duration_minutes/60:.2f} hours)",
            f"Average segment: {self.stats['duration_seconds']/self.stats['segments']:.1f} seconds",
        ]

        for line in stats_lines:
            logger.info(f"  {line}")

        logger.info("\nDataset location:")
        logger.info(f"  {self.config.final_path.absolute()}")

        logger.info("\nDataset structure:")
        logger.info(f"  {self.config.final_path}/")
        logger.info(f"    ├── wavs/  ({self.stats['processed']} files)")
        logger.info(f"    └── metadata.csv  ({self.stats['transcribed']} entries)")

        # Quality assessment
        logger.info("\nQuality Assessment:")

        if duration_minutes >= self.config.min_total_duration_minutes:
            logger.info(f"  ✓ Duration: {duration_minutes:.1f} min (sufficient)")
        else:
            logger.warning(
                f"  ⚠ Duration: {duration_minutes:.1f} min "
                f"(recommended: {self.config.min_total_duration_minutes}+ min)"
            )

        if self.stats['segments'] >= 100:
            logger.info(f"  ✓ Segments: {self.stats['segments']} (sufficient)")
        else:
            logger.warning(f"  ⚠ Segments: {self.stats['segments']} (recommended: 100+)")

        logger.info("\nNext steps:")
        logger.info("  1. Review metadata.csv and fix any transcription errors")
        logger.info("  2. Listen to random samples to verify quality")
        logger.info("  3. Remove any low-quality segments")
        logger.info("  4. Use dataset for RVC training")

        logger.info("\n" + "=" * 60)

    def clean_intermediate_files(self, keep_raw: bool = False):
        """
        Clean up intermediate files to save disk space.

        Args:
            keep_raw: Keep raw downloaded audio files
        """
        logger.info("Cleaning intermediate files...")

        if not keep_raw:
            logger.info("  Removing raw audio...")
            shutil.rmtree(self.config.raw_audio_path, ignore_errors=True)

        logger.info("  Removing clean audio...")
        shutil.rmtree(self.config.clean_audio_path, ignore_errors=True)

        logger.info("  Removing segments...")
        shutil.rmtree(self.config.segments_path, ignore_errors=True)

        logger.info("  Removing processed (keeping final dataset)...")
        # Don't remove processed as it's used by final dataset
        # Or we could move files instead of copy in finalize_dataset

        logger.info("✓ Cleanup complete")

    def export_config(self, output_path: Path):
        """
        Export configuration to file for reproducibility.

        Args:
            output_path: Path to save configuration
        """
        import json

        config_dict = {
            'youtube_urls': self.config.youtube_urls,
            'target_sample_rate': self.config.target_sample_rate,
            'whisper_model': self.config.whisper_model,
            'min_segment_length': self.config.min_segment_length,
            'max_segment_length': self.config.max_segment_length,
            'silence_thresh': self.config.silence_thresh,
        }

        with open(output_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"✓ Configuration exported to: {output_path}")
