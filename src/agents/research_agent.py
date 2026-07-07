"""
MediGuide AI - Research Agent
==============================
Specialist sub-agent that retrieves and synthesizes evidence-based medical
information from the MCP (Model Context Protocol) medical knowledge server.

Capabilities:
  - Disease/condition explanations in plain language
  - Treatment overview and options
  - Medication information (uses, side effects, precautions)
  - Preventive health guidance
  - Clinical study summaries

Integration:
  - Connects to the custom MCP Medical Knowledge Server (mcp_server/server.py)
  - Uses real-time tool calls to fetch structured medical data
  - Synthesizes information into user-friendly responses

Design Pattern: Sub-agent of OrchestratorAgent, invoked for information queries.
"""

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

from src.tools.medical_tools import (
    search_medical_database,
    get_condition_overview,
    get_medication_info,
    get_treatment_options,
    get_preventive_guidelines,
    get_specialist_recommendation,
)


def research_condition(condition_name: str, detail_level: str = "standard") -> dict:
    """
    Retrieves comprehensive information about a medical condition.

    Args:
        condition_name: Name of the condition (e.g., "type 2 diabetes", "hypertension").
        detail_level: "brief" | "standard" | "detailed" — controls response depth.

    Returns:
        dict with overview, causes, symptoms, diagnosis_methods, treatments,
        complications, prognosis, and prevention.
    """
    return get_condition_overview(condition_name, detail_level)


def research_medication(medication_name: str) -> dict:
    """
    Retrieves medication information including uses, dosing, side effects, and contraindications.

    Args:
        medication_name: Generic or brand name of the medication.

    Returns:
        dict with drug_class, uses, common_side_effects, serious_warnings,
        contraindications, and interactions_to_watch.

    Security Note: This function does NOT provide specific dosing advice.
    Always direct users to pharmacist/physician for actual dosing.
    """
    return get_medication_info(medication_name)


def find_treatment_options(condition: str, patient_context: str = "") -> dict:
    """
    Retrieves an overview of treatment approaches for a given condition.

    Args:
        condition: The medical condition to research treatments for.
        patient_context: Optional context like "elderly patient" or "pregnant" for filtering.

    Returns:
        dict with first_line_treatments, lifestyle_modifications, alternative_therapies,
        and clinical_considerations.
    """
    return get_treatment_options(condition, patient_context)


def get_prevention_tips(health_topic: str) -> dict:
    """
    Retrieves evidence-based preventive health guidelines for a topic.

    Args:
        health_topic: e.g., "heart disease prevention", "diabetes prevention",
                      "cancer screening", "vaccination schedule".

    Returns:
        dict with screening_recommendations, lifestyle_factors, risk_reduction_strategies.
    """
    return get_preventive_guidelines(health_topic)


def recommend_specialist(condition_or_symptoms: str) -> dict:
    """
    Recommends the appropriate type of medical specialist for a condition or symptom set.

    Args:
        condition_or_symptoms: The health concern to find a specialist for.

    Returns:
        dict with recommended_specialist_type, what_they_treat, and
        questions_to_ask_doctor.
    """
    return get_specialist_recommendation(condition_or_symptoms)


def search_health_info(query: str, source_preference: str = "peer_reviewed") -> dict:
    """
    Searches the medical knowledge base with a free-text query.
    Prioritizes peer-reviewed and evidence-based sources.

    Args:
        query: Natural language medical question or topic.
        source_preference: "peer_reviewed" | "clinical_guidelines" | "patient_education".

    Returns:
        dict with results, source_quality_rating, and confidence_score.
    """
    return search_medical_database(query, source_preference)


# ─────────────────────────────────────────────────────────────────────────────
# Research Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
research_agent = Agent(
    name="ResearchAgent",
    model="gemini-2.0-flash",

    instruction="""
You are the MediGuide Medical Research Specialist — an AI agent that synthesizes reliable,
evidence-based medical information into clear, accessible explanations for patients and caregivers.

## Your Research Process
1. Identify the specific topic: condition, medication, treatment, or prevention
2. Choose the most appropriate research tool:
   - research_condition() → for disease/condition information
   - research_medication() → for drug information
   - find_treatment_options() → for treatment overviews
   - get_prevention_tips() → for preventive health
   - recommend_specialist() → when user needs specialist guidance
   - search_health_info() → for general medical queries
3. Synthesize results into a clear, structured response
4. Always cite that information comes from medical knowledge bases
5. Recommend professional consultation for personalized advice

## Response Structure
### 📚 Medical Information: [Topic]
**Source Quality:** [evidence level]

[Main content in plain language]

### 🔬 Key Facts
[Bullet points of most important information]

### 💊 Important Warnings / Precautions
[Any safety-critical information]

### 👨‍⚕️ Next Steps
[When to see a doctor, what to ask, etc.]

### ⚠️ Medical Disclaimer
[Always include — this is educational only, not personalized medical advice]

## Accuracy Guidelines
- Only present information supported by medical consensus
- Clearly indicate when evidence is limited or evolving
- Distinguish between proven treatments and emerging research
- Never overpromise on treatment effectiveness
- For medications: NEVER recommend specific doses — that requires a doctor/pharmacist
""",

    tools=[
        FunctionTool(func=research_condition),
        FunctionTool(func=research_medication),
        FunctionTool(func=find_treatment_options),
        FunctionTool(func=get_prevention_tips),
        FunctionTool(func=recommend_specialist),
        FunctionTool(func=search_health_info),
    ],
)
