"""
MediGuide Vision AI — Vercel Serverless Entrypoint & REST API
==============================================================
Provides a top-level FastAPI instance `app` that serves:
  1. The interactive client UI (public/index.html)
  2. Multi-Agent Clinical REST endpoints (Lab analysis, Drug interactions, Risk score, Chrono-schedule)
  3. Static academic documents downloads
"""

import os
import sys
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add root directory to sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.tools.lab_tools import analyze_lab_report
from src.tools.medical_tools import check_drug_interactions, compute_health_risk_score, get_emergency_contacts
from src.tools.food_drug_tools import check_food_drug_interactions, generate_medication_schedule
from src.tools.security import SecurityLayer

app = FastAPI(
    title="MediGuide Vision AI",
    description="Multiagent Medical Image Analysis and Healthcare Navigation API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = SecurityLayer()

# ── FRONTEND HTML ROUTE ──────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_path = os.path.join(_ROOT, "public", "index.html")
    if not os.path.exists(html_path):
        html_path = os.path.join(_ROOT, "index.html")
    
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>MediGuide Vision AI is running!</h1><p>Visit /docs for API documentation.</p>")


# ── HEALTH CHECK ─────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "MediGuide Vision AI",
        "version": "2.0.0",
        "project": "Major Project Review 2 (ILR)",
        "batch": "2023120304 - Section C (23ITMNP-C06)",
        "guide": "Dr. L. Sunitha",
        "institution": "Vardhaman College of Engineering (Autonomous)",
        "agents": ["VisionAgent", "LabAgent", "TriageAgent", "SchedulerAgent", "ResearchAgent"]
    }


# ── PII SANITIZATION ENDPOINT ────────────────────────────────────────────────
class SanitizeRequest(BaseModel):
    text: str

@app.post("/api/sanitize")
async def sanitize_query(req: SanitizeRequest):
    return security.process_input(req.text)


# ── LAB ANALYSIS ENDPOINT ────────────────────────────────────────────────────
class LabReportRequest(BaseModel):
    lab_values: Dict[str, float]
    age: int = 40
    gender: str = "unknown"

@app.post("/api/analyze-lab")
async def api_analyze_lab(req: LabReportRequest):
    try:
        return analyze_lab_report(req.lab_values, age=req.age, gender=req.gender)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── DRUG INTERACTIONS ENDPOINT ───────────────────────────────────────────────
class DrugCheckRequest(BaseModel):
    drugs: List[str]

@app.post("/api/check-interactions")
async def api_check_interactions(req: DrugCheckRequest):
    try:
        return check_drug_interactions(req.drugs)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── FOOD-DRUG INTERACTIONS ENDPOINT ──────────────────────────────────────────
class FoodDrugRequest(BaseModel):
    drugs: List[str]
    foods: Optional[List[str]] = None

@app.post("/api/check-food")
async def api_check_food(req: FoodDrugRequest):
    try:
        return check_food_drug_interactions(req.drugs, req.foods)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── HEALTH RISK SCORE ENDPOINT ───────────────────────────────────────────────
class RiskScoreRequest(BaseModel):
    symptoms: List[str]
    duration: str = "1 day"
    severity: str = "moderate"
    age: int = 40
    gender: str = "unknown"
    existing_conditions: str = "none"
    red_flags: Optional[List[str]] = None

@app.post("/api/risk-score")
async def api_risk_score(req: RiskScoreRequest):
    try:
        return compute_health_risk_score(
            symptoms=req.symptoms,
            duration=req.duration,
            severity=req.severity,
            age=req.age,
            gender=req.gender,
            existing_conditions=req.existing_conditions,
            red_flags=req.red_flags or []
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── MEDICATION SCHEDULER ENDPOINT ────────────────────────────────────────────
class ScheduleRequest(BaseModel):
    medications: List[Dict[str, str]]

@app.post("/api/schedule")
async def api_schedule(req: ScheduleRequest):
    try:
        return generate_medication_schedule(req.medications)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── STATIC DOCUMENTS DOWNLOAD ────────────────────────────────────────────────
@app.get("/documents/{filename}")
async def get_document(filename: str):
    file_path = os.path.join(_ROOT, "documents", filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(_ROOT, "public", "documents", filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail=f"Document {filename} not found")
