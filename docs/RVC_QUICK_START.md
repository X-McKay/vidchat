# RVC Voice Training - Quick Start Guide

Train a custom RVC voice model from YouTube URLs in 2 simple steps!

## Prerequisites

✅ Already installed:
- RVC repository at `~/RVC`
- Python 3.10 environment
- Required dependencies (yt-dlp, librosa, soundfile, etc.)

## Step 1: Prepare the Voice Dataset

Run the setup script with your desired voice name:

```bash
cd /home/al/git/vidchat
./setup_rvc_voice.sh robg
```

This script will:
1. Download audio from the 4 YouTube URLs in `youtube_list.py`
2. Convert audio to proper format (44.1kHz, mono, WAV)
3. Split into training segments (5-15 seconds each)
4. Preprocess the dataset (resample to 40kHz)
5. Extract F0 features (pitch information)
6. Extract embeddings (voice characteristics)
7. Create training configuration files

**Time required:** 15-30 minutes (depending on video lengths)

## Step 2: Start Training

Once setup is complete, start training:

```bash
cd /home/al/git/vidchat
uv run vidchat-cli train-rvc robg --epochs 300 --batch-size 8
```

Training parameters:
- `--epochs 300` - Train for 300 epochs (more = better quality)
- `--batch-size 8` - Process 8 samples at once (reduce if out of memory)
- Training runs in background by default

**Time required:** 4-8 hours on CPU (1-2 hours on compatible GPU)

## Step 3: Monitor Progress

Check training status:

```bash
uv run vidchat-cli rvc-status robg
```

Follow training logs in real-time:

```bash
uv run vidchat-cli rvc-status robg --follow
```

Or tail the log file directly:

```bash
tail -f ~/RVC/logs/robg/train.log
```

## Step 4: Check Checkpoints

List generated model checkpoints:

```bash
ls -lh ~/RVC/logs/robg/*.pth
```

Checkpoints are saved every 10 epochs:
- `G_10.pth`, `G_20.pth`, ..., `G_300.pth`
- `D_10.pth`, `D_20.pth`, ..., `D_300.pth`

The final model will be at:
- Generator: `~/RVC/logs/robg/G_300.pth`
- Index: `~/RVC/logs/robg/added_*.index`

## Quick Reference

### Train a different voice:

```bash
# Setup new voice "alice"
./setup_rvc_voice.sh alice

# Start training
uv run vidchat-cli train-rvc alice --epochs 200 --batch-size 4
```

### Change YouTube URLs:

Edit `youtube_list.py`:
```python
youtube_videos = [
    "https://www.youtube.com/watch?v=YOUR_VIDEO_ID",
    # Add more URLs...
]
```

Then run setup script again with a new voice name.

### Training Options:

```bash
# Train with more epochs (better quality, takes longer)
uv run vidchat-cli train-rvc robg --epochs 500 --batch-size 8

# Train with smaller batch size (less memory)
uv run vidchat-cli train-rvc robg --epochs 300 --batch-size 4

# Run in foreground (see output in terminal)
uv run vidchat-cli train-rvc robg --epochs 300 --no-background
```

## Troubleshooting

### Setup fails during audio download:

```bash
# Install yt-dlp if missing
~/.local/share/mise/installs/python/3.10.19/bin/python3 -m pip install yt-dlp
```

### Training crashes with "Out of Memory":

```bash
# Reduce batch size
uv run vidchat-cli train-rvc robg --epochs 300 --batch-size 2
```

### Training stopped unexpectedly:

```bash
# Check the log for errors
tail -100 ~/RVC/logs/robg/train.log

# Restart training (will resume from last checkpoint)
uv run vidchat-cli train-rvc robg --epochs 300 --batch-size 8
```

## What's Next?

Once training completes:

1. **Test the model** with RVC's inference tools
2. **Integrate into VidChat** - Use trained model for voice conversion
3. **Fine-tune** - Train for more epochs if quality isn't good enough

## Complete Workflow Summary

```bash
# 1. Setup dataset and preprocessing (15-30 min)
./setup_rvc_voice.sh robg

# 2. Start training (4-8 hours CPU)
uv run vidchat-cli train-rvc robg --epochs 300 --batch-size 8

# 3. Monitor progress
uv run vidchat-cli rvc-status robg --follow

# 4. When done, model is at:
#    ~/RVC/logs/robg/G_300.pth
#    ~/RVC/logs/robg/added_*.index
```

## Notes

- **Dataset Size:** Current setup uses ~3-4 minutes of audio. For best results, add more YouTube videos (target: 10-30 minutes)
- **Training Time:** CPU training is slow. GPU training (when compatible) is 4-8x faster
- **Quality:** More epochs + more data = better voice quality
- **GPU Issue:** RTX 5090 not currently supported by PyTorch 2.5. Training uses CPU mode automatically.

## Files Generated

```
~/RVC/
├── datasets/robg/              # Processed audio segments
├── logs/robg/
│   ├── 0_gt_wavs/             # Ground truth audio
│   ├── 1_16k_wavs/            # Resampled 16kHz
│   ├── 2a_f0/                 # F0 pitch features
│   ├── 2b-f0nsf/              # F0 no silence features
│   ├── 3_feature768/          # Voice embeddings
│   ├── config.json            # Training configuration
│   ├── filelist.txt           # Training file list
│   ├── train.log              # Training progress log
│   ├── G_*.pth                # Generator checkpoints
│   └── D_*.pth                # Discriminator checkpoints
└── configs/robg.json          # Config template
```
