# Contributing to VidChat

Thank you for your interest in contributing to VidChat! This document provides guidelines and instructions for contributing.

## 🎯 Goals

VidChat is designed to be:

- **Reproducible** - Anyone can clone and run it
- **OS-agnostic** - Works on Linux, macOS, Windows
- **Well-documented** - Clear setup and usage instructions
- **Modular** - Easy to extend and customize
- **Privacy-focused** - All processing happens locally

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/vidchat.git
cd vidchat
```

### 2. Setup Development Environment

```bash
# Run automated setup
bash scripts/setup.sh

# Or manual setup
uv sync --all-extras
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions focused and modular

### Project Structure

```
src/vidchat/
├── core/        # Core agent logic
├── tts/         # TTS engines (extend BaseTTS)
├── avatar/      # Avatar renderers
├── audio/       # Audio processing
├── web/         # Web interface
├── data/        # Voice data preparation
├── training/    # Model training
├── config/      # Configuration
└── utils/       # Utilities
```

### Configuration

- **Always use relative paths** - No absolute paths or OS-specific paths
- **Use config.yaml** - Don't hardcode configuration
- **Paths via config_loader** - Use `vidchat.utils.config_loader` for paths

Example:
```python
from vidchat.utils.config_loader import load_config

config = load_config()
data_dir = config.paths.data_dir  # Always relative to project root
```

### Testing

Before submitting:

1. **Test on your platform** - Ensure your changes work
2. **Check imports** - Make sure all imports are relative or from installed packages
3. **Test with clean setup** - Try `bash scripts/setup.sh` in a fresh clone
4. **Document changes** - Update relevant docs

### Commits

- Write clear, concise commit messages
- One logical change per commit
- Reference issues when applicable

Example:
```
Add YAML config loader for paths

- Implements config_loader.py with PathConfig
- Updates pyproject.toml to include PyYAML
- Adds config.example.yaml template

Fixes #123
```

## 🔧 Common Tasks

### Adding a New TTS Engine

1. Create a new file in `src/vidchat/tts/`
2. Extend `BaseTTS` class
3. Implement required methods
4. Add configuration to `config.yaml`
5. Update documentation

Example:
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

### Adding a New Avatar Renderer

1. Create a new file in `src/vidchat/avatar/`
2. Implement the renderer interface
3. Add configuration to `config.yaml`
4. Update `docs/AVATAR_GUIDE.md`

### Adding Documentation

1. Place docs in `docs/` directory
2. Use clear markdown formatting
3. Include code examples
4. Link from README.md

## 🐛 Reporting Bugs

When reporting bugs, include:

1. **OS and version** (Linux/macOS/Windows)
2. **Python version** (`python --version`)
3. **Steps to reproduce**
4. **Expected vs actual behavior**
5. **Error messages** (full traceback if available)
6. **Configuration** (sanitized `config.yaml`)

## 💡 Feature Requests

For feature requests:

1. Check if it already exists in issues
2. Describe the use case clearly
3. Explain why it fits VidChat's goals
4. Consider if it can be a plugin/extension

## 📦 Pull Request Process

1. **Update documentation** - Add/update relevant docs
2. **Test your changes** - Ensure they work on your platform
3. **Keep PRs focused** - One feature/fix per PR
4. **Describe changes** - Explain what and why in PR description
5. **Be responsive** - Address review feedback promptly

### PR Checklist

- [ ] Code follows project style
- [ ] All paths are relative (no OS-specific paths)
- [ ] Configuration uses `config.yaml`
- [ ] Documentation updated
- [ ] Tested locally
- [ ] Commit messages are clear
- [ ] No sensitive data (API keys, personal URLs) in commits

## 🌍 OS Compatibility

To ensure OS compatibility:

### Paths

```python
# ✅ Good - Use pathlib and relative paths
from pathlib import Path
from vidchat.utils.config_loader import load_config

config = load_config()
data_path = config.paths.data_dir / "training" / "file.txt"

# ❌ Bad - Hardcoded absolute paths
data_path = "/home/user/vidchat/.data/training/file.txt"
data_path = "C:\\Users\\user\\vidchat\\.data\\training\\file.txt"
```

### File Operations

```python
# ✅ Good - Use pathlib
path = Path("data") / "file.txt"
path.mkdir(parents=True, exist_ok=True)

# ❌ Bad - OS-specific commands
os.system("mkdir -p data/file.txt")
```

### Commands

```python
# ✅ Good - Use subprocess with list
import subprocess
subprocess.run(["python", "-m", "module"], check=True)

# ❌ Bad - Shell commands
os.system("python -m module")
```

## 📚 Resources

- **Python Docs** - https://docs.python.org/
- **PEP 8** - https://pep8.org/
- **Pathlib** - https://docs.python.org/3/library/pathlib.html
- **Type Hints** - https://docs.python.org/3/library/typing.html

## 🤝 Community

- Be respectful and welcoming
- Help others when you can
- Share knowledge and experiences
- Follow the Code of Conduct (if applicable)

## ❓ Questions

If you have questions:

1. Check existing documentation
2. Search existing issues
3. Open a discussion on GitHub
4. Ask in pull request comments

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to VidChat! Your efforts help make this project better for everyone. 🚀
