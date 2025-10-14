## Voice Data Preparation Guide

Complete guide for preparing voice training data from YouTube videos using VidChat's integrated pipeline.

## Overview

The voice data preparation system automates the entire process of creating a training dataset:

1. **Download** audio from YouTube videos
2. **Clean** and normalize audio quality
3. **Segment** audio based on silence detection
4. **Resample** to consistent sample rate
5. **Transcribe** with OpenAI Whisper
6. **Package** as ready-to-use training dataset

## Quick Start

### 1. Install Dependencies

```bash
# Install voice preparation dependencies
uv sync --extra voice-prep

# Or install all optional dependencies
uv sync --all-extras
```

### 2. Prepare YouTube URLs

Edit `youtube_list.py` with your target videos:

```python
youtube_videos = [
    "https://www.youtube.com/watch?v=VIDEO_ID_1",
    "https://www.youtube.com/watch?v=VIDEO_ID_2",
    "https://www.youtube.com/shorts/SHORT_ID",
]
```

### 3. Run Pipeline

```bash
# Basic usage (uses youtube_list.py)
uv run python prepare_voice_data.py

# With custom URL file
uv run python prepare_voice_data.py --urls my_urls.txt

# Verbose output
uv run python prepare_voice_data.py --verbose
```

### 4. Review Dataset

The pipeline creates:
```
voice_data/
└── voice_dataset/
    ├── wavs/              # Audio segments (22050Hz WAV)
    │   ├── video1_seg0000.wav
    │   ├── video1_seg0001.wav
    │   └── ...
    └── metadata.csv       # Transcriptions
```

## Configuration

### Using Python Configuration File

Create a custom config file (e.g., `my_config.py`):

```python
youtube_videos = [
    "https://www.youtube.com/watch?v=VIDEO_1",
    "https://www.youtube.com/watch?v=VIDEO_2",
]

# Optional: Additional configuration
# (These override defaults when loaded programmatically)
```

Then use it:
```bash
python prepare_voice_data.py --config my_config.py
```

### Using Text File for URLs

Create `urls.txt`:
```
https://www.youtube.com/watch?v=VIDEO_1
https://www.youtube.com/watch?v=VIDEO_2
# Comments start with #
https://www.youtube.com/watch?v=VIDEO_3
```

Use it:
```bash
python prepare_voice_data.py --urls urls.txt
```

### Command-Line Options

```bash
python prepare_voice_data.py [OPTIONS]

Options:
  --config FILE           Config file (default: youtube_list.py)
  --urls FILE             Text file with URLs (one per line)
  --output-dir DIR        Output directory (default: voice_data)
  --whisper-model SIZE    Whisper model: tiny/base/small/medium/large
  --target-sr HZ          Target sample rate (default: 22050)
  --skip-download         Skip download (use existing raw audio)
  --skip-transcription    Skip transcription (use existing metadata)
  --no-noise-reduction    Disable noise reduction
  --verbose               Verbose output
  --clean-intermediate    Delete intermediate files after completion
```

## Advanced Configuration

### Programmatic Usage

```python
from vidchat.data.config import DataPrepConfig
from vidchat.data.pipeline import VoiceDataPipeline

# Create custom configuration
config = DataPrepConfig(
    youtube_urls=[
        "https://www.youtube.com/watch?v=VIDEO_1",
        "https://www.youtube.com/watch?v=VIDEO_2",
    ],
    output_dir="my_voice_data",

    # Audio settings
    target_sample_rate=22050,
    normalize_audio=True,
    apply_noise_reduction=True,
    noise_reduction_strength=0.5,

    # Segmentation settings
    min_segment_length=2000,  # 2 seconds
    max_segment_length=10000,  # 10 seconds
    silence_thresh=-40,  # dBFS
    min_silence_len=500,  # milliseconds

    # Transcription settings
    whisper_model="medium",
    whisper_language="en",

    # Performance
    parallel_downloads=3,
    verbose=True,
)

# Run pipeline
pipeline = VoiceDataPipeline(config)
stats = pipeline.run()

# Print statistics
print(f"Processed {stats['segments']} segments")
print(f"Total duration: {stats['duration_seconds']/60:.1f} minutes")
```

### Individual Components

Use pipeline components separately:

```python
from vidchat.data.downloader import YouTubeDownloader
from vidchat.data.preprocessor import AudioPreprocessor
from vidchat.data.transcriber import WhisperTranscriber

# Download only
downloader = YouTubeDownloader(config)
files = downloader.download_all([
    "https://www.youtube.com/watch?v=VIDEO_ID"
])

# Preprocess only
preprocessor = AudioPreprocessor(config)
cleaned = preprocessor.clean_all(input_dir="raw_audio")
segments = preprocessor.segment_all(input_dir="clean_audio")
processed = preprocessor.resample_all(input_dir="segments")

# Transcribe only
transcriber = WhisperTranscriber(config)
transcriptions = transcriber.transcribe_all(input_dir="processed")
```

