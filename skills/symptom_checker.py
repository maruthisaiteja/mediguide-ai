"""
MediGuide AI - Symptom Checker Skill
======================================
An Agent Skill (compatible with Agents CLI) that provides a structured
symptom checking workflow as a standalone, reusable skill.

Agent Skills are reusable, composable units of agent behavior that can be:
  - Invoked from the CLI: agents run skill symptom_checker --symptoms "fever,headache"
  - Integrated into the multi-agent system as a sub-capability
  - Shared and published for other agents to use

This skill demonstrates the "Agent Skills / Agents CLI" course concept.

Usage (Agents CLI):
  agents skills run symptom_checker --input '{"symptoms": "fever, headache, fatigue", "duration": "3 days"}'

Usage (Python):
  from skills.symptom_checker import SymptomCheckerSkill
  result = SymptomCheckerSkill().run(symptoms="fever, headache", duration="2 days")
"""

from typing import Optional
import json
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.tools.medical_tools import (
    lookup_symptom_patterns,
    calculate_risk_factors,
    format_triage_response,
)


# ─────────────────────────────────────────────────────────────────────────────
# Skill Metadata (used by Agents CLI for discovery)
# ─────────────────────────────────────────────────────────────────────────────
SKILL_METADATA = {
    "name": "symptom_checker",
    "version": "1.0.0",
    "description": "Structured symptom assessment and triage guidance skill",
    "author": "MediGuide AI Team",
    "category": "healthcare",
    "inputs": {
        "symptoms": {"type": "string", "required": True, "description": "Comma-separated list of symptoms"},
        "duration": {"type": "string", "required": False, "default": "unknown", "description": "How long symptoms have been present"},
        "severity": {"type": "string", "required": False, "default": "moderate", "description": "mild | moderate | severe"},
        "age_group": {"type": "string", "required": False, "default": "adult", "description": "child | adult | elderly"},
        "existing_conditions": {"type": "string", "required": False, "default": "none"},
    },
    "outputs": {
        "triage_level": "integer (1-5)",
        "triage_color": "string (GREEN/YELLOW/ORANGE/RED)",
        "urgency_description": "string",
        "recommended_action": "string",
        "possible_condition_categories": "list",
        "red_flags_to_watch": "list",
        "disclaimer": "string",
    },
    "safety_level": "advisory",
    "disclaimer": "Educational use only. Not a substitute for medical diagnosis.",
}


