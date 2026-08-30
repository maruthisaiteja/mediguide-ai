"""Unit tests for the OrchestratorAgent tools and routing logic."""
import pytest
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.agents.orchestrator import (
    route_to_emergency,
    validate_input,
    check_medications,
    calculate_risk_score,
    check_food_interactions,
    create_medication_schedule,
    root_agent
)

def test_route_to_emergency_chest_pain():
    res = route_to_emergency("I have sudden severe chest pain and arm numbness")
    assert res["status"] == "EMERGENCY"
    assert "emergency_contacts" in res
    assert "immediate_steps" in res

def test_validate_input_valid():
    res = validate_input("What causes migraine and how to prevent it?")
    assert res["is_valid"] is True

def test_check_medications_duplication():
    res = check_medications("trimox, amoxicillin")
    assert res["interactions_found"] >= 1
    assert any("DUPLICATION" in str(w).upper() or "AMOXICILLIN" in str(w).upper() for w in res["warnings"])

def test_calculate_risk_score():
    res = calculate_risk_score(
        symptoms_csv="chest pain, shortness of breath",
        duration="2 hours",
        severity="severe",
        age=68,
        gender="male",
        existing_conditions="diabetes, hypertension"
    )
    assert 1 <= res["health_risk_score"] <= 100
    assert res["risk_tier"] in ["CRITICAL", "HIGH"]

def test_check_food_interactions():
    res = check_food_interactions("simvastatin, warfarin", "grapefruit, alcohol")
    assert res["total_interactions"] >= 2

def test_create_medication_schedule():
    csv_str = "levothyroxine:50mcg:once daily,metformin:500mg:twice daily,atorvastatin:20mg:once daily"
    res = create_medication_schedule(csv_str)
    assert res["total_medications"] == 3
    assert "daily_schedule" in res

def test_root_agent_structure():
    assert root_agent.name == "MediGuideOrchestrator"
    assert len(root_agent.sub_agents) == 5
    assert len(root_agent.tools) >= 5
