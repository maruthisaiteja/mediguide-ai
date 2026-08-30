"""
MediGuide AI - Medical Tools Library
======================================
Core tool functions used by the agent system. These functions implement
the medical knowledge retrieval and processing logic.

In a production system, these would connect to:
  - FHIR-compliant medical databases
  - NIH/PubMed APIs
  - Clinical decision support systems
  - Hospital EMR systems via HL7

For this capstone, they use a curated knowledge base that demonstrates
the full agent tool-calling capability.

Design Pattern: Tool functions are pure Python — they don't import agents.
This enables clean testing, mocking, and reuse across multiple agents.
"""

from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Medical Knowledge Base (Curated Demo Data)
# In production: replace with real medical API calls
# ─────────────────────────────────────────────────────────────────────────────

SYMPTOM_DATABASE = {
    "fever": {
        "urgency_base": 2,
        "associated_conditions": ["influenza", "COVID-19", "pneumonia", "UTI", "meningitis"],
        "red_flags": ["fever > 39.4°C/103°F", "stiff neck with fever", "rash with fever", "fever > 3 days"],
        "body_system": "immune",
    },
    "headache": {
        "urgency_base": 2,
        "associated_conditions": ["tension headache", "migraine", "hypertension", "meningitis", "sinusitis"],
        "red_flags": ["thunderclap headache", "headache with neck stiffness", "worst headache of life"],
        "body_system": "neurological",
    },
    "chest pain": {
        "urgency_base": 5,  # Immediate emergency level
        "associated_conditions": ["angina", "heart attack", "GERD", "costochondritis", "pleuritis"],
        "red_flags": ["radiating to left arm", "sweating", "shortness of breath with pain"],
        "body_system": "cardiovascular",
    },
    "shortness of breath": {
        "urgency_base": 4,
        "associated_conditions": ["asthma", "COPD", "pneumonia", "heart failure", "anxiety"],
        "red_flags": ["sudden severe onset", "at rest", "with chest pain", "lips turning blue"],
        "body_system": "respiratory",
    },
    "fatigue": {
        "urgency_base": 1,
        "associated_conditions": ["anemia", "thyroid disorders", "diabetes", "depression", "sleep apnea"],
        "red_flags": ["extreme fatigue with weight loss", "fatigue with blood in stool"],
        "body_system": "general",
    },
    "nausea": {
        "urgency_base": 2,
        "associated_conditions": ["gastroenteritis", "food poisoning", "GERD", "pregnancy", "appendicitis"],
        "red_flags": ["vomiting blood", "nausea with severe abdominal pain", "can't keep fluids down for 24h"],
        "body_system": "digestive",
    },
    "cough": {
        "urgency_base": 2,
        "associated_conditions": ["common cold", "influenza", "asthma", "GERD", "COVID-19", "pneumonia"],
        "red_flags": ["coughing up blood", "persistent cough > 3 weeks", "cough with high fever"],
        "body_system": "respiratory",
    },
    "dizziness": {
        "urgency_base": 3,
        "associated_conditions": ["vertigo", "hypotension", "anemia", "inner ear issues", "TIA"],
        "red_flags": ["sudden severe dizziness", "dizziness with chest pain", "fainting"],
        "body_system": "neurological",
    },
}

