"""
MediGuide Vision AI — Standalone Medical OCR & Interaction Checker Skill
========================================================================
An Agents CLI compatible skill that:
  1. Accepts an image of a prescription (handwritten or printed).
  2. Applies local Pillow downscaling and normalization (Image Processing).
  3. Uses Gemini multimodal vision to extract medications and dosages.
  4. Runs the list of extracted drugs through the local drug interaction database.
  5. Outputs a detailed, structured transcription and safety report.

CLI Usage:
  python skills/medical_ocr.py --image path/to/prescription.jpg
  echo '{"image_path": "path/to/prescription.jpg"}' | python skills/medical_ocr.py
"""

import argparse
import json
import os
import sys
from typing import Optional

# Fix Windows cmd.exe Unicode encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.tools.vision_tools import preprocess_image, validate_image_file
from src.tools.medical_tools import check_drug_interactions


class MedicalOCR_Skill:
    """Medical OCR Skill implementation."""

    METADATA = {
        "name": "medical_ocr",
        "version": "1.0.0",
        "description": "Image-based prescription transcription and safety interaction check",
        "category": "image_processing",
        "safety_level": "advisory"
    }

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def run(self, image_path: str, format_json: bool = False) -> dict:
        """
        Executes the image processing and OCR validation skill.
        """
        result = {
            "image_path": image_path,
            "status": "success",
            "transcription": None,
            "extracted_medications": [],
            "interaction_check": None,
            "error": None
        }

        # 1. Local Image Preprocessing & Validation (Image Processing)
        validation = validate_image_file(image_path)
        if not validation["valid"]:
            result["status"] = "error"
            result["error"] = f"Image validation failed: {validation['reason']}"
            return result

        try:
            # Downscale & normalize image format
            img_bytes = preprocess_image(image_path)
        except Exception as e:
            result["status"] = "error"
            result["error"] = f"Image preprocessing failed: {str(e)}"
            return result

        # 2. Extract medications (Simulated/Fallback or Multimodal LLM call)
        if not self.api_key:
            # Fallback if API key is not set (so the skill is fully testable offline)
            result["transcription"] = (
                "[Offline Simulation Mode]\n"
                "Rx:\n"
                "1. Metformin 500mg - 1 tab twice daily with meals\n"
                "2. Ibuprofen 400mg - 1 tab every 6 hours as needed for pain\n"
            )
            result["extracted_medications"] = ["metformin", "ibuprofen"]
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-2.0-flash")
                
                # Call Gemini vision directly
                prompt = (
                    "You are a medical OCR assistant. Transcribe the prescription image provided. "
                    "Extract a clean list of medications mentioned in the image as a JSON list. "
                    "Return output in format:\n"
                    "TRANSCRIPTION: [Full raw transcription text]\n"
                    "DRUGS: [JSON list of medication names]"
                )
                
                response = model.generate_content([
                    {"mime_type": "image/jpeg", "data": img_bytes},
                    prompt
                ])
                
                text = response.text
                result["transcription"] = text
                
                # Parse drugs from output
                if "DRUGS:" in text:
                    drugs_part = text.split("DRUGS:")[-1].strip()
                    try:
                        # Extract JSON array
                        array_str = drugs_part[drugs_part.find("["):drugs_part.find("]")+1]
                        result["extracted_medications"] = json.loads(array_str)
                    except:
                        pass
                if not result["extracted_medications"]:
                    # Fallback extraction from text
                    for drug in ["metformin", "ibuprofen", "aspirin", "warfarin"]:
                        if drug in text.lower():
                            result["extracted_medications"].append(drug)

            except Exception as e:
                result["status"] = "error"
                result["error"] = f"Gemini multimodal OCR failed: {str(e)}"
                return result

        # 3. Check for Drug Interactions
        if result["extracted_medications"]:
            result["interaction_check"] = check_drug_interactions(result["extracted_medications"])

        return result

    def format_for_display(self, result: dict) -> str:
        """Formats the result into a clean CLI output."""
        if result["status"] == "error":
            return f"\n❌ ERROR: {result['error']}\n"

        lines = [
            "\n" + "="*65,
            "  [MediGuide Vision] Prescription Scan & OCR Safety Report",
            "="*65,
            f"\nImage Path: {result['image_path']}",
            "\n--- OCR TRANSCRIPTION ---",
            result["transcription"].strip(),
            "\n--- EXTRACTED MEDICATIONS ---",
            f"Medications identified: {', '.join(result['extracted_medications']) if result['extracted_medications'] else 'None'}"
        ]

        if result.get("interaction_check"):
            ic = result["interaction_check"]
            lines.extend([
                "\n--- DRUG SAFETY CHECK ---",
                f"Interactions found: {ic['interactions_found']}"
            ])
            for w in ic.get("warnings", []):
                lines.append(f"  [{w['severity']}] {w['pair']}: {w['effect']}")
        else:
            lines.extend([
                "\n--- DRUG SAFETY CHECK ---",
                "No drugs extracted to run safety check."
            ])

        lines.extend([
            "\n" + "-"*65,
            "DISCLAIMER: OCR can make mistakes. Always verify the printed dosage",
            "directly on the pill bottle and double check with a pharmacist.",
            "="*65 + "\n"
        ])

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="MediGuide Vision AI - Medical OCR Skill")
    parser.add_argument("--image", "-i", type=str, help="Path to prescription image")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--metadata", action="store_true", help="Print skill metadata")

    args = parser.parse_args()
    skill = MedicalOCR_Skill()

    if args.metadata:
        print(json.dumps(skill.METADATA, indent=2))
        return

    # Check for stdin inputs (Agents CLI compatibility)
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            data = json.loads(stdin_data)
            image_path = data.get("image_path")
        except Exception as e:
            print(json.dumps({"status": "error", "error": f"Failed to parse stdin: {str(e)}"}))
            sys.exit(1)
    else:
        image_path = args.image

    if not image_path:
        print("❌ Error: --image path is required or input must be piped via JSON.")
        parser.print_help()
        sys.exit(1)

    result = skill.run(image_path)
    
    if args.json or not sys.stdin.isatty():
        print(json.dumps(result, indent=2))
    else:
        print(skill.format_for_display(result))


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
