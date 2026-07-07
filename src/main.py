"""
MediGuide AI - Main Entry Point
================================
The main application entry point for MediGuide AI.
Provides multiple interfaces:
  1. Interactive CLI chat interface
  2. Single-query mode (for scripting/testing)
  3. API server mode (via FastAPI)

Usage:
  Interactive: python src/main.py
  Single query: python src/main.py --query "I have a headache and fever"
  API server:   python src/main.py --serve

Environment:
  Requires GOOGLE_API_KEY in .env file (see .env.example)
  Optional: MCP_SERVER_URL for connecting to the MCP knowledge server

Kaggle Concepts Demonstrated:
  - Agent / Multi-agent system (ADK) ✅
  - MCP Server integration ✅
  - Security features ✅
  - Agent skills (CLI) ✅
  - Deployability (Docker) ✅
"""

import os
import sys
import argparse
import asyncio
import json
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other imports
# CRITICAL: Never hardcode API keys in source code
load_dotenv()

# Validate required environment variables
def validate_environment():
    """Validates that all required environment variables are set."""
    required_vars = ["GOOGLE_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n📋 Setup instructions:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your Google API key: GOOGLE_API_KEY=your_key_here")
        print("   3. Get a key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)

    print("✅ Environment validated successfully")


# ─────────────────────────────────────────────────────────────────────────────
# Import after environment validation
# ─────────────────────────────────────────────────────────────────────────────

def setup_adk():
    """Initializes and returns the ADK runner with the MediGuide agent."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from src.agents.orchestrator import root_agent

    # Session service for multi-turn conversation memory
    session_service = InMemorySessionService()

    # Create the ADK runner
    runner = Runner(
        agent=root_agent,
        app_name="mediguide_ai",
        session_service=session_service,
    )

    return runner, session_service


async def run_agent_query(runner, session_service, user_id: str, session_id: str, query: str) -> str:
    """
    Runs a single query through the MediGuide agent system.

    Args:
        runner: The ADK Runner instance.
        session_service: Session service for conversation memory.
        user_id: Unique identifier for the user.
        session_id: Unique identifier for this conversation session.
        query: The user's health query.

    Returns:
        The agent's response as a string.
    """
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import Content, Part
    from src.tools.security import SecurityLayer

    # Apply security layer before sending to agent
    security = SecurityLayer()
    security_result = security.process_input(query)

    # Handle blocked content
    if security_result["blocked"]:
        return f"⚠️ {security_result['block_reason']}"

    # Inform user if PII was redacted
    pii_notice = ""
    if security_result["redactions_made"]:
        pii_notice = f"\n\n*Note: For your privacy, some personal information was redacted from your message: {', '.join(security_result['redactions_made'])}*"

    # Create the user message
    user_message = Content(
        role="user",
        parts=[Part(text=security_result["safe_text"])],
    )

    # Run the agent and collect the response
    final_response = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text

    # Apply output security layer
    security_filtered_response = security.process_output(final_response)

    return security_filtered_response + pii_notice


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface (Agent Skill: interactive chat)
# ─────────────────────────────────────────────────────────────────────────────

def print_banner():
    """Prints the MediGuide AI welcome banner."""
    print("\n" + "="*65)
    print("  🏥  MediGuide AI — Multi-Agent Healthcare Assistant")
    print("  Powered by Google ADK + Gemini 2.0 Flash")
    print("  Kaggle AI Agents Capstone Project")
    print("="*65)
    print("\n📋 What I can help with:")
    print("  • Symptom assessment and triage guidance")
    print("  • Medical condition and medication information")
    print("  • Medication reminder scheduling")
    print("  • Doctor appointment preparation")
    print("  • Preventive health screening guidance")
    print("  • Drug interaction checking")
    print("\n⚠️  IMPORTANT DISCLAIMER")
    print("  MediGuide AI provides EDUCATIONAL information only.")
    print("  It is NOT a substitute for professional medical advice.")
    print("  Always consult a qualified healthcare professional.")
    print("\nType 'help' for commands | 'quit' to exit")
    print("-"*65 + "\n")


async def interactive_chat():
    """Runs the interactive CLI chat interface."""
    print_banner()

    runner, session_service = setup_adk()

    # Generate session IDs
    user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create session
    await session_service.create_session(
        app_name="mediguide_ai",
        user_id=user_id,
        session_id=session_id,
    )

    print(f"🔐 Session started: {session_id}")
    print("💬 How can I help you with your health today?\n")

    conversation_count = 0

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye! Stay healthy!")
            break

        if not user_input:
            continue

        # Handle special commands
        if user_input.lower() in ["quit", "exit", "q", "bye"]:
            print("\n👋 Goodbye! Take care of your health!")
            break

        if user_input.lower() == "help":
            print("\n📚 Available Commands:")
            print("  'symptoms [list]'  — Triage your symptoms")
            print("  'info [condition]' — Learn about a condition")
            print("  'meds [drug name]' — Get medication information")
            print("  'check [drug1, drug2]' — Check drug interactions")
            print("  'schedule'         — View your health schedule")
            print("  'history'          — Show conversation summary")
            print("  'quit'             — Exit the application\n")
            continue

        if user_input.lower() == "history":
            print(f"\n📊 Session Summary:")
            print(f"  Session ID: {session_id}")
            print(f"  Queries answered: {conversation_count}")
            print(f"  Session started: {session_id.split('_')[1]}\n")
            continue

        # Process through the agent
        print("\n🤔 MediGuide AI is thinking...\n")
        conversation_count += 1

        try:
            response = await run_agent_query(
                runner, session_service, user_id, session_id, user_input
            )
            print(f"MediGuide AI:\n{response}\n")
            print("-" * 50 + "\n")
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            print("Please try again or rephrase your question.\n")


async def single_query_mode(query: str):
    """Runs a single query and outputs the result (useful for scripting)."""
    runner, session_service = setup_adk()

    user_id = "cli_user"
    session_id = f"single_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    await session_service.create_session(
        app_name="mediguide_ai",
        user_id=user_id,
        session_id=session_id,
    )

    print(f"Query: {query}\n")
    print("Response:")
    print("-" * 50)

    response = await run_agent_query(runner, session_service, user_id, session_id, query)
    print(response)


# ─────────────────────────────────────────────────────────────────────────────
# Argument Parser & Main
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MediGuide AI — Multi-Agent Healthcare Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:     python src/main.py
  Single query:         python src/main.py --query "I have a headache and fever for 2 days"
  Start MCP server:     python mcp_server/server.py
  With Docker:          docker-compose up
        """,
    )

    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Run a single query and exit (non-interactive mode)",
    )

    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demonstration with sample queries",
    )

    return parser.parse_args()