CONDITION_DATABASE = {
    "type 2 diabetes": {
        "category": "metabolic",
        "overview": "A chronic condition affecting how the body processes blood sugar (glucose).",
        "causes": ["Insulin resistance", "Insufficient insulin production", "Genetic factors", "Obesity", "Physical inactivity"],
        "key_symptoms": ["Increased thirst and urination", "Fatigue", "Blurred vision", "Slow-healing wounds", "Frequent infections"],
        "diagnosis": ["HbA1c test (≥6.5%)", "Fasting blood glucose (≥126 mg/dL)", "OGTT"],
        "treatments": ["Lifestyle changes (diet, exercise)", "Metformin (first-line medication)", "Other oral/injectable medications", "Insulin therapy (advanced stages)"],
        "prevention": ["Healthy weight maintenance", "Regular physical activity", "Balanced diet low in refined carbs", "Regular blood sugar monitoring"],
        "specialists": ["Endocrinologist", "Diabetologist"],
    },
    "hypertension": {
        "category": "cardiovascular",
        "overview": "High blood pressure — a condition where blood force against artery walls is consistently too high.",
        "causes": ["Genetics", "Age", "Obesity", "High salt diet", "Physical inactivity", "Chronic stress", "Kidney disease"],
        "key_symptoms": ["Often asymptomatic (called 'silent killer')", "Headaches (in severe cases)", "Vision changes", "Shortness of breath"],
        "diagnosis": ["Blood pressure reading ≥130/80 mmHg on multiple occasions"],
        "treatments": ["Lifestyle modifications", "ACE inhibitors", "ARBs", "Beta-blockers", "Calcium channel blockers", "Diuretics"],
        "prevention": ["DASH diet", "Regular exercise", "Limit alcohol", "Quit smoking", "Stress management"],
        "specialists": ["Cardiologist", "Nephrologist"],
    },
    "migraine": {
        "category": "neurological",
        "overview": "A neurological condition causing recurring, severe headaches often with other symptoms.",
        "causes": ["Hormonal changes", "Certain foods/drinks", "Stress", "Sensory stimuli", "Genetics"],
        "key_symptoms": ["Throbbing/pulsating head pain (usually one side)", "Nausea/vomiting", "Sensitivity to light and sound", "Aura (visual disturbances)"],
        "diagnosis": ["Clinical history", "Neurological examination", "MRI/CT to rule out other causes"],
        "treatments": ["Pain relievers (NSAIDs, acetaminophen)", "Triptans", "CGRP inhibitors", "Preventive medications (beta-blockers, antidepressants)", "Lifestyle adjustments"],
        "prevention": ["Identify and avoid triggers", "Regular sleep schedule", "Stress management", "Regular meals"],
        "specialists": ["Neurologist", "Headache Specialist"],
    },
}

MEDICATION_DATABASE = {
    "metformin": {
        "drug_class": "Biguanide antidiabetic",
        "primary_uses": ["Type 2 diabetes management", "Prediabetes (sometimes)", "PCOS (off-label)"],
        "mechanism": "Reduces glucose production in the liver; improves insulin sensitivity",
        "common_side_effects": ["Nausea", "Diarrhea", "Stomach upset", "Metallic taste"],
        "serious_warnings": ["Lactic acidosis (rare but serious)", "Avoid in severe kidney disease"],
        "contraindications": ["Severe kidney impairment (eGFR < 30)", "Iodinated contrast dye procedures"],
        "interactions": ["Alcohol (increased lactic acidosis risk)", "Certain contrast agents"],
        "monitoring": ["Regular kidney function tests", "Vitamin B12 levels (long-term use)"],
    },
    "ibuprofen": {
        "drug_class": "NSAID (Non-steroidal anti-inflammatory drug)",
        "primary_uses": ["Pain relief", "Fever reduction", "Anti-inflammatory"],
        "mechanism": "Inhibits COX-1 and COX-2 enzymes, reducing prostaglandin synthesis",
        "common_side_effects": ["Stomach upset", "Heartburn", "Nausea"],
        "serious_warnings": ["GI bleeding", "Cardiovascular risk with long-term use", "Kidney damage with prolonged use"],
        "contraindications": ["Peptic ulcer disease", "Severe kidney or heart failure", "Aspirin allergy"],
        "interactions": ["Warfarin (increased bleeding)", "Lithium", "ACE inhibitors"],
        "monitoring": ["Kidney function with prolonged use", "Signs of GI bleeding"],
    },
    "aspirin": {
        "drug_class": "NSAID / Antiplatelet agent",
        "primary_uses": ["Pain/fever relief (standard dose)", "Heart attack and stroke prevention (low dose)", "Antiplatelet therapy"],
        "mechanism": "Irreversibly inhibits COX enzymes; inhibits platelet aggregation at low doses",
        "common_side_effects": ["Stomach irritation", "Nausea", "Tinnitus (high doses)"],
        "serious_warnings": ["GI bleeding", "Reye's syndrome in children with viral illness (NEVER give to children with flu/chickenpox)", "Allergic reactions"],
        "contraindications": ["Children with viral illness", "Active peptic ulcer", "Bleeding disorders"],
        "interactions": ["Warfarin (increased bleeding risk)", "Other NSAIDs", "Methotrexate"],
        "monitoring": ["Signs of bleeding", "Kidney function"],
    },
    "warfarin": {
        "drug_class": "Anticoagulant (blood thinner)",
        "primary_uses": ["Deep vein thrombosis prevention/treatment", "Atrial fibrillation stroke prevention", "Artificial heart valve patients"],
        "mechanism": "Inhibits Vitamin K-dependent clotting factors",
        "common_side_effects": ["Bleeding (the therapeutic effect)", "Easy bruising"],
        "serious_warnings": ["Severe bleeding risk", "Many drug and food interactions", "Narrow therapeutic index"],
        "contraindications": ["Active bleeding", "Pregnancy (teratogenic)", "Severe liver disease"],
        "interactions": ["MANY: NSAIDs, antibiotics, antifungals, vitamin K rich foods"],
        "monitoring": ["Regular INR blood tests (critical)", "Signs of bleeding"],
    },
}

