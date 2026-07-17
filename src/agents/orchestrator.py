"""
MediGuide AI - Main Orchestrator Agent
======================================
The root coordinator agent that receives user health queries and intelligently
routes them to specialized sub-agents: Triage, Research, and Scheduler.

Architecture:
  User → OrchestratorAgent → [TriageAgent | ResearchAgent | SchedulerAgent]

Key Concepts Demonstrated:
  - Multi-agent system using Google ADK (Agent Development Kit)
  - Agent-to-agent delegation via sub-agents
  - Tool-based reasoning and action taking
  - Security-first design (PII redaction before LLM calls)
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from src.agents.triage_agent import triage_agent
from src.agents.research_agent import research_agent
from src.agents.scheduler_agent import scheduler_agent
from src.agents.vision_agent import vision_agent
from src.tools.security import SecurityLayer
from src.tools.medical_tools import (
    get_emergency_contacts,
    check_drug_interactions,
    get_first_aid_guide,
    validate_health_query,
)


# ─────────────────────────────────────────────
# Security Layer: applied to every user message
# ─────────────────────────────────────────────
security = SecurityLayer()


def route_to_emergency(query: str) -> dict:
    """
    Immediately routes critical/emergency health queries.
    Returns emergency contacts and basic first aid information.

    Args:
        query: The user's emergency health query.

    Returns:
        dict with emergency_contacts and first_aid_steps.
    """
    contacts = get_emergency_contacts()
    first_aid = get_first_aid_guide(query)
    return {
        "status": "EMERGENCY",
        "message": "⚠️ This appears to be an emergency. Please call emergency services immediately.",
        "emergency_contacts": contacts,
        "immediate_steps": first_aid,
        "disclaimer": (
            "MediGuide AI is NOT a substitute for professional medical advice. "
            "In any emergency, always call your local emergency number (e.g., 911, 112, 108)."
        ),
    }


def validate_input(user_input: str) -> dict:
    """
    Validates and sanitizes user health queries before processing.
    Checks for: harmful content, off-topic requests, and query clarity.

    Args:
        user_input: Raw text from the user.

    Returns:
        dict with is_valid, sanitized_input, and reason if invalid.
    """
    return validate_health_query(user_input)


def check_medications(drug_list: str) -> dict:
    """
    Checks for potential drug-drug interactions using the medical knowledge base.

    Args:
        drug_list: Comma-separated list of medication names (e.g., "aspirin, warfarin").

    Returns:
        dict with interaction_warnings and severity levels.
    """
    drugs = [d.strip() for d in drug_list.split(",")]
    return check_drug_interactions(drugs)


# ─────────────────────────────────────────────────────────────────────────────
# Root Orchestrator Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="MediGuideOrchestrator",
    model="gemini-2.0-flash",

    # System instructions define the agent's personality, scope, and routing logic
    instruction="""
You are MediGuide AI — a compassionate, knowledgeable, and safety-first healthcare navigation assistant.
Your mission is to help users understand their health concerns, find reliable medical information,
and organize their healthcare journey — all while being clear that you are an AI assistant, NOT a doctor.

## Your Capabilities
1. **Symptom Triage** → delegate to TriageAgent for symptom analysis and urgency assessment
2. **Medical Research** → delegate to ResearchAgent for condition info, treatments, medications
3. **Health Scheduling** → delegate to SchedulerAgent for reminders, appointments, follow-ups
4. **Visual Triage & OCR** → delegate to VisionAgent for prescription scanning, rash photos, pill identification
5. **Emergency Routing** → use route_to_emergency() for any life-threatening situations
6. **Drug Interactions** → use check_medications() for medication safety checks
7. **Input Validation** → always validate_input() before processing sensitive queries

## Routing Rules
- If user describes chest pain, difficulty breathing, stroke symptoms, severe bleeding → IMMEDIATELY call route_to_emergency()
- If user provides an image or requests OCR of a prescription, skin condition analysis, or pill bottle → delegate to VisionAgent
- If user asks about symptoms, what condition they might have (text-only) → delegate to TriageAgent
- If user wants to know about a disease, treatment options, medications (text-only) → delegate to ResearchAgent
- If user wants to schedule appointments, set medication reminders (text-only) → delegate to SchedulerAgent
- If user asks about medication combinations → use check_medications()
- ALWAYS validate_input() first for any health query

## Safety Guardrails
- Never diagnose. Always recommend consulting a qualified healthcare professional.
- Always include a medical disclaimer in health-related responses.
- Never store or repeat Personally Identifiable Information (PII) unnecessarily.
- If unsure about routing, ask the user a clarifying question.

## Communication Style
- Be warm, empathetic, and clear
- Use plain language — avoid medical jargon unless explaining a term
- Structure responses with clear sections
- Always end health responses with the disclaimer
""",

    # Sub-agents this orchestrator can delegate to
    sub_agents=[
        triage_agent,
        research_agent,
        scheduler_agent,
        vision_agent,
    ],

    # Direct tools available to the orchestrator
    tools=[
        FunctionTool(func=route_to_emergency),
        FunctionTool(func=validate_input),
        FunctionTool(func=check_medications),
    ],
)
