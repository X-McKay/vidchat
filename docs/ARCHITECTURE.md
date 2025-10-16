# VidChat Architecture

This document describes the modular architecture of VidChat and how components interact.

## Overview

VidChat is designed with a clean separation of concerns, making it easy to:
- Extend functionality (add new TTS engines, avatar styles, etc.)
- Test components independently
- Train custom voice models (RVC)
- Customize behavior through configuration

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│                    (Entry Point)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │   vidchat.core.agent       │
         │     VidChatAgent           │
         │  (Orchestrates everything) │
         └────────────┬───────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
    ┌────────┐  ┌─────────┐  ┌──────────┐
    │   AI   │  │   TTS   │  │  Avatar  │
    │ Agent  │  │ Engine  │  │ Renderer │
    └────────┘  └─────────┘  └──────────┘
         │            │            │
         │            │            │
         │            │            ▼
         │            │       ┌──────────┐
         │            │       │  Audio   │
         │            │       │ Analyzer │
         │            │       └──────────┘
         │            │
         ▼            ▼
    ┌──────────────────────┐
    │  Configuration       │
    │  (vidchat.config)    │
    └──────────────────────┘
```

## Core Components

### 1. VidChatAgent (`vidchat.core.agent`)

The main orchestrator that ties everything together.

**Responsibilities:**
- Initialize and manage all components
- Handle chat loop and async operations
- Synchronize audio and video playback
- Manage pygame and OpenCV windows

**Key Methods:**
- `chat(user_input)`: Get AI response
- `display_and_speak(response)`: Show avatar with synced audio
- `show_message(message, duration)`: Display static message
- `close()`: Clean up resources

**Dependencies:**
- `vidchat.tts`: Text-to-speech engine
- `vidchat.avatar`: Avatar renderer
- `vidchat.audio`: Audio analyzer
- `pydantic_ai`: AI agent

### 2. Text-to-Speech (`vidchat.tts`)

Abstract TTS interface with multiple implementations.

**Base Class: `BaseTTS`**
```python
class BaseTTS(ABC):
    @abstractmethod
    def synthesize(text: str, output_path: str | Path) -> str

    @abstractmethod
    def is_available() -> bool

    @abstractmethod
    def get_sample_rate() -> int
```

**Implementations:**

#### PiperTTS (`vidchat.tts.piper`)
- High-quality neural TTS
- Uses Piper CLI via subprocess
- Supports multiple voice models
- Fast generation (~300ms for typical sentence)

#### RVCTTS (`vidchat.tts.rvc`)
- Voice conversion (placeholder)
- Will use trained RVC models
- Converts any voice to target voice

#### HybridTTS (`vidchat.tts.rvc`)
- Combines Piper + RVC
- First generates speech with Piper
- Then converts voice with RVC
- Best of both: natural speech + custom voice

### 3. Avatar Renderer (`vidchat.avatar`)

Renders the visual avatar with dynamic expressions.

**Class: `AvatarRenderer`**

**Features:**
- Dynamic mouth animation (based on audio amplitude)
- Blinking animation (optional)
- Head movement (optional)
- Emotion-based expressions (neutral, happy, sad, etc.)
- Customizable colors
- Text display with word wrapping

**Key Methods:**
- `render_frame(text, mouth_openness, emotion)`: Render single frame
- `update_head_position(mouth_openness)`: Update head sway
- `_should_blink()`: Determine blink timing

**Rendering Pipeline:**
1. Draw gradient background
2. Draw avatar head with shadow
3. Draw eyes (with blink)
4. Draw mouth (size based on audio)
5. Draw text panel at bottom
6. Add status indicator

### 4. Audio Analyzer (`vidchat.audio`)

Analyzes audio files for lip-sync and processing.

**Class: `AudioAnalyzer`**

**Features:**
- RMS amplitude analysis
- Silence detection
- Amplitude smoothing
- Audio file introspection

**Key Methods:**
- `analyze_amplitude(audio_path, target_fps)`: Extract amplitude per frame
- `smooth_amplitude(amplitudes, window_size)`: Smooth for natural movement
- `detect_silence(audio_path, threshold)`: Find silent regions
- `get_audio_info(audio_path)`: Get sample rate, duration, etc.

**Amplitude Analysis Process:**
1. Read WAV file
2. Convert to numpy array (int16 samples)
3. Group samples by video frame (e.g., 735 samples per frame at 30 FPS)
4. Calculate RMS amplitude for each frame
5. Normalize to 0.0-1.0 range
6. Apply threshold to filter noise
7. Return list of amplitude values

### 5. Configuration (`vidchat.config`)

Type-safe configuration using dataclasses.

**Classes:**
- `AppConfig`: Main application config
- `TTSConfig`: TTS engine settings
- `AvatarConfig`: Avatar appearance and animation
- `AIAgentConfig`: AI model and prompts
- `AudioConfig`: Audio processing parameters
- `RVCConfig`: RVC training and inference settings

**Benefits:**
- Type checking with mypy/pyright
- IDE autocomplete
- Clear documentation
- Easy serialization (for saving/loading configs)

**Example:**
```python
from vidchat.config import AppConfig, TTSConfig

