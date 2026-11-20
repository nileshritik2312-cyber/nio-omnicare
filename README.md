# Nio OmniCare — Clinical Triage & Telemetry Prototype

**Nio OmniCare** is a non-diagnostic clinical triage and patient telemetry evaluation prototype combining an interactive single-page web dashboard (`index.html`) with a modular Python FastAPI backend (`app/main.py`).

- **Live Web Dashboard (GitHub Pages):** `[https://nileshritik2312-cyber.github.io/nio-omnicare/](https://nileshritik2312-cyber.github.io/nio-omnicare/)`
- **Source Repository:** `[https://github.com/nileshritik2312-cyber/nio-omnicare](https://github.com/nileshritik2312-cyber/nio-omnicare)`

---

## 1. System Architecture

* **Frontend Triage Dashboard (`index.html`):** Browser-based command interface designed for GitHub Pages and local testing. Supports one-click test scenarios (`PT-7734` Critical, `PT-4091` Urgent, `PT-1024` Routine), custom vital signs input, optional Gemini API key input, color-coded urgency badges (`red`, `amber`, `green`), and structured JSON output inspection.
* **Backend Triage API (`app/main.py`):** FastAPI service exposing `/health` and `/api/v1/triage/evaluate` with Pydantic request/response validation and automatic Swagger UI documentation at `/docs`.
* **Hybrid AI + Rule Fallback Engine:** Attempts structured JSON triage generation via Gemini (`gemini-2.5-flash`) when an API key is configured and available, and automatically falls back to deterministic clinical threshold and red-flag rules when offline, unauthenticated, or rate/quota-limited.

## 2. Dataset Assumptions

* **Simulated & Synthetic Triage Payloads:** All patient IDs (`PT-7734`, `PT-4091`, `PT-1024`) and telemetry examples used in this prototype are synthetic/simulated inputs created for demonstration and evaluation—no real patient health records (PHI) are bundled or stored.
* **Input Ranges & Units:** Oxygen saturation ($SpO_2$) is assumed in percentage (`50–100%`), heart rate in beats per minute (`20–260 bpm`), and body temperature in Celsius (`°C`, defaulting to `37.0°C` if omitted).
* **Stateless Evaluation:** Each triage request is evaluated independently without maintaining longitudinal patient histories or electronic health record (EHR) context.

## 3. Clinical Boundaries

* **Strictly Non-Diagnostic:** Nio OmniCare is a clinical triage decision-support prototype, not a medical device or diagnostic tool. It does not diagnose diseases, prescribe medications, calculate drug dosages, or replace licensed medical judgment.
* **Escalation & Governance Guardrails:** High-risk indicators (such as chest pain, severe shortness of breath, $SpO_2 < 92$, or extreme heart rate values) trigger `Critical` classification, `governance_flag: true`, and `requires_immediate_dispatch: true` to prompt rapid human clinical review.

## 4. Limitations

* **Prototype Scope:** The rule-based fallback uses simplified threshold heuristics suitable for a prototype rather than validated emergency department triage scales (such as ESI or CTAS).
* **No External EHR / Device Integration:** Telemetry is entered manually or via preset payloads rather than streamed directly from bedside monitors or hospital information systems.
* **API & Network Dependency for Live LLM Mode:** Live Gemini responses require network access, a valid `GEMINI_API_KEY`, and available API quota; otherwise the deterministic fallback engine handles requests.

## 5. Roadmap & Blueprint Alignment

This prototype delivers the core **clinical triage & telemetry evaluation engine** for the broader **Nio OmniCare** vision (*Future Health Digital Innovation Challenge — Population Health: Closing the Screening-to-Care Loop*):

* **Phase 1 (Current Prototype):** Interactive triage dashboard (`index.html`), FastAPI service (`app/main.py`), and hybrid Gemini + deterministic clinical fallback engine.
* **Phase 2 (Care Loop & Multi-Lingual Nudges):** Screening-to-care follow-up tracking for clinics, camps, and frontline health workers (ASHAs/ANMs), paired with multi-lingual SMS/WhatsApp follow-up nudges for vulnerable groups.
* **Phase 3 (Crisis & Resource Coordination):** Multi-node registry and geospatial routing for hospitals, blood/organ banks, pharmaceuticals, and transport using PostgreSQL/PostGIS and disaster code protocols (Code Red, Amber, Blue).
* **Phase 4 (Resilient Edge & Hardware Scale):** IoT wearable vitals streaming, offline mesh-network relays during connectivity blackouts, and medical supply routing via containerized cloud microservices.

## 6. Quick Start (Local FastAPI Server)

```bash
git clone https://github.com/nileshritik2312-cyber/nio-omnicare.git
cd nio-omnicare
pip install -r requirements.txt
uvicorn app.main:app --reload
