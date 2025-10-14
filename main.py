"""
VidChat - AI Chat Agent with Avatar and Audio Responses
"""
import sys
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider
import pyttsx3
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import time


class VidChatAgent:
    """Simple AI chat agent with video avatar and audio responses."""

    def __init__(self, model_name: str = "llama3.2"):
        """Initialize the agent with Ollama model and TTS engine."""
        # Initialize PydanticAI agent with Ollama (via OpenAI-compatible API)
        ollama_provider = OllamaProvider(base_url='http://localhost:11434/v1')
        self.model = OpenAIChatModel(
            model_name=model_name,
            provider=ollama_provider
        )
        self.agent = Agent(
            model=self.model,
            system_prompt="You are a friendly AI assistant. Keep your responses concise and helpful."
        )

        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Speed of speech

        # Avatar display settings
        self.width = 640
        self.height = 480
        self.window_name = "VidChat - AI Assistant"

    def create_avatar_frame(self, text: str, speaking: bool = False):
        """Create a simple avatar frame with text overlay."""
        # Create a blank frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (20, 20, 40)  # Dark blue background

        # Draw a simple circular avatar
        center_x, center_y = self.width // 2, self.height // 3
        radius = 80
        color = (100, 200, 100) if speaking else (100, 150, 200)
        cv2.circle(frame, (center_x, center_y), radius, color, -1)

        # Draw eyes
        eye_offset = 25
        eye_radius = 10
        cv2.circle(frame, (center_x - eye_offset, center_y - 10), eye_radius, (255, 255, 255), -1)
        cv2.circle(frame, (center_x + eye_offset, center_y - 10), eye_radius, (255, 255, 255), -1)
        cv2.circle(frame, (center_x - eye_offset, center_y - 10), 5, (50, 50, 50), -1)
        cv2.circle(frame, (center_x + eye_offset, center_y - 10), 5, (50, 50, 50), -1)

        # Draw mouth
        if speaking:
            cv2.ellipse(frame, (center_x, center_y + 20), (20, 15), 0, 0, 180, (50, 50, 50), -1)
        else:
            cv2.ellipse(frame, (center_x, center_y + 25), (25, 10), 0, 0, 180, (50, 50, 50), 2)

        # Add text at the bottom
        self._add_text_to_frame(frame, text)

        return frame

    def _add_text_to_frame(self, frame, text: str):
        """Add wrapped text to the bottom of the frame."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 1
        color = (255, 255, 255)

        # Word wrap the text
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            (text_width, _), _ = cv2.getTextSize(test_line, font, font_scale, thickness)

            if text_width < self.width - 40:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Display last few lines at the bottom
        y_start = self.height - 100
        line_height = 25

        for i, line in enumerate(lines[-3:]):  # Show last 3 lines
            y = y_start + i * line_height
            cv2.putText(frame, line, (20, y), font, font_scale, color, thickness, cv2.LINE_AA)

    def speak(self, text: str):
        """Convert text to speech."""
        print(f"\n[AI Speaking]: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def display_response(self, response_text: str):
        """Display avatar with response and speak it."""
        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)

        # Show thinking state
        thinking_frame = self.create_avatar_frame("Thinking...", False)
        cv2.imshow(self.window_name, thinking_frame)
        cv2.waitKey(500)

        # Show speaking state with response
        speaking_frame = self.create_avatar_frame(response_text, True)
        cv2.imshow(self.window_name, speaking_frame)

        # Speak the response (this will block until done)
        self.speak(response_text)

        # Show idle state
        idle_frame = self.create_avatar_frame(response_text, False)
        cv2.imshow(self.window_name, idle_frame)
        cv2.waitKey(2000)  # Show for 2 seconds

    async def chat(self, user_input: str) -> str:
        """Send user input to the agent and get response."""
        print(f"\n[You]: {user_input}")

        # Get response from PydanticAI agent
        result = await self.agent.run(user_input)

        # Extract text from the ModelResponse
        # The response contains parts, we get the text from the first TextPart
        response_obj = result.response
        if hasattr(response_obj, 'parts') and len(response_obj.parts) > 0:
            response_text = response_obj.parts[0].content
        else:
            response_text = str(response_obj)

        return response_text

    def close(self):
        """Clean up resources."""
        cv2.destroyAllWindows()


async def main():
    """Main function to run the VidChat agent."""
    print("=" * 60)
    print("VidChat - AI Chat Agent with Avatar and Audio")
    print("=" * 60)
    print("\nInitializing agent...")
    print("Note: Make sure Ollama is running with llama3.2 model installed")
    print("      Run: ollama pull llama3.2")
    print("\nType 'quit' or 'exit' to end the chat\n")

    try:
        # Initialize the agent
        agent = VidChatAgent(model_name="llama3.2")

        # Chat loop
        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nGoodbye!")
                    break

                # Get response from agent
                response = await agent.chat(user_input)

                # Display avatar and speak response
                agent.display_response(response)

            except KeyboardInterrupt:
                print("\n\nChat interrupted by user.")
                break
            except Exception as e:
                print(f"\nError during chat: {e}")
                print("Please make sure Ollama is running and the model is available.")

        # Clean up
        agent.close()

    except Exception as e:
        print(f"\nError initializing agent: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is installed and running")
        print("2. Run: ollama pull llama3.2")
        print("3. Check that all dependencies are installed: uv sync")
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
