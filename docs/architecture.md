# MediGuide AI — Detailed Architecture Documentation

## System Overview

MediGuide AI is a multi-agent healthcare navigation system implementing the following Google ADK course concepts:

1. **Multi-Agent System (ADK)** — Orchestrator + 3 specialist sub-agents
2. **MCP Server** — Custom Model Context Protocol server with 8 tools
3. **Security Features** — PII redaction, injection detection, audit logging
4. **Deployability** — Docker + Docker Compose + Cloud Run
5. **Agent Skills** — Symptom checker + medication reminder (Agents CLI compatible)
6. **Antigravity** — Demonstrated in video

---

## Component Architecture

### 1. Agent Layer (`src/agents/`)

#### OrchestratorAgent (`orchestrator.py`)
- **Type**: Root Agent (Google ADK `Agent`)
- **Model**: Gemini 2.0 Flash
- **Role**: Intent understanding and sub-agent delegation
- **Direct Tools**:
  - `route_to_emergency()` — Immediate emergency response
  - `validate_input()` — Query validation
  - `check_medications()` — Drug interaction checking
- **Sub-agents**: TriageAgent, ResearchAgent, SchedulerAgent
- **Memory**: InMemorySessionService (multi-turn conversation)

#### TriageAgent (`triage_agent.py`)
- **Type**: Sub-agent (Google ADK `Agent`)
- **Role**: Symptom analysis and urgency classification
- **Triage Levels**:
  ```
  Level 1 (GREEN)      — Non-urgent, self-care
  Level 2 (YELLOW)     — Semi-urgent, 48-72 hours
  Level 3 (ORANGE)     — Urgent, same day
  Level 4 (ORANGE-RED) — Very urgent, emergency room
  Level 5 (RED)        — Emergency, call now
  ```
- **Tools**: `analyze_symptoms()`, `identify_red_flags()`, `get_body_system_assessment()`

#### ResearchAgent (`research_agent.py`)
- **Type**: Sub-agent (Google ADK `Agent`)
- **Role**: Evidence-based medical information retrieval
- **MCP Integration**: Calls MCP server tools for knowledge retrieval
- **Tools**: 6 research tools covering conditions, medications, treatments, prevention, specialists, search

#### SchedulerAgent (`scheduler_agent.py`)
- **Type**: Sub-agent (Google ADK `Agent`)
- **Role**: Health schedule management
- **Storage**: In-memory schedule store (session-scoped)
- **Tools**: Medication reminders, appointment scheduling, health goals, preventive screening schedule

---

### 2. MCP Server (`mcp_server/`)

#### Server (`server.py`)
- **Framework**: FastAPI with Uvicorn
- **Transport**: HTTP + SSE (Server-Sent Events)
- **Protocol**: MCP/1.0
- **Endpoints**:
  ```
  GET  /           — Server info
  GET  /health     — Health check (used by Docker/K8s)
  GET  /tools      — Tool discovery (MCP tool manifest)
  POST /tools/call — Tool invocation (MCP tool call)
  GET  /resources  — Knowledge resource listing
  GET  /events     — SSE streaming transport
  GET  /docs       — FastAPI auto-generated API docs
  ```

#### Tool Registry (`tools.py`)
- **8 Medical Knowledge Tools**:
  ```
  get_condition_info          — Disease/condition information
  get_medication_info         — Drug information (no dosing)
  check_drug_interactions     — Interaction warnings
  get_specialist_recommendation — Care navigation
  get_preventive_guidelines   — Evidence-based prevention
  search_medical_knowledge    — Free-text search
  get_body_system_info        — Body system assessment
  get_emergency_contacts      — Emergency numbers by region
  ```
- **Implementation**: Async wrappers around synchronous medical tool functions
- **Pattern**: `asyncio.to_thread()` for sync-to-async bridging

---

### 3. Security Layer (`src/tools/security.py`)

#### Processing Pipeline
```
User Input
    │
    ▼
[1] Blocked Content Check
    └─ Self-harm queries → Crisis resources
    │
    ▼
[2] Prompt Injection Detection
    └─ 16+ injection patterns
    └─ Strict mode: block | Lenient mode: warn
    │
    ▼
[3] PII Redaction
    └─ 7 PII types: phone, email, SSN, Aadhaar, card, passport, address
    │
    ▼
[4] Off-Topic Detection (non-blocking)
    └─ Warning if clearly outside healthcare domain
    │
    ▼
Safe Input → Agent System
    │
    ▼
Agent Response → [Output Scan] → User
```

