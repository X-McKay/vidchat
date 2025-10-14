# VidChat CLI Guide

Comprehensive command-line interface for managing VidChat services, dependencies, and runtime environments.

## Quick Start

```bash
# Install mise for version management
curl https://mise.jdx.dev/install.sh | sh

# Let mise install the correct Python and Node versions
mise install

# Install all dependencies
vidchat-cli install --all

# Download required models
vidchat-cli models

# Check status
vidchat-cli status

# Start all services
vidchat-cli start all
```

## Prerequisites

### mise (Recommended)

mise manages runtime versions (Python, Node.js) automatically:

```bash
# Install mise
curl https://mise.jdx.dev/install.sh | sh

# Or with Homebrew (macOS)
brew install mise

# Add to your shell (bash example)
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
```

The project includes `.mise.toml` which specifies:
- Python 3.13
- Node.js 22

When you `cd` into the project, mise automatically activates the correct versions.

### Manual Setup (Without mise)

If not using mise, ensure you have:
- Python 3.13+
- Node.js 22+
- UV package manager
- Ollama

## CLI Commands

### Status Checking

#### `vidchat-cli status`

Check the status of all VidChat services and dependencies.

**Output includes:**
- Ollama service status (running/stopped/not installed)
- Web server status (running/stopped)
- Frontend build status
- Python dependencies status
- Node dependencies status
- TTS model availability

**Example:**
```bash
$ vidchat-cli status

VidChat Service Status

┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Service            ┃ Status        ┃ Details                          ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Ollama             │ ✓ Running     │ Port 11434, PID: 1234           │
│ Web Server         │ ✓ Running     │ Port 8000, PID: 5678            │
│ Python Deps        │ ✓ Installed   │ Python dependencies OK          │
│ Node Deps          │ ✓ Installed   │ Node dependencies OK            │
│ TTS Models         │ ✓ Available   │ Piper TTS model downloaded      │
└────────────────────┴───────────────┴──────────────────────────────────┘
```

### Installation

#### `vidchat-cli install [OPTIONS]`

Install Python and Node.js dependencies.

**Options:**
- `--all` - Install all optional dependencies (web, voice-prep)
- `--web / --no-web` - Install web dependencies (default: enabled)
- `--voice-prep` - Install voice preparation dependencies
- `--help` - Show help message

**Examples:**
```bash
# Install core + web dependencies (default)
vidchat-cli install

# Install everything
vidchat-cli install --all

# Install only core dependencies (no web)
vidchat-cli install --no-web

# Install with voice preparation tools
vidchat-cli install --voice-prep
```

**What it does:**
1. Runs `uv sync` with appropriate extras
2. Installs Node.js dependencies in frontend directory
3. Creates Python virtual environment if needed

#### `vidchat-cli models`

Download required AI and TTS models.

**Downloads:**
- Ollama llama3.2 model (~2GB)
- Piper TTS voice model (~61MB)

**Example:**
```bash
$ vidchat-cli models

Downloading Models

⠋ Downloading llama3.2 model...
✓ llama3.2 downloaded
⠋ Downloading Piper TTS model...
✓ Piper TTS model downloaded

✓ All models downloaded successfully!
```

### Building

#### `vidchat-cli build`

Build the React frontend for production.

**What it does:**
1. Runs TypeScript compilation
2. Runs Vite build process
3. Outputs to `src/vidchat/web/frontend/dist/`

**Example:**
```bash
$ vidchat-cli build

Building Frontend

⠋ Building React frontend...
✓ Frontend built successfully

✓ Frontend ready!
```

### Starting Services

#### `vidchat-cli start SERVICE [OPTIONS]`

Start VidChat services.

**Arguments:**
- `SERVICE` - Service to start: `web`, `ollama`, or `all`

**Options:**
- `--host TEXT` - Host to bind to (default: 127.0.0.1)
- `--port INTEGER` - Port to bind to (default: 8000)
- `--background / -d` - Run in background (daemon mode)

**Examples:**

**Start web server (foreground):**
```bash
vidchat-cli start web
# Press Ctrl+C to stop
```

**Start web server (background):**
```bash
vidchat-cli start web --background
```

**Start web server on all interfaces:**
```bash
vidchat-cli start web --host 0.0.0.0 --port 8080
```

**Start Ollama service:**
```bash
vidchat-cli start ollama
```

**Start all services:**
```bash
vidchat-cli start all --background
```

**What happens:**
1. Checks if service is already running
2. Checks dependencies (auto-builds frontend if needed)
3. Starts the service
4. Reports status and access URLs

### Stopping Services

#### `vidchat-cli stop SERVICE [OPTIONS]`

Stop VidChat services gracefully.

**Arguments:**
- `SERVICE` - Service to stop: `web`, `ollama`, or `all`

**Options:**
- `--force / -f` - Force kill process (SIGKILL instead of SIGTERM)

**Examples:**

**Stop web server gracefully:**
```bash
vidchat-cli stop web
```

**Stop all services:**
```bash
vidchat-cli stop all
```

**Force kill if not responding:**
```bash
vidchat-cli stop web --force
```

### Cleaning

#### `vidchat-cli clean`

Clean build artifacts and cache files.

**What it removes:**
- Frontend `dist/` directory
- Python `__pycache__/` directories
- Python `*.pyc` files

**Example:**
```bash
$ vidchat-cli clean

Cleaning Build Artifacts

⠋ Cleaning...
✓ Cleaned

✓ Build artifacts cleaned!
```

## Using mise Tasks

The `.mise.toml` file defines convenient tasks you can run with `mise run`:

