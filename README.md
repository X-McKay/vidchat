# VidChat - AI Chat Agent with Voice Cloning (Web-Only)

An interactive AI chat agent with XTTS v2 zero-shot voice cloning and web interface.

## 🎯 Getting Started

**New to VidChat?** Start here:
- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[END_TO_END_GUIDE.md](END_TO_END_GUIDE.md)** - Comprehensive usage guide
- **[test_end_to_end.py](test_end_to_end.py)** - Automated test suite

**Version 0.3.0** - Web-only (OpenCV desktop UI removed for simplicity)

## 🚀 Quick Start

```bash
# 1. Install dependencies
uv sync --extra voice-cloning --extra web

# 2. Start Ollama (if not running)
ollama serve &

# 3. Run test suite
uv run python test_end_to_end.py

# 4. Start web server (in another terminal)
uv run uvicorn vidchat.web.server:app --host 127.0.0.1 --port 8000

# 5. Test the web interface
uv run python test_webapp.py
```

**That's it!** See [QUICKSTART.md](QUICKSTART.md) for more options.

## ✨ Features

### Core Features (v0.3.0)
- **🎙️ Zero-Shot Voice Cloning**: XTTS v2 clones any voice with just 6 seconds of audio
- **🎓 RVC Voice Training**: Train custom voice models with GPU acceleration and MLflow tracking
- **🤖 AI-Powered Chat**: Ollama LLM (llama3.2) via PydanticAI for intelligent responses
- **🌐 Web Interface**: FastAPI backend with WebSocket support for real-time audio streaming
- **🎵 High-Quality Audio**: 24kHz voice synthesis with cloned voice
- **🌐 17 Languages**: Multilingual support for voice synthesis
- **⚡ Fast**: ~1-2 seconds per sentence generation
- **📊 MLflow Tracking**: Experiment tracking with system metrics monitoring

### Technical Features
- **📦 Modular Design**: Clean separation of concerns (AI, TTS, Web)
- **🔧 Easy Configuration**: Simple AppConfig for customization
- **🧪 Fully Tested**: Comprehensive test suite validates all components
- **🐍 Modern Python**: Uses PydanticAI, FastAPI, and latest Python features
- **🌍 Cross-Platform**: Works on Linux, macOS, and Windows
- **🔒 Privacy-First**: All processing runs locally, no external API calls

## 📋 Prerequisites

