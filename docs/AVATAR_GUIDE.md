# VidChat Avatar System Guide

VidChat now supports three types of avatar rendering, from simple geometric shapes to photorealistic talking heads powered by AI.

## Avatar Types

### 1. Geometric Avatar (Original)
Simple 2D geometric shapes with basic animations.

**Features:**
- Lightweight and fast
- No external dependencies
- Basic lip-sync via mouth size
- Eye blinking
- Head movement

**Use case:** Testing, low-resource environments

### 2. Image Avatar (Default - NEW!)
Uses a portrait image with text overlays and visual indicators.

**Features:**
- Uses real portrait image (3D rendered or photo)
- Professional appearance
- Speaking indicators (glow effect)
- Text panel with word wrapping
- 460+ FPS rendering performance
- No additional setup required

**Use case:** Production use with good visual quality

### 3. SadTalker Avatar (Most Realistic)
AI-powered realistic talking head animations using OpenTalker's SadTalker.

**Features:**
- Photorealistic lip-sync
- Natural head movements
- Facial expressions
- Eye gaze and blinks
- Professional quality output

**Use case:** Maximum realism, demo/production environments with GPU

## Quick Start

### Using Image Avatar (Default)

No setup required! Just run:

```bash
uv run python main.py
```

The application will automatically use the included portrait image at `assets/avatars/default_avatar.png`.

### Using Your Own Image

1. Place your portrait image in `assets/avatars/`
2. Configure VidChat:

```python
from vidchat.config import AppConfig, AvatarConfig

config = AppConfig(
    avatar=AvatarConfig(
        renderer_type="image",
        avatar_image="assets/avatars/my_photo.jpg"
    )
)
```

**Image Guidelines:**
- Format: PNG, JPG, or JPEG
- Resolution: 512x512 or higher recommended
- Portrait orientation
- Clear face, neutral expression
- Good lighting
- Uncluttered background

## SadTalker Setup Guide

### Prerequisites

- NVIDIA GPU with CUDA support (recommended)
- Python 3.8
- At least 8GB GPU VRAM
- 10GB disk space for models

### Installation Steps

#### 1. Install SadTalker

```bash
# Clone SadTalker repository
cd ~/
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker

# Create conda environment
conda create -n sadtalker python=3.8
conda activate sadtalker

# Install PyTorch with CUDA
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113

# Install dependencies
conda install ffmpeg
pip install -r requirements.txt

# Download checkpoints
bash scripts/download_models.sh
```

#### 2. Verify Installation

```bash
cd ~/SadTalker
python inference.py --driven_audio examples/driven_audio/bus_chinese.wav \
                    --source_image examples/source_image/full_body_1.png \
                    --result_dir ./results
```

If this generates a video in `results/`, SadTalker is working!

#### 3. Configure VidChat

Edit your VidChat configuration:

```python
from vidchat.config import AppConfig, AvatarConfig

config = AppConfig(
    avatar=AvatarConfig(
        renderer_type="sadtalker",
        avatar_image="assets/avatars/my_photo.png",
        sadtalker_path="/home/username/SadTalker",
        sadtalker_use_enhancer=True,  # Use GFPGAN for quality
        sadtalker_still_mode=False,   # Natural head movement
        sadtalker_preprocess="crop",  # or "full" for full body
    )
)
```

#### 4. Run VidChat with SadTalker

```bash
# Activate SadTalker environment
conda activate sadtalker

# Run VidChat
cd /path/to/vidchat
uv run python main.py
```

## Configuration Reference

### AvatarConfig Options

```python
from vidchat.config import AvatarConfig

config = AvatarConfig(
    # Renderer selection
    renderer_type="image",  # "geometric", "image", or "sadtalker"

    # Image/SadTalker settings
    avatar_image=None,  # Path to image (None = use default)

    # Display settings
    width=800,
    height=600,
    fps=30,

    # Colors (BGR format)
    bg_color=(25, 25, 35),
    avatar_idle_color=(100, 180, 220),
    avatar_speaking_color=(120, 220, 140),
    text_color=(255, 255, 255),

    # Animation settings
    enable_blink=True,
    blink_interval=3.0,
    enable_head_movement=False,
    head_movement_amplitude=5.0,

    # SadTalker specific
    sadtalker_path=None,  # Path to SadTalker installation
    sadtalker_use_enhancer=True,  # Use GFPGAN
    sadtalker_still_mode=False,  # Less head movement
    sadtalker_preprocess="crop",  # "crop" or "full"
)
```

## Comparison

| Feature | Geometric | Image | SadTalker |
|---------|-----------|-------|-----------|
| Setup Required | None | None | Extensive |
| GPU Required | No | No | Yes (recommended) |
| Realism | Low | Medium | Very High |
| Performance | 1000+ FPS | 460+ FPS | Real-time |
| File Size | None | ~3MB | ~8GB (models) |
| Lip-sync | Basic | Visual indicator | Photorealistic |
| Head Movement | Simple | None | Natural |
| Facial Expressions | None | None | Yes |
| Quality | Simple | Professional | Cinematic |

## Use Cases

