"""
MediGuide AI - Medication Reminder Skill
==========================================
An Agent Skill for intelligent medication reminder management.
Compatible with Agents CLI for standalone invocation.

This skill provides:
  - Smart medication scheduling based on timing preferences
  - Adherence tips personalized to medication type
  - Side effect monitoring reminders
  - Refill alerts based on supply estimation
  - Export to calendar-compatible format (iCal/JSON)

Usage (Agents CLI):
  agents skills run medication_reminder --input '{"medication": "metformin", "frequency": "twice daily"}'

Usage (Python):
  from skills.medication_reminder import MedicationReminderSkill
  skill = MedicationReminderSkill()
  result = skill.create_reminder("metformin", "twice daily", notes="take with meals")
"""

import json
import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

# Add parent directory for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────────────────────────────────────
# Skill Metadata
# ─────────────────────────────────────────────────────────────────────────────
SKILL_METADATA = {
    "name": "medication_reminder",
    "version": "1.0.0",
    "description": "Intelligent medication reminder and adherence management skill",
    "author": "MediGuide AI Team",
    "category": "healthcare",
    "inputs": {
        "medication": {"type": "string", "required": True, "description": "Medication name"},
        "frequency": {"type": "string", "required": True, "description": "How often to take (e.g., 'twice daily', 'every 8 hours')"},
        "notes": {"type": "string", "required": False, "description": "Additional notes (e.g., 'take with food')"},
        "start_date": {"type": "string", "required": False, "default": "today"},
        "duration_days": {"type": "integer", "required": False, "description": "Treatment duration in days (optional)"},
    },
    "outputs": {
        "reminder_id": "string",
        "schedule": "list of suggested reminder times",
        "adherence_tips": "list",
        "side_effect_monitoring": "list",
        "export_formats": "list",
    },
    "safety_level": "advisory",
    "disclaimer": "Always follow your doctor's or pharmacist's exact instructions.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Frequency Parser
# ─────────────────────────────────────────────────────────────────────────────
FREQUENCY_SCHEDULES = {
    "once daily": ["08:00"],
    "twice daily": ["08:00", "20:00"],
    "three times daily": ["08:00", "14:00", "20:00"],
    "four times daily": ["08:00", "12:00", "16:00", "20:00"],
    "every 4 hours": ["06:00", "10:00", "14:00", "18:00", "22:00"],
    "every 6 hours": ["06:00", "12:00", "18:00", "00:00"],
    "every 8 hours": ["06:00", "14:00", "22:00"],
    "every 12 hours": ["08:00", "20:00"],
    "every 24 hours": ["08:00"],
    "weekly": ["Monday 08:00"],
    "monthly": ["1st of month 08:00"],
    "at bedtime": ["22:00"],
    "with meals": ["08:00", "13:00", "19:00"],
    "before meals": ["07:30", "12:30", "18:30"],
    "after meals": ["08:30", "13:30", "19:30"],
    "morning": ["08:00"],
    "evening": ["20:00"],
}


class MedicationReminderSkill:
    """
    Medication Reminder Skill — intelligent scheduling and adherence support.
    """

    def __init__(self):
        self.name = SKILL_METADATA["name"]
        self.version = SKILL_METADATA["version"]
        self._reminders: list = []  # In-memory store for this session

    def create_reminder(
        self,
        medication: str,
        frequency: str,
        notes: str = "",
        start_date: str = "today",
        duration_days: Optional[int] = None,
    ) -> dict:
        """
        Creates a medication reminder with intelligent scheduling.

        Args:
            medication: Name of the medication.
            frequency: How often to take (e.g., "twice daily", "every 8 hours").
            notes: Additional instructions (e.g., "take with food").
            start_date: Start date — "today", "tomorrow", or ISO date.
            duration_days: Optional treatment duration.

        Returns:
            dict with reminder details, schedule, adherence tips, and export options.
        """
        reminder_id = str(uuid.uuid4())[:8]
        created_at = datetime.now()

        # Parse frequency to get suggested times
        suggested_times = self._parse_frequency(frequency)

        # Generate adherence tips
        adherence_tips = self._generate_adherence_tips(medication, frequency, notes)

        # Generate side effect monitoring reminders
        monitoring_reminders = self._generate_monitoring_reminders(medication)

        # Calculate end date if duration provided
        end_date = None
        if duration_days:
            end_date = (created_at + timedelta(days=duration_days)).strftime("%Y-%m-%d")

        # Calculate estimated refill date
        refill_alert = None
        if duration_days and duration_days > 7:
            refill_date = (created_at + timedelta(days=duration_days - 7)).strftime("%Y-%m-%d")
            refill_alert = f"Set a refill reminder for {refill_date} (7 days before end of supply)"

        reminder = {
            "reminder_id": reminder_id,
            "medication": medication,
            "frequency": frequency,
            "suggested_times": suggested_times,
            "notes": notes,
            "start_date": start_date,
            "end_date": end_date,
            "duration_days": duration_days,
            "created_at": created_at.isoformat(),
            "status": "active",
            "adherence_tips": adherence_tips,
            "side_effect_monitoring": monitoring_reminders,
            "refill_alert": refill_alert,
            "setup_instructions": self._get_setup_instructions(medication, suggested_times),
            "export_options": [
                "📱 Set recurring alarms on your phone",
                "📅 Add to Google Calendar",
                "💊 Use a pill organizer",
                "🔔 Enable notifications in a health app (Google Fit, MyFitnessPal)",
            ],
            "safety_reminder": (
                f"⚠️ Always follow your doctor's exact prescription for {medication}. "
                "Never change your dosage without consulting your healthcare provider."
            ),
        }

        self._reminders.append(reminder)
        return reminder

    def list_reminders(self) -> dict:
        """Lists all active medication reminders."""
        active = [r for r in self._reminders if r.get("status") == "active"]
        return {
            "total_reminders": len(active),
            "reminders": active,
            "tip": "Review your medication schedule with your doctor at every visit.",
        }

    def format_for_display(self, reminder: dict) -> str:
        """Formats a reminder for human-readable display."""
        if "error" in reminder:
            return f"❌ Error: {reminder['error']}"

        lines = [
            "\n" + "="*55,
            f"  💊 Medication Reminder Created",
            "="*55,
            f"\n🆔 Reminder ID: {reminder['reminder_id']}",
            f"💊 Medication:  {reminder['medication']}",
            f"⏰ Frequency:   {reminder['frequency']}",
        ]

        if reminder.get("notes"):
            lines.append(f"📝 Notes:       {reminder['notes']}")

        lines.append(f"\n📅 Suggested Times:")
        for time in reminder.get("suggested_times", []):
            lines.append(f"   🔔 {time}")

        if reminder.get("end_date"):
            lines.append(f"\n🗓️  Treatment End: {reminder['end_date']}")

        if reminder.get("refill_alert"):
            lines.append(f"♻️  {reminder['refill_alert']}")

        lines.append("\n✅ Adherence Tips:")
        for tip in reminder.get("adherence_tips", [])[:4]:
            lines.append(f"   • {tip}")

        if reminder.get("side_effect_monitoring"):
            lines.append("\n👁️  Monitor For:")
            for item in reminder["side_effect_monitoring"][:3]:
                lines.append(f"   • {item}")

        lines.extend([
            "",
            "─" * 55,
            reminder.get("safety_reminder", ""),
            "="*55 + "\n",
        ])

        return "\n".join(lines)

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _parse_frequency(self, frequency: str) -> list:
        """Maps frequency description to suggested times."""
        freq_lower = frequency.lower().strip()

        for key, times in FREQUENCY_SCHEDULES.items():
            if key in freq_lower or freq_lower in key:
                return times

        # Default: try to extract times-per-day
        if "once" in freq_lower or "1" in freq_lower:
            return ["08:00"]
        elif "twice" in freq_lower or "2" in freq_lower:
            return ["08:00", "20:00"]
        elif "three" in freq_lower or "3" in freq_lower:
            return ["08:00", "14:00", "20:00"]

        return ["08:00", "20:00"]  # Default: twice daily

    def _generate_adherence_tips(self, medication: str, frequency: str, notes: str) -> list:
        """Generates personalized adherence tips."""
        tips = [
            f"Set {len(self._parse_frequency(frequency))} daily alarm(s) labeled '{medication}'",
            "Use a weekly pill organizer to easily track if you've taken it",
            "Take it at the same time each day to build a habit",
            "Link it to an existing daily routine (e.g., breakfast, brushing teeth)",
            "Keep your medications visible but stored properly (away from heat/moisture)",
        ]

        # Notes-specific tips
        if "food" in notes.lower():
            tips.append("Prepare your medication next to your meal plate as a visual reminder")
        if "water" in notes.lower():
            tips.append("Keep a glass of water next to your medications")
        if "bedtime" in frequency.lower():
            tips.append("Place the medication on your nightstand as a bedtime reminder")

        tips.append("Never double-dose if you miss one — consult your pharmacist for guidance")
        return tips

    def _generate_monitoring_reminders(self, medication: str) -> list:
        """Returns relevant monitoring reminders based on medication type."""
        med_lower = medication.lower()

        monitoring = ["Report any unusual symptoms to your doctor promptly"]

        if any(drug in med_lower for drug in ["metformin", "insulin", "glipizide"]):
            monitoring.extend([
                "Monitor blood sugar levels as directed by your doctor",
                "Watch for hypoglycemia signs: shakiness, sweating, confusion",
                "Keep a glucose diary and bring it to appointments",
            ])
        elif any(drug in med_lower for drug in ["warfarin", "coumadin"]):
            monitoring.extend([
                "Watch for unusual bruising or bleeding",
                "Attend all scheduled INR blood test appointments",
                "Avoid sudden changes in Vitamin K intake (leafy greens)",
            ])
        elif any(drug in med_lower for drug in ["lisinopril", "enalapril", "ramipril"]):
            monitoring.extend([
                "Monitor blood pressure as directed",
                "Watch for persistent dry cough (common side effect)",
                "Avoid potassium supplements unless directed",
            ])
        elif any(drug in med_lower for drug in ["statin", "atorvastatin", "rosuvastatin", "simvastatin"]):
            monitoring.extend([
                "Report any unexplained muscle pain or weakness immediately",
                "Get annual liver function tests",
                "Take in the evening for best effectiveness (most statins)",
            ])
        else:
            monitoring.extend([
                "Note any new symptoms that start after beginning this medication",
                "Attend follow-up appointments to assess medication effectiveness",
            ])

        return monitoring

    def _get_setup_instructions(self, medication: str, times: list) -> list:
        """Returns step-by-step setup instructions for device reminders."""
        return [
            f"iPhone: Open Clock → Alarm → Add → Set for {times[0]} → Label: '{medication}'",
            f"Android: Open Clock → Alarm → + → {times[0]} → Label: '{medication}'",
            "Google Calendar: Create recurring event, set notification 10 minutes before",
            "Ask Google Assistant: 'Hey Google, remind me to take my medication every day at 8am'",
            "Ask Siri: 'Siri, remind me to take my medication every day at 8am'",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point for Agents CLI invocation."""
    import argparse

    parser = argparse.ArgumentParser(description="MediGuide Medication Reminder Skill")
    parser.add_argument("--medication", "-m", type=str, help="Medication name")
    parser.add_argument("--frequency", "-f", type=str, help="How often to take")
    parser.add_argument("--notes", "-n", type=str, default="")
    parser.add_argument("--start-date", type=str, default="today")
    parser.add_argument("--duration", type=int, help="Treatment duration in days")
    parser.add_argument("--list", action="store_true", help="List all reminders")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--metadata", action="store_true", help="Show skill metadata")

    args = parser.parse_args()

    skill = MedicationReminderSkill()

    if args.metadata:
        print(json.dumps(SKILL_METADATA, indent=2))
        return

    if args.list:
        result = skill.list_reminders()
        print(json.dumps(result, indent=2) if args.json else json.dumps(result, indent=2))
        return

    # Accept JSON from stdin (Agents CLI mode)
    if not args.medication and not sys.stdin.isatty():
        try:
            input_data = json.load(sys.stdin)
            args.medication = input_data.get("medication", "")
            args.frequency = input_data.get("frequency", "twice daily")
            args.notes = input_data.get("notes", "")
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
            sys.exit(1)

    if not args.medication or not args.frequency:
        print("Error: --medication and --frequency are required")
        parser.print_help()
        sys.exit(1)

    result = skill.create_reminder(
        medication=args.medication,
        frequency=args.frequency,
        notes=args.notes,
        start_date=args.start_date,
        duration_days=args.duration,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(skill.format_for_display(result))


if __name__ == "__main__":
    main()
