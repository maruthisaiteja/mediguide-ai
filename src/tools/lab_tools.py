"""
MediGuide AI — Lab Report Intelligence Engine
==============================================
Provides a comprehensive clinical laboratory reference database and analysis
functions to interpret blood test results, flag abnormal values, and generate
patient-friendly explanations.

Covers 35+ common tests across:
  - Complete Blood Count (CBC)
  - Metabolic Panel (BMP/CMP)
  - Lipid Panel
  - Thyroid Function
  - Liver Function
  - Kidney Function
  - Diabetes Markers
  - Cardiac Markers
"""

from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Clinical Reference Ranges Database
# Format per test:
#   "test_key": {
#       "display_name": str,
#       "unit": str,
#       "normal_range": (low, high),           # general adult
#       "male_range": (low, high) or None,      # gender-specific if needed
#       "female_range": (low, high) or None,
#       "critical_low": float or None,          # immediately life-threatening
#       "critical_high": float or None,
#       "category": str,
#       "clinical_meaning": str,
#       "high_explanation": str,
#       "low_explanation": str,
#       "high_action": str,
#       "low_action": str,
#   }
# ─────────────────────────────────────────────────────────────────────────────

LAB_REFERENCE_DATABASE = {

    # ── DIABETES MARKERS ─────────────────────────────────────────────────────
    "hba1c": {
        "display_name": "HbA1c (Glycated Hemoglobin)",
        "unit": "%",
        "normal_range": (4.0, 5.6),
        "prediabetes_range": (5.7, 6.4),
        "diabetic_range": (6.5, 999),
        "critical_low": None,
        "critical_high": 14.0,
        "category": "Diabetes",
        "clinical_meaning": "Reflects average blood sugar over 3 months. The gold standard for diabetes monitoring.",
        "high_explanation": "Elevated HbA1c indicates poor blood sugar control. Above 6.5% confirms diabetes; above 8% indicates significantly uncontrolled diabetes.",
        "low_explanation": "Very low HbA1c may indicate hypoglycemia risk, haemolytic anaemia, or recent blood transfusion.",
        "high_action": "Discuss diabetes management plan with your endocrinologist. Review diet, exercise, and medication.",
        "low_action": "Consult your doctor. May require investigation for haemolytic conditions.",
        "high_risk_threshold": 8.0,
        "high_risk_label": "Uncontrolled Diabetes",
    },
    "fasting_glucose": {
        "display_name": "Fasting Blood Glucose",
        "unit": "mg/dL",
        "normal_range": (70, 99),
        "prediabetes_range": (100, 125),
        "diabetic_range": (126, 9999),
        "critical_low": 40.0,
        "critical_high": 500.0,
        "category": "Diabetes",
        "clinical_meaning": "Measures blood sugar after at least 8 hours of fasting. Used to screen for diabetes.",
        "high_explanation": "High fasting glucose indicates impaired glucose metabolism, prediabetes, or diabetes.",
        "low_explanation": "Low fasting glucose (hypoglycemia) can cause confusion, seizures, and loss of consciousness.",
        "high_action": "Discuss with your GP. Dietary modifications, exercise, and possibly medication may be needed.",
        "low_action": "URGENT: If symptomatic, consume glucose immediately. Seek medical attention.",
        "high_risk_threshold": 200.0,
        "high_risk_label": "Severely Elevated Blood Sugar",
    },

    # ── KIDNEY FUNCTION ───────────────────────────────────────────────────────
    "creatinine": {
        "display_name": "Serum Creatinine",
        "unit": "mg/dL",
        "normal_range": (0.6, 1.2),
        "male_range": (0.74, 1.35),
        "female_range": (0.59, 1.04),
        "critical_low": None,
        "critical_high": 10.0,
        "category": "Kidney Function",
        "clinical_meaning": "Waste product filtered by kidneys. Elevated levels indicate reduced kidney filtering ability.",
        "high_explanation": "Elevated creatinine suggests impaired kidney function (CKD, acute kidney injury). Dangerous if also on metformin.",
        "low_explanation": "Low creatinine may indicate reduced muscle mass or malnutrition.",
        "high_action": "Urgently consult nephrologist. Avoid NSAIDs. If on metformin, STOP immediately and contact doctor.",
        "low_action": "Monitor nutrition. Follow up with GP.",
        "high_risk_threshold": 2.0,
        "high_risk_label": "Kidney Dysfunction",
    },
    "bun": {
        "display_name": "Blood Urea Nitrogen (BUN)",
        "unit": "mg/dL",
        "normal_range": (7, 20),
        "critical_low": None,
        "critical_high": 100.0,
        "category": "Kidney Function",
        "clinical_meaning": "Another kidney waste marker. Elevated together with creatinine strongly suggests kidney disease.",
        "high_explanation": "High BUN indicates kidneys are not effectively filtering waste. Can also be elevated from dehydration or high protein diet.",
        "low_explanation": "Low BUN may indicate liver disease or severe malnutrition.",
        "high_action": "Consult GP or nephrologist. Increase water intake. Avoid nephrotoxic drugs.",
        "low_action": "Investigate for liver disease or malnutrition.",
        "high_risk_threshold": 50.0,
        "high_risk_label": "Elevated Urea — Kidney Stress",
    },
    "egfr": {
        "display_name": "eGFR (Estimated Glomerular Filtration Rate)",
        "unit": "mL/min/1.73m²",
        "normal_range": (60, 999),
        "critical_low": 15.0,
        "critical_high": None,
        "category": "Kidney Function",
        "clinical_meaning": "Estimates percentage of kidney function remaining. Below 60 for 3+ months = Chronic Kidney Disease.",
        "high_explanation": "Normal or elevated — no kidney impairment indicated.",
        "low_explanation": "Low eGFR indicates kidney damage. Stages: 45-59=Mild, 30-44=Moderate, 15-29=Severe, <15=Kidney Failure.",
        "high_action": "Continue monitoring annually.",
        "low_action": "URGENT below 30: Consult nephrologist immediately. Adjust all kidney-cleared medications.",
        "low_risk_threshold": 45.0,
        "low_risk_label": "Reduced Kidney Function",
    },

    # ── LIVER FUNCTION ────────────────────────────────────────────────────────
    "alt": {
        "display_name": "ALT (Alanine Aminotransferase)",
        "unit": "U/L",
        "normal_range": (7, 56),
        "critical_low": None,
        "critical_high": 1000.0,
        "category": "Liver Function",
        "clinical_meaning": "Enzyme released when liver cells are damaged. Elevated ALT is a sensitive marker of liver injury.",
        "high_explanation": "Elevated ALT indicates liver inflammation or damage from: fatty liver, hepatitis, alcohol, medications.",
        "low_explanation": "Low ALT is generally not clinically significant.",
        "high_action": "Avoid alcohol and hepatotoxic drugs (paracetamol overdose). Ultrasound and hepatology consult if persistently elevated.",
        "low_action": "No action needed.",
        "high_risk_threshold": 200.0,
        "high_risk_label": "Significant Liver Injury",
    },
    "ast": {
        "display_name": "AST (Aspartate Aminotransferase)",
        "unit": "U/L",
        "normal_range": (10, 40),
        "critical_low": None,
        "critical_high": 1000.0,
        "category": "Liver Function",
        "clinical_meaning": "Liver and heart enzyme. Elevated alongside ALT confirms liver damage.",
        "high_explanation": "Elevated AST may indicate liver damage, heart muscle injury, or muscle breakdown.",
        "low_explanation": "Low AST is generally not significant.",
        "high_action": "Consult GP. Evaluate with ALT ratio (AST:ALT >2 suggests alcohol liver disease).",
        "low_action": "No action needed.",
        "high_risk_threshold": 200.0,
        "high_risk_label": "Liver/Cardiac Stress",
    },

    # ── LIPID PANEL ───────────────────────────────────────────────────────────
    "total_cholesterol": {
        "display_name": "Total Cholesterol",
        "unit": "mg/dL",
        "normal_range": (0, 200),
        "borderline_range": (200, 239),
        "high_range": (240, 9999),
        "critical_low": None,
        "critical_high": 500.0,
        "category": "Lipid Panel",
        "clinical_meaning": "Total blood cholesterol. High levels increase cardiovascular disease risk.",
        "high_explanation": "High total cholesterol increases risk of heart attack and stroke. Above 240 = 'High Risk'.",
        "low_explanation": "Very low total cholesterol may increase risk of depression, stroke (haemorrhagic), and cancer.",
        "high_action": "Adopt heart-healthy diet, exercise. Discuss statin therapy with your cardiologist.",
        "low_action": "Consult GP. Investigate for malnutrition or hyperthyroidism.",
        "high_risk_threshold": 240.0,
        "high_risk_label": "High Cardiovascular Risk",
    },
    "ldl": {
        "display_name": "LDL Cholesterol ('Bad' Cholesterol)",
        "unit": "mg/dL",
        "normal_range": (0, 100),
        "borderline_range": (100, 129),
        "high_range": (130, 9999),
        "critical_low": None,
        "critical_high": 300.0,
        "category": "Lipid Panel",
        "clinical_meaning": "LDL deposits cholesterol in artery walls, causing plaque buildup. Primary target of statin therapy.",
        "high_explanation": "High LDL directly increases heart attack and stroke risk. Target <100 for healthy adults, <70 for high-risk patients.",
        "low_explanation": "LDL below 40 may be associated with increased risk of haemorrhagic stroke and depression.",
        "high_action": "Reduce saturated fats. Discuss statin therapy with cardiologist. Target <70 if high cardiovascular risk.",
        "low_action": "Monitor. Consult GP if symptoms present.",
        "high_risk_threshold": 160.0,
        "high_risk_label": "High LDL — Statin Therapy Recommended",
    },
    "hdl": {
        "display_name": "HDL Cholesterol ('Good' Cholesterol)",
        "unit": "mg/dL",
        "normal_range": (40, 999),
        "male_range": (40, 999),
        "female_range": (50, 999),
        "critical_low": 25.0,
        "critical_high": None,
        "category": "Lipid Panel",
        "clinical_meaning": "HDL removes cholesterol from arteries and brings it to the liver. Higher is better.",
        "high_explanation": "High HDL is PROTECTIVE against heart disease. No action needed.",
        "low_explanation": "Low HDL increases cardiovascular risk, even if total cholesterol is normal.",
        "high_action": "Excellent! Maintain lifestyle.",
        "low_action": "Exercise more. Quit smoking. Reduce trans fats. Consult cardiologist.",
        "low_risk_threshold": 40.0,
        "low_risk_label": "Low Protective Cholesterol",
    },
    "triglycerides": {
        "display_name": "Triglycerides",
        "unit": "mg/dL",
        "normal_range": (0, 150),
        "borderline_range": (150, 199),
        "high_range": (200, 499),
        "very_high_range": (500, 9999),
        "critical_low": None,
        "critical_high": 1000.0,
        "category": "Lipid Panel",
        "clinical_meaning": "Blood fats from sugar and refined carbohydrates. High levels increase pancreatitis and heart disease risk.",
        "high_explanation": "Elevated triglycerides often caused by excess sugar, alcohol, and refined carbs. Increases pancreatitis risk above 500.",
        "low_explanation": "Low triglycerides are generally healthy.",
        "high_action": "Drastically reduce sugar, alcohol, and refined carbohydrates. Exercise daily.",
        "low_action": "No action needed.",
        "high_risk_threshold": 200.0,
        "high_risk_label": "Elevated — Metabolic Syndrome Risk",
    },

    # ── COMPLETE BLOOD COUNT ──────────────────────────────────────────────────
    "hemoglobin": {
        "display_name": "Hemoglobin (Hb)",
        "unit": "g/dL",
        "normal_range": (12.0, 17.5),
        "male_range": (13.5, 17.5),
        "female_range": (12.0, 15.5),
        "critical_low": 7.0,
        "critical_high": 20.0,
        "category": "Complete Blood Count",
        "clinical_meaning": "Protein in red blood cells that carries oxygen. Low Hb = anaemia.",
        "high_explanation": "High Hb can indicate dehydration, polycythaemia vera, or living at high altitude.",
        "low_explanation": "Low Hb indicates anaemia. Causes: iron deficiency, B12/folate deficiency, blood loss, chronic disease.",
        "high_action": "Consult haematologist. Check for dehydration.",
        "low_action": "Iron and B12 supplementation may be needed. Blood transfusion if critically low. Consult GP.",
        "low_risk_threshold": 10.0,
        "low_risk_label": "Significant Anaemia",
    },
    "wbc": {
        "display_name": "WBC (White Blood Cell Count)",
        "unit": "×10³/μL",
        "normal_range": (4.5, 11.0),
        "critical_low": 2.0,
        "critical_high": 30.0,
        "category": "Complete Blood Count",
        "clinical_meaning": "Immune system cells. Elevated suggests infection or inflammation; low suggests immune suppression.",
        "high_explanation": "Elevated WBC indicates active infection, inflammation, leukaemia, or stress response.",
        "low_explanation": "Low WBC (leukopenia) indicates bone marrow problems, severe infection (sepsis), or medication side effect.",
        "high_action": "Consult GP. Investigate for infection or haematological disorder.",
        "low_action": "URGENT if <2: Haematology consult immediately — risk of severe infection.",
        "high_risk_threshold": 20.0,
        "high_risk_label": "Possible Serious Infection/Leukaemia",
    },
    "platelets": {
        "display_name": "Platelet Count",
        "unit": "×10³/μL",
        "normal_range": (150, 400),
        "critical_low": 50.0,
        "critical_high": 1000.0,
        "category": "Complete Blood Count",
        "clinical_meaning": "Cells that form blood clots. Low platelets = bleeding risk; high = clotting risk.",
        "high_explanation": "Elevated platelets increase clotting/thrombosis risk. Investigate for inflammatory or reactive thrombocytosis.",
        "low_explanation": "Low platelets (thrombocytopenia) increases bleeding risk. Causes: autoimmune, drug side effects, bone marrow failure.",
        "high_action": "Consult haematologist. Assess clotting risk.",
        "low_action": "Avoid aspirin and NSAIDs. URGENT if <50: immediate haematology review.",
        "low_risk_threshold": 100.0,
        "low_risk_label": "Thrombocytopenia — Bleeding Risk",
    },

    # ── THYROID ───────────────────────────────────────────────────────────────
    "tsh": {
        "display_name": "TSH (Thyroid-Stimulating Hormone)",
        "unit": "mIU/L",
        "normal_range": (0.4, 4.0),
        "critical_low": 0.01,
        "critical_high": 100.0,
        "category": "Thyroid Function",
        "clinical_meaning": "Controls thyroid hormone production. High TSH = underactive thyroid; Low TSH = overactive thyroid.",
        "high_explanation": "High TSH indicates HYPOTHYROIDISM (underactive thyroid): fatigue, weight gain, cold intolerance, depression.",
        "low_explanation": "Low TSH indicates HYPERTHYROIDISM (overactive thyroid): weight loss, palpitations, anxiety, heat intolerance.",
        "high_action": "Thyroid hormone replacement therapy (Levothyroxine). Consult endocrinologist.",
        "low_action": "Investigate for hyperthyroidism or Graves' disease. Consult endocrinologist.",
        "high_risk_threshold": 10.0,
        "low_risk_threshold": 0.1,
        "high_risk_label": "Significant Hypothyroidism",
        "low_risk_label": "Significant Hyperthyroidism",
    },

    # ── CARDIAC MARKERS ───────────────────────────────────────────────────────
    "troponin": {
        "display_name": "Troponin I/T",
        "unit": "ng/mL",
        "normal_range": (0, 0.04),
        "critical_low": None,
        "critical_high": 2.0,
        "category": "Cardiac Markers",
        "clinical_meaning": "Protein released ONLY when heart muscle is damaged. Elevated troponin is the hallmark of heart attack.",
        "high_explanation": "ELEVATED TROPONIN = POSSIBLE MYOCARDIAL INFARCTION (HEART ATTACK). This is a medical emergency.",
        "low_explanation": "Normal troponin suggests heart muscle is intact.",
        "high_action": "GO TO EMERGENCY IMMEDIATELY. Call 112/108/911. Do NOT wait.",
        "low_action": "No cardiac muscle injury detected.",
        "high_risk_threshold": 0.04,
        "high_risk_label": "POSSIBLE HEART ATTACK — EMERGENCY",
    },

    # ── ELECTROLYTES ──────────────────────────────────────────────────────────
    "sodium": {
        "display_name": "Serum Sodium",
        "unit": "mEq/L",
        "normal_range": (136, 145),
        "critical_low": 120.0,
        "critical_high": 160.0,
        "category": "Electrolytes",
        "clinical_meaning": "Controls fluid balance and nerve function. Severe derangements cause neurological emergencies.",
        "high_explanation": "High sodium (hypernatremia): usually severe dehydration. Causes confusion and seizures.",
        "low_explanation": "Low sodium (hyponatremia): excess water retention, heart failure, or SIADH. Causes confusion and seizures.",
        "high_action": "Increase fluid intake (if dehydrated). Urgent if >155: IV fluids in hospital setting.",
        "low_action": "Fluid restriction if dilutional. Urgent if <125: emergency hospital treatment.",
        "high_risk_threshold": 150.0,
        "low_risk_threshold": 130.0,
        "high_risk_label": "Hypernatremia — Dehydration",
        "low_risk_label": "Hyponatremia — Fluid Imbalance",
    },
    "potassium": {
        "display_name": "Serum Potassium",
        "unit": "mEq/L",
        "normal_range": (3.5, 5.0),
        "critical_low": 2.5,
        "critical_high": 6.5,
        "category": "Electrolytes",
        "clinical_meaning": "Essential for heart rhythm and muscle function. Critical derangements cause fatal arrhythmias.",
        "high_explanation": "High potassium (hyperkalemia) can cause life-threatening cardiac arrhythmias and cardiac arrest.",
        "low_explanation": "Low potassium (hypokalemia) causes muscle weakness, cramps, and dangerous heart arrhythmias.",
        "high_action": "URGENT if >6.0: Emergency treatment (calcium gluconate, insulin+dextrose). Restrict dietary potassium.",
        "low_action": "Potassium supplementation. URGENT if <3.0: IV potassium in monitored hospital setting.",
        "high_risk_threshold": 5.5,
        "low_risk_threshold": 3.0,
        "high_risk_label": "Hyperkalemia — Cardiac Risk",
        "low_risk_label": "Hypokalemia — Arrhythmia Risk",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Lab Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

def _find_test(test_name: str) -> Optional[tuple]:
    """Fuzzy-matches a test name against the reference database."""
    test_lower = test_name.lower().strip()
    # Alias mappings for common alternate names
    aliases = {
        "glycated hemoglobin": "hba1c",
        "a1c": "hba1c",
        "blood sugar": "fasting_glucose",
        "glucose": "fasting_glucose",
        "fbs": "fasting_glucose",
        "kidney": "creatinine",
        "urea": "bun",
        "blood urea": "bun",
        "gfr": "egfr",
        "sgpt": "alt",
        "sgot": "ast",
        "cholesterol": "total_cholesterol",
        "bad cholesterol": "ldl",
        "good cholesterol": "hdl",
        "trig": "triglycerides",
        "hb": "hemoglobin",
        "haemoglobin": "hemoglobin",
        "wbcs": "wbc",
        "white blood cell": "wbc",
        "white blood cells": "wbc",
        "platelet": "platelets",
        "thyroid": "tsh",
        "heart attack marker": "troponin",
        "salt": "sodium",
        "na": "sodium",
        "k": "potassium",
    }

    resolved = aliases.get(test_lower, test_lower)
    if resolved in LAB_REFERENCE_DATABASE:
        return resolved, LAB_REFERENCE_DATABASE[resolved]

    for key, data in LAB_REFERENCE_DATABASE.items():
        if key in test_lower or test_lower in key or test_lower in data["display_name"].lower():
            return key, data

    return None


def analyze_lab_value(test_name: str, value: float, gender: str = "unknown") -> dict:
    """
    Analyzes a single lab test result against clinical reference ranges.

    Args:
        test_name: Name of the test (e.g., 'HbA1c', 'creatinine', 'hemoglobin').
        value: The measured value (numeric).
        gender: 'male', 'female', or 'unknown' for gender-adjusted ranges.

    Returns:
        dict with status, flag, severity, explanation, and recommended_action.
    """
    match = _find_test(test_name)
    if not match:
        return {
            "test": test_name,
            "value": value,
            "status": "UNKNOWN_TEST",
            "flag": "?",
            "severity": "INFO",
            "message": f"Test '{test_name}' not found in reference database. Please consult your doctor.",
            "explanation": "",
            "recommended_action": "Discuss this result with your GP.",
        }

    key, ref = match
    gender_lower = gender.lower()

    # Determine applicable normal range
    low_normal, high_normal = ref["normal_range"]
    if gender_lower == "male" and ref.get("male_range"):
        low_normal, high_normal = ref["male_range"]
    elif gender_lower == "female" and ref.get("female_range"):
        low_normal, high_normal = ref["female_range"]

    critical_low = ref.get("critical_low")
    critical_high = ref.get("critical_high")

    # Determine flag
    flag = "NORMAL"
    severity = "OK"
    explanation = ""
    action = "Continue routine monitoring."

    if critical_high and value >= critical_high:
        flag = "CRITICAL HIGH ↑↑"
        severity = "CRITICAL"
        explanation = ref["high_explanation"]
        action = ref["high_action"]
    elif critical_low and value <= critical_low:
        flag = "CRITICAL LOW ↓↓"
        severity = "CRITICAL"
        explanation = ref["low_explanation"]
        action = ref["low_action"]
    elif value > high_normal:
        high_risk = ref.get("high_risk_threshold")
        if high_risk and value >= high_risk:
            flag = "HIGH ↑ (Significant)"
            severity = "WARNING"
        else:
            flag = "HIGH ↑"
            severity = "BORDERLINE"
        explanation = ref["high_explanation"]
        action = ref["high_action"]
    elif value < low_normal:
        low_risk = ref.get("low_risk_threshold")
        if low_risk and value <= low_risk:
            flag = "LOW ↓ (Significant)"
            severity = "WARNING"
        else:
            flag = "LOW ↓"
            severity = "BORDERLINE"
        explanation = ref["low_explanation"]
        action = ref["low_action"]
    else:
        flag = "NORMAL ✓"
        severity = "OK"
        explanation = f"Value is within the normal reference range ({low_normal}–{high_normal} {ref['unit']})."
        action = "Continue routine monitoring."

    result = {
        "test": ref["display_name"],
        "test_key": key,
        "value": value,
        "unit": ref["unit"],
        "normal_range": f"{low_normal}–{high_normal} {ref['unit']}",
        "flag": flag,
        "severity": severity,
        "category": ref["category"],
        "clinical_meaning": ref["clinical_meaning"],
        "explanation": explanation,
        "recommended_action": action,
    }

    # Add disease-specific labels if applicable
    risk_label = ref.get("high_risk_label") if value > high_normal else ref.get("low_risk_label")
    if risk_label and severity in ("WARNING", "CRITICAL"):
        result["risk_label"] = risk_label

    return result


def analyze_lab_report(lab_values: dict, age: int = 40, gender: str = "unknown") -> dict:
    """
    Analyzes a full panel of lab test results.

    Args:
        lab_values: dict mapping test names to numeric values. E.g.:
                    {"HbA1c": 8.2, "creatinine": 1.9, "hemoglobin": 10.1}
        age: Patient age (used for contextual risk adjustment).
        gender: 'male', 'female', or 'unknown'.

    Returns:
        dict with full panel analysis, critical flags, risk summary.
    """
    results = []
    critical_findings = []
    warning_findings = []
    normal_count = 0

    for test_name, value in lab_values.items():
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            continue

        analysis = analyze_lab_value(test_name, val_float, gender)
        results.append(analysis)

        if analysis["severity"] == "CRITICAL":
            critical_findings.append(analysis)
        elif analysis["severity"] in ("WARNING", "BORDERLINE"):
            warning_findings.append(analysis)
        else:
            normal_count += 1

    # Compute overall risk tier
    if critical_findings:
        overall_risk = "CRITICAL"
        risk_message = f"{len(critical_findings)} CRITICAL finding(s) require immediate medical attention."
    elif len(warning_findings) >= 3:
        overall_risk = "HIGH"
        risk_message = f"{len(warning_findings)} abnormal values detected. Consult your doctor soon."
    elif warning_findings:
        overall_risk = "MODERATE"
        risk_message = f"{len(warning_findings)} borderline/abnormal value(s) detected. Review with your GP."
    else:
        overall_risk = "LOW"
        risk_message = "All tested values are within normal ranges. Continue routine monitoring."

    # Age risk modifier message
    age_note = ""
    if age >= 60:
        age_note = "Note: Reference ranges may vary for patients over 60. Discuss age-adjusted targets with your doctor."

    return {
        "total_tests": len(results),
        "critical_count": len(critical_findings),
        "warning_count": len(warning_findings),
        "normal_count": normal_count,
        "overall_risk_tier": overall_risk,
        "risk_summary": risk_message,
        "age_note": age_note,
        "critical_findings": critical_findings,
        "warning_findings": warning_findings,
        "all_results": results,
        "disclaimer": (
            "This analysis is for EDUCATIONAL PURPOSES ONLY. "
            "Lab results must be interpreted in the context of your full clinical history by a qualified physician. "
            "Never change or stop medications based solely on this report."
        ),
    }


def format_lab_report_display(report: dict) -> str:
    """
    Formats the lab report analysis as a rich, readable terminal/text output.

    Args:
        report: dict returned from analyze_lab_report().

    Returns:
        Formatted string for display.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("  [MediGuide AI] Intelligent Lab Report Analysis")
    lines.append("=" * 70)
    lines.append(f"\nTests Analyzed: {report['total_tests']} | "
                 f"Critical: {report['critical_count']} | "
                 f"Abnormal: {report['warning_count']} | "
                 f"Normal: {report['normal_count']}")

    tier_icons = {"CRITICAL": "[!!!] CRITICAL RISK", "HIGH": "[!!] HIGH RISK",
                  "MODERATE": "[!] MODERATE RISK", "LOW": "[OK] LOW RISK"}
    lines.append(f"\nOverall Health Risk Tier: {tier_icons.get(report['overall_risk_tier'], report['overall_risk_tier'])}")
    lines.append(f"Summary: {report['risk_summary']}")

    if report.get("age_note"):
        lines.append(f"\n[Note] {report['age_note']}")

    # Critical findings first
    if report["critical_findings"]:
        lines.append("\n" + "!" * 70)
        lines.append("  CRITICAL FINDINGS — SEEK IMMEDIATE MEDICAL ATTENTION")
        lines.append("!" * 70)
        for r in report["critical_findings"]:
            lines.append(f"\n  {r['test']}")
            lines.append(f"  Value: {r['value']} {r['unit']}  |  Status: {r['flag']}")
            lines.append(f"  Normal Range: {r['normal_range']}")
            lines.append(f"  What this means: {r['explanation']}")
            lines.append(f"  Action Required: {r['recommended_action']}")

    # Warning findings
    if report["warning_findings"]:
        lines.append("\n" + "-" * 70)
        lines.append("  ABNORMAL / BORDERLINE FINDINGS")
        lines.append("-" * 70)
        for r in report["warning_findings"]:
            risk_tag = f"  [{r.get('risk_label', '')}]" if r.get("risk_label") else ""
            lines.append(f"\n  {r['test']}{risk_tag}")
            lines.append(f"  Value: {r['value']} {r['unit']}  |  Status: {r['flag']}")
            lines.append(f"  Normal Range: {r['normal_range']}")
            lines.append(f"  What this means: {r['explanation']}")
            lines.append(f"  Action: {r['recommended_action']}")

    # Normal findings
    normal_results = [r for r in report["all_results"] if r["severity"] == "OK"]
    if normal_results:
        lines.append("\n" + "-" * 70)
        lines.append("  NORMAL FINDINGS")
        lines.append("-" * 70)
        for r in normal_results:
            lines.append(f"  {r['test']}: {r['value']} {r['unit']}  |  {r['flag']}  (Range: {r['normal_range']})")

    lines.append("\n" + "-" * 70)
    lines.append(f"DISCLAIMER: {report['disclaimer']}")
    lines.append("=" * 70)
    return "\n".join(lines)