### Development & Testing
**Recommended:** Geometric or Image avatar
- Fast iteration
- No setup overhead
- Resource efficient

### Production Deployment
**Recommended:** Image avatar
- Professional appearance
- No GPU required
- Easy customization
- Fast rendering

### Demos & Presentations
**Recommended:** SadTalker avatar
- Maximum wow factor
- Photorealistic quality
- Natural animations
- Requires GPU setup

## Troubleshooting

### Image Avatar Issues

**Problem:** "Avatar image not found"
```bash
# Verify image exists
ls -la assets/avatars/default_avatar.png

# If missing, restore from backup or use custom image
cp /path/to/your/photo.png assets/avatars/default_avatar.png
```

**Problem:** Image appears distorted
- Ensure image is portrait orientation
- Use aspect ratio close to 2:3 (e.g., 400x600, 512x768)

### SadTalker Issues

**Problem:** "SadTalker not available"
```bash
# Check installation
ls -la ~/SadTalker/inference.py

# Verify conda environment
conda activate sadtalker
python -c "import torch; print(torch.cuda.is_available())"
```

**Problem:** "Generation timeout"
- Increase timeout in sadtalker_renderer.py
- Check GPU memory availability
- Try with `sadtalker_use_enhancer=False`

**Problem:** "Out of memory"
- Reduce image resolution
- Close other GPU applications
- Use `sadtalker_still_mode=True`

## Custom Avatar Creation

### Creating Your Own 3D Avatar

1. **Generate with AI:**
   - Use Midjourney, DALL-E, or Stable Diffusion
   - Prompt: "professional portrait, 3D render, friendly person, glasses, business casual, soft lighting, neutral background"

2. **Use Photo:**
   - Take a well-lit selfie
   - Neutral expression
   - Face camera directly
   - Plain background

3. **Edit Image:**
   ```bash
   # Crop to square
   convert input.jpg -gravity center -crop 512x512+0+0 output.png

   # Enhance (optional)
   convert output.png -auto-level -contrast-stretch 2% enhanced.png
   ```

4. **Place in Assets:**
   ```bash
   cp enhanced.png assets/avatars/my_avatar.png
   ```

### Multiple Avatar Support

Switch avatars dynamically:

```python
from vidchat.avatar import ImageAvatarRenderer

# Avatar 1: Professional
avatar_prof = ImageAvatarRenderer(image_path="assets/avatars/professional.png")

# Avatar 2: Casual
avatar_casual = ImageAvatarRenderer(image_path="assets/avatars/casual.png")

# Use based on context
if business_context:
    frame = avatar_prof.render_frame(text, mouth_openness)
else:
    frame = avatar_casual.render_frame(text, mouth_openness)
```

## Performance Tips

### Image Avatar
- Already optimized (460+ FPS)
- No additional tuning needed
- Works on any hardware

### SadTalker Avatar
1. **Enable Enhancer** for quality (but slower):
   ```python
   sadtalker_use_enhancer=True  # Better quality, 2-3x slower
   ```

2. **Use Still Mode** for faster generation:
   ```python
   sadtalker_still_mode=True  # Less animation, faster
   ```

3. **Preprocess Mode:**
   ```python
   sadtalker_preprocess="crop"  # Faster, face only
   # vs
   sadtalker_preprocess="full"  # Slower, full body
   ```

4. **GPU Optimization:**
   ```bash
   # Check CUDA version
   nvcc --version

   # Monitor GPU usage
   nvidia-smi -l 1
   ```

## API Reference

### ImageAvatarRenderer

```python
from vidchat.avatar import ImageAvatarRenderer

renderer = ImageAvatarRenderer(
    config=avatar_config,
    image_path="path/to/image.png"
)

# Render frame
frame = renderer.render_frame(
    text="Hello world",
    mouth_openness=0.5,  # 0.0 to 1.0
    emotion="neutral"    # Future use
)
```

### SadTalkerRenderer

```python
from vidchat.avatar import SadTalkerRenderer

renderer = SadTalkerRenderer(
    config=avatar_config,
    image_path="path/to/portrait.png",
    sadtalker_path="/home/user/SadTalker",
    use_enhancer=True
)

# Check availability
if renderer.is_available():
    # Generate video
    video_path = renderer.generate_video(
        audio_path="speech.wav",
        output_path="output.mp4",
        still_mode=False,
        preprocess="crop"
    )
```

## Future Enhancements

Planned features:
- [ ] Real-time SadTalker integration (streaming mode)
- [ ] Multiple avatar presets (professional, casual, cartoon)
- [ ] Emotion-based expression changes
- [ ] Custom background support
- [ ] Avatar gesture library
- [ ] Video avatar support (not just images)
- [ ] Web-based avatar editor

## Resources

- **SadTalker GitHub:** https://github.com/OpenTalker/SadTalker
- **SadTalker Paper:** [CVPR 2023] Learning Realistic 3D Motion Coefficients
- **VidChat Docs:** See ARCHITECTURE.md for technical details
- **Example Images:** Check `assets/avatars/` for samples

## Credits

- Default avatar created with AI generation
- SadTalker by OpenTalker team
- VidChat avatar system designed for modularity and extensibility
