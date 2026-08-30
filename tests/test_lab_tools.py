"""Unit tests for clinical laboratory reference analyzer."""
import pytest
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.tools.lab_tools import analyze_lab_value, analyze_lab_report, format_lab_report_display

def test_analyze_lab_value_normal_glucose():
    res = analyze_lab_value("glucose", 85.0)
    assert res["severity"] == "OK"
    assert "NORMAL" in res["flag"]

def test_analyze_lab_value_high_hba1c():
    res = analyze_lab_value("hba1c", 8.5)
    assert res["severity"] in ["WARNING", "CRITICAL"]
    assert "Uncontrolled Diabetes" in str(res.get("risk_label", "")) or "HIGH" in res["flag"]

def test_analyze_lab_value_critical_troponin():
    # Troponin > 0.04 indicates potential heart attack
    res = analyze_lab_value("troponin", 0.09)
    assert res["severity"] in ["CRITICAL", "WARNING"]
    assert "Troponin" in res["test"]

def test_analyze_lab_report_panel():
    panel = {
        "HbA1c": 8.2,
        "creatinine": 2.1,
        "hemoglobin": 10.1,
        "TSH": 0.1,
        "troponin": 0.09,
        "potassium": 6.2
    }
    report = analyze_lab_report(panel, age=55, gender="male")
    assert report["total_tests"] == 6
    assert report["overall_risk_tier"] in ["CRITICAL", "HIGH"]
    assert len(report["warning_findings"]) + len(report["critical_findings"]) >= 4

def test_format_lab_report_display():
    panel = {"HbA1c": 8.2, "fasting_glucose": 215.0}
    report = analyze_lab_report(panel)
    formatted = format_lab_report_display(report)
    assert "MediGuide" in formatted
    assert "HbA1c" in formatted