## Pipeline Stages Explained

### Stage 1: Download Audio

- Uses `yt-dlp` to download best quality audio
- Extracts audio to WAV format
- Parallel downloads (configurable)
- Handles YouTube videos, shorts, and playlists

**Configuration:**
```python
config = DataPrepConfig(
    audio_format="wav",
    audio_quality="0",  # Best quality
    parallel_downloads=3,
)
```

### Stage 2: Clean Audio

- Normalizes volume levels
- Reduces background noise (optional)
- Converts to consistent format

**Configuration:**
```python
config = DataPrepConfig(
    normalize_audio=True,
    apply_noise_reduction=True,
    noise_reduction_strength=0.5,  # 0.0 to 1.0
)
```

### Stage 3: Segment Audio

- Splits audio on silence
- Keeps segments between 2-10 seconds
- Removes excessive silence

**Configuration:**
```python
config = DataPrepConfig(
    min_segment_length=2000,  # milliseconds
    max_segment_length=10000,
    silence_thresh=-40,  # dBFS
    min_silence_len=500,  # milliseconds
    keep_silence=200,  # milliseconds at edges
)
```

### Stage 4: Resample

- Resamples all audio to target sample rate
- Ensures consistency across dataset
- Standard: 22050Hz for voice training

**Configuration:**
```python
config = DataPrepConfig(
    target_sample_rate=22050,  # Hz
)
```

### Stage 5: Transcribe

- Uses OpenAI Whisper for transcription
- Supports multiple model sizes
- Generates confidence scores
- Filters low-confidence transcriptions

**Configuration:**
```python
config = DataPrepConfig(
    whisper_model="medium",  # tiny/base/small/medium/large
    whisper_language="en",
    whisper_fp16=True,  # Use FP16 if GPU available
    min_transcription_confidence=0.8,
)
```

### Stage 6: Finalize

- Creates final dataset structure
- Copies files to `voice_dataset/`
- Generates metadata.csv
- Exports pipeline configuration

## Quality Metrics

### Target Metrics

✅ **Total duration:** 30+ minutes (minimum), 1-3 hours (ideal)
✅ **Number of segments:** 100+ (minimum), 300-1000 (ideal)
✅ **Transcription accuracy:** 90%+ (manually verified)
✅ **Audio quality:** Consistent, no background music
✅ **Segment length:** 2-10 seconds each

### Quality Checks

The pipeline automatically checks:
- Total audio duration
- Number of segments created
- Transcription confidence scores

After completion, manually verify:
1. Listen to random samples
2. Check transcription accuracy
3. Remove poor quality segments
4. Fix transcription errors in metadata.csv

## Examples

### Example 1: Basic Usage

```bash
# 1. Edit youtube_list.py with your URLs
# 2. Run pipeline
uv run python prepare_voice_data.py --verbose

# 3. Review results
ls voice_data/voice_dataset/wavs/
head voice_data/voice_dataset/metadata.csv
```

### Example 2: Custom Configuration

```python
# custom_prep.py
from vidchat.data.config import DataPrepConfig
from vidchat.data.pipeline import VoiceDataPipeline

config = DataPrepConfig(
    youtube_urls=[
        "https://www.youtube.com/watch?v=EXAMPLE_1",
        "https://www.youtube.com/watch?v=EXAMPLE_2",
    ],
    output_dir="custom_voice_data",
    whisper_model="large",  # Better accuracy
    target_sample_rate=22050,
    verbose=True,
)

pipeline = VoiceDataPipeline(config)
stats = pipeline.run()
```

### Example 3: Resuming After Interruption

```bash
# If pipeline was interrupted, skip completed stages
uv run python prepare_voice_data.py --skip-download --skip-transcription
```

### Example 4: Different Whisper Models

```bash
# Fast (less accurate)
python prepare_voice_data.py --whisper-model tiny

# Balanced (recommended)
python prepare_voice_data.py --whisper-model medium

# Best accuracy (slower)
python prepare_voice_data.py --whisper-model large
```

## Troubleshooting

### Issue: "yt-dlp not found"

```bash
# Install yt-dlp
uv sync --extra voice-prep

# Or manually
pip install yt-dlp
```

### Issue: "openai-whisper not found"

```bash
# Install Whisper
uv sync --extra voice-prep

# Or manually
pip install openai-whisper
```

### Issue: "CUDA out of memory"

