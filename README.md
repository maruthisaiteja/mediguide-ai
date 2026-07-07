# 🏥 MediGuide AI — Multi-Agent Healthcare Navigation System

> **Kaggle AI Agents: Intensive Vibe Coding Capstone Project**
> Track: **Agents for Good** | Built with **Google ADK + Gemini 2.0 Flash**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-Latest-green.svg)](https://github.com/google/adk-python)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

---

## 🎯 Problem Statement

Healthcare navigation is broken. When people feel unwell, they face:
- **Information overload** — Google gives 10 million results, most unreliable
- **Access barriers** — Doctor appointments take days or weeks
- **Fragmented care** — Separate apps for symptoms, medications, appointments
- **Dangerous decisions** — 40% of people self-medicate incorrectly

**MediGuide AI solves this** by providing a single, intelligent, multi-agent healthcare navigation system that helps users understand their symptoms, find reliable medical information, manage medications, and prepare for doctor visits — all in one place, available 24/7.

---

## 🤖 What is MediGuide AI?

MediGuide AI is a **multi-agent AI system** built with Google's ADK (Agent Development Kit) that acts as a personal healthcare navigator. It combines:

| Component | Purpose |
|---|---|
| 🧠 **Orchestrator Agent** | Routes queries to the right specialist sub-agent |
| 🚦 **Triage Agent** | Analyzes symptoms with 5-level urgency classification |
| 📚 **Research Agent** | Retrieves evidence-based medical information via MCP |
| 📅 **Scheduler Agent** | Manages medication reminders and appointments |
| 🔒 **Security Layer** | PII redaction, injection detection, audit logging |
| 🔌 **MCP Server** | Custom Model Context Protocol medical knowledge server |
| 🛠️ **Agent Skills** | Reusable CLI-compatible symptom checker & medication reminder skills |

---

## ✅ Kaggle Evaluation Concepts Demonstrated

| Concept | Implementation | Location |
|---|---|---|
| ✅ **Agent / Multi-agent system (ADK)** | Root orchestrator + 3 specialist sub-agents | `src/agents/` |
| ✅ **MCP Server** | Custom FastAPI MCP server with 8 medical tools | `mcp_server/` |
| ✅ **Security Features** | PII redaction, prompt injection detection, audit logging | `src/tools/security.py` |
| ✅ **Deployability** | Docker multi-stage build + Docker Compose + Cloud Run ready | `Dockerfile`, `docker-compose.yml` |
| ✅ **Agent Skills (Agents CLI)** | Symptom checker + medication reminder skills | `skills/` |
| ✅ **Antigravity** | Demonstrated in video walkthrough | YouTube video |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
│                    (CLI / API / Chat)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                    ┌─────▼──────┐
                    │  Security   │  ← PII Redaction + Injection Detection
                    │   Layer    │
                    └─────┬──────┘
                          │
          ┌───────────────▼───────────────┐
          │      Orchestrator Agent        │  ← Google ADK Root Agent
          │    (MediGuide Coordinator)     │     Gemini 2.0 Flash
          │                               │     Multi-turn memory
          └──────┬──────────┬─────────────┘
                 │          │          │
         ┌───────▼──┐  ┌────▼────┐  ┌─▼──────────┐
         │  Triage  │  │Research │  │ Scheduler  │
         │  Agent   │  │  Agent  │  │   Agent    │
         │          │  │         │  │            │
         │5-level   │  │MCP tools│  │Medications │
         │urgency   │  │8 tools  │  │Appointments│
         │Red flags │  │Evidence │  │Health goals│
         └──────────┘  └────┬────┘  └────────────┘
                            │
               ┌────────────▼────────────┐
               │   MCP Medical Server    │  ← Custom MCP Server
               │   (FastAPI + SSE)       │     8 Knowledge Tools
               │   localhost:8080        │     HTTP/SSE Transport
               └─────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google API Key ([Get one free](https://aistudio.google.com/app/apikey))
- Docker (optional, for containerized deployment)

### 1. Clone the Repository
```bash
git clone https://github.com/maruthisaiteja/mediguide-ai.git
cd mediguide-ai
```

### 2. Set Up Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### 3. Start the MCP Server (Terminal 1)
```bash
python mcp_server/server.py
# Server starts at http://localhost:8080
# Docs at http://localhost:8080/docs
```

### 4. Run MediGuide AI (Terminal 2)
```bash
# Interactive chat mode
python src/main.py

# Single query mode
python src/main.py --query "I have a headache and fever for 2 days"

# Run demo with sample queries
python src/main.py --demo
```

---

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up

# Run demo in Docker
docker-compose run --rm agent python src/main.py --demo

# Start MCP server only
docker-compose up mcp-server

# Stop all services
docker-compose down
```

---

## ☁️ Cloud Run Deployment

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/mediguide-ai

# Deploy to Cloud Run
gcloud run deploy mediguide-ai \
  --image gcr.io/PROJECT_ID/mediguide-ai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key
```

---

## 🛠️ Agent Skills (Agents CLI)

```bash
# Run symptom checker skill
python skills/symptom_checker.py --symptoms "fever, headache, fatigue" --duration "2 days" --severity severe

# Run medication reminder skill
python skills/medication_reminder.py --medication "metformin" --frequency "twice daily" --notes "take with meals"

# JSON output mode
python skills/symptom_checker.py --symptoms "chest pain" --json

# Skills in pipeline mode (Agents CLI compatible)
echo '{"symptoms": "fever, headache"}' | python skills/symptom_checker.py

# View skill metadata
python skills/symptom_checker.py --metadata
```

---

## 🔌 MCP Server API

The MCP server runs at `http://localhost:8080` with these endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server health check |
| GET | `/tools` | List all 8 available tools |
| POST | `/tools/call` | Execute a tool |
| GET | `/resources` | List knowledge resources |
| GET | `/events` | SSE streaming endpoint |
| GET | `/docs` | Interactive API documentation |

**Example Tool Call:**
```bash
curl -X POST http://localhost:8080/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_condition_info",
    "parameters": {
      "condition_name": "type 2 diabetes",
      "detail_level": "standard"
    }
  }'
```

---

## 🔒 Security Features

MediGuide AI implements defense-in-depth security:

| Feature | Implementation |
|---|---|
| **PII Redaction** | Phone, email, SSN, Aadhaar, credit card, address detection & redaction |
| **Prompt Injection Detection** | Pattern-based detection of jailbreak/injection attempts |
| **Content Filtering** | Blocks queries involving self-harm instructions |
| **Output Scanning** | Prevents PII from leaking in agent responses |
| **Audit Logging** | Tamper-evident security event log (without logging actual PII) |
| **No API Keys in Code** | All secrets via `.env` file (never committed) |
| **Non-root Docker** | Container runs as unprivileged user |

---

## 📁 Project Structure

```
mediguide-ai/
│
├── src/                        # Main application code
│   ├── agents/
│   │   ├── orchestrator.py     # Root coordinator agent (ADK)
│   │   ├── triage_agent.py     # Symptom triage sub-agent
│   │   ├── research_agent.py   # Medical research sub-agent
│   │   └── scheduler_agent.py  # Health scheduling sub-agent
│   ├── tools/
│   │   ├── security.py         # Security layer (PII, injection detection)
│   │   └── medical_tools.py    # Medical knowledge tool functions
│   └── main.py                 # Application entry point
│
├── mcp_server/                 # MCP Medical Knowledge Server
│   ├── server.py               # FastAPI MCP server
│   └── tools.py                # Tool registry & manifest
│
├── skills/                     # Agent Skills (Agents CLI compatible)
│   ├── symptom_checker.py      # Symptom assessment skill
│   └── medication_reminder.py  # Medication tracking skill
│
├── docs/                       # Documentation
│   ├── architecture.md         # Detailed architecture docs
│   └── KAGGLE_WRITEUP.md       # Competition writeup
│
├── Dockerfile                  # Multi-stage Docker build
├── docker-compose.yml          # Service orchestration
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template (safe to commit)
├── .gitignore                  # Excludes .env and secrets
└── README.md                   # This file
```

---

## ⚠️ Medical Disclaimer

**MediGuide AI is an educational tool and NOT a substitute for professional medical advice, diagnosis, or treatment.**

- Always seek the advice of a qualified healthcare provider with questions about a medical condition
- Never disregard professional medical advice based on information from this AI
- In case of a medical emergency, call your local emergency number immediately (India: 112/108, USA: 911, UK: 999)
- This tool is designed to help users navigate health information, not to diagnose or prescribe

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built for the **Kaggle AI Agents: Intensive Vibe Coding Capstone** using:
- [Google ADK](https://github.com/google/adk-python) — Multi-agent framework
- [Gemini 2.0 Flash](https://deepmind.google/technologies/gemini/) — LLM backbone
- [FastAPI](https://fastapi.tiangolo.com/) — MCP server transport
- Medical content based on publicly available educational resources (WHO, CDC, NHS guidelines)