DRUG_INTERACTION_DATABASE = {
    frozenset(["warfarin", "aspirin"]): {
        "severity": "HIGH",
        "interaction": "Significantly increases bleeding risk when combined.",
        "recommendation": "Avoid combination unless specifically prescribed. Discuss with doctor.",
    },
    frozenset(["warfarin", "ibuprofen"]): {
        "severity": "HIGH",
        "interaction": "NSAIDs increase anticoagulant effect and GI bleeding risk.",
        "recommendation": "Avoid. Use acetaminophen for pain if on warfarin.",
    },
    frozenset(["metformin", "ibuprofen"]): {
        "severity": "MODERATE",
        "interaction": "NSAIDs can reduce kidney function, affecting metformin clearance.",
        "recommendation": "Use with caution. Stay well hydrated. Short-term use generally acceptable.",
    },
    frozenset(["aspirin", "ibuprofen"]): {
        "severity": "MODERATE",
        "interaction": "Ibuprofen can block aspirin's cardioprotective antiplatelet effect.",
        "recommendation": "If taking low-dose aspirin for heart protection, take aspirin first and wait 30 minutes before ibuprofen.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Tool Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_emergency_contacts() -> dict:
    """Returns emergency contact numbers for major regions."""
    return {
        "India": {"emergency": "112", "ambulance": "108", "mental_health": "iCall: 9152987821"},
        "USA": {"emergency": "911", "poison_control": "1-800-222-1222", "crisis": "988"},
        "UK": {"emergency": "999", "NHS_advice": "111"},
        "EU": {"emergency": "112"},
        "Australia": {"emergency": "000"},
    }


def get_first_aid_guide(query: str) -> list:
    """Returns immediate first aid steps for common emergencies."""
    query_lower = query.lower()

    if any(kw in query_lower for kw in ["chest pain", "heart attack"]):
        return [
            "Call emergency services immediately (112/911/108)",
            "Have the person sit or lie in a comfortable position",
            "Loosen tight clothing around chest and neck",
            "If prescribed, give nitroglycerin under the tongue",
            "If person is unresponsive and not breathing, begin CPR",
            "Give aspirin (325mg) if not allergic and not contraindicated",
        ]
    elif any(kw in query_lower for kw in ["stroke", "face drooping"]):
        return [
            "Use FAST test: Face drooping, Arm weakness, Speech difficulty → Time to call 911/112",
            "Call emergency services immediately — every minute matters in stroke",
            "Note the time symptoms started — critical for treatment decisions",
            "Do NOT give food, water, or medications",
            "Keep the person calm and still",
            "If unconscious, place in recovery position",
        ]
    elif any(kw in query_lower for kw in ["bleeding", "wound"]):
        return [
            "Apply firm, direct pressure with a clean cloth",
            "Do not remove the cloth — add more on top if it soaks through",
            "Elevate the injured area above heart level if possible",
            "Call emergency services if bleeding is severe or won't stop",
            "Do not use a tourniquet unless trained to do so",
        ]
    else:
        return [
            "Call emergency services: 112 (India/EU), 911 (USA), 999 (UK)",
            "Stay calm and keep the person comfortable",
            "Do not move the person if spinal injury is suspected",
            "Stay on the line with emergency services for guidance",
        ]


def lookup_symptom_patterns(symptom_list: list) -> dict:
    """Looks up symptom patterns from the medical knowledge base."""
    patterns = {}
    for symptom in symptom_list:
        for db_symptom, data in SYMPTOM_DATABASE.items():
            if db_symptom in symptom or symptom in db_symptom:
                patterns[symptom] = data
                break
    return patterns


def calculate_risk_factors(
    symptoms: list,
    duration: str,
    severity: str,
    age_group: str,
    existing_conditions: str,
) -> dict:
    """Calculates aggregate risk level from multiple factors."""
    base_urgency = 1
    risk_factors = []

    # Symptom-based urgency
    for symptom in symptoms:
        for db_symptom, data in SYMPTOM_DATABASE.items():
            if db_symptom in symptom or symptom in db_symptom:
                base_urgency = max(base_urgency, data["urgency_base"])

    # Duration modifier
    if "week" in duration.lower() or "month" in duration.lower():
        risk_factors.append("Extended duration suggests need for medical evaluation")

    # Severity modifier
    severity_map = {"mild": 0, "moderate": 1, "severe": 2}
    severity_boost = severity_map.get(severity.lower(), 1)
    base_urgency = min(5, base_urgency + (severity_boost // 2))

    # Age risk modifier
    if age_group.lower() in ["elderly", "senior", "child", "infant", "baby"]:
        base_urgency = min(5, base_urgency + 1)
        risk_factors.append(f"Age group ({age_group}) may require more cautious assessment")

    # Existing conditions modifier
    if existing_conditions.lower() not in ["none", "n/a", "unknown", ""]:
        risk_factors.append(f"Pre-existing conditions ({existing_conditions}) may affect assessment")

    urgency_labels = {
        1: ("GREEN", "Non-urgent — Self-care appropriate"),
        2: ("YELLOW", "Semi-urgent — See doctor within 48-72 hours"),
        3: ("ORANGE", "Urgent — Medical attention within 24 hours"),
        4: ("ORANGE-RED", "Very Urgent — Same-day emergency care"),
        5: ("RED", "EMERGENCY — Call emergency services NOW"),
    }

    level_color, level_desc = urgency_labels.get(base_urgency, urgency_labels[2])

    return {
        "urgency_level": base_urgency,
        "triage_color": level_color,
        "description": level_desc,
        "risk_factors": risk_factors,
    }


def format_triage_response(symptoms: list, patterns: dict, risk: dict, duration: str, severity: str) -> dict:
    """Formats the complete triage assessment response."""
    all_conditions = set()
    all_red_flags = []

    for symptom_data in patterns.values():
        all_conditions.update(symptom_data.get("associated_conditions", []))
        all_red_flags.extend(symptom_data.get("red_flags", []))

    action_map = {
        1: "Rest, hydrate, monitor symptoms. Visit GP if not improving in 3-5 days.",
        2: "Schedule a GP appointment within 48-72 hours. Monitor for worsening.",
        3: "Seek medical attention today. Visit urgent care or call your doctor.",
        4: "Go to emergency room or call emergency services. Do not delay.",
        5: "CALL EMERGENCY SERVICES IMMEDIATELY. This is a medical emergency.",
    }

    return {
        "triage_level": risk["urgency_level"],
        "triage_color": risk["triage_color"],
        "urgency_description": risk["description"],
        "symptoms_assessed": symptoms,
        "duration": duration,
        "severity": severity,
        "possible_condition_categories": list(all_conditions)[:5],  # Top 5 only
        "red_flags_to_watch": all_red_flags[:5],
        "recommended_action": action_map.get(risk["urgency_level"], action_map[2]),
        "risk_modifiers": risk["risk_factors"],
        "disclaimer": (
            "⚠️ This is an AI-generated triage assessment for informational purposes only. "
            "It is NOT a medical diagnosis. Always consult a qualified healthcare professional "
            "for medical advice, diagnosis, or treatment."
        ),
    }


def validate_health_query(query: str) -> dict:
    """Validates that the query is appropriate for a health assistant."""
    if len(query.strip()) < 5:
        return {"is_valid": False, "reason": "Query too short. Please provide more detail."}

    if len(query) > 2000:
        return {"is_valid": False, "reason": "Query too long. Please summarize your question."}

    return {"is_valid": True, "sanitized_input": query.strip(), "reason": "Valid health query"}


def check_drug_interactions(drug_list: list) -> dict:
    """Checks a list of drugs for known interactions and therapeutic duplications."""
    warnings = []
    drug_list_lower = [d.lower().strip() for d in drug_list]

    # Brand to generic active ingredient mappings for clinical intelligence
    brand_mappings = {
        "trimox": "amoxicillin",
        "timox": "amoxicillin",
        "amoxil": "amoxicillin",
        "advil": "ibuprofen",
        "motrin": "ibuprofen",
        "coumadin": "warfarin",
    }

    # Normalize drug list to active ingredients
    resolved_drugs = []
    for d in drug_list_lower:
        resolved = brand_mappings.get(d, d)
        resolved_drugs.append((d, resolved))

    # 1. Check for Therapeutic Duplications (e.g. Amoxicillin + Trimox)
    for i, (orig1, gen1) in enumerate(resolved_drugs):
        for j, (orig2, gen2) in enumerate(resolved_drugs[i+1:]):
            if gen1 == gen2:
                warnings.append({
                    "drug_pair": f"{orig1} + {orig2}",
                    "severity": "CRITICAL / OVERDOSE RISK",
                    "interaction": f"Therapeutic Duplication detected. Both contain the active ingredient '{gen1}'.",
                    "recommendation": f"DO NOT take '{orig1}' and '{orig2}' together. This represents double-dosing of the same active drug.",
                })

    # 2. Check for Drug-Drug Interactions
    for i, (orig1, gen1) in enumerate(resolved_drugs):
        for j, (orig2, gen2) in enumerate(resolved_drugs[i+1:]):
            if gen1 == gen2:
                continue # Already handled in duplication
            pair = frozenset([gen1, gen2])
            if pair in DRUG_INTERACTION_DATABASE:
                interaction = DRUG_INTERACTION_DATABASE[pair]
                warnings.append({
                    "drug_pair": f"{orig1} + {orig2}",
                    "severity": interaction["severity"],
                    "interaction": interaction["interaction"],
                    "recommendation": interaction["recommendation"],
                })

    return {
        "drugs_checked": drug_list,
        "interactions_found": len(warnings),
        "warnings": warnings,
        "disclaimer": "This is not a complete interaction checker. Always consult your pharmacist.",
        "no_interaction_note": "No interactions found does not mean the combination is safe. Check with your pharmacist." if not warnings else "",
    }


def get_condition_overview(condition_name: str, detail_level: str = "standard") -> dict:
    """Retrieves condition information from the medical database."""
    condition_lower = condition_name.lower()

    for db_condition, data in CONDITION_DATABASE.items():
        if condition_lower in db_condition or db_condition in condition_lower:
            if detail_level == "brief":
                return {
                    "condition": db_condition,
                    "overview": data["overview"],
                    "key_symptoms": data["key_symptoms"][:3],
                    "specialists": data["specialists"],
                }
            return {
                "condition": db_condition,
                **data,
                "source": "MediGuide Medical Knowledge Base (educational purposes only)",
                "disclaimer": "This information is for educational purposes. Consult your doctor for personalized advice.",
            }

    return {
        "condition": condition_name,
        "status": "not_in_database",
        "message": f"Detailed information for '{condition_name}' is not in our current knowledge base. I recommend consulting PubMed (pubmed.ncbi.nlm.nih.gov) or speaking with your doctor.",
        "general_advice": "For any health condition, consulting a qualified healthcare professional is always the best first step.",
    }


def get_medication_info(medication_name: str) -> dict:
    """Retrieves medication information from the database."""
    med_lower = medication_name.lower().strip()

    if med_lower in MEDICATION_DATABASE:
        return {
            "medication": medication_name,
            **MEDICATION_DATABASE[med_lower],
            "dosing_note": "⚠️ Dosing information is NOT provided — always follow your doctor's prescription or package insert.",
            "disclaimer": "Educational information only. Consult your pharmacist or physician for personalized advice.",
        }

    return {
        "medication": medication_name,
        "status": "not_in_database",
        "message": f"Specific information for '{medication_name}' is not in our database.",
        "recommendation": "Consult your pharmacist for complete information about this medication.",
    }


def get_treatment_options(condition: str, patient_context: str = "") -> dict:
    """Returns treatment overview for a condition."""
    condition_data = get_condition_overview(condition)

    if condition_data.get("status") == "not_in_database":
        return condition_data

    return {
        "condition": condition,
        "treatments": condition_data.get("treatments", []),
        "lifestyle_modifications": [
            t for t in condition_data.get("treatments", [])
            if any(kw in t.lower() for kw in ["lifestyle", "diet", "exercise", "weight"])
        ],
        "context_note": f"Note for {patient_context}: Treatment options may vary based on individual factors." if patient_context else "",
        "disclaimer": "Treatment decisions should always be made with your healthcare provider.",
    }


def get_preventive_guidelines(health_topic: str) -> dict:
    """Returns preventive health guidelines for a topic."""
    return {
        "topic": health_topic,
        "general_guidelines": [
            "Regular check-ups with your primary care physician",
            "Maintain a healthy weight (BMI 18.5-24.9)",
            "Exercise at least 150 minutes of moderate activity per week",
            "Eat a balanced diet rich in fruits, vegetables, and whole grains",
            "Avoid smoking and limit alcohol consumption",
            "Manage stress through mindfulness, exercise, or counseling",
            "Get adequate sleep (7-9 hours for adults)",
            "Stay up-to-date with recommended vaccinations",
            "Know your family health history",
        ],
        "source": "Based on WHO and major public health organization guidelines",
        "disclaimer": "For personalized prevention advice, consult your healthcare provider.",
    }


def get_specialist_recommendation(condition_or_symptoms: str) -> dict:
    """Recommends appropriate specialist types."""
    text_lower = condition_or_symptoms.lower()

    specialist_map = {
        ("heart", "chest", "blood pressure", "cardiovascular", "cardiac"): "Cardiologist",
        ("brain", "headache", "migraine", "neurological", "seizure", "stroke", "nerve"): "Neurologist",
        ("diabetes", "thyroid", "hormone", "metabolism", "endocrine"): "Endocrinologist",
        ("skin", "rash", "acne", "dermatitis", "psoriasis"): "Dermatologist",
        ("bone", "joint", "arthritis", "fracture", "muscle"): "Orthopedist / Rheumatologist",
        ("mental", "anxiety", "depression", "psychiatric", "mood"): "Psychiatrist / Psychologist",
        ("eye", "vision", "retina"): "Ophthalmologist",
        ("ear", "hearing", "sinus", "throat", "nose"): "ENT (Ear, Nose, Throat) Specialist",
        ("lung", "breathing", "asthma", "respiratory", "copd"): "Pulmonologist",
        ("stomach", "digestive", "bowel", "liver", "gastro"): "Gastroenterologist",
        ("kidney", "urine", "bladder", "renal"): "Nephrologist / Urologist",
        ("cancer", "tumor", "oncology", "lymphoma"): "Oncologist",
    }

    recommended = "General Practitioner (GP) / Primary Care Physician"
    for keywords, specialist in specialist_map.items():
        if any(kw in text_lower for kw in keywords):
            recommended = specialist
            break

    return {
        "condition_or_symptoms": condition_or_symptoms,
        "recommended_specialist": recommended,
        "first_step": "Start with your General Practitioner (GP) who can provide a referral.",
        "questions_to_ask": [
            f"What could be causing my {condition_or_symptoms}?",
            "What diagnostic tests do you recommend?",
            "Do I need a specialist referral?",
            "What should I monitor at home?",
            "When should I seek emergency care?",
        ],
        "tip": "Bring a written list of symptoms, duration, and current medications to your appointment.",
    }


def get_body_system_info(body_area: str) -> dict:
    """Returns health information about a specific body system."""
    body_systems = {
        "cardiovascular": {
            "common_conditions": ["Hypertension", "Coronary artery disease", "Heart failure", "Arrhythmias"],
            "warning_signs": ["Chest pain/pressure", "Shortness of breath", "Palpitations", "Ankle swelling"],
            "self_care": ["Regular exercise", "Heart-healthy diet", "No smoking", "Limit alcohol", "Stress management"],
        },
        "respiratory": {
            "common_conditions": ["Asthma", "COPD", "Pneumonia", "Bronchitis", "Allergies"],
            "warning_signs": ["Persistent cough", "Wheezing", "Coughing blood", "Shortness of breath at rest"],
            "self_care": ["No smoking", "Avoid air pollutants", "Vaccinations (flu, pneumococcal)", "Exercise"],
        },
        "digestive": {
            "common_conditions": ["GERD", "IBS", "Peptic ulcer", "IBD", "Gallstones"],
            "warning_signs": ["Persistent abdominal pain", "Blood in stool", "Unexplained weight loss", "Difficulty swallowing"],
            "self_care": ["Balanced diet", "Adequate fiber", "Stay hydrated", "Limit processed foods"],
        },
        "neurological": {
            "common_conditions": ["Migraine", "Epilepsy", "Parkinson's disease", "Multiple sclerosis"],
            "warning_signs": ["Severe sudden headache", "Vision changes", "Weakness or numbness", "Coordination problems"],
            "self_care": ["Regular sleep", "Stress management", "Mental stimulation", "Regular exercise"],
        },
    }

    area_lower = body_area.lower()
    for system, info in body_systems.items():
        if system in area_lower or area_lower in system:
            return {"body_system": system, **info}

    return {
        "body_system": body_area,
        "message": "Consult your doctor for specific information about this body area.",
        "general_advice": "Regular health check-ups are the best way to monitor all body systems.",
    }


def search_medical_database(query: str, source_preference: str = "peer_reviewed") -> dict:
    """Searches the medical knowledge base with a free-text query."""
    query_lower = query.lower()
    results = []

    # Search conditions
    for condition, data in CONDITION_DATABASE.items():
        if any(term in query_lower for term in condition.split()) or condition in query_lower:
            results.append({
                "type": "condition",
                "name": condition,
                "relevance": "high",
                "summary": data["overview"],
            })

    # Search medications
    for medication, data in MEDICATION_DATABASE.items():
        if medication in query_lower:
            results.append({
                "type": "medication",
                "name": medication,
                "relevance": "high",
                "summary": f"{data['drug_class']}: used for {', '.join(data['primary_uses'][:2])}",
            })

    # Search symptoms
    for symptom, data in SYMPTOM_DATABASE.items():
        if symptom in query_lower:
            results.append({
                "type": "symptom_pattern",
                "name": symptom,
                "relevance": "medium",
                "summary": f"May be associated with: {', '.join(data['associated_conditions'][:3])}",
            })

    return {
        "query": query,
        "results_count": len(results),
        "results": results[:5],  # Limit to top 5
        "source_quality": source_preference,
        "confidence": "high" if results else "low",
        "disclaimer": "Search results are from curated medical knowledge base for educational purposes.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Health Risk Score Engine
# ─────────────────────────────────────────────────────────────────────────────

def compute_health_risk_score(
    symptoms: list,
    duration: str,
    severity: str,
    age: int,
    gender: str,
    existing_conditions: str,
    red_flags: list = None,
) -> dict:
    """
    Computes a quantified Health Risk Score (1-100) using a weighted multi-factor
    clinical algorithm. This transforms vague triage colors into a measurable,
    defensible clinical risk metric.

    Scoring Factors:
      - Symptom Urgency Base (0-35 pts)
      - Symptom Count (0-10 pts)
      - Duration (0-10 pts)
      - Severity (0-15 pts)
      - Age Risk (0-10 pts)
      - Existing Conditions (0-10 pts)
      - Red Flag Multiplier (0-10 pts bonus)

    Args:
        symptoms: List of symptom strings (e.g., ["chest pain", "shortness of breath"]).
        duration: Duration string (e.g., "2 days", "3 weeks").
        severity: "mild", "moderate", or "severe".
        age: Patient age in years.
        gender: "male", "female", or "unknown".
        existing_conditions: String of pre-existing conditions (e.g., "diabetes, hypertension").
        red_flags: Optional list of detected red flag symptoms.

    Returns:
        dict with score (1-100), risk_tier, gauge_display, contributing_factors, and recommendations.
    """
    score = 0
    factors = []
    red_flags = red_flags or []

    # ── Factor 1: Symptom Urgency Base (max 35 pts) ──────────────────────────
    max_urgency = 1
    matched_symptoms = []
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        for db_symptom, data in SYMPTOM_DATABASE.items():
            if db_symptom in symptom_lower or symptom_lower in db_symptom:
                matched_symptoms.append(db_symptom)
                max_urgency = max(max_urgency, data["urgency_base"])
                break

    # Emergency symptoms override
    emergency_keywords = ["chest pain", "heart attack", "stroke", "can't breathe",
                          "difficulty breathing", "unconscious", "severe bleeding",
                          "seizure", "anaphylaxis", "overdose"]
    for s in symptoms:
        if any(kw in s.lower() for kw in emergency_keywords):
            max_urgency = 5
            break

    urgency_score = {1: 7, 2: 14, 3: 21, 4: 28, 5: 35}.get(max_urgency, 14)
    score += urgency_score
    factors.append({
        "factor": "Symptom Urgency",
        "points": urgency_score,
        "detail": f"Urgency level {max_urgency}/5 based on {len(symptoms)} symptom(s)",
    })

    # ── Factor 2: Symptom Count (max 10 pts) ─────────────────────────────────
    count_pts = min(10, len(symptoms) * 2)
    score += count_pts
    if count_pts > 0:
        factors.append({
            "factor": "Symptom Count",
            "points": count_pts,
            "detail": f"{len(symptoms)} symptoms reported (multiple symptoms = higher concern)",
        })

    # ── Factor 3: Duration (max 10 pts) ──────────────────────────────────────
    duration_lower = duration.lower()
    duration_pts = 3  # default
    if any(x in duration_lower for x in ["month", "year", "chronic"]):
        duration_pts = 10
        dur_label = "Chronic (months/years)"
    elif any(x in duration_lower for x in ["week", "weeks"]):
        duration_pts = 7
        dur_label = "Extended (weeks)"
    elif any(x in duration_lower for x in ["day", "days"]):
        duration_pts = 4
        dur_label = "Short (days)"
    elif any(x in duration_lower for x in ["hour", "hours", "sudden", "sudden onset"]):
        duration_pts = 8  # Sudden onset = higher risk for some conditions
        dur_label = "Sudden onset"
    else:
        dur_label = "Unknown duration"

    score += duration_pts
    factors.append({
        "factor": "Duration",
        "points": duration_pts,
        "detail": dur_label,
    })

    # ── Factor 4: Severity (max 15 pts) ──────────────────────────────────────
    severity_map = {"mild": 3, "moderate": 9, "severe": 15}
    sev_pts = severity_map.get(severity.lower(), 9)
    score += sev_pts
    factors.append({
        "factor": "Reported Severity",
        "points": sev_pts,
        "detail": f"Patient-reported severity: {severity}",
    })

    # ── Factor 5: Age Risk (max 10 pts) ──────────────────────────────────────
    if age >= 75:
        age_pts = 10
        age_label = "Very elderly (75+) — highest risk"
    elif age >= 65:
        age_pts = 7
        age_label = "Elderly (65-74) — elevated risk"
    elif age >= 50:
        age_pts = 4
        age_label = "Middle-aged (50-64) — moderate risk"
    elif age <= 5 or age <= 2:
        age_pts = 8
        age_label = "Infant/young child — elevated risk"
    elif age <= 12:
        age_pts = 5
        age_label = "Child — moderate risk"
    else:
        age_pts = 1
        age_label = "Adult (13-49) — baseline risk"

    score += age_pts
    factors.append({
        "factor": "Age Risk",
        "points": age_pts,
        "detail": age_label,
    })

    # ── Factor 6: Existing Conditions (max 10 pts) ───────────────────────────
    high_risk_conditions = [
        "diabetes", "heart disease", "cardiac", "cancer", "hiv", "aids",
        "copd", "asthma", "kidney disease", "liver disease", "immunocompromised",
        "hypertension", "stroke", "autoimmune", "transplant",
    ]
    conditions_lower = existing_conditions.lower()
    matched_conditions = [c for c in high_risk_conditions if c in conditions_lower]
    cond_pts = min(10, len(matched_conditions) * 4)
    if conditions_lower not in ["none", "n/a", "unknown", ""]:
        cond_pts = max(cond_pts, 3)  # At least 3 pts if any condition mentioned

    score += cond_pts
    if cond_pts > 0:
        factors.append({
            "factor": "Pre-existing Conditions",
            "points": cond_pts,
            "detail": f"Risk-elevating conditions: {', '.join(matched_conditions) if matched_conditions else existing_conditions}",
        })

    # ── Factor 7: Red Flags Bonus (max 10 pts) ───────────────────────────────
    red_flag_keywords = [
        "chest pain", "difficulty breathing", "sudden severe headache",
        "loss of consciousness", "paralysis", "vision loss", "blood in stool",
        "coughing blood", "severe abdominal pain", "high fever",
    ]
    detected_red_flags = []
    for symptom in symptoms:
        for flag in red_flag_keywords:
            if flag in symptom.lower():
                detected_red_flags.append(flag)
    detected_red_flags += [f for f in red_flags if f]

    red_flag_pts = min(10, len(set(detected_red_flags)) * 5)
    score += red_flag_pts
    if red_flag_pts > 0:
        factors.append({
            "factor": "Red Flag Symptoms",
            "points": red_flag_pts,
            "detail": f"Red flags detected: {', '.join(list(set(detected_red_flags))[:3])}",
        })


    # Cap score at 100
    score = min(100, score)

    # ── Risk Tier Classification ──────────────────────────────────────────────
    if score >= 80:
        risk_tier = "CRITICAL"
        tier_color = "RED"
        recommendation = "SEEK EMERGENCY CARE IMMEDIATELY. Call 112/108/911 or go to the nearest ER."
    elif score >= 60:
        risk_tier = "HIGH"
        tier_color = "ORANGE"
        recommendation = "Seek medical attention TODAY. Visit urgent care or call your doctor immediately."
    elif score >= 40:
        risk_tier = "MODERATE"
        tier_color = "YELLOW"
        recommendation = "Schedule a GP appointment within 24-48 hours. Monitor symptoms closely."
    elif score >= 20:
        risk_tier = "LOW-MODERATE"
        tier_color = "YELLOW-GREEN"
        recommendation = "Monitor symptoms. Visit GP within 3-5 days if no improvement."
    else:
        risk_tier = "LOW"
        tier_color = "GREEN"
        recommendation = "Likely self-limiting. Rest, hydrate, and monitor. Visit GP if symptoms worsen."

    # ── ASCII Gauge Display ───────────────────────────────────────────────────
    filled = int(score / 5)  # 20 segments for 100 score
    empty = 20 - filled
    gauge = f"[{'#' * filled}{'.' * empty}] {score}/100"

    return {
        "health_risk_score": score,
        "risk_tier": risk_tier,
        "triage_color": tier_color,
        "gauge_display": gauge,
        "contributing_factors": factors,
        "recommendation": recommendation,
        "matched_symptoms": matched_symptoms,
        "detected_red_flags": list(set(detected_red_flags)),
        "disclaimer": (
            "This Health Risk Score is a decision-support tool based on reported symptoms only. "
            "It is NOT a medical diagnosis. Always consult a qualified healthcare professional."
        ),
    }
