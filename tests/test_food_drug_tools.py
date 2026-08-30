"""Unit tests for food-drug interaction engine and medication scheduler."""
import pytest
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.tools.food_drug_tools import (
    check_food_drug_interactions,
    create_medication_schedule,
    format_food_drug_display,
    format_schedule_display
)

def test_check_food_drug_grapefruit_warfarin():
    res = check_food_drug_interactions(["warfarin", "simvastatin"], ["grapefruit"])
    assert res["total_interactions"] >= 2
    assert any("grapefruit" in w["food_substance"].lower() for w in res["high_warnings"] + res["critical_warnings"])

def test_check_food_drug_alcohol_metformin():
    res = check_food_drug_interactions(["metformin"], ["alcohol"])
    assert res["total_interactions"] >= 1

def test_create_medication_schedule():
    meds = [
        {"name": "levothyroxine", "dose": "50mcg", "frequency": "once daily"},
        {"name": "metformin", "dose": "500mg", "frequency": "twice daily"},
        {"name": "atorvastatin", "dose": "20mg", "frequency": "once daily"}
    ]
    schedule = create_medication_schedule(meds)
    assert schedule["total_medications"] == 3
    assert len(schedule["daily_schedule"]) >= 2
    # Levothyroxine should be early morning (06:30), Atorvastatin at night (22:00)
    assert "06:30" in schedule["daily_schedule"]
    assert "22:00" in schedule["daily_schedule"]

def test_format_displays():
    res = check_food_drug_interactions(["warfarin"], ["grapefruit"])
    fmt1 = format_food_drug_display(res)
    assert "MediGuide" in fmt1
    assert "Warfarin" in fmt1

    meds = [{"name": "atorvastatin", "dose": "20mg", "frequency": "night"}]
    sch = create_medication_schedule(meds)
    fmt2 = format_schedule_display(sch)
    assert "Schedule" in fmt2
    assert "Atorvastatin" in fmt2
