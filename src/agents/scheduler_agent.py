"""
MediGuide AI - Scheduler Agent
================================
Specialist sub-agent responsible for health scheduling intelligence:
  - Medication reminders with intelligent timing
  - Appointment tracking and preparation
  - Follow-up care coordination
  - Preventive health screening reminders
  - Health goal tracking

Design Pattern: Sub-agent of OrchestratorAgent.
Invoked when user asks about reminders, appointments, or tracking.

Storage: Uses in-memory schedule store (can be extended to DB/Google Calendar).
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from google.adk.agents import Agent
from google.adk.tools import FunctionTool


# ─────────────────────────────────────────────────────────────────────────────
# In-Memory Schedule Store (session-scoped)
# In production: connect to a database or Google Calendar API
# ─────────────────────────────────────────────────────────────────────────────
_schedule_store: dict = {
    "medications": [],
    "appointments": [],
    "reminders": [],
    "health_goals": [],
}


def add_medication_reminder(
    medication_name: str,
    dosage_description: str,
    frequency: str,
    start_date: str = "today",
    notes: str = "",
) -> dict:
    """
    Creates a medication reminder entry in the health schedule.

    Args:
        medication_name: Name of the medication (generic or brand).
        dosage_description: Descriptive dosage info (e.g., "as prescribed by doctor").
                            NOTE: We do not store specific dosages for safety.
        frequency: How often to take (e.g., "twice daily", "every 8 hours", "weekly").
        start_date: When to start — "today", "tomorrow", or ISO date "2024-01-15".
        notes: Any additional notes (e.g., "take with food", "avoid sunlight").

    Returns:
        dict with reminder_id, medication_name, schedule_summary, and next_reminder_time.

    Security Note: Dosage details are not stored — users must follow their prescription label.
    """
    reminder_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()

    entry = {
        "id": reminder_id,
        "type": "medication",
        "medication": medication_name,
        "dosage_description": dosage_description,  # descriptive only, not medical advice
        "frequency": frequency,
        "start_date": start_date,
        "notes": notes,
        "created_at": created_at,
        "active": True,
    }

    _schedule_store["medications"].append(entry)

    return {
        "status": "created",
        "reminder_id": reminder_id,
        "medication": medication_name,
        "frequency": frequency,
        "schedule_summary": f"Reminder set for {medication_name} — {frequency}",
        "next_reminder_time": "Based on your frequency, set an alarm on your device.",
        "tips": [
            f"Set recurring phone alarms for '{medication_name}'",
            "Use pill organizers for daily medications",
            "Enable notification in your preferred health app",
        ],
        "important": "Always follow your doctor's or pharmacist's exact instructions.",
    }


def schedule_appointment(
    appointment_type: str,
    doctor_or_facility: str,
    preferred_date: str,
    reason: str,
    priority: str = "routine",
) -> dict:
    """
    Schedules a healthcare appointment and provides preparation guidance.

    Args:
        appointment_type: Type of appointment (e.g., "GP visit", "specialist", "lab test").
        doctor_or_facility: Doctor name or healthcare facility.
        preferred_date: Preferred date in ISO format or natural language.
        reason: Reason for the appointment.
        priority: "routine" | "urgent" | "follow-up".

    Returns:
        dict with appointment_id, preparation_checklist, questions_to_ask, and reminders.
    """
    appt_id = str(uuid.uuid4())[:8]
    created_at = datetime.now().isoformat()

    # Generate smart preparation checklist based on appointment type
    prep_checklist = _get_appointment_prep(appointment_type, reason)

    entry = {
        "id": appt_id,
        "type": "appointment",
        "appointment_type": appointment_type,
        "doctor_or_facility": doctor_or_facility,
        "preferred_date": preferred_date,
        "reason": reason,
        "priority": priority,
        "created_at": created_at,
        "status": "scheduled",
    }

    _schedule_store["appointments"].append(entry)

    return {
        "status": "scheduled",
        "appointment_id": appt_id,
        "summary": f"{appointment_type} with {doctor_or_facility} on {preferred_date}",
        "priority": priority,
        "preparation_checklist": prep_checklist,
        "questions_to_prepare": _generate_appointment_questions(appointment_type, reason),
        "reminders": [
            "Set a reminder 24 hours before your appointment",
            "Set a reminder 2 hours before to prepare and travel",
            "Confirm the appointment the day before",
        ],
        "what_to_bring": [
            "Photo ID and insurance card",
            "List of current medications",
            "Previous test results (if any)",
            "List of symptoms and duration",
            "Emergency contact information",
        ],
    }


def list_schedule() -> dict:
    """
    Returns the complete health schedule including medications, appointments, and reminders.

    Returns:
        dict with all active schedule entries organized by category.
    """
    active_medications = [m for m in _schedule_store["medications"] if m.get("active")]
    upcoming_appointments = _schedule_store["appointments"]
    active_reminders = _schedule_store["reminders"]

    return {
        "schedule_summary": {
            "active_medications": len(active_medications),
            "upcoming_appointments": len(upcoming_appointments),
            "active_reminders": len(active_reminders),
        },
        "medications": active_medications,
        "appointments": upcoming_appointments,
        "reminders": active_reminders,
        "health_goals": _schedule_store["health_goals"],
        "generated_at": datetime.now().isoformat(),
    }


def add_health_goal(
    goal: str,
    target_date: str,
    metric: str = "",
    tracking_frequency: str = "weekly",
) -> dict:
    """
    Adds a health goal to the tracker (e.g., weight loss, exercise, hydration).

    Args:
        goal: Description of the health goal.
        target_date: Target completion date.
        metric: How to measure progress (e.g., "steps per day", "kg", "hours of sleep").
        tracking_frequency: How often to check in — "daily" | "weekly" | "monthly".

    Returns:
        dict with goal_id, milestones, and tips for success.
    """
    goal_id = str(uuid.uuid4())[:8]

    entry = {
        "id": goal_id,
        "goal": goal,
        "target_date": target_date,
        "metric": metric,
        "tracking_frequency": tracking_frequency,
        "created_at": datetime.now().isoformat(),
        "progress": "just_started",
    }

    _schedule_store["health_goals"].append(entry)

    return {
        "status": "created",
        "goal_id": goal_id,
        "goal": goal,
        "target_date": target_date,
        "tips": [
            "Track progress in a health journal or app",
            "Start with small, achievable milestones",
            "Celebrate progress, not just outcomes",
            "Share your goal with a supportive friend or family member",
        ],
        "recommended_apps": [
            "Google Fit — general health tracking",
            "MyFitnessPal — nutrition and exercise",
            "Headspace — mental wellness",
        ],
    }


def get_preventive_screening_schedule(age: int, biological_sex: str) -> dict:
    """
    Generates a personalized preventive health screening schedule based on age and sex.
    Based on standard clinical guidelines (WHO, CDC, NHS).

    Args:
        age: Patient's age in years.
        biological_sex: "male" | "female" | "intersex".

    Returns:
        dict with recommended_screenings organized by urgency.
    """
    screenings = []

    # Universal screenings by age
    if age >= 18:
        screenings.append({"test": "Blood Pressure", "frequency": "Every 2 years", "urgency": "routine"})
        screenings.append({"test": "Blood Sugar / HbA1c", "frequency": "Every 3 years", "urgency": "routine"})

    if age >= 35:
        screenings.append({"test": "Cholesterol Panel", "frequency": "Every 5 years", "urgency": "routine"})
        screenings.append({"test": "Diabetes Screening", "frequency": "Every 3 years", "urgency": "routine"})

    if age >= 45:
        screenings.append({"test": "Colorectal Cancer Screening", "frequency": "Every 10 years", "urgency": "important"})

    if age >= 65:
        screenings.append({"test": "Bone Density (DEXA)", "frequency": "Every 2 years", "urgency": "important"})

    # Sex-specific screenings
    if biological_sex.lower() == "female":
        if 21 <= age <= 65:
            screenings.append({"test": "Pap Smear (Cervical Cancer)", "frequency": "Every 3 years", "urgency": "important"})
        if age >= 40:
            screenings.append({"test": "Mammogram (Breast Cancer)", "frequency": "Every 2 years", "urgency": "important"})

    if biological_sex.lower() == "male":
        if age >= 50:
            screenings.append({"test": "PSA Test (Prostate)", "frequency": "Discuss with doctor", "urgency": "discuss"})

    return {
        "age": age,
        "biological_sex": biological_sex,
        "recommended_screenings": screenings,
        "disclaimer": "These are general guidelines. Your doctor may recommend different timing based on your personal risk factors.",
        "source": "Based on WHO, CDC, and NHS preventive care guidelines",
    }


# ─── Helper functions ────────────────────────────────────────────────────────

def _get_appointment_prep(appointment_type: str, reason: str) -> list:
    """Returns a preparation checklist tailored to the appointment type."""
    base = ["Fast for 8–12 hours if blood work is involved", "Wear comfortable clothing"]
    type_lower = appointment_type.lower()

    if "specialist" in type_lower or "cardiolog" in type_lower:
        base.extend(["Bring ECG/Echo reports if available", "List all symptoms with dates"])
    elif "lab" in type_lower or "blood" in type_lower:
        base.extend(["Confirm fasting requirements with lab", "Stay hydrated before the test"])
    elif "dental" in type_lower:
        base.extend(["Brush and floss before appointment", "List any dental concerns"])
    elif "eye" in type_lower or "ophth" in type_lower:
        base.extend(["Bring current glasses/contacts", "Arrange transport — eyes may be dilated"])

    base.append(f"Prepare a summary of why you're going: '{reason}'")
    return base


def _generate_appointment_questions(appointment_type: str, reason: str) -> list:
    """Generates smart questions for the patient to ask their doctor."""
    return [
        f"What could be causing {reason}?",
        "What tests do you recommend and why?",
        "What are my treatment options and their side effects?",
        "Are there lifestyle changes that could help?",
        "When should I follow up or call if things get worse?",
        "Are there any red flag symptoms I should watch for?",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler Agent Definition
# ─────────────────────────────────────────────────────────────────────────────
scheduler_agent = Agent(
    name="SchedulerAgent",
    model="gemini-2.0-flash",

    instruction="""