config = AppConfig(
    tts=TTSConfig(
        provider="piper",
        piper_model="models/my-voice.onnx",
        sample_rate=22050
    ),
    enable_audio_sync=True,
    debug=True
)
```

### 6. Training (`vidchat.training`)

RVC model training utilities (coming soon).

**Modules:**

#### rvc_train_with_tracking.py
Complete RVC training pipeline with MLflow integration:
- GPU-accelerated preprocessing (pitch & feature extraction)
- Intelligent preprocessing cache (SHA256-based validation)
- MLflow experiment tracking with system metrics
- Model checkpointing every 10 epochs
- Real-time training progress monitoring

**Key Functions:**
- `train_rvc_with_tracking()`: Main training orchestration
- `compute_cache_key()`: Generate cache hash from audio files
- `is_cache_valid()`: Validate preprocessing cache
- `save_cache_metadata()`: Persist cache information
- `parse_log_metrics()`: Extract metrics from training logs
- `tail_and_log_metrics()`: Real-time metric logging to MLflow

#### mlflow_tracker.py
MLflow experiment tracking wrapper:
- Automatic experiment and run management
- System metrics monitoring (CPU, GPU, memory)
- Model checkpoint logging
- Training metrics visualization

#### AudioPreprocessor
- Resample audio to target sample rate
- Normalize audio levels
- Remove silence from recordings
- Split audio into segments

### 7. Utilities (`vidchat.utils`)

Helper functions and utilities.

**Modules:**
- `logger.py`: Logging setup and configuration

## Data Flow

### Chat Interaction Flow

1. **User Input** → `main.py` reads from terminal
2. **AI Processing** → `VidChatAgent.chat()` sends to Ollama
3. **Response** → PydanticAI returns structured response
4. **TTS Generation** → `PiperTTS.synthesize()` creates audio
5. **Audio Analysis** → `AudioAnalyzer.analyze_amplitude()` extracts data
6. **Smoothing** → `AudioAnalyzer.smooth_amplitude()` smooths values
7. **Playback** → pygame plays audio while OpenCV renders frames
8. **Animation** → `AvatarRenderer.render_frame()` for each frame
9. **Display** → OpenCV shows synced video

### RVC Training Flow (Implemented)

1. **Prepare Voice Data** → `prepare_voice_data.py` downloads from YouTube
2. **Cache Check** → `is_cache_valid()` checks if preprocessing needed
3. **Preprocessing (GPU)** → Resample, extract pitch (RMVPE), extract features (HuBERT)
4. **Filelist Creation** → Generate training index with correct format
5. **Training** → `train_rvc_with_tracking()` trains Generator & Discriminator
6. **MLflow Logging** → Track metrics, system stats, and model checkpoints
7. **Export** → Checkpoints saved every 10 epochs as G_*.pth, D_*.pth

See [docs/RVC_TRAINING.md](RVC_TRAINING.md) for complete guide.

## Extension Points

### Adding a New TTS Engine

1. Create class extending `BaseTTS`
2. Implement required methods
3. Register in `vidchat.tts.__init__.py`
4. Update `TTSConfig` with new options

```python
from vidchat.tts.base import BaseTTS

