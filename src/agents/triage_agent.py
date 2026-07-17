"""
MediGuide AI - Triage Agent
============================
Specialist sub-agent responsible for analyzing user-reported symptoms,
assessing urgency levels, and providing structured triage guidance.

Triage Levels (inspired by clinical triage systems):
  - LEVEL 1 (RED)    : Life-threatening — immediate emergency care required
  - LEVEL 2 (ORANGE) : Urgent — same-day or next-day medical attention
  - LEVEL 3 (YELLOW) : Semi-urgent — see a doctor within 48-72 hours
  - LEVEL 4 (GREEN)  : Non-urgent — self-care with monitoring
  - LEVEL 5 (BLUE)   : Informational — general wellness query

Design Pattern: This agent is a sub-agent of the OrchestratorAgent.
It is invoked when the user describes symptoms or asks "what do I have?"
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from src.tools.medical_tools import (
    lookup_symptom_patterns,
    get_body_system_info,
    calculate_risk_factors,
    format_triage_response,
)


def analyze_symptoms(
    symptoms: str,
    duration: str = "unknown",
    severity: str = "moderate",
    patient_age: str = "adult",
    existing_conditions: str = "none",
) -> dict:
    """
    Analyzes a list of symptoms and returns structured triage assessment.

    Args:
        symptoms: Comma-separated symptoms (e.g., "fever, headache, fatigue").
        duration: How long symptoms have been present (e.g., "3 days", "1 week").
        severity: Patient's self-reported severity: "mild", "moderate", "severe".
        patient_age: Age group — "child", "adult", "elderly".
        existing_conditions: Known pre-existing medical conditions.

    Returns:
        dict with triage_level, urgency, possible_conditions, red_flags,
        and recommended_action.
    """
    symptom_list = [s.strip().lower() for s in symptoms.split(",")]
    patterns = lookup_symptom_patterns(symptom_list)
    risk = calculate_risk_factors(
        symptom_list, duration, severity, patient_age, existing_conditions
    )

    return format_triage_response(symptom_list, patterns, risk, duration, severity)


def identify_red_flags(symptoms: str) -> dict:
    """
    Scans symptoms for critical "red flag" indicators that warrant immediate emergency care.

    Red flags include: chest pain, stroke symptoms (FAST), anaphylaxis signs,
    meningitis rash, severe respiratory distress, etc.

    Args:
        symptoms: Symptom description from the user.

    Returns:
        dict with has_red_flags (bool), red_flags_found (list), and action_required.
    """
    # Critical emergency symptom keywords
    emergency_patterns = {
        "cardiac": ["chest pain", "chest tightness", "left arm pain", "jaw pain", "heart attack"],
        "stroke": ["face drooping", "arm weakness", "speech difficulty", "sudden headache", "confusion"],
        "respiratory": ["can't breathe", "difficulty breathing", "choking", "turning blue", "cyanosis"],
        "anaphylaxis": ["throat swelling", "allergic reaction", "anaphylaxis", "epipen"],
        "neurological": ["seizure", "loss of consciousness", "unresponsive", "convulsions"],
        "trauma": ["severe bleeding", "head injury", "broken bone", "deep wound"],
        "sepsis": ["high fever", "confusion", "rapid heart rate", "sepsis"],
    }

    symptoms_lower = symptoms.lower()
    found_flags = {}

    for category, keywords in emergency_patterns.items():
        matched = [kw for kw in keywords if kw in symptoms_lower]
        if matched:
            found_flags[category] = matched

    has_red_flags = bool(found_flags)

    return {
        "has_red_flags": has_red_flags,
        "red_flags_found": found_flags,
        "action_required": (
            "CALL EMERGENCY SERVICES IMMEDIATELY" if has_red_flags
            else "No immediate emergency detected — proceed with standard triage"
        ),
        "emergency_numbers": {
            "India": "112 / 108",
            "USA": "911",
            "UK": "999",
            "EU": "112",
        } if has_red_flags else {},
    }


def get_body_system_assessment(body_area: str) -> dict:
    """
    Returns health assessment guidance for a specific body system or area.

    Args:
        body_area: e.g., "respiratory", "cardiovascular", "digestive", "neurological".

    Returns:
        dict with common_conditions, warning_signs, and self_care_options.
    """
    return get_body_system_info(body_area)


# ─────────────────────────────────────────────────────────────────────────────
# Triage Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
triage_agent = LlmAgent(
    name="TriageAgent",
    model="gemini-2.5-flash",

    instruction="""
You are the MediGuide Triage Specialist — an AI agent with deep expertise in clinical symptom assessment.
Your role is to analyze the user's symptoms and provide a structured, safe triage assessment.

## Your Process (always follow this sequence)
1. First, call identify_red_flags() with the user's symptoms
   - If red flags found → immediately alert the user to seek emergency care
   - If no red flags → proceed with full triage
2. Call analyze_symptoms() with all available details (duration, severity, age, conditions)
3. Present a clear, structured triage report
4. Recommend next steps based on triage level

## Triage Output Format
Always structure your response as:
### 🔍 Symptom Assessment
[List symptoms identified]

### 🚦 Triage Level: [LEVEL NAME]
[Urgency and explanation]

### 🩺 Possible Considerations
[General categories of conditions — NEVER diagnose specifically]

### ✅ Recommended Next Steps
[Clear, actionable guidance]

### ⚠️ Medical Disclaimer
[Always include]

## Critical Rules
- NEVER provide a specific diagnosis — only general considerations and patterns
- Always recommend professional medical evaluation
- Be empathetic but clear about urgency
- Ask follow-up questions if symptoms are vague or insufficient
""",

    tools=[
        FunctionTool(func=analyze_symptoms),
        FunctionTool(func=identify_red_flags),
        FunctionTool(func=get_body_system_assessment),
    ],
)
