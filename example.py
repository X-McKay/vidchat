#!/usr/bin/env python3
"""
Simple example script for VidChat.
This demonstrates basic usage of the VidChatAgent.
"""
import asyncio
from main import VidChatAgent


async def simple_demo():
    """Run a simple demo with predefined questions."""
    print("=" * 60)
    print("VidChat - Simple Example Demo")
    print("=" * 60)
    print("\nThis demo will ask the AI a few questions automatically.")
    print("Watch the avatar window and listen to the audio responses!\n")

    # Initialize the agent
    print("Initializing agent...")
    agent = VidChatAgent(model_name="llama3.2")

    # List of demo questions
    questions = [
        "Hello! Please introduce yourself briefly.",
        "What's 2 plus 2?",
        "Tell me a fun fact about Python programming.",
    ]

    # Ask each question
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*60}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'='*60}")

        # Get and display response
        response = await agent.chat(question)
        agent.display_response(response)

        # Wait a bit between questions
        if i < len(questions):
            print("\nMoving to next question...")
            await asyncio.sleep(2)

    # Clean up
    print(f"\n{'='*60}")
    print("Demo completed!")
    print(f"{'='*60}")
    agent.close()


if __name__ == "__main__":
    asyncio.run(simple_demo())
