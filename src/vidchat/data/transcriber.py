"""
Whisper-based transcription for voice training data.
"""
import logging
import csv
from pathlib import Path
from typing import List, Dict, Optional

from .config import DataPrepConfig


logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Transcribe audio files using OpenAI Whisper.
    """

    def __init__(self, config: DataPrepConfig):
        """
        Initialize transcriber.

        Args:
            config: Data preparation configuration
        """
        self.config = config
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model."""
        try:
            import whisper
            self.whisper = whisper

            logger.info(f"Loading Whisper model: {self.config.whisper_model}")
            self.model = whisper.load_model(self.config.whisper_model)
            logger.info("✓ Whisper model loaded")

        except ImportError:
            logger.error(
                "openai-whisper not installed. Install with: pip install openai-whisper"
            )
            self.whisper = None
            self.model = None

    def transcribe_audio(
        self,
        audio_path: Path,
        language: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Transcribe a single audio file.

        Args:
            audio_path: Path to audio file
            language: Language code (uses config.whisper_language if None)

        Returns:
            Dictionary with transcription results:
            {
                'filename': filename,
                'text': transcribed text,
                'confidence': average confidence score,
                'language': detected/specified language
            }
        """
        if self.model is None:
            logger.error("Whisper model not loaded")
            return None

        if language is None:
            language = self.config.whisper_language

        if self.config.verbose:
            logger.info(f"Transcribing: {audio_path.name}")

        try:
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                fp16=self.config.whisper_fp16,
                verbose=False
            )

            text = result["text"].strip()

            # Basic text cleaning
            text = text.replace("  ", " ")  # Remove double spaces
            text = text.strip()

            # Calculate confidence (if available)
            confidence = 1.0
            if "segments" in result and result["segments"]:
                # Average confidence from segments
                confidences = [
                    seg.get("no_speech_prob", 0.0)
                    for seg in result["segments"]
                ]
                # Convert no_speech_prob to confidence
                confidence = 1.0 - (sum(confidences) / len(confidences))

            return {
                'filename': audio_path.name,
                'text': text,
                'confidence': confidence,
                'language': result.get('language', language)
            }

        except Exception as e:
            logger.error(f"Error transcribing {audio_path.name}: {e}")
            return None

    def transcribe_all(
        self,
        input_dir: Optional[Path] = None,
        output_csv: Optional[Path] = None
    ) -> List[Dict[str, any]]:
        """
        Transcribe all audio files in a directory.

        Args:
            input_dir: Input directory (uses config.processed_path if None)
            output_csv: Output CSV path (saves to config.final_path/metadata.csv if None)

        Returns:
            List of transcription results
        """
        if input_dir is None:
            input_dir = self.config.processed_path

        if output_csv is None:
            output_csv = self.config.final_path / "metadata.csv"

        audio_files = sorted(input_dir.glob("*.wav"))

        logger.info(f"Transcribing {len(audio_files)} audio files...")

        transcriptions = []
        for i, audio_file in enumerate(audio_files, 1):
            result = self.transcribe_audio(audio_file)

            if result:
                transcriptions.append(result)

                if self.config.verbose:
                    preview = result['text'][:50]
                    logger.info(f"  [{i}/{len(audio_files)}] {preview}...")

        logger.info(f"✓ Transcribed {len(transcriptions)}/{len(audio_files)} files")

        # Save to CSV
        if transcriptions:
            self._save_metadata(transcriptions, output_csv)

        return transcriptions

    def _save_metadata(
        self,
        transcriptions: List[Dict[str, any]],
        output_path: Path
    ):
        """
        Save transcriptions to CSV file.

        Args:
            transcriptions: List of transcription dictionaries
            output_path: Output CSV file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['filename', 'text', 'confidence', 'language']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for trans in transcriptions:
                writer.writerow({
                    'filename': trans['filename'],
                    'text': trans['text'],
                    'confidence': trans.get('confidence', 1.0),
                    'language': trans.get('language', 'en')
                })

        logger.info(f"✓ Saved metadata to: {output_path}")

    def filter_low_confidence(
        self,
        transcriptions: List[Dict[str, any]],
        min_confidence: Optional[float] = None
    ) -> List[Dict[str, any]]:
        """
        Filter transcriptions by confidence threshold.

        Args:
            transcriptions: List of transcription dictionaries
            min_confidence: Minimum confidence (uses config.min_transcription_confidence if None)

        Returns:
            Filtered list of transcriptions
        """
        if min_confidence is None:
            min_confidence = self.config.min_transcription_confidence

        filtered = [
            t for t in transcriptions
            if t.get('confidence', 1.0) >= min_confidence
        ]

        removed_count = len(transcriptions) - len(filtered)
        if removed_count > 0:
            logger.info(
                f"Filtered out {removed_count} low-confidence transcriptions "
                f"(threshold: {min_confidence})"
            )

        return filtered

    def load_metadata(self, csv_path: Path) -> List[Dict[str, any]]:
        """
        Load transcriptions from CSV file.

        Args:
            csv_path: Path to metadata CSV file

        Returns:
            List of transcription dictionaries
        """
        transcriptions = []

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert confidence to float
                row['confidence'] = float(row.get('confidence', 1.0))
                transcriptions.append(row)

        return transcriptions
