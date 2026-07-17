"""
MediGuide AI — Standalone Lab Report Analyzer Skill
====================================================
CLI skill for analyzing blood test results directly from the command line.
Accepts typed lab values or JSON input and outputs a comprehensive
color-coded clinical analysis report.

CLI Usage:
  # Analyze comma-separated test:value pairs
  python skills/lab_report_analyzer.py --values "HbA1c:8.2,creatinine:1.9,hemoglobin:10.1,TSH:0.1"

  # Include patient context
  python skills/lab_report_analyzer.py --values "HbA1c:8.2,WBC:14.5,platelets:85" --age 65 --gender female

  # JSON input
  python skills/lab_report_analyzer.py --json '{"HbA1c": 8.2, "creatinine": 1.9}'

  # Also check food-drug interactions
  python skills/lab_report_analyzer.py --values "HbA1c:8.2" --medications "metformin,warfarin" --foods "grapefruit,alcohol"

  # Generate daily medication schedule
  python skills/lab_report_analyzer.py --schedule "metformin:500mg:twice daily,atorvastatin:20mg:once daily,lisinopril:10mg:once daily"
"""

import argparse
import json
import sys
import os

# Fix Windows cmd.exe Unicode encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.lab_tools import analyze_lab_report, format_lab_report_display
from src.tools.food_drug_tools import (
    check_food_drug_interactions,
    generate_medication_schedule,
    format_food_drug_display,
    format_schedule_display,
)


def parse_values_string(values_str: str) -> dict:
    """Parses 'HbA1c:8.2,creatinine:1.9' into {'HbA1c': 8.2, 'creatinine': 1.9}."""
    result = {}
    for pair in values_str.split(","):
        pair = pair.strip()
        if ":" in pair:
            parts = pair.split(":", 1)
            test_name = parts[0].strip()
            try:
                value = float(parts[1].strip())
                result[test_name] = value
            except ValueError:
                print(f"  Warning: Could not parse value for '{test_name}' — skipping.")
    return result


def parse_schedule_string(schedule_str: str) -> list:
    """Parses 'metformin:500mg:twice daily,aspirin:75mg:once daily' into list of dicts."""
    medications = []
    for entry in schedule_str.split(","):
        parts = entry.strip().split(":")
        if len(parts) >= 2:
            medications.append({
                "name": parts[0].strip(),
                "dose": parts[1].strip() if len(parts) > 1 else "",
                "frequency": parts[2].strip() if len(parts) > 2 else "once daily",
            })
    return medications


def print_demo_examples():
    """Prints built-in demo examples to show the system's power without any input."""
    print("\n" + "=" * 70)
    print("  [MediGuide AI] Lab Analyzer — DEMO MODE")
    print("=" * 70)

    # Demo 1: Diabetic patient with kidney stress
    print("\n  DEMO CASE: Diabetic patient with kidney complications\n")
    demo_values = {
        "HbA1c": 8.9,
        "fasting_glucose": 215,
        "creatinine": 2.1,
        "eGFR": 38,
        "hemoglobin": 9.8,
        "WBC": 11.8,
        "total_cholesterol": 248,
        "LDL": 168,
        "triglycerides": 310,
        "TSH": 8.5,
    }
    report = analyze_lab_report(demo_values, age=58, gender="male")
    print(format_lab_report_display(report))

    # Demo 2: Food-drug interactions
    print("\n")
    food_result = check_food_drug_interactions(
        ["warfarin", "simvastatin", "metformin"],
        ["grapefruit", "alcohol", "vitamin_k_foods"]
    )
    print(format_food_drug_display(food_result))

    # Demo 3: Medication schedule
    print("\n")
    meds = [
        {"name": "metformin", "dose": "500mg", "frequency": "twice daily"},
        {"name": "atorvastatin", "dose": "20mg", "frequency": "once daily"},
        {"name": "lisinopril", "dose": "10mg", "frequency": "once daily"},
        {"name": "aspirin", "dose": "75mg", "frequency": "once daily"},
        {"name": "levothyroxine", "dose": "50mcg", "frequency": "once daily"},
    ]
    schedule = generate_medication_schedule(meds)
    print(format_schedule_display(schedule))


def main():
    parser = argparse.ArgumentParser(
        description="MediGuide AI — Intelligent Lab Report Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--values", type=str,
                        help="Comma-separated test:value pairs. E.g.: HbA1c:8.2,creatinine:1.9")
    parser.add_argument("--json", type=str,
                        help='JSON dict of lab values. E.g.: \'{"HbA1c": 8.2, "creatinine": 1.9}\'')
    parser.add_argument("--age", type=int, default=40,
                        help="Patient age (default: 40)")
    parser.add_argument("--gender", type=str, default="unknown",
                        choices=["male", "female", "unknown"],
                        help="Patient gender for gender-adjusted ranges")
    parser.add_argument("--medications", type=str,
                        help="Comma-separated medication list for food-drug check")
    parser.add_argument("--foods", type=str,
                        help="Comma-separated food/substance list for food-drug check")
    parser.add_argument("--schedule", type=str,
                        help="Generate schedule. Format: name:dose:frequency,name:dose:frequency")
    parser.add_argument("--demo", action="store_true",
                        help="Run built-in demo with a sample diabetic patient case")

    args = parser.parse_args()

    # Demo mode
    if args.demo or (not args.values and not args.json and not args.medications and not args.schedule):
        print_demo_examples()
        return

    # Lab analysis
    if args.values or args.json:
        if args.json:
            try:
                lab_values = json.loads(args.json)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON — {e}")
                sys.exit(1)
        else:
            lab_values = parse_values_string(args.values)

        if not lab_values:
            print("Error: No valid lab values could be parsed.")
            sys.exit(1)

        print(f"\nAnalyzing {len(lab_values)} lab test(s)...")
        report = analyze_lab_report(lab_values, age=args.age, gender=args.gender)
        print(format_lab_report_display(report))

    # Food-drug interaction check
    if args.medications:
        drug_list = [d.strip() for d in args.medications.split(",")]
        food_list = [f.strip() for f in args.foods.split(",")] if args.foods else None
        print(f"\nChecking food-drug interactions for {len(drug_list)} medication(s)...")
        result = check_food_drug_interactions(drug_list, food_list)
        print(format_food_drug_display(result))

    # Medication schedule
    if args.schedule:
        medications = parse_schedule_string(args.schedule)
        print(f"\nGenerating daily schedule for {len(medications)} medication(s)...")
        schedule = generate_medication_schedule(medications)
        print(format_schedule_display(schedule))


if __name__ == "__main__":
    main()
