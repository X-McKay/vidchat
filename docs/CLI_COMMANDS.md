# VidChat CLI Command Reference

Quick reference for all `vidchat-cli` commands.

## Command Overview

```
vidchat-cli COMMAND [OPTIONS] [ARGS]
```

## Commands

### `status`
Check the status of all VidChat services.

```bash
vidchat-cli status
```

**Output:**
- Service status (running/stopped)
- Process IDs
- Port information
- Dependencies status
- Model availability

### `install`
Install all required dependencies.

```bash
# Install core + web dependencies (default)
vidchat-cli install

# Install all optional dependencies
vidchat-cli install --all

# Install without web dependencies
vidchat-cli install --no-web

# Install with voice prep tools
vidchat-cli install --voice-prep
```

**Options:**
- `--all` - Install all optional dependencies
- `--web / --no-web` - Install web dependencies (default: enabled)
- `--voice-prep` - Install voice preparation tools

### `models`
Download required AI and TTS models.

```bash
vidchat-cli models
```

**Downloads:**
- Ollama llama3.2 model
- Piper TTS voice model

### `build`
Build the React frontend.

```bash
vidchat-cli build
```

**Output:** Production-ready frontend in `src/vidchat/web/frontend/dist/`

### `start`
Start VidChat services.

```bash
# Start web server (foreground)
vidchat-cli start web

# Start web server (background)
vidchat-cli start web --background

# Start web server on custom host/port
vidchat-cli start web --host 0.0.0.0 --port 8080

# Start Ollama
vidchat-cli start ollama

# Start all services
vidchat-cli start all

# Start all in background
vidchat-cli start all --background
```

**Arguments:**
- `SERVICE` - Service to start: `web`, `ollama`, or `all`

**Options:**
- `--host TEXT` - Host to bind to (default: 127.0.0.1)
- `--port INTEGER` - Port to bind to (default: 8000)
- `--background / -d` - Run in background

### `stop`
Stop VidChat services.

```bash
# Stop all services (default if no argument provided)
vidchat-cli stop

# Stop web server only
vidchat-cli stop web

# Stop Ollama only
vidchat-cli stop ollama

# Stop all services (explicit)
vidchat-cli stop all

# Force kill all services
vidchat-cli stop --force
```

**Arguments:**
- `SERVICE` - Service to stop: `web`, `ollama`, or `all` (default: `all`)

**Options:**
- `--force / -f` - Force kill (SIGKILL instead of SIGTERM)

### `clean`
Clean build artifacts and cache.

```bash
vidchat-cli clean
```

**Removes:**
- Frontend `dist/` directory
- Python `__pycache__/` directories
- Python `*.pyc` files

### `logs`
Show service logs.

```bash
vidchat-cli logs web
vidchat-cli logs ollama
```

**Note:** Currently a placeholder. Run services in foreground for logs.

## Global Options

```bash
# Show help
vidchat-cli --help
vidchat-cli COMMAND --help

# Install shell completion
vidchat-cli --install-completion bash
vidchat-cli --install-completion zsh
vidchat-cli --install-completion fish

# Show completion script
vidchat-cli --show-completion
```

## Common Workflows

### First-Time Setup
```bash
vidchat-cli install --all
vidchat-cli models
vidchat-cli build
vidchat-cli status
```

### Development
```bash
# Terminal 1
vidchat-cli start ollama

# Terminal 2
vidchat-cli start web
```

### Production
```bash
vidchat-cli start all --background
vidchat-cli status
```

### Restart Services
```bash
vidchat-cli stop all
vidchat-cli start all --background
```

### Update Dependencies
```bash
uv sync --upgrade
cd src/vidchat/web/frontend && npm update
vidchat-cli build
```

## Exit Codes

- `0` - Success
- `1` - Error (with error message)

## Environment Variables

- `VIDCHAT_HOST` - Default web server host
- `VIDCHAT_PORT` - Default web server port
- `OLLAMA_HOST` - Ollama server URL

## Shell Completion

### Bash
```bash
vidchat-cli --install-completion bash
source ~/.bashrc
```

### Zsh
```bash
vidchat-cli --install-completion zsh
source ~/.zshrc
```

### Fish
```bash
vidchat-cli --install-completion fish
source ~/.config/fish/config.fish
```

## Troubleshooting Commands

```bash
# Check what's wrong
vidchat-cli status

# Force restart
vidchat-cli stop all --force
vidchat-cli start all --background

# Reinstall dependencies
vidchat-cli clean
vidchat-cli install --all

# Check ports
lsof -i :8000   # Web server
lsof -i :11434  # Ollama

# Check processes
ps aux | grep ollama
ps aux | grep uvicorn
```

## Tips

1. Always check `vidchat-cli status` first
2. Use `--background` for production deployments
3. Use `--force` if services won't stop gracefully
4. Run `vidchat-cli clean` if builds seem stale
5. Install shell completion for faster usage

## Related Commands

### mise Tasks
```bash
mise tasks                # List all tasks
mise run install          # Install dependencies
mise run start-web        # Start web server
mise run build-frontend   # Build frontend
mise run clean            # Clean artifacts
```

### Direct Commands
```bash
vidchat                   # Terminal chat (no web UI)
python main.py            # Same as above
python start_web_server.py  # Start web server directly
```

## Documentation Links

- [CLI Guide](CLI_GUIDE.md) - Full CLI documentation
- [Quick Start](QUICKSTART.md) - 5-minute setup guide
- [Main README](README.md) - Project overview
- [Web Interface](WEB_INTERFACE_README.md) - Web UI docs
- [Avatar Guide](AVATAR_GUIDE.md) - Avatar configuration
- [Voice Data Prep](VOICE_DATA_PREP_GUIDE.md) - Voice training

## Getting Help

```bash
vidchat-cli --help
vidchat-cli COMMAND --help
```

For issues, check [GitHub Issues](https://github.com/your-repo/issues).
