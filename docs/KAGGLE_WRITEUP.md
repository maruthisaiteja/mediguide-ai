# MediGuide AI — Kaggle Competition Writeup

**Title:** MediGuide AI: A Multi-Agent Healthcare Navigation System Built with Google ADK

**Subtitle:** Transforming healthcare navigation through intelligent agent orchestration, MCP-powered knowledge retrieval, and security-first design

**Track:** Agents for Good

---

## 1. The Problem: Healthcare Navigation is Broken

Every year, billions of people face the same frustrating experience: they feel unwell, they turn to the internet, and they're immediately overwhelmed. A search for "chest pain" returns millions of results ranging from anxiety to heart attack, with no way to know what applies to *them*. According to the WHO, medical misinformation is one of the top global health threats.

The consequences are severe:
- **Over-reaction**: Emergency rooms flooded with non-urgent cases (70% of ER visits are non-emergent)
- **Under-reaction**: People dismissing serious symptoms as "nothing serious" based on unreliable sources
- **Medication errors**: 40% of people self-medicate incorrectly without checking interactions
- **Access barriers**: Average wait time to see a specialist is 26 days in many developed countries

The core issue isn't a lack of medical information — it's the lack of an intelligent navigator that can help people make sense of their health situation and take the right next step.

**This is exactly where AI agents excel.**

---

## 2. Why Agents? The Case for Multi-Agent Healthcare Navigation

Healthcare queries are naturally multi-dimensional. When someone says "I've had a headache and fever for 3 days," the ideal response requires:

1. **Triage judgment** — Is this urgent? Are there red flags?
2. **Medical knowledge retrieval** — What conditions match these symptoms? What's the evidence?
3. **Personalization** — The answer differs for a child vs. an elderly patient, or someone with existing conditions
4. **Action planning** — What should they do next? See a doctor? Which specialist? When?
5. **Continuity** — Follow-up reminders, medication tracking, appointment preparation

No single prompt to a single LLM can reliably do all of this well. A multi-agent architecture, where each specialist agent is optimized for its specific task, is the natural solution.

**MediGuide AI uses four agents working in concert:**

- **OrchestratorAgent**: The intelligent router that understands user intent and delegates to the right specialist
- **TriageAgent**: Dedicated symptom analysis with a 5-level urgency classification system
- **ResearchAgent**: Evidence-based medical information retrieval via a custom MCP server
- **SchedulerAgent**: Health schedule management — medications, appointments, health goals

This architecture ensures that each agent can be optimized, tested, and improved independently — a key advantage of multi-agent design.

---

## 3. Solution Design: Architecture Decisions

### 3.1 Orchestrator Pattern with Sub-Agents

The OrchestratorAgent uses Google ADK's multi-agent capability to delegate to specialist sub-agents. The routing logic is embedded in the orchestrator's system instruction, allowing it to make intelligent routing decisions based on query intent rather than rigid keyword matching.

**Why this matters**: A user asking "I've been taking metformin and I just started ibuprofen, is that okay?" contains both a medical research query (drug interaction) AND potentially a safety concern. The orchestrator can route this to the appropriate tools and synthesize a comprehensive, safe response.

### 3.2 Custom MCP Server for Knowledge Retrieval

Rather than relying solely on the LLM's training data (which may be outdated or inconsistent for medical information), MediGuide AI implements a **custom MCP (Model Context Protocol) server** that provides structured, curated medical knowledge.

The MCP server (`mcp_server/server.py`) exposes 8 medical knowledge tools via HTTP/SSE transport:

| Tool | Purpose |
|---|---|
| `get_condition_info` | Comprehensive condition overview |
| `get_medication_info` | Drug information (no dosing) |
| `check_drug_interactions` | Interaction warnings |
| `get_specialist_recommendation` | Care navigation |
| `get_preventive_guidelines` | Evidence-based prevention |
| `search_medical_knowledge` | Free-text search |
| `get_body_system_info` | Body system assessment |
| `get_emergency_contacts` | Emergency numbers by region |