```bash
# Install all dependencies
mise run install

# Build frontend
mise run build-frontend

# Start frontend dev server (with hot reload)
mise run dev-frontend

# Start web server
mise run start-web

# Start Ollama
mise run start-ollama

# Download models
mise run models

# Test imports
mise run test-imports

# Clean artifacts
mise run clean
```

**Example workflow:**
```bash
# One-time setup
mise install              # Install Python 3.13 and Node 22
mise run install          # Install dependencies
mise run models           # Download models

# Development
mise run dev-frontend     # Terminal 1: Frontend dev server
mise run start-web        # Terminal 2: Backend server

# Or production
mise run build-frontend   # Build frontend
mise run start-web        # Serve built frontend
```

## Common Workflows

### First-Time Setup

```bash
# 1. Install mise
curl https://mise.jdx.dev/install.sh | sh

# 2. Activate mise in your shell
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
source ~/.bashrc

# 3. Install runtimes
mise install

# 4. Install dependencies
vidchat-cli install --all

# 5. Download models
vidchat-cli models

# 6. Build frontend
vidchat-cli build

# 7. Check everything is ready
vidchat-cli status
```

### Starting Development Environment

```bash
# Terminal 1: Start Ollama
vidchat-cli start ollama

# Terminal 2: Start frontend dev server (hot reload)
cd src/vidchat/web/frontend
npm run dev

# Terminal 3: Start backend
vidchat-cli start web

# Access frontend at: http://localhost:5173 (Vite dev server)
# Backend at: http://localhost:8000
```

### Starting Production Environment

```bash
# Start all services in background
vidchat-cli start all --background

# Check status
vidchat-cli status

# Access at: http://localhost:8000

# Stop when done
vidchat-cli stop all
```

### Updating Dependencies

```bash
# Update Python dependencies
uv sync --upgrade

# Update Node dependencies
cd src/vidchat/web/frontend
npm update

# Rebuild frontend
vidchat-cli build
```

### Troubleshooting

**Check what's wrong:**
```bash
vidchat-cli status
```

**Services not starting:**
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :11434

# Force kill stuck processes
vidchat-cli stop all --force

# Restart
vidchat-cli start all
```

**Dependencies issues:**
```bash
# Reinstall dependencies
vidchat-cli clean
vidchat-cli install --all

# Check imports
uv run python -c "from vidchat import VidChatAgent; print('OK')"
```

**Frontend build issues:**
```bash
# Clean and rebuild
vidchat-cli clean
cd src/vidchat/web/frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
vidchat-cli build
```

## Environment Variables

The CLI respects these environment variables:

- `VIDCHAT_HOST` - Default host for web server (default: 127.0.0.1)
- `VIDCHAT_PORT` - Default port for web server (default: 8000)
- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)

**Example:**
```bash
export VIDCHAT_HOST=0.0.0.0
export VIDCHAT_PORT=3000
vidchat-cli start web
```

## Advanced Usage

### Running Multiple Instances

**Web server on different port:**
```bash
vidchat-cli start web --host 0.0.0.0 --port 8001 --background
vidchat-cli start web --host 0.0.0.0 --port 8002 --background
```

### Custom Ollama Configuration

**Using remote Ollama:**
```bash
export OLLAMA_HOST=http://remote-server:11434
vidchat-cli start web
```

### Integration with systemd (Linux)

Create `/etc/systemd/system/vidchat.service`:

```ini
[Unit]
Description=VidChat Web Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/vidchat
ExecStart=/path/to/mise exec -- vidchat-cli start web --host 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable vidchat
sudo systemctl start vidchat
sudo systemctl status vidchat
```

## Help and Completion

**Get help for any command:**
```bash
vidchat-cli --help
vidchat-cli start --help
vidchat-cli install --help
```

**Shell completion:**
```bash
# Bash
vidchat-cli --install-completion bash

# Zsh
vidchat-cli --install-completion zsh

# Fish
vidchat-cli --install-completion fish
```

## Comparison: CLI vs Manual

| Task | Manual | With CLI |
|------|--------|----------|
| Check status | Multiple commands + manual inspection | `vidchat-cli status` |
| Install deps | `uv sync --extra web && cd frontend && npm install` | `vidchat-cli install` |
| Start services | Multiple terminals, remember ports/commands | `vidchat-cli start all` |
| Stop services | Find PIDs, kill processes | `vidchat-cli stop all` |
| Download models | Manual wget commands, ollama pull | `vidchat-cli models` |
| Build frontend | `cd` to directory, run npm build | `vidchat-cli build` |

## Best Practices

1. **Use mise for version management** - Ensures consistent Python/Node versions
2. **Check status first** - Run `vidchat-cli status` before starting services
3. **Use background mode for production** - `--background` flag for daemon mode
4. **Regular updates** - Keep dependencies current
5. **Clean when needed** - Run `vidchat-cli clean` if builds seem stale

## Troubleshooting Guide

### Port Already in Use

**Problem:** "Port 8000 already in use"

**Solution:**
```bash
# Find what's using the port
lsof -i :8000

# Stop with CLI
vidchat-cli stop web --force

# Or manually kill
kill -9 <PID>
```

### Ollama Not Found

**Problem:** "Ollama is not installed"

**Solution:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
vidchat-cli status
```

### Dependencies Missing

**Problem:** "Python dependencies not OK"

**Solution:**
```bash
# Reinstall
vidchat-cli install --all

# Verify
vidchat-cli status
```

### Frontend Not Building

**Problem:** "Frontend build failed"

**Solution:**
```bash
# Clean and rebuild
vidchat-cli clean
cd src/vidchat/web/frontend
rm -rf node_modules
npm install --legacy-peer-deps
vidchat-cli build
```

## License

Same as main VidChat project license.
