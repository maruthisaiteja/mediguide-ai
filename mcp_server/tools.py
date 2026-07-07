"""
MediGuide AI - MCP Tool Registry and Manifest
===============================================
Defines the tool registry for the MCP server.
Each tool has:
  - A manifest entry (schema for tool discovery)
  - An async implementation function
  - Input validation
  - Structured output format

The tool manifest follows the MCP tool schema specification,
allowing any MCP-compatible client (including ADK agents) to
discover and invoke these tools dynamically.
"""

import asyncio
import sys
import os
from typing import Any, Callable, Coroutine

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.tools.medical_tools import (
    get_condition_overview,
    get_medication_info,
    check_drug_interactions,
    get_specialist_recommendation,
    get_preventive_guidelines,
    search_medical_database,
    get_body_system_info,
    lookup_symptom_patterns,
    get_emergency_contacts,
)


# ─────────────────────────────────────────────────────────────────────────────
# MCP Tool Manifest
# This is what agents see when they call GET /tools
# ─────────────────────────────────────────────────────────────────────────────
MEDICAL_TOOLS_MANIFEST = [
    {
        "name": "get_condition_info",
        "description": (
            "Retrieves comprehensive medical information about a health condition. "
            "Returns overview, causes, symptoms, diagnosis methods, treatments, and prevention. "
            "Use for: 'Tell me about diabetes', 'What is hypertension?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "condition_name": {
                    "type": "string",
                    "description": "Name of the medical condition (e.g., 'type 2 diabetes', 'hypertension', 'migraine')",
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["brief", "standard", "detailed"],
                    "description": "Level of detail in the response",
                    "default": "standard",
                },
            },
            "required": ["condition_name"],
        },
        "category": "medical_knowledge",
        "safety_level": "educational",
    },
    {
        "name": "get_medication_info",
        "description": (
            "Retrieves medication information: drug class, uses, side effects, warnings, "
            "contraindications, and interactions. Does NOT provide dosing instructions. "
            "Use for: 'Tell me about metformin', 'What are the side effects of ibuprofen?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "medication_name": {
                    "type": "string",
                    "description": "Generic or brand name of the medication",
                },
            },
            "required": ["medication_name"],
        },
        "category": "medication_safety",
        "safety_level": "educational",
    },
    {
        "name": "check_drug_interactions",
        "description": (
            "Checks for known drug-drug interactions in a list of medications. "
            "Returns severity levels and recommendations. "
            "Use for: 'Is it safe to take aspirin and warfarin together?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "medications": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of medication names to check for interactions",
                },
            },
            "required": ["medications"],
        },
        "category": "medication_safety",
        "safety_level": "advisory",
    },
    {
        "name": "get_specialist_recommendation",
        "description": (
            "Recommends the appropriate medical specialist for a condition or symptom set. "
            "Also generates smart questions to ask the doctor. "
            "Use for: 'What type of doctor should I see for heart problems?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "condition_or_symptoms": {
                    "type": "string",
                    "description": "The health concern or symptom set to find a specialist for",
                },
            },
            "required": ["condition_or_symptoms"],
        },
        "category": "care_navigation",
        "safety_level": "educational",
    },
    {
        "name": "get_preventive_guidelines",
        "description": (
            "Returns evidence-based preventive health guidelines for a specific topic. "
            "Use for: 'How can I prevent heart disease?', 'What are diabetes prevention tips?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "health_topic": {
                    "type": "string",
                    "description": "The preventive health topic (e.g., 'heart disease prevention')",
                },
            },
            "required": ["health_topic"],
        },
        "category": "preventive_health",
        "safety_level": "educational",
    },
    {
        "name": "search_medical_knowledge",
        "description": (
            "Free-text search across the medical knowledge base. "
            "Searches conditions, medications, and symptom patterns simultaneously. "
            "Use for broad queries or when the specific category is unclear."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language medical query",
                },
                "source_preference": {
                    "type": "string",
                    "enum": ["peer_reviewed", "clinical_guidelines", "patient_education"],
                    "description": "Preferred type of source",
                    "default": "peer_reviewed",
                },
            },
            "required": ["query"],
        },
        "category": "search",
        "safety_level": "educational",
    },
    {
        "name": "get_body_system_info",
        "description": (
            "Returns health information about a specific body system: "
            "common conditions, warning signs, and self-care options. "
            "Use for: 'Tell me about cardiovascular health', 'What affects the respiratory system?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "body_area": {
                    "type": "string",
                    "description": "Body system name (e.g., 'cardiovascular', 'respiratory', 'digestive', 'neurological')",
                },
            },
            "required": ["body_area"],
        },
        "category": "medical_knowledge",
        "safety_level": "educational",
    },
    {
        "name": "get_emergency_contacts",
        "description": (
            "Returns emergency contact numbers for major world regions. "
            "Use when the user may need emergency assistance."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "category": "emergency",
        "safety_level": "critical",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# MCP Tool Registry
# ─────────────────────────────────────────────────────────────────────────────
class MCPToolRegistry:
    """
    Registry that maps tool names to their async implementations.
    Handles parameter validation and standardized error responses.
    """

    def __init__(self):
        # Register all tools
        self.tools: dict[str, Callable] = {
            "get_condition_info": self._get_condition_info,
            "get_medication_info": self._get_medication_info,
            "check_drug_interactions": self._check_drug_interactions,
            "get_specialist_recommendation": self._get_specialist_recommendation,
            "get_preventive_guidelines": self._get_preventive_guidelines,
            "search_medical_knowledge": self._search_medical_knowledge,
            "get_body_system_info": self._get_body_system_info,
            "get_emergency_contacts": self._get_emergency_contacts,
        }

    async def execute(self, tool_name: str, parameters: dict) -> Any:
        """
        Executes a tool by name with given parameters.
        All tools are async for non-blocking server operation.
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")

        handler = self.tools[tool_name]
        return await handler(parameters)

    # ── Tool Implementations ──────────────────────────────────────────────────

    async def _get_condition_info(self, params: dict) -> dict:
        """MCP handler for get_condition_info tool."""
        condition = params.get("condition_name", "")
        detail = params.get("detail_level", "standard")
        if not condition:
            raise ValueError("condition_name is required")
        return await asyncio.to_thread(get_condition_overview, condition, detail)

    async def _get_medication_info(self, params: dict) -> dict:
        """MCP handler for get_medication_info tool."""
        medication = params.get("medication_name", "")
        if not medication:
            raise ValueError("medication_name is required")
        return await asyncio.to_thread(get_medication_info, medication)

    async def _check_drug_interactions(self, params: dict) -> dict:
        """MCP handler for check_drug_interactions tool."""
        medications = params.get("medications", [])
        if not medications or len(medications) < 2:
            raise ValueError("At least 2 medications are required to check interactions")
        return await asyncio.to_thread(check_drug_interactions, medications)

    async def _get_specialist_recommendation(self, params: dict) -> dict:
        """MCP handler for get_specialist_recommendation tool."""
        concern = params.get("condition_or_symptoms", "")
        if not concern:
            raise ValueError("condition_or_symptoms is required")
        return await asyncio.to_thread(get_specialist_recommendation, concern)

    async def _get_preventive_guidelines(self, params: dict) -> dict:
        """MCP handler for get_preventive_guidelines tool."""
        topic = params.get("health_topic", "general health")
        return await asyncio.to_thread(get_preventive_guidelines, topic)

    async def _search_medical_knowledge(self, params: dict) -> dict:
        """MCP handler for search_medical_knowledge tool."""
        query = params.get("query", "")
        source_pref = params.get("source_preference", "peer_reviewed")
        if not query:
            raise ValueError("query is required")
        return await asyncio.to_thread(search_medical_database, query, source_pref)

    async def _get_body_system_info(self, params: dict) -> dict:
        """MCP handler for get_body_system_info tool."""
        body_area = params.get("body_area", "")
        if not body_area:
            raise ValueError("body_area is required")
        return await asyncio.to_thread(get_body_system_info, body_area)

    async def _get_emergency_contacts(self, params: dict) -> dict:
        """MCP handler for get_emergency_contacts tool."""
        return await asyncio.to_thread(get_emergency_contacts)
