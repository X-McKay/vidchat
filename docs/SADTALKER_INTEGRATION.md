# SadTalker Integration Guide

## Overview

VidChat now supports **two rendering modes** for avatars:

1. **Frame-Based Rendering** (Image/Geometric Renderer) - Current default
   - Displays a static portrait image
   - Adds subtle visual indicators when speaking (border glow)
   - Fast and lightweight
   - **Does NOT animate the actual mouth**

2. **Video-Based Rendering** (SadTalker) - Requires installation
   - Generates realistic talking head videos
   - **Actual lip-sync animation** using the avatar's face
   - Natural head movements and expressions
   - Requires SadTalker installation

## What Was Wrong Before

### The Problem
The previous implementation had a **fake mouth overlay** that drew colored shapes (lips, teeth, glow effects) on top of the static avatar image. This was not realistic lip-sync - it was just graphics drawn over the image.

### The Fix
We've removed the fake mouth overlay and implemented proper architecture to support SadTalker, which generates **real animated videos** where the avatar's actual face moves naturally.

## Current Implementation (Frame-Based)

**What you'll see now:**
- Static avatar image
- Subtle border glow when speaking
- Text panel at the bottom
- **No mouth animation** (this is intentional - static images can't have real lip-sync)

**Files modified:**
- `src/vidchat/avatar/image_renderer.py` - Removed fake mouth drawing code
- `src/vidchat/web/server.py` - Added support for both rendering modes
- Frontend components - Added video playback support

## SadTalker Integration (Video-Based)

### How SadTalker Works

**Input:** Portrait image + Audio file
**Output:** MP4 video with realistic talking head animation

**Workflow:**
1. User sends message → AI generates text response
2. TTS generates audio from text
3. **SadTalker generates video** (image + audio → video)
4. Video is streamed to frontend and played

### Installation

#### Prerequisites
- Python 3.8
- PyTorch 1.12.1+cu113 (CUDA support recommended)
- FFmpeg

#### Steps

1. **Clone SadTalker repository:**
   ```bash
   cd ~
   git clone https://github.com/OpenTalker/SadTalker.git
   cd SadTalker
   ```

2. **Create conda environment:**
   ```bash
   conda create -n sadtalker python=3.8
   conda activate sadtalker
   ```

3. **Install dependencies:**
   ```bash
   pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
   pip install -r requirements.txt
   ```

4. **Download pre-trained models:**
   ```bash
   bash scripts/download_models.sh
   ```

5. **Test installation:**
   ```bash
   python inference.py --driven_audio examples/driven_audio/bus_chinese.wav \\
                       --source_image examples/source_image/full_body_1.png \\
                       --enhancer gfpgan
   ```

### Configuration

To use SadTalker with VidChat:

1. **Update your config:**
   ```python
   # In your config file or environment
   config.avatar.renderer_type = "sadtalker"
   config.avatar.sadtalker_path = "/path/to/SadTalker"  # Optional, auto-detects common locations
   ```

2. **Supported paths** (auto-detected):
   - `~/SadTalker`
   - `/opt/SadTalker`
   - `<vidchat_project>/external/SadTalker`

### How It Works

The `SadTalkerRenderer` class ([sadtalker_renderer.py](src/vidchat/avatar/sadtalker_renderer.py)) provides:

```python
class SadTalkerRenderer:
    def generate_video(self, audio_path: str) -> Path:
        """
        Generate talking head video using SadTalker.

        Args:
            audio_path: Path to audio file (WAV)

        Returns:
            Path to generated MP4 video
        """
```

The web server automatically detects the renderer type and uses the appropriate workflow:

```python
if isinstance(vidchat_agent.avatar, SadTalkerRenderer):
    # Video workflow: Generate complete video
    video_path = agent.avatar.generate_video(audio_path)
    # Send video to client
else:
    # Frame workflow: Stream frames with audio
    # Render frames synchronized to audio amplitude
```

## Architecture

### Backend Flow

**Frame-Based (Current):**
```
User Message → AI Response → TTS Audio
                          ↓
                   Analyze Amplitude
                          ↓
              Render Frames (static image + border)
                          ↓
                Stream Audio + Frames to Frontend
```

**Video-Based (SadTalker):**
```
User Message → AI Response → TTS Audio
                          ↓
          SadTalker: Generate Video (image + audio)
                          ↓
              Stream Video to Frontend
                          ↓
          Frontend plays video (includes audio)
```

### Frontend Components

**Avatar.tsx** - Handles both rendering modes:
- `<canvas>` element for frame-based rendering
- `<video>` element for video playback
- Automatically switches based on data type

**Chat.tsx** - Handles WebSocket messages:
- `type: "frame"` → Update canvas
- `type: "audio"` → Play audio
- `type: "video"` → Play video

## Testing

### Test Frame-Based Renderer (Current)
1. Open [http://127.0.0.1:8000](http://127.0.0.1:8000)
2. Send a message
3. Observe:
   - Static avatar image
   - Subtle border glow when speaking
   - **No mouth animation** (this is correct!)

### Test SadTalker Renderer (After Installation)
1. Install SadTalker (see above)
2. Configure VidChat to use SadTalker
3. Restart web server
4. Send a message
5. Observe:
   - Realistic video with lip-sync
   - Natural head movements
   - Actual facial animation

## Performance Considerations

### Frame-Based
- **Fast:** Real-time rendering
- **Low resource:** Minimal CPU/GPU usage
- **Lightweight:** Small data transfer (JPEG frames)

### SadTalker
- **Slower:** Video generation takes time (few seconds per response)
- **High resource:** Requires GPU for good performance
- **Larger files:** MP4 videos are larger than frame streams
- **Better quality:** Realistic animation

## Troubleshooting

### SadTalker Not Working
1. Check installation:
   ```bash
   cd ~/SadTalker
   python inference.py --driven_audio examples/driven_audio/bus_chinese.wav \\
                       --source_image examples/source_image/full_body_1.png
   ```

2. Verify path in config:
   ```python
   print(agent.avatar.sadtalker_path)
   print(agent.avatar.is_available())
   ```

3. Check logs:
   ```bash
   # Server logs will show SadTalker generation attempts
   tail -f vidchat_web.log
   ```

### Frontend Not Playing Video
1. Check browser console for errors
2. Verify video data is received:
   ```javascript
   // In browser console
   // You should see WebSocket messages with type: "video"
   ```

3. Check video codec support (MP4/H.264)

## Next Steps

1. **For immediate use:** The current frame-based renderer works without any installation
2. **For realistic lip-sync:** Install SadTalker following the guide above
3. **Future improvements:**
   - Cache generated videos for repeated phrases
   - Optimize video generation speed
   - Support for different avatar styles
   - Real-time lip-sync using lighter models

## Summary of Changes

| Component | Before | After |
|-----------|--------|-------|
| **Image Renderer** | Fake mouth overlay drawn on image | Clean static image with subtle indicator |
| **Web Server** | Only frame streaming | Supports both frame and video modes |
| **Frontend** | Only canvas rendering | Supports both canvas and video playback |
| **Architecture** | Single rendering approach | Flexible, supports multiple renderers |

## References

- **SadTalker GitHub:** https://github.com/OpenTalker/SadTalker
- **SadTalker Paper:** CVPR 2023
- **VidChat Documentation:** [README.md](README.md)
