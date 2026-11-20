import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

app = FastAPI(
    title="Nio OmniCare Clinical Triage API",
    description="Non-diagnostic clinical telemetry and patient triage engine with hybrid AI + rule-based fallback.",
    version="3.0.0",
)

SYSTEM_PROMPT = (
    "You are the Clinical Triage & Telemetry Evaluation Engine for Nio OmniCare. "
    "Evaluate incoming patient symptoms and vital signs to classify urgency (Critical, Urgent, Routine) "
    "and provide a concise 1-2 sentence non-diagnostic clinical summary. Return strictly valid JSON."
)


class VitalSigns(BaseModel):
    spo2: int = Field(..., ge=50, le=100, description="Oxygen saturation percentage")
    heart_rate: int = Field(..., ge=20, le=260, description="Heart rate in bpm")
    temperature_c: Optional[float] = Field(37.0, description="Body temperature in Celsius")


class TriageRequest(BaseModel):
    patient_id: str = Field(..., example="PT-7734")
    symptoms: List[str] = Field(..., example=["chest pain", "severe shortness of breath"])
    vital_signs: VitalSigns


class TriageMetadata(BaseModel):
    ui_badge_color: Literal["red", "amber", "green"]
    requires_immediate_dispatch: bool
    timestamp: str


class TriageResponse(BaseModel):
    patient_id: str
    urgency_level: Literal["Critical", "Urgent", "Routine"]
    recommended_action: str
    ai_clinical_note: str
    confidence_score: float
    governance_flag: bool
    metadata: TriageMetadata


def fallback_clinical_engine(payload: TriageRequest) -> TriageResponse:
    symptoms_lower = ", ".join(payload.symptoms).lower()
    spo2 = payload.vital_signs.spo2
    hr = payload.vital_signs.heart_rate
    temp = payload.vital_signs.temperature_c or 37.0
    red_flags = ["chest pain", "shortness of breath", "unconscious", "stroke", "severe bleeding", "syncope"]

    if any(flag in symptoms_lower for flag in red_flags) or spo2 < 92 or hr >= 130 or hr <= 45:
        urgency, color, dispatch, gov, conf = "Critical", "red", True, True, 0.96
        action = "Escalate immediately to emergency physician/resuscitation team and initiate continuous monitoring."
        note = (
            f"High-risk presentation ({', '.join(payload.symptoms)}) with critical vital signs "
            f"(SpO2 {spo2}%, HR {hr} bpm) requires immediate emergency escalation."
        )
    elif spo2 < 95 or hr > 105 or temp >= 38.5 or "dizziness" in symptoms_lower:
        urgency, color, dispatch, gov, conf = "Urgent", "amber", False, True, 0.90
        action = "Prioritize prompt clinician evaluation within 30-60 minutes and repeat vitals."
        note = (
            f"Patient reports {', '.join(payload.symptoms)} with moderately abnormal vitals "
            f"(SpO2 {spo2}%, HR {hr} bpm, Temp {temp}°C), warranting prompt clinical review."
        )
    else:
        urgency, color, dispatch, gov, conf = "Routine", "green", False, False, 0.92
        action = "Schedule standard outpatient or telehealth review and monitor symptoms."
        note = (
            f"Patient presents with {', '.join(payload.symptoms)} and stable vitals "
            f"(SpO2 {spo2}%, HR {hr} bpm). No acute red flags identified."
        )

    return TriageResponse(
        patient_id=payload.patient_id,
        urgency_level=urgency,
        recommended_action=action,
        ai_clinical_note=note,
        confidence_score=conf,
        governance_flag=gov,
        metadata=TriageMetadata(
            ui_badge_color=color,
            requires_immediate_dispatch=dispatch,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@app.get("/")
def serve_dashboard():
    index_path = Path(__file__).resolve().parent.parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"status": "Nio OmniCare API Online", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "nio-omnicare", "version": "3.0.0"}


@app.post("/api/v1/triage/evaluate", response_model=TriageResponse)
def evaluate_triage(payload: TriageRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and genai is not None:
        try:
            client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=payload.model_dump_json(),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            parsed = json.loads(response.text)
            return TriageResponse(**parsed)
        except Exception:
            pass

    return fallback_clinical_engine(payload)