Solutions:
1. Use smaller Whisper model: `--whisper-model small`
2. Disable FP16 in config: `whisper_fp16=False`
3. Process fewer files at once

### Issue: "No segments created"

Causes:
- Audio too short
- Silence threshold too aggressive
- No clear speech in audio

Solutions:
```python
config = DataPrepConfig(
    silence_thresh=-50,  # More lenient (was -40)
    min_silence_len=800,  # Longer silence (was 500)
    min_segment_length=1000,  # Shorter segments (was 2000)
)
```

### Issue: "Low transcription quality"

Solutions:
1. Use larger Whisper model: `--whisper-model large`
2. Manually correct metadata.csv
3. Remove poor quality segments

### Issue: "Insufficient audio duration"

The pipeline warns if duration < 30 minutes. Solutions:
1. Add more YouTube URLs
2. Use longer videos
3. Process anyway (might still work for RVC)

## Directory Structure

```
voice_data/
├── 01_raw_audio/           # Downloaded audio (can be deleted)
├── 02_clean_audio/         # Cleaned audio (can be deleted)
├── 03_segments/            # Segmented audio (can be deleted)
├── 04_processed/           # Resampled segments (can be deleted)
└── voice_dataset/          # Final dataset (keep this!)
    ├── wavs/               # All audio segments
    │   ├── video1_seg0000.wav
    │   ├── video1_seg0001.wav
    │   └── ...
    ├── metadata.csv        # Transcriptions
    └── pipeline_config.json # Configuration used
```

**Disk space:** Raw audio can use 100MB+ per video. Clean intermediate files with:
```bash
python prepare_voice_data.py --clean-intermediate
```

## Next Steps

After preparing your dataset:

1. **Review Quality**
   ```bash
   # Check metadata
   head -20 voice_data/voice_dataset/metadata.csv

   # Count segments
   ls voice_data/voice_dataset/wavs/ | wc -l
   ```

2. **Manual Corrections**
   - Open `metadata.csv` in spreadsheet editor
   - Listen to audio while reading transcriptions
   - Fix errors, remove bad segments

3. **Use for Training**
   - Your dataset is ready for RVC training
   - See `TRAINING_PLANS.md` for training instructions
   - Dataset format compatible with standard voice training tools

## Tips for Best Results

### Choosing YouTube Videos

✅ **Good sources:**
- Interviews (single speaker, clear audio)
- Podcasts (minimal background noise)
- Lectures/presentations
- Voice-over narration
- Clean studio recordings

❌ **Avoid:**
- Music videos
- Multi-speaker conversations
- Noisy environments
- Heavy audio effects
- Compressed/low-quality audio

### Optimizing Quality

1. **Start with 3-5 videos** (~1-2 hours total)
2. **Check first batch** before processing more
3. **Listen to samples** to verify quality
4. **Adjust configuration** based on results
5. **Iterate** until satisfied

### Performance Tips

- **Parallel downloads:** Set `parallel_downloads=5` for faster downloading
- **Skip existing:** Use `skip_existing=True` to resume interrupted runs
- **GPU acceleration:** Whisper runs faster with CUDA
- **Smaller model:** Use `whisper-model=small` for faster transcription

## Reference

### DataPrepConfig Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `youtube_urls` | `[]` | List of YouTube URLs |
| `output_dir` | `"voice_data"` | Output directory |
| `target_sample_rate` | `22050` | Target sample rate (Hz) |
| `normalize_audio` | `True` | Normalize volume |
| `apply_noise_reduction` | `True` | Apply noise reduction |
| `min_segment_length` | `2000` | Min segment length (ms) |
| `max_segment_length` | `10000` | Max segment length (ms) |
| `silence_thresh` | `-40` | Silence threshold (dBFS) |
| `whisper_model` | `"medium"` | Whisper model size |
| `whisper_language` | `"en"` | Language code |
| `parallel_downloads` | `3` | Parallel download workers |
| `verbose` | `True` | Verbose output |

### Whisper Model Comparison

| Model | Size | Speed | Accuracy | GPU RAM |
|-------|------|-------|----------|---------|
| tiny | 39M | Very Fast | Low | ~1GB |
| base | 74M | Fast | Medium | ~1GB |
| small | 244M | Medium | Good | ~2GB |
| medium | 769M | Slow | Very Good | ~5GB |
| large | 1550M | Very Slow | Excellent | ~10GB |

**Recommendation:** Use `medium` for best balance of speed and accuracy.

## Credits

- **yt-dlp:** YouTube download
- **OpenAI Whisper:** Transcription
- **librosa:** Audio processing
- **pydub:** Audio manipulation
- **noisereduce:** Noise reduction

For more information, see [VOICE_DATAPREP.md](VOICE_DATAPREP.md) (original manual process).