### Required
- **Python 3.13+**
- **UV package manager** - [Install UV](https://github.com/astral-sh/uv)
- **Ollama** - Local LLM server

### Optional
- **Node.js 22+** - For web interface development
- **mise** - Automatic runtime version management

### Installing Prerequisites

**UV (Package Manager):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Ollama (LLM Server):**
```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

**Pull LLM Model:**
```bash
ollama pull llama3.2
```

## 🛠️ Installation

### Option 1: Automated Setup (Recommended)

Run the setup script which handles everything:

```bash
bash scripts/setup.sh
```

The script will:
1. Check prerequisites
2. Create directory structure
3. Install Python dependencies
4. Download Piper TTS models
5. Check Ollama installation
6. Optionally setup SadTalker
7. Optionally build web interface

### Option 2: Manual Setup

```bash
# 1. Install Python dependencies
uv sync --all-extras

# 2. Download Piper TTS model
mkdir -p models
cd models
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ..

# 3. Create configuration
cp config.example.yaml config.yaml

# 4. Install Ollama and pull model
ollama pull llama3.2
```

## 🎯 Usage

### Web Interface

```bash
# Start all services in background
uv run vidchat-cli start all --background

# Open browser to http://localhost:8000
```

### Terminal Chat

```bash
uv run vidchat
```

### CLI Commands

```bash
# Check status
uv run vidchat-cli status

# Start services
uv run vidchat-cli start web
uv run vidchat-cli start ollama
uv run vidchat-cli start all --background

# Stop services
uv run vidchat-cli stop all

# Build frontend
uv run vidchat-cli build
```

## ⚙️ Configuration

VidChat uses a YAML configuration file for all settings.

1. **Copy the example config:**
   ```bash
   cp config.example.yaml config.yaml
   ```

2. **Edit config.yaml:**
   ```yaml
   # Voice Training
   voice_training:
     voice_name: "my_voice"
     training_urls:
       - "https://www.youtube.com/watch?v=YOUR_VIDEO"
     epochs: 300
     batch_size: 4

   # Application Settings
   app:
     window_name: "VidChat"
     fps: 30
     width: 800
     height: 600

   # Avatar Settings
   avatar:
     type: "image"  # "geometric", "image", or "sadtalker"
     image_path: "assets/avatars/default_avatar.png"
   ```

3. **All paths are relative to project root** - works on any OS!

### RVC Voice Training

Train custom voice models with GPU acceleration and MLflow experiment tracking:

```bash
# 1. Prepare voice data from YouTube
uv run python src/vidchat/data/prepare_voice_data.py your_voice_name \
  --urls "https://www.youtube.com/watch?v=VIDEO_ID"

# 2. Train voice model with GPU
uv run python src/vidchat/training/rvc_train_with_tracking.py your_voice_name \
  --epochs 500 --batch-size 4 --gpu

# 3. View training metrics
mlflow ui --backend-store-uri file://$(pwd)/.data/mlruns
```

**Features:**
- GPU-accelerated preprocessing (pitch extraction, feature extraction)
- Intelligent preprocessing cache (skip reprocessing when data unchanged)
- MLflow experiment tracking with system metrics
- Model checkpoints saved every 10 epochs
- Real-time training progress monitoring

See [docs/RVC_TRAINING.md](docs/RVC_TRAINING.md) for comprehensive guide.

## 📁 Project Structure

```
vidchat/
├── config.yaml              # Your configuration (gitignored)
├── config.example.yaml      # Configuration template
├── pyproject.toml          # Dependencies and build config
├── README.md               # This file
│
├── scripts/                # Setup and utility scripts
│   └── setup.sh           # Automated setup script
│
├── docs/                   # Documentation
│   ├── QUICKSTART.md
│   ├── CLI_GUIDE.md
│   ├── AVATAR_GUIDE.md
│   └── ...
│
├── src/vidchat/           # Main package
│   ├── core/             # Core agent
│   ├── tts/              # Text-to-speech engines
│   ├── avatar/           # Avatar renderers
│   ├── audio/            # Audio processing
│   ├── web/              # Web interface
│   ├── data/             # Voice data preparation
│   ├── training/         # Model training
│   ├── config/           # Configuration
│   └── utils/            # Utilities
│
├── assets/               # Asset files
│   └── avatars/         # Avatar images
│
├── models/              # TTS models (downloaded)
├── .data/               # Data directory (gitignored)
│   ├── training/       # Training data
│   ├── voice_data/     # Voice datasets
│   ├── downloads/      # Downloaded files
│   ├── logs/           # Log files
│   └── models/         # Training checkpoints
│
├── output/              # Output files (gitignored)
└── external/            # External dependencies (gitignored)
    ├── SadTalker/      # AI avatar renderer
    └── RVC/            # Voice conversion
```

## 🔧 Troubleshooting

### "Ollama not running"

```bash
# Start Ollama
ollama serve

# Verify model
ollama list
```

### "Config file not found"

```bash
# Create config from example
cp config.example.yaml config.yaml
```

### "Piper TTS model missing"

```bash
# Download model
bash scripts/setup.sh
```

### "Permission denied: scripts/setup.sh"

```bash
# Make executable
chmod +x scripts/setup.sh
```

## 📚 Documentation

Comprehensive guides are available in the `docs/` directory:

**Getting Started:**
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute setup guide
- **[docs/CLI_GUIDE.md](docs/CLI_GUIDE.md)** - Complete CLI documentation
- **[docs/CLI_COMMANDS.md](docs/CLI_COMMANDS.md)** - Quick command reference

**Voice & Training:**
- **[docs/RVC_TRAINING.md](docs/RVC_TRAINING.md)** - Complete RVC training guide
- **[docs/XTTS_VOICE_CLONING.md](docs/XTTS_VOICE_CLONING.md)** - Zero-shot voice cloning with XTTS v2
- **[docs/VOICE_DATA_PREP_GUIDE.md](docs/VOICE_DATA_PREP_GUIDE.md)** - Voice data preparation
- **[docs/VOICE_CLONING_SOLUTIONS.md](docs/VOICE_CLONING_SOLUTIONS.md)** - Comparison of voice cloning options
- **[docs/MLFLOW_TRACKING.md](docs/MLFLOW_TRACKING.md)** - Experiment tracking guide

**Interface & Features:**
- **[docs/WEB_INTERFACE_README.md](docs/WEB_INTERFACE_README.md)** - Web interface guide
- **[docs/AVATAR_GUIDE.md](docs/AVATAR_GUIDE.md)** - Avatar customization
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture

## 🔒 Privacy & Security

- **All processing is local** - No data sent to external servers
- **config.yaml is gitignored** - Your URLs and settings stay private
- **Models downloaded to local directories** - Full control over data
- **External dependencies optional** - Only install what you need

## 🤝 Contributing

Contributions are welcome! This project is designed to be:

- **Reproducible** - Anyone can clone and run it
- **OS-agnostic** - Works on Linux, macOS, Windows
- **Well-documented** - Clear setup and usage instructions
- **Modular** - Easy to extend and customize

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple platforms if possible
5. Submit a pull request

## 📄 License

This project is open source and available for educational and personal use.

## 🙏 Credits

**Core Technologies:**
- [Piper TTS](https://github.com/rhasspy/piper) - High-quality text-to-speech
- [PydanticAI](https://ai.pydantic.dev/) - AI agent framework
- [Ollama](https://ollama.com/) - Local LLM server
- [OpenCV](https://opencv.org/) - Computer vision
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - UI library

**Optional:**
- [SadTalker](https://github.com/OpenTalker/SadTalker) - AI avatar animations
- [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) - Voice conversion

---

**Enjoy chatting with your AI assistant!** 🤖✨

For issues or questions, please open an issue on GitHub.