class SymptomCheckerSkill:
    """
    Symptom Checker Skill — a reusable, composable agent skill.

    This class wraps the symptom assessment logic into a self-contained
    skill that can be invoked by the Agents CLI, integrated into multi-agent
    systems, or used directly in Python code.
    """

    def __init__(self):
        self.name = SKILL_METADATA["name"]
        self.version = SKILL_METADATA["version"]

    def run(
        self,
        symptoms: str,
        duration: str = "unknown",
        severity: str = "moderate",
        age_group: str = "adult",
        existing_conditions: str = "none",
    ) -> dict:
        """
        Runs the symptom checker skill and returns a triage assessment.

        Args:
            symptoms: Comma-separated symptoms (e.g., "fever, headache, fatigue").
            duration: How long symptoms have persisted.
            severity: Patient-reported severity level.
            age_group: Patient age group for risk adjustment.
            existing_conditions: Known pre-existing conditions.

        Returns:
            dict: Complete triage assessment with urgency level and recommendations.
        """
        # Parse and normalize symptoms
        symptom_list = [s.strip().lower() for s in symptoms.split(",") if s.strip()]

        if not symptom_list:
            return {
                "error": "No symptoms provided",
                "usage": "Provide at least one symptom: e.g., 'fever, headache'",
            }

        # Run triage assessment
        patterns = lookup_symptom_patterns(symptom_list)
        risk = calculate_risk_factors(
            symptom_list, duration, severity, age_group, existing_conditions
        )
        assessment = format_triage_response(symptom_list, patterns, risk, duration, severity)

        # Add skill metadata to response
        assessment["skill_info"] = {
            "skill_name": self.name,
            "skill_version": self.version,
            "input_received": {
                "symptoms": symptoms,
                "duration": duration,
                "severity": severity,
                "age_group": age_group,
                "existing_conditions": existing_conditions,
            },
        }

        return assessment

    def format_for_display(self, assessment: dict) -> str:
        """
        Formats the triage assessment for human-readable display.

        Args:
            assessment: Result from the run() method.

        Returns:
            Formatted string ready for display.
        """
        if "error" in assessment:
            return f"❌ Error: {assessment['error']}"

        lines = [
            "\n" + "="*55,
            "  🏥 MediGuide Symptom Assessment",
            "="*55,
            f"\n📋 Symptoms: {', '.join(assessment.get('symptoms_assessed', []))}",
            f"⏱️  Duration: {assessment.get('duration', 'unknown')}",
            f"📊 Severity: {assessment.get('severity', 'unknown')}",
            "",
            f"🚦 TRIAGE LEVEL {assessment.get('triage_level', '?')}: "
            f"{assessment.get('triage_color', '')} — {assessment.get('urgency_description', '')}",
            "",
            "✅ RECOMMENDED ACTION:",
            f"   {assessment.get('recommended_action', '')}",
        ]

        if assessment.get("possible_condition_categories"):
            lines.append("\n🩺 Possible Condition Categories:")
            for condition in assessment["possible_condition_categories"][:3]:
                lines.append(f"   • {condition}")

        if assessment.get("red_flags_to_watch"):
            lines.append("\n⚠️  Red Flags to Watch For:")
            for flag in assessment["red_flags_to_watch"][:3]:
                lines.append(f"   🔴 {flag}")

        if assessment.get("risk_modifiers"):
            lines.append("\n📌 Risk Factors Considered:")
            for factor in assessment["risk_modifiers"]:
                lines.append(f"   • {factor}")

        lines.extend([
            "",
            "─" * 55,
            f"⚠️  {assessment.get('disclaimer', '')}",
            "="*55 + "\n",
        ])

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point (for Agents CLI invocation)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    CLI entry point for the symptom checker skill.
    Reads JSON input from stdin or command-line arguments.

    Usage:
      echo '{"symptoms": "fever, headache"}' | python skills/symptom_checker.py
      python skills/symptom_checker.py --symptoms "fever, headache" --duration "2 days"
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="MediGuide Symptom Checker Skill")
    parser.add_argument("--symptoms", "-s", type=str, help="Comma-separated symptoms")
    parser.add_argument("--duration", "-d", type=str, default="unknown")
    parser.add_argument("--severity", type=str, default="moderate", choices=["mild", "moderate", "severe"])
    parser.add_argument("--age-group", type=str, default="adult")
    parser.add_argument("--conditions", type=str, default="none")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of formatted text")
    parser.add_argument("--metadata", action="store_true", help="Show skill metadata")

    args = parser.parse_args()

    if args.metadata:
        print(json.dumps(SKILL_METADATA, indent=2))
        return

    # Accept JSON from stdin (Agents CLI mode)
    if not args.symptoms and not sys.stdin.isatty():
        try:
            input_data = json.load(sys.stdin)
            args.symptoms = input_data.get("symptoms", "")
            args.duration = input_data.get("duration", "unknown")
            args.severity = input_data.get("severity", "moderate")
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
            sys.exit(1)

    if not args.symptoms:
        print("Error: --symptoms is required")
        parser.print_help()
        sys.exit(1)

    skill = SymptomCheckerSkill()
    result = skill.run(
        symptoms=args.symptoms,
        duration=args.duration,
        severity=args.severity,
        age_group=args.age_group,
        existing_conditions=args.conditions,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(skill.format_for_display(result))


if __name__ == "__main__":
    main()
