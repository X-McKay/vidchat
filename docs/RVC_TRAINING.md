# RVC Voice Training Guide

Complete guide to training custom voice models using Retrieval-based Voice Conversion (RVC) with GPU acceleration and MLflow tracking.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Data Preparation](#data-preparation)
- [Training Process](#training-process)
- [Monitoring & Metrics](#monitoring--metrics)
- [Preprocessing Cache](#preprocessing-cache)
- [GPU Acceleration](#gpu-acceleration)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

## Overview

VidChat's RVC training pipeline provides:

- **GPU-Accelerated Processing**: 89% GPU utilization on RTX 5090, 279W power draw
- **Intelligent Caching**: Skip reprocessing when data unchanged (saves hours)
- **MLflow Tracking**: Complete experiment tracking with metrics and system monitoring
- **Automatic Checkpointing**: Model saved every 10 epochs
- **Real-time Monitoring**: Track training progress and system metrics

### What is RVC?

Retrieval-based Voice Conversion (RVC) is a voice cloning technology that trains a neural network to convert any audio to sound like a target voice. Unlike zero-shot methods (XTTS), RVC requires training but produces higher quality results.

## Prerequisites

### Required

- **Python 3.10+** (RVC requires specific Python version)
- **CUDA-capable GPU** - Tested on RTX 5090, works on most NVIDIA GPUs
- **~10GB GPU RAM** - For training with batch size 4
- **~50GB disk space** - For voice data, models, and checkpoints

### Setup RVC

```bash
# Clone RVC into external directory
cd external
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC
cd RVC

# Download pretrained models
mkdir -p assets/pretrained_v2
cd assets/pretrained_v2
wget https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0G40k.pth
wget https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/pretrained_v2/f0D40k.pth
```

## Quick Start

Train a voice model in 3 steps:

```bash
# 1. Prepare voice data from YouTube
uv run python src/vidchat/data/prepare_voice_data.py robg \
  --urls "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# 2. Train with GPU acceleration
uv run python src/vidchat/training/rvc_train_with_tracking.py robg \
  --epochs 500 \
  --batch-size 4 \
  --gpu

# 3. View training metrics
mlflow ui --backend-store-uri file://$(pwd)/.data/mlruns
# Open http://localhost:5000
```

## Data Preparation

### Option 1: YouTube Audio (Recommended)

Extract voice data from YouTube videos:

```bash
uv run python src/vidchat/data/prepare_voice_data.py <voice_name> \
  --urls "URL1" "URL2" "URL3" \
  --duration 600  # Extract up to 600 seconds per video
```

**What it does:**
1. Downloads audio from YouTube using `yt-dlp`
2. Converts to 40kHz WAV (required for RVC)
3. Splits into 3-10 second segments
4. Saves to `.data/voice_data/<voice_name>/`

**Requirements:**
- Videos should contain clear, single-speaker audio
- Minimum 5-10 minutes of total audio recommended
- Background music/noise will reduce quality

### Option 2: Your Own Audio Files

Place WAV files directly in `.data/voice_data/<voice_name>/`:

```bash
mkdir -p .data/voice_data/my_voice
cp ~/my_recordings/*.wav .data/voice_data/my_voice/
```

**Audio Requirements:**
- Format: WAV, 16-bit PCM
- Sample rate: Any (will be resampled to 40kHz)
- Length: 3-10 seconds per file (or will be split)
- Quality: Clear speech, minimal background noise
- Quantity: 100+ segments recommended (5-10 minutes total)

## Training Process

### Basic Training

```bash
uv run python src/vidchat/training/rvc_train_with_tracking.py <voice_name> \
  --epochs 500 \
  --batch-size 4 \
  --gpu
```

### Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `voice_name` | Required | Name of voice (must match data directory) |
| `--epochs` | 300 | Number of training epochs (500 recommended) |
| `--batch-size` | 4 | Batch size (4 for 10GB GPU, 8+ for 24GB+) |
| `--save-freq` | 10 | Save checkpoint every N epochs |
| `--gpu` | False | Enable GPU acceleration (required for practical training) |

### Training Stages

The training script executes 5 preprocessing stages, then training:

#### 1. Audio Preprocessing (1-2 minutes)
- Resamples audio to 40kHz
- Normalizes volume
- Splits into 3.7-second segments
- Output: `external/RVC/logs/<voice>/1_16k_wavs/`

#### 2. Pitch Extraction (1-5 minutes with GPU)
- Extracts F0 (fundamental frequency) using RMVPE
- GPU-accelerated: 89% utilization, ~2 minutes for 143 files
- CPU fallback: ~40+ minutes
- Output: `external/RVC/logs/<voice>/2a_f0/`, `2b-f0nsf/`

#### 3. Feature Extraction (2-10 minutes with GPU)
- Extracts 768-dim acoustic features using HuBERT
- GPU-accelerated for faster processing
- Output: `external/RVC/logs/<voice>/3_feature768/`

#### 4. Filelist Creation (seconds)
- Creates training file index
- Format: `wav|feature|f0|f0nsf|speaker_id`
- Output: `external/RVC/logs/<voice>/filelist.txt`

#### 5. Config Generation (seconds)
- Generates training configuration
- Sets hyperparameters (learning rate, batch size, etc.)
- Output: `external/RVC/logs/<voice>/config.json`

#### 6. Model Training (hours)
- Trains generator and discriminator networks
- Saves checkpoints every 10 epochs
- Logs metrics to MLflow
- Monitors GPU usage, memory, temperature

### Training Output

**Checkpoints:**
```
external/RVC/logs/<voice>/
├── G_0.pth          # Initial generator
├── G_10.pth         # Generator at epoch 10
├── G_20.pth         # Generator at epoch 20
├── ...
├── G_500.pth        # Final generator (use this!)
├── D_0.pth          # Initial discriminator
├── D_10.pth         # Discriminator at epoch 10
├── ...
└── D_500.pth        # Final discriminator
```

**Logs:**
```
external/RVC/logs/<voice>/
├── train.log              # Training log with metrics
├── config.json            # Training configuration
├── cache_metadata.json    # Preprocessing cache info
└── filelist.txt           # Training data index
```

## Monitoring & Metrics

### MLflow Tracking

Every training run is tracked in MLflow:

```bash
# Start MLflow UI
mlflow ui --backend-store-uri file://$(pwd)/.data/mlruns

# Open in browser
open http://localhost:5000
```

**Tracked Metrics:**
- `loss_disc` - Discriminator loss
- `loss_gen` - Generator loss
- `loss_fm` - Feature matching loss
- `loss_mel` - Mel-spectrogram loss
- `loss_kl` - KL divergence loss

**System Metrics** (logged every 30s):
- `system.cpu_percent` - CPU usage
- `system.memory_percent` - RAM usage
- `system.gpu_utilization` - GPU usage %
- `system.gpu_memory_used` - GPU memory (MB)
- `system.gpu_temperature` - GPU temp (°C)
- `system.gpu_power_draw` - Power consumption (W)

**Artifacts:**
- All model checkpoints (G_*.pth, D_*.pth)
- Training configuration (config.json)
- Training log (train.log)

### Training Log

Real-time training progress:

```bash
# Watch training log
tail -f external/RVC/logs/<voice>/train.log

# Check GPU usage
watch -n 1 nvidia-smi
```

### Example Training Metrics

```
INFO:robg:Train Epoch: 1 [0%]
INFO:robg:[0, 0.0001]
INFO:robg:loss_disc=3.923, loss_gen=4.932, loss_fm=13.516, loss_mel=31.050, loss_kl=9.000

INFO:robg:Train Epoch: 10 [2%]
INFO:robg:[9, 0.0001]
INFO:robg:loss_disc=2.145, loss_gen=3.621, loss_fm=10.234, loss_mel=25.678, loss_kl=7.456

...

INFO:robg:Train Epoch: 500 [100%]
INFO:robg:[499, 0.0001]
INFO:robg:loss_disc=0.823, loss_gen=1.234, loss_fm=5.678, loss_mel=12.345, loss_kl=3.456
```

## Preprocessing Cache

**Major Time Saver!** The training script intelligently caches preprocessing results.

### How It Works

1. **Cache Key Generation**: SHA256 hash of:
   - All audio file names, sizes, and modification times
   - Preprocessing parameters (sample rate, f0 method, model version, GPU flag)

2. **Cache Validation**: On subsequent runs, checks:
   - Cache key matches current data
   - All output directories exist (0_gt_wavs, 1_16k_wavs, 2a_f0, 2b-f0nsf, 3_feature768)
   - Filelist exists

3. **Cache Usage**:
   - **Valid cache**: Skips all 5 preprocessing stages instantly
   - **Invalid cache**: Runs full preprocessing and saves new cache

### Cache Location

```
external/RVC/logs/<voice>/cache_metadata.json
```

### Example Cache Metadata

```json
{
  "cache_key": "a1b2c3d4e5f6...",
  "timestamp": 1697845234.567,
  "preprocessing_params": {
    "sample_rate": 40000,
    "segment_length": 3.7,
    "f0_method": "rmvpe",
    "model_version": "v2",
    "gpu": true
  }
}
```

### When Cache is Invalidated

Cache automatically invalidates when:
- Audio files added, removed, or modified
- Preprocessing parameters change (sample rate, f0 method, etc.)
- GPU flag changed
- Manual deletion of cache file

### Cache Management

```bash
# View cache status
cat external/RVC/logs/<voice>/cache_metadata.json

# Force reprocessing (delete cache)
rm external/RVC/logs/<voice>/cache_metadata.json

# Clear all preprocessing data
rm -rf external/RVC/logs/<voice>/{0_gt_wavs,1_16k_wavs,2a_f0,2b-f0nsf,3_feature768,filelist.txt,cache_metadata.json}
```

## GPU Acceleration

### GPU Setup

**IMPORTANT**: Always use the `--gpu` flag for practical training!

```bash
# With GPU (recommended)
uv run python src/vidchat/training/rvc_train_with_tracking.py robg --epochs 500 --gpu

# Without GPU (CPU-only, very slow)
uv run python src/vidchat/training/rvc_train_with_tracking.py robg --epochs 500
```

### GPU Performance

**With GPU (RTX 5090):**
- Pitch extraction: ~2 minutes for 143 files
- Feature extraction: ~5 minutes
- GPU utilization: 89%
- Power draw: 279W
- Memory: 20GB / 32GB

**Without GPU (CPU-only):**
- Pitch extraction: ~40+ minutes for 143 files
- Feature extraction: ~30+ minutes
- Much slower training (hours → days)

### GPU Monitoring

```bash
# Real-time GPU stats
watch -n 1 nvidia-smi

# Detailed GPU info
nvidia-smi --query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu,utilization.memory,power.draw --format=csv
```

### GPU Troubleshooting

**"CUDA out of memory"**
```bash
# Reduce batch size
--batch-size 2  # or even 1
```

**"No CUDA-capable device detected"**
```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch sees GPU
python -c "import torch; print(torch.cuda.is_available())"
```

**"RTX 5090 not supported"**
```bash
# The training script automatically handles this via PTX compilation
# No action needed - it's configured in the code
```

## Troubleshooting

### Common Issues

#### 1. Training Data Not Found

```
❌ Training data not found: .data/voice_data/<voice>
```

**Solution:**
```bash
# Prepare data first
uv run python src/vidchat/data/prepare_voice_data.py <voice> --urls "URL"
```

#### 2. Preprocessing Fails

```
❌ Preprocessing failed:
[error message]
```

**Solutions:**
- Check audio file format (should be WAV)
- Ensure sufficient disk space (~50GB)
- Delete cache and retry: `rm external/RVC/logs/<voice>/cache_metadata.json`

#### 3. GPU Not Used

**Symptoms:**
- GPU utilization 0%
- Training very slow
- "device=cpu" in logs

**Solution:**
```bash
# Add --gpu flag!
uv run python src/vidchat/training/rvc_train_with_tracking.py <voice> --epochs 500 --gpu
```

#### 4. Training Crashes

**ValueError: cannot reshape array**

This was a matplotlib incompatibility - already fixed in the codebase. If you still see this:

```bash
# Update matplotlib
pip install --upgrade matplotlib
```

**CUDA out of memory**

```bash
# Reduce batch size
--batch-size 2  # or 1
```

#### 5. MLflow UI Not Working

```bash
# Specify correct path
mlflow ui --backend-store-uri file://$(pwd)/.data/mlruns

# Or use absolute path
mlflow ui --backend-store-uri file:///home/user/vidchat/.data/mlruns
```

### Debug Mode

```bash
# Run with verbose output
PYTHONUNBUFFERED=1 uv run python src/vidchat/training/rvc_train_with_tracking.py <voice> --epochs 500 --gpu 2>&1 | tee training.log
```

## Advanced Usage

### Custom Training Parameters

Edit config after preprocessing:

```bash
# Edit config before training
nano external/RVC/logs/<voice>/config.json
```

Key parameters:
- `learning_rate`: 0.0001 (default)
- `batch_size`: 4 (default)
- `epochs`: Set via `--epochs` flag
- `segment_size`: 17280 (audio segment size)

### Resume Training

```bash
# Training automatically resumes from latest checkpoint
uv run python src/vidchat/training/rvc_train_with_tracking.py <voice> --epochs 1000 --gpu
```

### Multiple Voices

Train different voices independently:

```bash
# Prepare multiple voices
uv run python src/vidchat/data/prepare_voice_data.py voice1 --urls "URL1"
uv run python src/vidchat/data/prepare_voice_data.py voice2 --urls "URL2"

# Train separately
uv run python src/vidchat/training/rvc_train_with_tracking.py voice1 --epochs 500 --gpu
uv run python src/vidchat/training/rvc_train_with_tracking.py voice2 --epochs 500 --gpu
```

### Export Model

```bash
# Latest checkpoint is in:
external/RVC/logs/<voice>/G_500.pth  # Generator model (use this for inference)
external/RVC/logs/<voice>/D_500.pth  # Discriminator model
```

### Batch Training Script

```bash
#!/bin/bash
# train_all_voices.sh

VOICES=("voice1" "voice2" "voice3")

for voice in "${VOICES[@]}"; do
  echo "Training $voice..."
  uv run python src/vidchat/training/rvc_train_with_tracking.py "$voice" \
    --epochs 500 \
    --batch-size 4 \
    --gpu
done

echo "All voices trained!"
```

## Best Practices

1. **Data Quality Over Quantity**
   - 5-10 minutes of clean audio > 1 hour of noisy audio
   - Single speaker, minimal background noise
   - Clear speech, not shouting or whispering

2. **Start Small, Scale Up**
   - Test with 50-100 epochs first
   - Verify model quality before full 500-epoch training
   - Use test audio samples to evaluate

3. **Monitor Training**
   - Watch MLflow metrics
   - Check for overfitting (losses stop decreasing)
   - Test checkpoints periodically

4. **GPU Utilization**
   - Always use `--gpu` flag
   - Monitor with `nvidia-smi`
   - Adjust batch size for your GPU memory

5. **Experiment Tracking**
   - Use MLflow to compare different runs
   - Tag experiments with descriptive names
   - Review system metrics for performance tuning

## Related Documentation

- [DATA_PREPARATION.md](DATA_PREPARATION.md) - Voice data preparation
- [MLFLOW_TRACKING.md](MLFLOW_TRACKING.md) - Experiment tracking guide
- [RTX_5090_GPU_SETUP.md](RTX_5090_GPU_SETUP.md) - GPU configuration
- [XTTS_VOICE_CLONING.md](XTTS_VOICE_CLONING.md) - Alternative zero-shot approach

## Support

If you encounter issues:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Review training logs: `external/RVC/logs/<voice>/train.log`
3. Check GPU status: `nvidia-smi`
4. Verify data preparation completed successfully
5. Open an issue on GitHub with logs and error messages
