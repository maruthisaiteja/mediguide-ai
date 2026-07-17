"""
MediGuide AI - Main Orchestrator Agent
======================================
The root coordinator agent that receives user health queries and intelligently
routes them to specialized sub-agents: Triage, Research, Scheduler, Vision, Lab.

Architecture:
  User → OrchestratorAgent → [TriageAgent | ResearchAgent | SchedulerAgent | VisionAgent | LabAgent]

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
from src.agents.lab_agent import lab_agent
from src.tools.security import SecurityLayer
from src.tools.medical_tools import (
    get_emergency_contacts,
    check_drug_interactions,
    get_first_aid_guide,
    validate_health_query,
    compute_health_risk_score,
)
from src.tools.food_drug_tools import (
    check_food_drug_interactions,
    generate_medication_schedule,
)


# ─────────────────────────────────────────────────────────────────────────────
# Security Layer: applied to every user message
# ─────────────────────────────────────────────────────────────────────────────
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
        "message": "This appears to be an emergency. Please call emergency services immediately.",
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

    Args:
        user_input: Raw text from the user.

    Returns:
        dict with is_valid, sanitized_input, and reason if invalid.
    """
    return validate_health_query(user_input)


def check_medications(drug_list: str) -> dict:
    """
    Checks for potential drug-drug interactions and therapeutic duplications.

    Args:
        drug_list: Comma-separated list of medication names (e.g., "aspirin, warfarin, trimox").

    Returns:
        dict with interaction_warnings, duplication alerts, and severity levels.
    """
    drugs = [d.strip() for d in drug_list.split(",")]
    return check_drug_interactions(drugs)


def calculate_risk_score(
    symptoms_csv: str,
    duration: str,
    severity: str,
    age: int,
    gender: str,
    existing_conditions: str,
) -> dict:
    """
    Computes a quantified Health Risk Score (1-100) from patient symptoms and context.
    Use this to give patients a concrete, measurable risk assessment.

    Args:
        symptoms_csv: Comma-separated symptom list (e.g., "chest pain, shortness of breath").
        duration: How long symptoms have been present (e.g., "2 days", "3 weeks").
        severity: Patient's reported severity: "mild", "moderate", or "severe".
        age: Patient's age in years.
        gender: "male", "female", or "unknown".
        existing_conditions: Pre-existing medical conditions (e.g., "diabetes, hypertension").

    Returns:
        dict with score (1-100), risk_tier, ASCII gauge display, and contributing factors.
    """
    symptoms = [s.strip() for s in symptoms_csv.split(",") if s.strip()]
    return compute_health_risk_score(
        symptoms=symptoms,
        duration=duration,
        severity=severity,
        age=age,
        gender=gender,
        existing_conditions=existing_conditions,
    )


def check_food_interactions(medications_csv: str, foods_csv: str = "") -> dict:
    """
    Checks for dangerous food-drug and lifestyle interactions.
    Flags grapefruit, alcohol, dairy, high-potassium foods, vitamin K foods, caffeine, etc.

    Args:
        medications_csv: Comma-separated list of patient's medications.
        foods_csv: Comma-separated foods/substances consumed (or empty for full check).

    Returns:
        dict with CRITICAL, HIGH, and MODERATE food-drug interaction warnings.
    """
    drug_list = [d.strip() for d in medications_csv.split(",") if d.strip()]
    food_list = [f.strip() for f in foods_csv.split(",") if f.strip()] if foods_csv else None
    return check_food_drug_interactions(drug_list, food_list)


