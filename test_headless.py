#!/usr/bin/env python3
"""
Headless test script for VidChat - tests AI interaction without display.
"""
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider


async def test_ollama_connection():
    """Test basic Ollama connection and response."""
    print("=" * 60)
    print("VidChat - Headless Test (No Display/Audio)")
    print("=" * 60)
    print("\nTesting Ollama connection and AI responses...\n")

    try:
        # Initialize PydanticAI agent with Ollama
        ollama_provider = OllamaProvider(base_url='http://localhost:11434/v1')
        model = OpenAIChatModel(
            model_name="llama3.2",
            provider=ollama_provider
        )
        agent = Agent(
            model=model,
            system_prompt="You are a friendly AI assistant. Keep your responses concise and helpful."
        )

        # Test questions
        questions = [
            "Hello! Please introduce yourself in one sentence.",
            "What's 2 plus 2?",
            "Name one benefit of Python programming.",
        ]

        # Ask each question
        for i, question in enumerate(questions, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}/{len(questions)}")
            print(f"{'='*60}")
            print(f"Question: {question}")

            # Get response from agent
            result = await agent.run(question)
            response_obj = result.response

            # Extract text from the ModelResponse
            if hasattr(response_obj, 'parts') and len(response_obj.parts) > 0:
                response_text = response_obj.parts[0].content
            else:
                response_text = str(response_obj)

            print(f"Response: {response_text}")
            print(f"Success: ✓")

        print(f"\n{'='*60}")
        print("All tests passed! ✓")
        print("The AI agent is working correctly.")
        print("\nNote: Display and audio features require:")
        print("  - X11 display (for avatar window)")
        print("  - Audio output (for text-to-speech)")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Ollama is running: ollama serve")
        print("2. Check that llama3.2 is available: ollama list")
        print("3. Try pulling the model: ollama pull llama3.2")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_ollama_connection())
    exit(0 if success else 1)
