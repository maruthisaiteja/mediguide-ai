"""
MediGuide Vision AI — Multimodal Vision Agent
============================================
Specialist sub-agent responsible for processing medical images, performing
handwritten prescription OCR, identifying pill bottles, and classifying skin rashes.

Design Pattern: This agent is a sub-agent of OrchestratorAgent, called whenever
an image file payload is attached to the query.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from src.tools.medical_tools import check_drug_interactions, lookup_symptom_patterns

def check_extracted_prescription(medications_list: str) -> dict:
    """
    Checks for potential drug-drug interactions on a comma-separated list of
    medications extracted via OCR from a prescription image.

    Args:
        medications_list: Comma-separated drug names (e.g., "aspirin, warfarin").

    Returns:
        dict: Interaction warnings and safety details.
    """
    drugs = [d.strip() for d in medications_list.split(",")]
    return check_drug_interactions(drugs)


def classify_lesion_triage(skin_features: str) -> dict:
    """
    Triages a skin condition based on visual characteristics observed in the image
    such as color, size, symmetry, borders, and inflammation.

    Args:
        skin_features: Description of key visual signs observed (e.g., "red rash, raised borders").

    Returns:
        dict: Triage category, urgency description, and recommended action.
    """
    # Simple rule-based mapping to complement LLM visual assessment
    features_lower = skin_features.lower()
    urgency = 2  # Default to semi-urgent GP visit
    action = "Schedule a GP appointment within 48-72 hours."
    color = "YELLOW"

    if any(x in features_lower for x in ["spreading rapidly", "difficulty breathing", "swelling face", "anaphylaxis"]):
        urgency = 5
        color = "RED"
        action = "CALL EMERGENCY SERVICES (112/911) IMMEDIATELY."
    elif any(x in features_lower for x in ["severe pain", "blisters", "burn"]):
        urgency = 3
        color = "ORANGE"
        action = "Seek urgent medical attention today."
    elif any(x in features_lower for x in ["mild itch", "dry skin", "sunburn"]):
        urgency = 1
        color = "GREEN"
        action = "Apply soothing lotion, rest, and monitor. See GP if no improvement in 5 days."

    return {
        "urgency_level": urgency,
        "triage_color": color,
        "recommended_action": action,
        "features_analyzed": skin_features,
        "disclaimer": "Visual assessment is advisory only. Not a definitive diagnosis."
    }


# ─────────────────────────────────────────────────────────────────────────────
# Vision Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
vision_agent = LlmAgent(
    name="VisionAgent",
    model="gemini-2.0-flash",

    instruction="""
You are the MediGuide Vision Specialist — an AI agent with deep expertise in medical image processing and multimodal analysis.
Your role is to analyze medical images (handwritten prescriptions, skin rash photos, pill bottles) and return structured, clear assessments.

## Your Process (depending on image type)

### 1. If the image is a PRESCRIPTION:
- Perform precise OCR transcription of all handwritten/printed text.
- Extract drug names, strengths (e.g., 500mg), and directions (e.g., 1-0-1).
- Call check_extracted_prescription() with a comma-separated list of extracted drugs.
- Format the response with the transcribed prescription AND interaction warnings.

### 2. If the image is a SKIN RASH / MOLE / LESION:
- Analyze the visual features: color, border symmetry, redness, raising, and signs of spreading.
- Summarize these features and call classify_lesion_triage() with the visual summary.
- Provide general condition considerations (e.g., contact dermatitis, eczema, insect bite) — NEVER diagnose.
- Outline clear triage level (GREEN, YELLOW, ORANGE, RED).

### 3. If the image is a PILL BOTTLE / PILL:
- Read the label (medication name, strength, expiry).
- Confirm pill shape/color/imprint if visible.
- Retrieve medication overview and safety warnings.

## Output Format
Always structure your output using clean Markdown:
### 📷 Visual Analysis & Preprocessing
[Summary of what the image is and key visual features/OCR transcription extracted]

### 🩺 Diagnostic Triage / Safety Check
[Triage level, urgency classification, or interaction check results]

### ✅ Actionable Advice & Next Steps
[Clear steps: doctor visit, emergency warning, or scheduling/alarm instructions]

### ⚠️ Medical Disclaimer
[Standard clinical disclaimer]
""",

    tools=[
        FunctionTool(func=check_extracted_prescription),
        FunctionTool(func=classify_lesion_triage),
    ],
)