def create_medication_schedule(medications_csv: str) -> dict:
    """
    Generates a personalized daily medication schedule with optimal timing.
    Format: "drugname:dose:frequency" pairs, comma-separated.
    Example: "metformin:500mg:twice daily,atorvastatin:20mg:once daily"

    Args:
        medications_csv: Medications in format "name:dose:frequency" joined by commas.

    Returns:
        dict with time-organized daily schedule (morning/afternoon/evening/night) and clinical notes.
    """
    medications = []
    for entry in medications_csv.split(","):
        parts = entry.strip().split(":")
        if len(parts) >= 1:
            medications.append({
                "name": parts[0].strip(),
                "dose": parts[1].strip() if len(parts) > 1 else "",
                "frequency": parts[2].strip() if len(parts) > 2 else "once daily",
            })
    return generate_medication_schedule(medications)


# ─────────────────────────────────────────────────────────────────────────────
# Root Orchestrator Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
root_agent = LlmAgent(
    name="MediGuideOrchestrator",
    model="gemini-2.5-flash",

    # System instructions define the agent's personality, scope, and routing logic
    instruction="""
You are MediGuide AI — an advanced multimodal healthcare navigation assistant powered by
a team of specialized AI agents. Your mission: help patients navigate their health safely,
prevent medication errors, and flag critical findings before they become emergencies.

## Your Specialist Team
1. **TriageAgent** — Symptom analysis, urgency classification
2. **ResearchAgent** — Medical knowledge, condition explanations
3. **SchedulerAgent** — Appointments, medication reminders
4. **VisionAgent** — Prescription OCR, X-ray/ECG/skin image analysis
5. **LabAgent** — Blood test analysis, food-drug interactions, medication schedules

## Your Direct Tools
- `calculate_risk_score()` — Computes 1-100 Health Risk Score from symptoms + context
- `check_medications()` — Drug-drug interaction + therapeutic duplication check
- `check_food_interactions()` — Food-drug interaction safety check (grapefruit, alcohol, etc.)
- `create_medication_schedule()` — Generates personalized daily medication schedule
- `route_to_emergency()` — Emergency routing with contacts + first aid
- `validate_input()` — Input validation and sanitization

## Routing Intelligence

### EMERGENCY (use route_to_emergency() immediately):
- Chest pain, difficulty breathing, stroke symptoms, loss of consciousness
- Severe bleeding, anaphylaxis, suspected overdose, seizures

### IMAGE ANALYSIS (delegate to VisionAgent):
- User provides an image OR mentions: prescription, rash, skin condition, pill bottle, X-ray, ECG, scan

### LAB RESULTS (delegate to LabAgent):
- User pastes blood test values, mentions lab report, asks about test results
- Questions about food-drug interactions or medication timing schedules
- "When should I take my medications?" type questions

### SYMPTOMS ONLY (delegate to TriageAgent):
- Describing symptoms in text without a medical report or image
- "What could be causing my headache?" type questions
- ALWAYS also call calculate_risk_score() for any symptom query to give a Risk Score

### MEDICAL RESEARCH (delegate to ResearchAgent):
- "What is diabetes?", "How does metformin work?", "What are the side effects of..."

### SCHEDULING (delegate to SchedulerAgent):
- "Remind me to take my medicine", "Schedule a doctor appointment"

## Response Enhancement Rules
- For ANY symptom query: compute and display the Health Risk Score gauge
- For ANY medication list: check drug-drug interactions AND food-drug interactions
- For ANY lab values: route to LabAgent for full interpretation
- ALWAYS end with a medical disclaimer

## Communication Style
- Warm, clear, empathetic — never cold or robotic
- Use structured Markdown with clear sections
- Lead with the most urgent findings first
- Plain language — no unexplained jargon
""",

    # Sub-agents this orchestrator can delegate to
    sub_agents=[
        triage_agent,
        research_agent,
        scheduler_agent,
        vision_agent,
        lab_agent,
    ],

    # Direct tools available to the orchestrator
    tools=[
        FunctionTool(func=route_to_emergency),
        FunctionTool(func=validate_input),
        FunctionTool(func=check_medications),
        FunctionTool(func=calculate_risk_score),
        FunctionTool(func=check_food_interactions),
        FunctionTool(func=create_medication_schedule),
    ],
)