class MyTTS(BaseTTS):
    def synthesize(self, text: str, output_path: str | Path) -> str:
        # Your implementation
        return str(output_path)

    def is_available(self) -> bool:
        return True

    def get_sample_rate(self) -> int:
        return 22050
```

### Adding New Avatar Styles

1. Extend `AvatarRenderer` or create new class
2. Override `render_frame()` method
3. Use same `mouth_openness` parameter for sync
4. Add configuration options to `AvatarConfig`

### Adding Emotion Detection

1. Create `vidchat.emotion` module
2. Analyze AI response text for emotion keywords
3. Pass emotion to `AvatarRenderer.render_frame()`
4. Renderer adjusts colors, expressions accordingly

## Testing Strategy

### Unit Tests

- **TTS**: Test synthesis with known text
- **Avatar**: Test frame rendering with various inputs
- **Audio**: Test amplitude analysis with known audio files
- **Config**: Test configuration serialization

### Integration Tests

- **Full Flow**: Test complete chat interaction
- **Sync**: Verify audio/video synchronization accuracy
- **Error Handling**: Test failure scenarios

### Headless Testing

Use headless tests for CI/CD:
```python
# test_headless.py
agent = VidChatAgent(config=test_config)
response = await agent.chat("test")
audio_path = agent.generate_speech(response)
amplitudes = agent.audio_analyzer.analyze_amplitude(audio_path)
assert len(amplitudes) > 0
```

## Performance Considerations

### CPU Usage
- **TTS**: ~10-15% during synthesis
- **Audio Analysis**: Negligible (<1%)
- **Avatar Rendering**: ~5-10% at 30 FPS
- **AI Processing**: Depends on Ollama model

### Memory Usage
- **Models**: ~100 MB (Piper model)
- **Runtime**: ~500 MB
- **Per Frame**: ~1.4 MB (800x600x3 bytes)

### Optimization Opportunities
1. Reuse rendered frames when mouth is closed
2. Reduce FPS when not speaking
3. Use GPU for avatar rendering (OpenGL)
4. Cache frequently used audio segments
5. Stream audio instead of full file loading

## Configuration Best Practices

### Development Config
```python
config = AppConfig(
    debug=True,
    log_level="DEBUG",
    avatar=AvatarConfig(
        fps=30,  # Lower FPS for development
    )
)
```

### Production Config
```python
config = AppConfig(
    debug=False,
    log_level="INFO",
    avatar=AvatarConfig(
        fps=60,  # Smoother animation
        enable_blink=True,
        enable_head_movement=True,
    ),
    enable_audio_sync=True,
)
```

### RVC Training Config
```python
config = AppConfig(
    rvc=RVCConfig(
        enabled=True,
        training_data_dir="data/my_voice",
        output_model_dir="models/rvc/my_voice",
        epochs=500,
        batch_size=8,
        learning_rate=0.0001,
    )
)
```

## Future Architecture Changes

### Planned Improvements

1. **Plugin System**: Load TTS/avatar engines dynamically
2. **Web Interface**: FastAPI backend, React frontend
3. **Streaming**: Real-time audio/video streaming
4. **Multi-user**: Support multiple concurrent sessions
5. **Cloud Deployment**: Docker containers, K8s orchestration

### Phase 2: RVC Integration

```
vidchat/training/
├── rvc_train_with_tracking.py (✅ implemented with GPU & MLflow)
├── mlflow_tracker.py (✅ implemented with system metrics)
├── extract_features_patched.py (✅ PyTorch 2.6 compatibility)
└── [Future: Model inference & voice conversion]
```

### Phase 3: Advanced Avatar

```
vidchat/avatar/
├── renderer.py (current)
├── sprite_renderer.py (2D sprites)
├── model_3d.py (3D faces)
└── emotion_detector.py (AI-based emotions)
```

## Conclusion

The modular architecture provides:
- **Flexibility**: Easy to extend and customize
- **Testability**: Components can be tested independently
- **Maintainability**: Clear separation of concerns
- **Scalability**: Ready for future enhancements

For examples of using the architecture, see [example.py](example.py).
