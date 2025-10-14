# VidChat - AI Chat Agent with Avatar and Audio

An interactive AI chat agent that responds with both visual avatar animations and spoken audio responses, similar to a Zoom-style video chat experience.

## Features

- **AI-Powered Conversations**: Uses Ollama and PydanticAI for intelligent responses
- **Visual Avatar**: Animated avatar that shows thinking and speaking states
- **Text-to-Speech**: Audio responses using pyttsx3
- **Real-time Display**: OpenCV-based video window showing the avatar
- **Simple Interface**: Command-line chat interface

## Prerequisites

Before running VidChat, make sure you have:

1. **Python 3.13+** installed
2. **UV package manager** installed (for dependency management)
3. **Ollama** installed and running

### Installing Ollama

If you don't have Ollama installed:

**Linux/macOS:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from [https://ollama.com/download](https://ollama.com/download)

### Pull the required model

After installing Ollama, pull the llama3.2 model:

```bash
ollama pull llama3.2
```

Make sure Ollama is running (it usually starts automatically, or run `ollama serve`).

## Installation

1. Clone or navigate to the project directory:
```bash
cd vidchat
```

2. Install dependencies using UV:
```bash
uv sync
```

This will install all required packages:
- pydantic-ai (for AI agent framework)
- ollama (for LLM integration)
- pyttsx3 (for text-to-speech)
- opencv-python (for video display)
- pillow (for image processing)

## Usage

### Running the Application

Start the interactive chat agent:

```bash
uv run python main.py
```

Or run the example demo script that asks a few predefined questions:

```bash
uv run python example.py
```

To test the AI functionality without display/audio (headless mode):

```bash
uv run python test_headless.py
```

### Using the Chat Interface

1. The application will initialize and open a video window with the avatar
2. Type your message in the terminal
3. Press Enter to send
4. Watch the avatar and listen to the audio response
5. Type `quit`, `exit`, or `bye` to end the chat

### Example Session

```
============================================================
VidChat - AI Chat Agent with Avatar and Audio
============================================================

Initializing agent...
Note: Make sure Ollama is running with llama3.2 model installed
      Run: ollama pull llama3.2

Type 'quit' or 'exit' to end the chat

You: Hello! How are you?

[You]: Hello! How are you?

[AI Speaking]: Hello! I'm doing well, thank you for asking! I'm here and ready to help you with anything you need. How can I assist you today?

You: What's the weather like?

[You]: What's the weather like?

[AI Speaking]: I don't have access to real-time weather data, but I'd be happy to help you check the weather if you tell me your location!

You: quit

Goodbye!
```

## How It Works

### Architecture

The application consists of a single main component, the `VidChatAgent` class, which handles:

1. **AI Agent**: Uses PydanticAI with Ollama's llama3.2 model for generating responses
2. **Avatar Rendering**: Creates simple animated avatar frames using OpenCV
3. **Text-to-Speech**: Converts AI responses to speech using pyttsx3
4. **State Management**: Manages thinking, speaking, and idle states

### Avatar States

- **Thinking**: Avatar appears with "Thinking..." text while the AI processes your input
- **Speaking**: Avatar changes color and shows an open mouth while speaking
- **Idle**: Avatar returns to neutral state after speaking

### Files

- `main.py`: Main application with the VidChatAgent class and interactive chat loop
- `example.py`: Simple demo script with predefined questions (requires display)
- `test_headless.py`: Headless test script to verify AI functionality without display/audio
- `pyproject.toml`: Project configuration and dependencies
- `README.md`: This file
- `PROJECT.md`: Project requirements and specifications

## Customization

You can customize various aspects of the application by modifying `main.py`:

### Change the AI Model

In the `VidChatAgent.__init__()` method, change the model name:

```python
agent = VidChatAgent(model_name="llama3.1")  # or any other Ollama model
```

### Adjust Speech Rate

In the `VidChatAgent.__init__()` method:

```python
self.tts_engine.setProperty('rate', 180)  # Faster speech
```

### Modify System Prompt

In the `VidChatAgent.__init__()` method:

```python
self.agent = Agent(
    model=self.model,
    system_prompt="Your custom system prompt here"
)
```

### Change Avatar Colors

In the `create_avatar_frame()` method, modify the color tuples:

```python
color = (R, G, B)  # RGB values 0-255
```

## Troubleshooting

### "Error initializing agent"

**Solution**: Make sure Ollama is running and the model is pulled
```bash
ollama serve  # Start Ollama if not running
ollama pull llama3.2  # Pull the model
```

### "No module named 'pydantic_ai'"

**Solution**: Install dependencies
```bash
uv sync
```

### Text-to-Speech not working (Linux)

**Solution**: Install espeak
```bash
# Ubuntu/Debian
sudo apt-get install espeak

# Fedora
sudo dnf install espeak
```

### Avatar window doesn't appear

**Solution**: Make sure you have display capabilities. On remote servers, you may need X11 forwarding or a virtual display.

## Future Enhancements

Potential improvements for future versions:

- More sophisticated avatar animations
- Multiple avatar styles/characters
- Voice input (speech-to-text)
- Better lip-syncing with audio
- Recording conversation history
- Web-based interface
- Multiple AI model support
- Customizable avatar images/videos

## License

This project is open source and available for educational and personal use.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve VidChat!