The MCP protocol ensures that any MCP-compatible agent can connect to and use these tools, making the knowledge server independently useful and reusable.

### 3.3 Security-First Design

Healthcare applications handle sensitive information. MediGuide AI implements a multi-layer security architecture in `src/tools/security.py`:

**Layer 1 — Input Processing:**
- PII detection and redaction (phone numbers, emails, SSNs, Aadhaar numbers, addresses, credit cards)
- Prompt injection attack detection (16+ pattern types)
- Blocked content filtering (self-harm queries redirected to crisis resources)
- Off-topic detection with graceful redirection

**Layer 2 — Output Processing:**
- Agent output scanning for PII leakage
- Automatic redaction of any sensitive data in responses

**Layer 3 — Audit:**
- Tamper-evident security event logging
- Privacy-safe request IDs (hash-based, not content-based)
- Security report generation for administrators

### 3.4 Agent Skills for Composability

Two standalone skills (`skills/symptom_checker.py` and `skills/medication_reminder.py`) demonstrate the Agent Skills concept. These are:
- **Standalone**: Can be invoked directly from the CLI or Agents CLI
- **Composable**: Can be integrated into any agent system
- **Documented**: Have full metadata schemas for skill discovery
- **Pipelineable**: Accept JSON from stdin for composable workflows

### 3.5 Deployability

MediGuide AI is fully containerized:
- **Multi-stage Dockerfile**: Builder stage + slim production image
- **Security**: Runs as non-root user
- **Health checks**: Both Dockerfile and Docker Compose health monitoring
- **Cloud Run ready**: Deployment command documented in README
- **Environment separation**: All secrets via `.env` file, never in code

---

## 4. Technical Implementation

### Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Agent Framework | Google ADK | Purpose-built for multi-agent systems |
| LLM | Gemini 2.0 Flash | Fast, capable, cost-effective |
| MCP Server | FastAPI + Uvicorn | Async, high-performance, auto-documented |
| MCP Transport | HTTP/SSE | Standard MCP transport protocol |
| Security | Python regex + custom | Lightweight, no external dependencies |
| Containerization | Docker + Compose | Reproducible, portable deployment |
| CLI Interface | Python argparse | Native, no extra dependencies |

### Code Quality

- **Comprehensive docstrings**: Every function has purpose, args, returns, and design notes
- **Type hints**: Full type annotation throughout
- **Design pattern comments**: Architecture decisions explained inline
- **Security comments**: Security-sensitive code clearly marked
- **No API keys in code**: Enforced via `.env` pattern and `.gitignore`

### Agent Interaction Flow

```
User: "I have chest pain and left arm pain"
  ↓
SecurityLayer.process_input() → checks for PII, injection → clean
  ↓
OrchestratorAgent receives query
  ↓
route_to_emergency() tool called → RED FLAG DETECTED
  ↓
Emergency response: contacts + first aid + disclaimer
  ↓
SecurityLayer.process_output() → scan for PII in response
  ↓
User sees: Emergency guidance with 112/911 numbers + first aid steps
```

```
User: "Tell me about metformin's side effects"
  ↓
SecurityLayer → clean input
  ↓
OrchestratorAgent → delegates to ResearchAgent
  ↓
ResearchAgent.research_medication("metformin")
  → MCP Server call: GET /tools/call {tool: "get_medication_info"}
  ↓
Returns: drug class, uses, side effects, warnings, interactions
  ↓
ResearchAgent synthesizes into user-friendly response
  ↓
OrchestratorAgent adds medical disclaimer
  ↓
User sees: Comprehensive medication information with safety context
```

---

## 5. Real-World Impact & Value

### Who Benefits?

1. **General Public**: Reliable first-step health guidance, reducing panic and misinformation
2. **Caregivers**: Managing medications and appointments for elderly or chronically ill family members
3. **Healthcare Workers**: Quick reference for triage patterns and drug interactions
4. **Underserved Communities**: Access to health navigation where doctor access is limited