async def run_demo():
    """Runs a demonstration with pre-set sample queries."""
    demo_queries = [
        "I've had a headache and fever for 2 days. What should I do?",
        "Can you tell me about type 2 diabetes?",
        "I take metformin and ibuprofen — are there any interactions?",
        "Can you set a reminder for my blood pressure medication twice daily?",
        "What specialist should I see for heart palpitations?",
    ]

    runner, session_service = setup_adk()
    user_id = "demo_user"
    session_id = "demo_session_001"

    await session_service.create_session(
        app_name="mediguide_ai",
        user_id=user_id,
        session_id=session_id,
    )

    print_banner()
    print("🎬 DEMO MODE — Running sample queries\n")

    for i, query in enumerate(demo_queries, 1):
        print(f"[Demo {i}/{len(demo_queries)}]")
        print(f"User: {query}\n")

        response = await run_agent_query(
            runner, session_service, user_id, session_id, query
        )
        print(f"MediGuide AI:\n{response}\n")
        print("=" * 65 + "\n")
        await asyncio.sleep(1)  # Pause between queries for readability


def main():
    """Main entry point."""
    validate_environment()
    args = parse_args()

    if args.demo:
        asyncio.run(run_demo())
    elif args.query:
        asyncio.run(single_query_mode(args.query))
    else:
        asyncio.run(interactive_chat())


if __name__ == "__main__":
    main()