#### PII Patterns
| PII Type | Pattern | Replacement |
|---|---|---|
| Phone | `\b(\+?\d{1,3}[-.]?)...` | `[PHONE_REDACTED]` |
| Email | `[A-Za-z0-9._%+\-]+@...` | `[EMAIL_REDACTED]` |
| SSN (US) | `\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b` | `[SSN_REDACTED]` |
| Aadhaar (IN) | `\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b` | `[AADHAAR_REDACTED]` |
| Credit Card | `\b(?:\d[ -]?){13,19}\b` | `[CARD_REDACTED]` |
| Passport | `\b[A-Z]{1,2}\d{6,9}\b` | `[PASSPORT_REDACTED]` |
| Address | Street address pattern | `[ADDRESS_REDACTED]` |

---

### 4. Medical Tools Library (`src/tools/medical_tools.py`)

#### Knowledge Bases (Demo — extensible to real APIs)
- `SYMPTOM_DATABASE`: 8 symptoms with urgency levels, associated conditions, red flags
- `CONDITION_DATABASE`: 3 conditions with full clinical detail (diabetes, hypertension, migraine)
- `MEDICATION_DATABASE`: 4 medications with safety profiles (metformin, ibuprofen, aspirin, warfarin)
- `DRUG_INTERACTION_DATABASE`: 4 known interaction pairs with severity levels

---

### 5. Agent Skills (`skills/`)

#### SymptomCheckerSkill (`symptom_checker.py`)
- **Agents CLI compatible**: Reads JSON from stdin
- **Formats**: Human-readable text or JSON output
- **Inputs**: symptoms, duration, severity, age_group, existing_conditions
- **Outputs**: Triage assessment with urgency level, recommendations, red flags

#### MedicationReminderSkill (`medication_reminder.py`)
- **Agents CLI compatible**: Reads JSON from stdin
- **Features**: Smart frequency parsing, adherence tips, side effect monitoring, refill alerts
- **Frequency patterns**: 15+ natural language patterns (twice daily, every 8 hours, with meals, etc.)

---

## Data Flow Diagrams

### Emergency Query Flow
```
"I have chest pain and left arm pain"
    → SecurityLayer (clean)
    → OrchestratorAgent
    → identify_red_flags() → CARDIAC RED FLAG DETECTED
    → route_to_emergency()
    → Returns: emergency contacts + first aid steps
    → SecurityLayer output scan
    → User gets immediate emergency response
```

### Research Query Flow
```
"What is type 2 diabetes?"
    → SecurityLayer (clean)
    → OrchestratorAgent → delegates to ResearchAgent
    → ResearchAgent.research_condition("type 2 diabetes")
    → [Optional] MCP Server call: POST /tools/call
        {"tool_name": "get_condition_info", "parameters": {...}}
    → Returns structured condition data
    → ResearchAgent synthesizes response
    → User gets evidence-based information + disclaimer
```

### Scheduling Flow
```
"Remind me to take metformin twice daily"
    → SecurityLayer (clean)
    → OrchestratorAgent → delegates to SchedulerAgent
    → SchedulerAgent.add_medication_reminder(
          medication="metformin",
          frequency="twice daily"
      )
    → Generates schedule: ["08:00", "20:00"]
    → Adherence tips, monitoring reminders
    → User gets full reminder setup guidance
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Deployment                     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Docker Compose Network                   │   │
│  │                                                       │   │
│  │  ┌───────────────────┐    ┌──────────────────────┐  │   │
│  │  │   MCP Server      │    │   Agent Service      │  │   │
│  │  │   Container       │    │   Container          │  │   │
│  │  │                   │◄───│                      │  │   │
│  │  │  FastAPI:8080     │    │  Python ADK Agent    │  │   │
│  │  │  Health: /health  │    │  Gemini 2.0 Flash    │  │   │
│  │  │  Non-root user    │    │  Non-root user       │  │   │
│  │  └───────────────────┘    └──────────────────────┘  │   │
│  │                                                       │   │
│  │  mediguide-network (bridge)                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Cloud Run option: gcloud run deploy mediguide-ai          │
└─────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```
Request → [PII Scan] → [Injection Check] → [Block Check] → Agent
                                                              │
Response ← [Output Scan] ← [PII Scrub] ←────────────────────┘

Audit Log (no PII stored):
  - Event type
  - Timestamp
  - Request number (not content)
  - Redaction count (not what was redacted)
```
