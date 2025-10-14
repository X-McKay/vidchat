#!/usr/bin/env bash
#
# VidChat Setup Script
# Automates the setup of VidChat with all dependencies
# OS-agnostic (Linux, macOS, Windows with Git Bash)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}VidChat Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print status messages
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
info "Checking prerequisites..."

if ! command_exists python3; then
    error "Python 3 is not installed. Please install Python 3.13+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
info "Found Python $PYTHON_VERSION"

if ! command_exists uv; then
    warning "UV package manager not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

success "Prerequisites check complete"
echo ""

# Step 2: Create directory structure
info "Creating directory structure..."
mkdir -p .data/{training,voice_data,downloads,logs,models}
mkdir -p models output external docs scripts
touch .data/.gitkeep models/.gitkeep output/.gitkeep external/.gitkeep
success "Directory structure created"
echo ""

# Step 3: Install Python dependencies
info "Installing Python dependencies..."
uv sync --all-extras
success "Python dependencies installed"
echo ""

# Step 4: Download Piper TTS model
info "Downloading Piper TTS model..."
if [ ! -f "models/en_US-lessac-medium.onnx" ]; then
    cd models
    wget -q --show-progress \
        https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx \
        https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
    cd ..
    success "Piper TTS model downloaded"
else
    info "Piper TTS model already exists, skipping download"
fi
echo ""

# Step 5: Check Ollama installation
info "Checking Ollama installation..."
if ! command_exists ollama; then
    warning "Ollama not found. Please install Ollama:"
    echo ""
    echo "  Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Windows: Download from https://ollama.com/download"
    echo ""
    warning "After installing Ollama, run: ollama pull llama3.2"
else
    success "Ollama is installed"

    # Check if llama3.2 model is available
    if ollama list | grep -q "llama3.2"; then
        success "llama3.2 model is available"
    else
        warning "llama3.2 model not found. Downloading..."
        ollama pull llama3.2
        success "llama3.2 model downloaded"
    fi
fi
echo ""

# Step 6: Setup external dependencies (optional)
info "Would you like to setup SadTalker for realistic avatars? (y/N)"
read -r -p "> " setup_sadtalker

if [[ "$setup_sadtalker" =~ ^[Yy]$ ]]; then
    info "Setting up SadTalker..."
    if [ ! -d "external/SadTalker" ]; then
        cd external
        git clone https://github.com/OpenTalker/SadTalker.git
        cd SadTalker

        # Install dependencies
        pip install -r requirements.txt

        # Download models
        bash scripts/download_models.sh

        cd "$PROJECT_ROOT"
        success "SadTalker setup complete"
    else
        info "SadTalker already exists, skipping"
    fi
fi
echo ""

# Step 7: Build web interface
info "Would you like to build the web interface? (y/N)"
read -r -p "> " build_web

if [[ "$build_web" =~ ^[Yy]$ ]]; then
    info "Building web interface..."
    if command_exists npm; then
        cd src/vidchat/web/frontend
        npm install
        npm run build
        cd "$PROJECT_ROOT"
        success "Web interface built"
    else
        warning "Node.js/npm not found. Skipping web interface build."
        info "Install Node.js 22+ to enable the web interface"
    fi
fi
echo ""

# Final summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Quick Start:${NC}"
echo ""
echo "  1. Start services:"
echo "     $ uv run vidchat-cli start all --background"
echo ""
echo "  2. Access web interface:"
echo "     http://localhost:8000"
echo ""
echo "  3. Or use terminal chat:"
echo "     $ uv run vidchat"
echo ""
echo -e "${BLUE}Voice Training:${NC}"
echo ""
echo "  1. Edit config.yaml to add your YouTube URLs"
echo "  2. Run: uv run vidchat-cli train-voice"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo ""
echo "  - README.md - Complete guide"
echo "  - docs/QUICKSTART.md - 5-minute setup"
echo "  - docs/CLI_GUIDE.md - CLI documentation"
echo ""
success "Happy chatting! 🤖"
