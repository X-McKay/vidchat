# XTTS v2 Voice Cloning Guide

This guide explains how to use Coqui XTTS v2 for zero-shot voice cloning in VidChat.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Supported Languages](#supported-languages)
- [Tips & Best Practices](#tips--best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

**XTTS v2** is a powerful voice cloning system that can replicate any voice with just **6 seconds** of reference audio. Unlike RVC which requires training, XTTS v2 provides:

- **Zero-shot cloning**: No training required
- **Fast inference**: Real-time speech synthesis
- **17 languages**: Multilingual support
- **High quality**: Natural-sounding voice cloning
- **Modern stack**: Compatible with Python 3.13 and PyTorch 2.8+

### Why XTTS v2 over RVC?

| Feature | XTTS v2 | RVC |
|---------|---------|-----|
| Training required | ❌ No | ✅ Yes (hours) |
| Reference audio needed | 6+ seconds | 10-15 minutes |
| Python version | 3.13 ✅ | 3.10 only |
| PyTorch version | 2.8+ ✅ | <2.6 only |
| RTX 5090 support | ✅ Yes | ❌ No |
| Setup time | 5 minutes | 2+ hours |

## Installation

### 1. Install XTTS Dependencies

```bash
# Install voice cloning extras
uv sync --extra voice-cloning
```

This installs:
- `coqui-tts>=0.27.0`
- PyTorch 2.8+
- Transformers
- Other required dependencies

### 2. First Run - Accept License

On first use, XTTS will download the model and ask you to accept the license:

```bash
# Test installation
uv run python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('✓ XTTS ready!')"
```

The model will be cached in `~/.local/share/tts/` for future use.

## Quick Start

### 1. Prepare Reference Audio

You need a 6+ second audio clip of the target voice. You can:

- **Use existing dataset**: If you prepared voice data with YouTube URLs
  ```bash
  # Audio segments are in ~/RVC/datasets/<voice_name>/
  ls ~/RVC/datasets/robg/segment_*.wav
  ```

- **Extract from video/audio**: Use any 6+ second clip
  ```bash
  ffmpeg -i input.mp4 -ss 00:00:10 -t 6 reference.wav
  ```

- **Record new audio**: Use any recording tool

### 2. Configure VidChat

Edit `config.yaml`:

```yaml
tts:
  provider: "xtts"  # Switch from piper to xtts

  # XTTS Configuration
  xtts:
    # Path to 6+ second reference audio
    reference_audio: "~/RVC/datasets/robg/segment_0000.wav"
    language: "en"  # Language code
```

### 3. Test Voice Cloning

```bash
# Test with the XTTS engine directly
uv run python src/vidchat/tts/xtts.py ~/RVC/datasets/robg/segment_0000.wav

# Or use the test script
uv run python test_xtts_voice_clone.py
```

### 4. Use in VidChat

```bash
# Start VidChat with XTTS voice cloning
uv run vidchat
```

## Configuration

### YAML Configuration

```yaml
# config.yaml
tts:
  provider: "xtts"  # Use XTTS for voice cloning

  xtts:
    # Reference audio (absolute or relative to project root)
    reference_audio: "~/RVC/datasets/robg/segment_0000.wav"

    # Language code
    language: "en"  # See supported languages below
```

### Path Options

Reference audio paths can be:

1. **Absolute path**:
   ```yaml
   reference_audio: "/home/user/audio/voice.wav"
   ```

2. **Home directory** (uses `~`):
   ```yaml
   reference_audio: "~/audio/voice.wav"
   ```

3. **Relative to project root**:
   ```yaml
   reference_audio: "assets/voices/my_voice.wav"
   ```

### Programmatic Usage

```python
from vidchat.tts.xtts import XTTSTTS

# Initialize with reference audio
tts = XTTSTTS(
    reference_audio="path/to/reference.wav",
    language="en"
)

# Generate speech
output_path = tts.synthesize(
    text="Hello! This is voice cloning with XTTS.",
    output_path="output/speech.wav"
)

print(f"Generated: {output_path}")
print(f"Sample rate: {tts.get_sample_rate()}Hz")  # 24000
```

## Supported Languages

XTTS v2 supports 17 languages:

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `pl` | Polish |
| `es` | Spanish | `tr` | Turkish |
| `fr` | French | `ru` | Russian |
| `de` | German | `nl` | Dutch |
| `it` | Italian | `cs` | Czech |
| `pt` | Portuguese | `ar` | Arabic |
| `zh-cn` | Chinese | `hu` | Hungarian |
| `ko` | Korean | `ja` | Japanese |
| `hi` | Hindi | | |

### Multilingual Usage

```python
# Spanish voice cloning
tts_es = XTTSTTS(
    reference_audio="spanish_voice.wav",
    language="es"
)
tts_es.synthesize("Hola! Esto es clonación de voz.", "output_es.wav")

# Japanese voice cloning
tts_ja = XTTSTTS(
    reference_audio="japanese_voice.wav",
    language="ja"
)
tts_ja.synthesize("こんにちは！音声クローニングです。", "output_ja.wav")
```

## Tips & Best Practices

### Reference Audio Quality

For best results, your reference audio should:

✅ **DO:**
- Be at least 6 seconds long (10+ seconds is better)
- Have clear, clean speech
- Be mostly the target voice (minimal background noise)
- Have consistent volume
- Use the same language you'll generate

❌ **DON'T:**
- Use audio with heavy background music
- Use heavily processed/filtered audio
- Mix multiple speakers
- Use very short clips (<6 seconds)

### Audio Preprocessing

If your reference audio has issues:

```bash
# Remove silence from beginning/end
ffmpeg -i input.wav -af silenceremove=1:0:-50dB output.wav

# Normalize volume
ffmpeg -i input.wav -filter:a loudnorm output.wav

# Convert to correct format (WAV, mono, 44.1kHz)
ffmpeg -i input.mp3 -ar 44100 -ac 1 output.wav
```

### Performance Optimization

```python
# Use GPU for faster generation
tts = XTTSTTS(
    reference_audio="voice.wav",
    device="cuda"  # Explicitly use GPU
)

# Or CPU if no GPU available
tts = XTTSTTS(
    reference_audio="voice.wav",
    device="cpu"
)

# Auto-detect (default)
tts = XTTSTTS(reference_audio="voice.wav")  # Uses CUDA if available
```

### Batch Generation

```python
from vidchat.tts.xtts import XTTSTTS
from pathlib import Path

# Initialize once
tts = XTTSTTS(reference_audio="voice.wav")

# Generate multiple files
texts = [
    "First sentence to synthesize.",
    "Second sentence with different content.",
    "Third and final sentence.",
]

output_dir = Path("output/batch")
output_dir.mkdir(parents=True, exist_ok=True)

for i, text in enumerate(texts):
    output = output_dir / f"speech_{i:03d}.wav"
    tts.synthesize(text, output)
    print(f"✓ Generated: {output}")
```

## Troubleshooting

### "ImportError: coqui-tts is not installed"

**Solution**: Install voice cloning dependencies
```bash
uv sync --extra voice-cloning
```

### "FileNotFoundError: Reference audio not found"

**Causes**:
1. Path is incorrect
2. File doesn't exist
3. Relative path from wrong location

**Solutions**:
```bash
# Check if file exists
ls -la ~/RVC/datasets/robg/segment_0000.wav

# Use absolute path
reference_audio: "/home/user/RVC/datasets/robg/segment_0000.wav"

# Or expand home directory
reference_audio: "~/RVC/datasets/robg/segment_0000.wav"
```

### Poor Voice Quality

**Possible causes**:
1. Reference audio too short (<6 seconds)
2. Reference audio has background noise
3. Reference audio heavily processed

**Solutions**:
- Use longer reference clip (10+ seconds)
- Clean reference audio (remove background noise)
- Try different reference audio segment
- Ensure reference audio is clear speech

### Slow Generation

**Causes**:
1. Running on CPU instead of GPU
2. First run (model loading)

**Solutions**:
```python
# Explicitly use GPU
tts = XTTSTTS(reference_audio="voice.wav", device="cuda")

# Check GPU availability
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

### "CUDA out of memory"

**Solution**: Use CPU or smaller text chunks
```python
# Use CPU
tts = XTTSTTS(reference_audio="voice.wav", device="cpu")

# Or split long text into sentences
long_text = "Very long text..."
sentences = long_text.split(". ")
for i, sentence in enumerate(sentences):
    tts.synthesize(sentence, f"output_{i}.wav")
```

### Wrong Language Output

**Cause**: Language mismatch between reference audio and config

**Solution**: Ensure language matches reference audio
```yaml
xtts:
  reference_audio: "spanish_voice.wav"
  language: "es"  # Must match reference audio language
```

## Technical Details

### Model Information

- **Model**: `tts_models/multilingual/multi-dataset/xtts_v2`
- **Sample Rate**: 24kHz (24000 Hz)
- **Architecture**: Transformer-based TTS
- **Training Data**: Multilingual dataset
- **License**: Coqui Public Model License (CPML)

### Output Format

- **Format**: WAV (uncompressed)
- **Sample Rate**: 24000 Hz
- **Channels**: Mono
- **Bit Depth**: 16-bit PCM

### Model Size & Storage

- **Model Size**: ~1.8 GB
- **Cache Location**: `~/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/`
- **Disk Space Required**: ~2 GB

### Performance Benchmarks

Approximate generation speeds on different hardware:

| Hardware | Speed | Real-time Factor |
|----------|-------|------------------|
| RTX 5090 | Very fast | 0.1x (10s audio in 1s) |
| RTX 4090 | Fast | 0.15x |
| RTX 3090 | Fast | 0.2x |
| CPU (Ryzen 9) | Moderate | 2x (10s audio in 20s) |

## See Also

- [Voice Cloning Solutions Comparison](VOICE_CLONING_SOLUTIONS.md)
- [Voice Data Preparation Guide](VOICE_DATA_PREP_GUIDE.md)
- [Configuration Guide](../README.md#configuration)
- [Coqui TTS Documentation](https://github.com/coqui-ai/TTS)

## License

XTTS v2 is released under the Coqui Public Model License (CPML). See [Coqui TTS License](https://github.com/coqui-ai/TTS/blob/dev/LICENSE.txt) for details.

---

**Next Steps:**
1. ✅ Install XTTS dependencies
2. ✅ Prepare reference audio (6+ seconds)
3. ✅ Configure `config.yaml`
4. ✅ Test voice cloning
5. ✅ Use in VidChat!