You are the MediGuide Health Scheduler — an AI agent that helps users organize
their healthcare journey through smart scheduling, reminders, and health goal tracking.

## Your Capabilities
1. **Medication Reminders** → add_medication_reminder() for tracking medications
2. **Appointment Scheduling** → schedule_appointment() for doctor visits and tests
3. **Schedule Overview** → list_schedule() to show all health events
4. **Health Goals** → add_health_goal() for wellness objectives
5. **Preventive Screening** → get_preventive_screening_schedule() for age-appropriate screenings

## Conversation Flow
1. Understand what the user wants to schedule or track
2. Ask for necessary details (what, when, frequency)
3. Create the schedule entry using the appropriate tool
4. Confirm the entry and provide helpful tips
5. Suggest related scheduling (e.g., if they set a medication reminder, suggest scheduling the follow-up appointment)

## Tone
- Organized, helpful, and encouraging
- Proactively offer related suggestions
- Celebrate when users are being proactive about their health

## Important Safety Note
- For medications: ALWAYS remind users to follow their doctor's exact prescription
- Never modify or override prescribed medication schedules
""",

    tools=[
        FunctionTool(func=add_medication_reminder),
        FunctionTool(func=schedule_appointment),
        FunctionTool(func=list_schedule),
        FunctionTool(func=add_health_goal),
        FunctionTool(func=get_preventive_screening_schedule),
    ],
)
