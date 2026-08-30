"""
MediGuide AI — Food-Drug & Lifestyle Interactions Engine
=========================================================
Identifies dangerous interactions between:
  - Drugs and common foods (grapefruit, alcohol, dairy, etc.)
  - Drugs and lifestyle factors (smoking, exercise, caffeine)
  - Drug timing conflicts (cannot take A and B at the same time)

Also generates personalized daily medication schedules with
optimal time-of-day slots based on each drug's clinical requirements.
"""

from typing import List, Dict

# ─────────────────────────────────────────────────────────────────────────────
# Food-Drug Interaction Database
# ─────────────────────────────────────────────────────────────────────────────

FOOD_DRUG_INTERACTIONS = {
    # Grapefruit is by far the most clinically significant food interaction
    "grapefruit": {
        "interacting_drugs": [
            "warfarin", "simvastatin", "atorvastatin", "lovastatin",
            "cyclosporine", "tacrolimus", "amlodipine", "felodipine",
            "nifedipine", "verapamil", "amiodarone", "carbamazepine",
            "buspirone", "sertraline", "sildenafil",
        ],
        "severity": "HIGH",
        "mechanism": "Grapefruit inhibits the CYP3A4 enzyme in the intestinal wall, dramatically increasing blood levels of many drugs.",
        "effect": "Blood drug levels can rise 2-5x, turning a normal dose into a toxic overdose.",
        "recommendation": "AVOID grapefruit and grapefruit juice for 24-72 hours around any dose of these medications.",
        "aliases": ["grapefruit juice", "pomelo"],
    },
    "alcohol": {
        "interacting_drugs": [
            "metformin", "warfarin", "metronidazole", "tinidazole",
            "paracetamol", "acetaminophen", "aspirin", "ibuprofen",
            "diazepam", "alprazolam", "codeine", "tramadol",
            "morphine", "gabapentin", "pregabalin", "amoxicillin",
        ],
        "severity": "HIGH",
        "mechanism": "Alcohol is metabolized by the same liver enzymes as many drugs, causing competitive inhibition or toxic byproduct formation.",
        "effect": "Increased drug toxicity, severe liver damage (with paracetamol), disulfiram-like reaction (with metronidazole), excessive CNS depression (with sedatives).",
        "recommendation": "AVOID alcohol entirely when taking antibiotics, blood thinners, painkillers, or CNS medications.",
        "aliases": ["beer", "wine", "spirits", "ethanol", "drinking"],
    },
    "dairy": {
        "interacting_drugs": [
            "tetracycline", "doxycycline", "ciprofloxacin", "levofloxacin",
            "norfloxacin", "ofloxacin", "bisphosphonates", "alendronate",
        ],
        "severity": "MODERATE",
        "mechanism": "Calcium in dairy chelates (binds) certain antibiotics and drugs, forming insoluble complexes that cannot be absorbed.",
        "effect": "Drug absorption reduced by up to 90%, making the antibiotic completely ineffective.",
        "recommendation": "Take these medications 2 hours BEFORE or 4 hours AFTER consuming dairy products.",
        "aliases": ["milk", "cheese", "yogurt", "calcium"],
    },
    "high_potassium_foods": {
        "interacting_drugs": [
            "spironolactone", "amiloride", "triamterene",
            "lisinopril", "enalapril", "ramipril", "losartan", "valsartan",
            "trimethoprim",
        ],
        "severity": "MODERATE",
        "mechanism": "ACE inhibitors/ARBs and potassium-sparing diuretics reduce potassium excretion. High potassium foods can push levels to dangerous, arrhythmia-causing levels.",
        "effect": "Life-threatening hyperkalemia (dangerously high potassium causing cardiac arrhythmia).",
        "recommendation": "Limit bananas, avocados, tomatoes, oranges, and potassium supplements when on these medications.",
        "aliases": ["bananas", "avocado", "potassium", "tomatoes", "orange juice"],
    },
    "vitamin_k_foods": {
        "interacting_drugs": ["warfarin", "acenocoumarol", "phenprocoumon"],
        "severity": "HIGH",
        "mechanism": "Warfarin works by blocking Vitamin K's role in clotting factor synthesis. Eating large amounts of Vitamin K reverses warfarin's anticoagulant effect.",
        "effect": "Unpredictable INR (blood thinning level), risk of blood clots if Vitamin K is too high; bleeding risk if suddenly reduced.",
        "recommendation": "Keep Vitamin K consumption CONSISTENT (don't suddenly increase or decrease). Monitor INR closely. Avoid drastic changes in green vegetable intake.",
        "aliases": ["spinach", "kale", "broccoli", "lettuce", "cabbage", "green vegetables"],
    },
    "caffeine": {
        "interacting_drugs": [
            "ciprofloxacin", "norfloxacin", "lithium",
            "clozapine", "theophylline", "adenosine",
        ],
        "severity": "MODERATE",
        "mechanism": "Fluoroquinolone antibiotics inhibit caffeine metabolism, causing caffeine to accumulate. Caffeine also counteracts adenosine.",
        "effect": "Severe caffeine toxicity: palpitations, anxiety, insomnia. Caffeine significantly worsens lithium toxicity risk.",
        "recommendation": "Reduce caffeine intake significantly when on fluoroquinolone antibiotics or lithium.",
        "aliases": ["coffee", "tea", "energy drinks", "cola"],
    },
    "tyramine_foods": {
        "interacting_drugs": [
            "phenelzine", "tranylcypromine", "isocarboxazid",
            "selegiline", "linezolid",
        ],
        "severity": "CRITICAL",
        "mechanism": "MAO inhibitors block tyramine breakdown. Tyramine from aged foods causes massive norepinephrine release.",
        "effect": "HYPERTENSIVE CRISIS: Sudden severe blood pressure spike (>180/120 mmHg), risk of stroke, brain bleed.",
        "recommendation": "STRICTLY AVOID aged cheeses, cured meats, fermented foods, red wine, soy sauce when on MAO inhibitors. Life-threatening.",
        "aliases": ["aged cheese", "red wine", "salami", "pepperoni", "soy sauce", "miso", "beer"],
    },
    "antacids": {
        "interacting_drugs": [
            "ciprofloxacin", "tetracycline", "doxycycline",
            "iron supplements", "ferrous sulfate", "levothyroxine",
        ],
        "severity": "MODERATE",
        "mechanism": "Antacids containing aluminum, magnesium, or calcium bind to drugs in the gut, preventing absorption.",
        "effect": "Reduced drug absorption and therapeutic failure.",
        "recommendation": "Take these drugs 2 hours BEFORE or 4 hours AFTER antacids.",
        "aliases": ["omeprazole", "pantoprazole", "antacid", "tums", "maalox", "milk of magnesia"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Daily Medication Timing Database
# Rules: when each drug should be taken relative to meals and time of day
# ─────────────────────────────────────────────────────────────────────────────

MED_TIMING_RULES = {
    "metformin":      {"slot": "WITH_MEAL",    "note": "Always take WITH food to minimize GI side effects (nausea)."},
    "lisinopril":     {"slot": "EVENING",      "note": "Best taken in the evening — blood pressure peaks in morning."},
    "enalapril":      {"slot": "EVENING",      "note": "Evening dose optimizes morning blood pressure control."},
    "ramipril":       {"slot": "EVENING",      "note": "Evening dose optimizes morning blood pressure control."},
    "atorvastatin":   {"slot": "NIGHT",        "note": "Statins are most effective at night when liver produces most cholesterol."},
    "simvastatin":    {"slot": "NIGHT",        "note": "Peak effectiveness overnight — take at bedtime."},
    "lovastatin":     {"slot": "NIGHT",        "note": "Take with evening meal for optimal absorption."},
    "levothyroxine":  {"slot": "MORNING_FASTED", "note": "Take 30-60 min BEFORE breakfast on empty stomach. Food severely reduces absorption."},
    "warfarin":       {"slot": "EVENING",      "note": "Consistent evening dosing allows INR monitoring the next morning."},
    "aspirin":        {"slot": "MORNING_WITH_FOOD", "note": "Take with food or milk to protect stomach lining."},
    "omeprazole":     {"slot": "MORNING_FASTED", "note": "Take 30-60 min BEFORE breakfast — most effective when stomach acid production is starting."},
    "pantoprazole":   {"slot": "MORNING_FASTED", "note": "Take before meals for best acid suppression."},
    "amlodipine":     {"slot": "ANY",          "note": "Can be taken any time daily — maintain consistency."},
    "ibuprofen":      {"slot": "WITH_MEAL",    "note": "ALWAYS take with food to reduce stomach bleeding risk."},
    "diclofenac":     {"slot": "WITH_MEAL",    "note": "Take with food to protect stomach."},
    "amoxicillin":    {"slot": "WITH_MEAL",    "note": "Take with or without food, but food reduces nausea."},
    "doxycycline":    {"slot": "WITH_MEAL",    "note": "Take WITH food and water. Do not lie down for 30 mins."},
    "ciprofloxacin":  {"slot": "ANY",          "note": "Avoid dairy and antacids within 2 hours."},
    "metoprolol":     {"slot": "MORNING_WITH_FOOD", "note": "Take with food for consistent absorption."},
    "bisoprolol":     {"slot": "MORNING",      "note": "Morning dosing to cover peak cardiovascular risk times."},
    "furosemide":     {"slot": "MORNING",      "note": "Morning only — avoid nighttime to prevent sleep-disrupting urination."},
    "spironolactone": {"slot": "MORNING_WITH_FOOD", "note": "Take with food. Monitor potassium levels carefully."},
    "prednisolone":   {"slot": "MORNING_WITH_FOOD", "note": "Morning dosing mimics natural cortisol rhythm. Take with food."},
    "gabapentin":     {"slot": "THREE_TIMES_DAILY", "note": "Divide evenly through the day — levels must be consistent."},
    "pregabalin":     {"slot": "TWICE_DAILY",  "note": "Take 12 hours apart for steady blood levels."},
    "paracetamol":    {"slot": "AS_NEEDED",    "note": "As needed for pain/fever. Max 4g/day. Space doses by 4-6 hours."},
}

# Time slot definitions for schedule generation
TIME_SLOTS = {
    "MORNING_FASTED":     {"time": "06:30", "label": "Early Morning (Empty Stomach)", "before_meal": True},
    "MORNING":            {"time": "08:00", "label": "Morning"},
    "MORNING_WITH_FOOD":  {"time": "08:00", "label": "Morning with Breakfast"},
    "WITH_MEAL":          {"time": ["08:00", "13:00", "20:00"], "label": "With Meals (Breakfast/Lunch/Dinner)"},
    "AFTERNOON":          {"time": "13:00", "label": "Afternoon"},
    "EVENING":            {"time": "18:00", "label": "Evening"},
    "NIGHT":              {"time": "22:00", "label": "Bedtime"},
    "TWICE_DAILY":        {"time": ["08:00", "20:00"], "label": "Twice Daily (12 hrs apart)"},
    "THREE_TIMES_DAILY":  {"time": ["08:00", "14:00", "20:00"], "label": "Three Times Daily (6-8 hrs apart)"},
    "ANY":                {"time": "09:00", "label": "Any Consistent Time Daily"},
    "AS_NEEDED":          {"time": "as needed", "label": "As Needed (PRN)"},
}


# ─────────────────────────────────────────────────────────────────────────────
# Analysis Functions
# ─────────────────────────────────────────────────────────────────────────────

def check_food_drug_interactions(drug_list: List[str], food_list: List[str] = None) -> dict:
    """
    Checks for dangerous food-drug interactions.

    Args:
        drug_list: List of drug names the patient is taking.
        food_list: Optional list of foods/substances. If None, checks all known dangerous foods.

    Returns:
        dict with interaction warnings organized by severity.
    """
    drugs_lower = [d.lower().strip() for d in drug_list]
    warnings = []

    foods_to_check = food_list if food_list else list(FOOD_DRUG_INTERACTIONS.keys())

    for food_key in foods_to_check:
        food_lower = food_key.lower().strip()
        # Match food against database (direct or alias)
        matched_food_key = None
        for db_key, db_data in FOOD_DRUG_INTERACTIONS.items():
            aliases = [db_key] + db_data.get("aliases", [])
            if any(food_lower in alias.lower() or alias.lower() in food_lower for alias in aliases):
                matched_food_key = db_key
                break

        if not matched_food_key:
            continue

        interaction = FOOD_DRUG_INTERACTIONS[matched_food_key]
        for drug in drugs_lower:
            interacting = interaction["interacting_drugs"]
            if any(drug in d.lower() or d.lower() in drug for d in interacting):
                warnings.append({
                    "drug": drug,
                    "food_substance": matched_food_key.replace("_", " ").title(),
                    "severity": interaction["severity"],
                    "mechanism": interaction["mechanism"],
                    "effect": interaction["effect"],
                    "recommendation": interaction["recommendation"],
                })

    # Deduplicate
    seen = set()
    unique_warnings = []
    for w in warnings:
        key = f"{w['drug']}_{w['food_substance']}"
        if key not in seen:
            seen.add(key)
            unique_warnings.append(w)

    critical = [w for w in unique_warnings if w["severity"] == "CRITICAL"]
    high = [w for w in unique_warnings if w["severity"] == "HIGH"]
    moderate = [w for w in unique_warnings if w["severity"] == "MODERATE"]

    return {
        "total_interactions": len(unique_warnings),
        "critical_count": len(critical),
        "high_count": len(high),
        "moderate_count": len(moderate),
        "critical_warnings": critical,
        "high_warnings": high,
        "moderate_warnings": moderate,
        "disclaimer": "This is not a complete food-drug interaction checker. Always consult your pharmacist.",
    }


def generate_medication_schedule(medications: List[Dict]) -> dict:
    """
    Generates a personalized daily medication schedule.

    Args:
        medications: List of dicts with 'name', 'dose', 'frequency' keys.
                     E.g.: [{"name": "metformin", "dose": "500mg", "frequency": "twice daily"}]

    Returns:
        dict with schedule organized by time of day.
    """
    schedule = {
        "06:30": [],
        "08:00": [],
        "09:00": [],
        "13:00": [],
        "14:00": [],
        "18:00": [],
        "20:00": [],
        "22:00": [],
        "as_needed": [],
    }

    med_details = []

    for med in medications:
        name = med.get("name", "").lower().strip()
        dose = med.get("dose", "")
        freq = med.get("frequency", "").lower()

        # Find timing rule
        timing = None
        for key in MED_TIMING_RULES:
            if key in name or name in key:
                timing = MED_TIMING_RULES[key]
                break

        if not timing:
            # Infer from frequency
            if "once" in freq or "daily" in freq:
                timing = {"slot": "MORNING", "note": "Take at same time every day for consistency."}
            elif "twice" in freq or "2x" in freq or "bid" in freq:
                timing = {"slot": "TWICE_DAILY", "note": "Take 12 hours apart."}
            elif "three" in freq or "3x" in freq or "tid" in freq:
                timing = {"slot": "THREE_TIMES_DAILY", "note": "Take 6-8 hours apart."}
            elif "as needed" in freq or "prn" in freq:
                timing = {"slot": "AS_NEEDED", "note": "Only when required."}
            else:
                timing = {"slot": "ANY", "note": "Take at consistent time daily."}

        slot_info = TIME_SLOTS.get(timing["slot"], TIME_SLOTS["ANY"])
        slot_times = slot_info["time"]

        display_name = name.title()
        entry = {
            "medication": display_name,
            "dose": dose,
            "note": timing["note"],
            "slot_label": slot_info["label"],
        }

        if isinstance(slot_times, list):
            for t in slot_times:
                if t in schedule:
                    schedule[t].append({**entry, "time": t})
        elif slot_times == "as needed":
            schedule["as_needed"].append({**entry, "time": "As Needed"})
        else:
            if slot_times in schedule:
                schedule[slot_times].append({**entry, "time": slot_times})

        med_details.append({
            "medication": display_name,
            "dose": dose,
            "frequency": freq,
            "optimal_timing": slot_info["label"],
            "clinical_note": timing["note"],
        })

    # Remove empty time slots
    final_schedule = {t: meds for t, meds in schedule.items() if meds}

    return {
        "daily_schedule": final_schedule,
        "medication_details": med_details,
        "total_medications": len(medications),
        "general_tips": [
            "Use a pill organizer with AM/PM compartments to track daily adherence.",
            "Set phone alarms matching this schedule.",
            "Never double-dose if you miss a scheduled time — skip and continue next dose.",
            "Store all medications away from heat, moisture, and direct sunlight.",
            "Always carry an updated medication list when visiting any doctor.",
        ],
        "disclaimer": "This schedule is a general guide. Your pharmacist or doctor may adjust timings based on your specific needs.",
    }


# Alias for backward compatibility
create_medication_schedule = generate_medication_schedule


def format_food_drug_display(result: dict) -> str:

    """Formats food-drug interaction results for terminal display."""
    lines = ["=" * 70,
             "  [MediGuide AI] Food-Drug & Lifestyle Interaction Safety Check",
             "=" * 70,
             f"\nTotal Interactions Found: {result['total_interactions']}"]

    if result["critical_count"]:
        lines.append(f"  CRITICAL: {result['critical_count']} | HIGH: {result['high_count']} | MODERATE: {result['moderate_count']}")

    if result["critical_warnings"]:
        lines.extend(["\n" + "!" * 70, "  CRITICAL WARNINGS — LIFE-THREATENING INTERACTIONS", "!" * 70])
        for w in result["critical_warnings"]:
            lines.extend([f"\n  Drug: {w['drug'].title()}  X  {w['food_substance']}",
                          f"  Effect: {w['effect']}",
                          f"  Action: {w['recommendation']}"])

    if result["high_warnings"]:
        lines.extend(["\n" + "-" * 70, "  HIGH SEVERITY INTERACTIONS", "-" * 70])
        for w in result["high_warnings"]:
            lines.extend([f"\n  Drug: {w['drug'].title()}  X  {w['food_substance']}",
                          f"  Mechanism: {w['mechanism']}",
                          f"  Effect: {w['effect']}",
                          f"  Action: {w['recommendation']}"])

    if result["moderate_warnings"]:
        lines.extend(["\n" + "-" * 70, "  MODERATE INTERACTIONS", "-" * 70])
        for w in result["moderate_warnings"]:
            lines.extend([f"\n  Drug: {w['drug'].title()}  X  {w['food_substance']}",
                          f"  Action: {w['recommendation']}"])

    if result["total_interactions"] == 0:
        lines.append("\n  No known food-drug interactions found for the provided medications.")

    lines.extend(["\n" + "-" * 70, f"  {result['disclaimer']}", "=" * 70])
    return "\n".join(lines)


def format_schedule_display(schedule_result: dict) -> str:
    """Formats the daily medication schedule for terminal display."""
    lines = ["=" * 70,
             "  [MediGuide AI] Personalized Daily Medication Schedule",
             "=" * 70,
             f"\nTotal Medications: {schedule_result['total_medications']}\n"]

    time_labels = {
        "06:30": "06:30 AM — Early Morning (Empty Stomach)",
        "08:00": "08:00 AM — Morning",
        "09:00": "09:00 AM — Mid-Morning",
        "13:00": "01:00 PM — Afternoon / Lunch",
        "14:00": "02:00 PM — Afternoon",
        "18:00": "06:00 PM — Evening",
        "20:00": "08:00 PM — Evening / Dinner",
        "22:00": "10:00 PM — Bedtime",
        "as_needed": "As Needed (PRN)",
    }

    for time_key, meds in schedule_result["daily_schedule"].items():
        label = time_labels.get(time_key, time_key)
        lines.append(f"  [{label}]")
        for m in meds:
            lines.append(f"    > {m['medication']} {m['dose']}")
            lines.append(f"      Note: {m['note']}")
        lines.append("")

    lines.append("  GENERAL TIPS:")
    for tip in schedule_result["general_tips"]:
        lines.append(f"    * {tip}")

    lines.extend(["\n" + "-" * 70, f"  {schedule_result['disclaimer']}", "=" * 70])
    return "\n".join(lines)
