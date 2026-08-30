"""Unit tests for medical tools, drug interactions, and health risk scoring."""
import pytest
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.tools.medical_tools import (
    check_drug_interactions,
    get_emergency_contacts,
    get_first_aid_guide,
    compute_health_risk_score
)

def test_check_drug_interactions_duplication():
    # Trimox and Amoxicillin are the same generic drug
    result = check_drug_interactions(["trimox", "amoxicillin"])
    assert result["interactions_found"] >= 1
    assert any("DUPLICATION" in str(w).upper() or "AMOXICILLIN" in str(w).upper() for w in result["warnings"])

def test_check_drug_interactions_severe_pair():
    # Warfarin and Aspirin have severe bleeding risk
    result = check_drug_interactions(["warfarin", "aspirin"])
    assert result["interactions_found"] >= 1
    assert any("severe" in str(w["severity"]).lower() or "critical" in str(w["severity"]).lower() or "high" in str(w["severity"]).lower() for w in result["warnings"])

def test_check_drug_interactions_safe():
    result = check_drug_interactions(["paracetamol", "amoxicillin"])
    assert result["interactions_found"] == 0

def test_emergency_contacts():
    contacts = get_emergency_contacts()
    assert len(contacts) > 0
    assert any("112" in str(v) or "911" in str(v) or "108" in str(v) for v in contacts.values())

def test_first_aid_guide_chest_pain():
    guide = get_first_aid_guide("chest pain")
    assert len(guide) > 0
    assert any("rest" in step.lower() or "emergency" in step.lower() or "aspirin" in step.lower() for step in guide)

def test_compute_health_risk_score_high_risk():
    # High risk case
    high_risk = compute_health_risk_score(
        symptoms=["chest pain", "shortness of breath"],
        duration="2 hours",
        severity="severe",
        age=72,
        gender="male",
        existing_conditions="hypertension, diabetes",
        red_flags=["sweating", "radiating to left arm"]
    )
    assert 1 <= high_risk["health_risk_score"] <= 100
    assert high_risk["health_risk_score"] >= 70
    assert high_risk["risk_tier"] in ["CRITICAL", "HIGH"]
    assert "gauge_display" in high_risk

def test_compute_health_risk_score_mild():
    # Mild case
    low_risk = compute_health_risk_score(
        symptoms=["fatigue"],
        duration="1 day",
        severity="mild",
        age=25,
        gender="female",
        existing_conditions="none",
        red_flags=[]
    )
    assert 1 <= low_risk["health_risk_score"] <= 100
    assert low_risk["health_risk_score"] <= 40
    assert low_risk["risk_tier"] in ["LOW", "LOW-MODERATE"]
