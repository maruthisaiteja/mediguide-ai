"""
MediGuide AI — Lab Analysis Sub-Agent
======================================
Specialist ADK sub-agent that intelligently analyzes laboratory blood test
reports, flags critical values, and generates patient-friendly explanations.

Handles both:
  - Typed lab values: {"HbA1c": 8.2, "creatinine": 1.9}
  - Extracted OCR values from uploaded lab report images
"""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from src.tools.lab_tools import analyze_lab_report, analyze_lab_value
from src.tools.food_drug_tools import check_food_drug_interactions, generate_medication_schedule


def analyze_blood_tests(lab_values_json: str, age: int = 40, gender: str = "unknown") -> dict:
    """
    Analyzes a set of blood test results against clinical reference ranges.
    Flags CRITICAL, HIGH, and BORDERLINE values with plain-English explanations.

    Args:
        lab_values_json: JSON string mapping test names to values.
                         E.g.: '{"HbA1c": 8.2, "creatinine": 1.9, "hemoglobin": 10.1}'
        age: Patient age for contextual risk adjustment.
        gender: 'male', 'female', or 'unknown'.

    Returns:
        Full lab analysis report with risk tier, flagged values, and actions.
    """
    import json
    try:
        if isinstance(lab_values_json, dict):
            lab_values = lab_values_json
        else:
            lab_values = json.loads(lab_values_json)
    except Exception as e:
        return {"error": f"Invalid lab values format. Use JSON: {{\"HbA1c\": 8.2, \"creatinine\": 1.9}}. Error: {str(e)}"}

    return analyze_lab_report(lab_values, age=age, gender=gender)


def check_single_lab_value(test_name: str, value: float, gender: str = "unknown") -> dict:
    """
    Checks a single lab test result against clinical reference ranges.

    Args:
        test_name: Name of the lab test (e.g., 'HbA1c', 'hemoglobin', 'TSH').
        value: The measured numeric value.
        gender: 'male', 'female', or 'unknown'.

    Returns:
        Analysis with flag status, clinical explanation, and recommended action.
    """
    return analyze_lab_value(test_name, value, gender)


def check_medication_food_safety(medications: str, foods_consumed: str = "") -> dict:
    """
    Checks for dangerous interactions between a patient's medications and foods/substances.

    Args:
        medications: Comma-separated list of medications.
        foods_consumed: Comma-separated list of foods/substances consumed (or empty for full check).

    Returns:
        dict with critical, high, and moderate food-drug interaction warnings.
    """
    drug_list = [d.strip() for d in medications.split(",") if d.strip()]
    food_list = [f.strip() for f in foods_consumed.split(",") if f.strip()] if foods_consumed else None
    return check_food_drug_interactions(drug_list, food_list)


def create_daily_med_schedule(medications_json: str) -> dict:
    """
    Generates a personalized daily medication schedule with optimal timing.

    Args:
        medications_json: JSON string list of medication dicts.
                          E.g.: '[{"name": "metformin", "dose": "500mg", "frequency": "twice daily"}]'

    Returns:
        dict with time-slot organized schedule and clinical notes per medication.
    """
    import json
    try:
        if isinstance(medications_json, list):
            medications = medications_json
        else:
            medications = json.loads(medications_json)
    except Exception as e:
        return {"error": f"Invalid medications format. Error: {str(e)}"}

    return generate_medication_schedule(medications)


# ─────────────────────────────────────────────────────────────────────────────
# Lab Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
lab_agent = LlmAgent(
    name="LabAgent",
    model="gemini-2.5-flash",

    instruction="""
You are the MediGuide Lab Intelligence Specialist — an AI agent with clinical expertise
in laboratory medicine, pharmacology, and preventive diagnostics.

Your role is to analyze laboratory test results, flag abnormal values, and generate
actionable, patient-friendly health reports.

## Your Capabilities

### 1. Full Blood Panel Analysis
When given lab values, call analyze_blood_tests() with a JSON dict of test:value pairs.
Example: {"HbA1c": 8.2, "creatinine": 1.9, "hemoglobin": 10.1, "TSH": 0.1}
Then interpret the results in plain English, prioritizing CRITICAL findings first.

### 2. Single Value Check
For a single test value question, call check_single_lab_value(test_name, value).

### 3. Food-Drug Safety
When patient mentions what they eat alongside their medications, call check_medication_food_safety().
Example: Patient drinks grapefruit juice while on warfarin = DANGEROUS.

### 4. Daily Medication Schedule
When patient wants to know when to take their medications, call create_daily_med_schedule()
with their full medication list. Generate a structured morning/afternoon/evening/night schedule.

## Output Structure (ALWAYS use this format)

### 🔬 Lab Report Analysis
[Overall risk tier — CRITICAL / HIGH / MODERATE / LOW]
[Risk summary sentence]

### 🚨 Critical Findings (if any)
[List each critical value with explanation and immediate action]

### ⚠️ Abnormal Findings
[List each high/low value with plain-English explanation and recommended next step]

### ✅ Normal Findings
[Brief table of normal values]

### 📋 Clinical Summary & Next Steps
[Overall interpretation: what do these results collectively suggest?]
[Priority actions: what should the patient do first?]

### ⚠️ Medical Disclaimer
[Standard disclaimer]

## Critical Rules
- NEVER make a definitive diagnosis.
- Always flag CRITICAL values FIRST and emphasize emergency action.
- Use plain language — patients reading this are NOT doctors.
- Always recommend professional follow-up.
- When HbA1c >8% + creatinine >1.5 are BOTH elevated → highlight the dangerous metformin contraindication.
- When troponin is elevated even slightly → classify as medical emergency immediately.
""",

    tools=[
        FunctionTool(func=analyze_blood_tests),
        FunctionTool(func=check_single_lab_value),
        FunctionTool(func=check_medication_food_safety),
        FunctionTool(func=create_daily_med_schedule),
    ],
)