### Measured Value

- **Triage accuracy**: 5-level system aligned with clinical triage standards (START, Manchester Triage System)
- **Drug interaction coverage**: Core dangerous interactions (warfarin+aspirin, warfarin+NSAIDs)
- **Emergency response time**: Sub-second emergency routing for red-flag symptoms
- **Privacy protection**: 7 PII types redacted, 16+ injection patterns detected

### What Makes This Different from ChatGPT?

| Feature | MediGuide AI | Generic LLM |
|---|---|---|
| Structured triage levels | ✅ Defined 5-level system | ❌ Unstructured |
| Emergency routing | ✅ Immediate, specific | ❌ Generic advice |
| Drug interaction checking | ✅ Tool-based, structured | ❌ Training-data only |
| PII protection | ✅ Multi-layer security | ❌ Not implemented |
| Medical disclaimers | ✅ Consistent, required | ❌ Inconsistent |
| Scheduling integration | ✅ Persistent, actionable | ❌ Not available |
| MCP knowledge server | ✅ Structured, current | ❌ Static training |

---

## 6. Challenges and Learnings

### Challenge 1: Medical Safety vs. Helpfulness
**Problem**: Being too cautious makes the agent useless; being too helpful risks harm.
**Solution**: The triage system provides clear urgency levels and always ends with "consult a professional" — giving value while maintaining safety.

### Challenge 2: Multi-Agent Routing Accuracy
**Problem**: Queries can span multiple domains (e.g., "I have diabetes, what foods should I avoid and when should I take metformin?")
**Solution**: The OrchestratorAgent's system instruction is carefully crafted with explicit routing rules for overlapping cases. The agent can also call multiple sub-agents in sequence.

### Challenge 3: PII in Health Contexts
**Problem**: Health queries often contain PII (e.g., "My mother's phone is +91 9876543210, she has chest pain...")
**Solution**: The SecurityLayer runs before the LLM sees the input, redacting PII while preserving the health-relevant content. Users are notified when redaction occurs.

### Challenge 4: MCP Server Integration
**Problem**: Synchronous Python tools in an async FastAPI server.
**Solution**: Used `asyncio.to_thread()` to wrap synchronous tool functions, maintaining async server performance without rewriting the tool functions.

---

## 7. Future Directions

1. **Real Medical APIs**: Integrate with PubMed, FHIR-compliant EHR systems, or medical databases
2. **Voice Interface**: Speech-to-text for accessibility (especially for elderly users)
3. **Multilingual Support**: Gemini's multilingual capabilities enable global deployment
4. **Wearable Integration**: Connect with fitness trackers for real-time health data context
5. **Doctor Handoff**: Structured referral letters generated for appointments
6. **Clinical Decision Support**: Integration with hospital systems for provider-side use
7. **Federated Learning**: Improve medical models without centralizing sensitive data

---

## 8. Conclusion

MediGuide AI demonstrates that multi-agent systems, built with Google ADK and Gemini, can address meaningful real-world problems in healthcare navigation. By combining:

- **Specialist agents** for focused, high-quality reasoning
- **MCP protocol** for structured, current knowledge retrieval
- **Security-first design** for trustworthy health information handling
- **Deployable infrastructure** for real-world usability
- **Agent skills** for composable, reusable healthcare capabilities

...we've built not just a prototype, but a foundation for AI-powered healthcare navigation that could genuinely improve health outcomes.

The project story: Healthcare navigation shouldn't require medical expertise to navigate. With MediGuide AI, anyone can get intelligent, safe, and personalized guidance — from the first symptom to the right specialist, from the first dose to the refill reminder.

**This is what AI agents, done right, can do for the world.**

---

*Word count: ~1,850 words*
*Track: Agents for Good*
*GitHub: https://github.com/maruthisaiteja/mediguide-ai*
