"""
MediGuide AI - MCP (Model Context Protocol) Medical Knowledge Server
=====================================================================
A custom MCP server that exposes medical knowledge tools to AI agents.
This server implements the Model Context Protocol specification, allowing
any MCP-compatible AI agent to access structured medical information.

MCP Architecture:
  AI Agent ←→ MCP Client ←→ [HTTP/SSE] ←→ MCP Server (this file)
                                              ↓
                                        Medical Knowledge Base

Why MCP?
  - Standardized tool discovery and invocation
  - Language-agnostic (any MCP client can connect)
  - Enables real-time knowledge retrieval vs. static training data
  - Pluggable — swap databases without changing agent code

Endpoints:
  - GET  /health          : Server health check
  - GET  /tools           : List available tools (MCP tool discovery)
  - POST /tools/call      : Execute a tool (MCP tool invocation)
  - GET  /resources       : List available resources
  - SSE  /events          : Server-Sent Events for streaming (MCP SSE transport)

Start the server:
  python mcp_server/server.py

Then connect from your ADK agent using the MCP client configuration.

Kaggle Evaluation: Demonstrates "MCP Server" course concept.
"""

import json
import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

# FastAPI for the HTTP/SSE transport layer
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mcp_server.tools import (
    MCPToolRegistry,
    MEDICAL_TOOLS_MANIFEST,
)

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-SERVER] %(levelname)s: %(message)s",
)
logger = logging.getLogger("mediguide.mcp_server")

# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Application
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MediGuide MCP Medical Knowledge Server",
    description=(
        "A Model Context Protocol (MCP) server exposing medical knowledge tools "
        "to AI agents. Part of the MediGuide AI multi-agent healthcare system."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow all origins in development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to your agent's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the tool registry
tool_registry = MCPToolRegistry()


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models for MCP Protocol
# ─────────────────────────────────────────────────────────────────────────────

class ToolCallRequest(BaseModel):
    """MCP tool call request schema."""
    tool_name: str
    parameters: dict = {}
    request_id: Optional[str] = None


class ToolCallResponse(BaseModel):
    """MCP tool call response schema."""
    request_id: Optional[str]
    tool_name: str
    result: Any
    execution_time_ms: float
    timestamp: str
    status: str  # "success" | "error"
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# MCP Server Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """
    Server health check endpoint.
    Used by orchestration systems and load balancers to verify server status.
    """
    return {
        "status": "healthy",
        "server": "MediGuide MCP Medical Knowledge Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "tools_available": len(MEDICAL_TOOLS_MANIFEST),
        "uptime": "operational",
    }


@app.get("/tools")
async def list_tools():
    """
    MCP Tool Discovery Endpoint.
    Returns the manifest of all available tools with their schemas.
    Agents call this to discover what tools are available.
    """
    logger.info("Tool discovery request received")
    return {
        "protocol": "MCP/1.0",
        "server_name": "mediguide-medical-knowledge",
        "tools": MEDICAL_TOOLS_MANIFEST,
        "total_tools": len(MEDICAL_TOOLS_MANIFEST),
    }


@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """
    MCP Tool Invocation Endpoint.
    Executes a tool by name with given parameters and returns the result.

    This is the core MCP interaction — agents call this to get medical data.
    """
    start_time = datetime.now()
    logger.info(f"Tool call: {request.tool_name} with params: {list(request.parameters.keys())}")

    try:
        # Validate tool exists
        if request.tool_name not in tool_registry.tools:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{request.tool_name}' not found. Call GET /tools to see available tools.",
            )

        # Execute the tool
        result = await tool_registry.execute(request.tool_name, request.parameters)

        # Calculate execution time
        exec_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"Tool '{request.tool_name}' executed in {exec_time:.2f}ms")

        return ToolCallResponse(
            request_id=request.request_id,
            tool_name=request.tool_name,
            result=result,
            execution_time_ms=exec_time,
            timestamp=datetime.now().isoformat(),
            status="success",
        )

    except HTTPException:
        raise
    except Exception as e:
        exec_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Tool '{request.tool_name}' failed: {str(e)}")

        return ToolCallResponse(
            request_id=request.request_id,
            tool_name=request.tool_name,
            result=None,
            execution_time_ms=exec_time,
            timestamp=datetime.now().isoformat(),
            status="error",
            error=str(e),
        )


@app.get("/resources")
async def list_resources():
    """
    MCP Resources Endpoint.
    Lists available knowledge resources that agents can access.
    """
    return {
        "resources": [
            {
                "id": "medical_conditions_db",
                "name": "Medical Conditions Database",
                "description": "Curated database of medical conditions with symptoms, treatments, and specialists",
                "type": "structured_knowledge",
                "record_count": 3,
            },
            {
                "id": "medication_db",
                "name": "Medication Information Database",
                "description": "Drug information including uses, side effects, interactions, and warnings",
                "type": "structured_knowledge",
                "record_count": 4,
            },
            {
                "id": "symptom_patterns",
                "name": "Symptom Pattern Database",
                "description": "Symptom-to-condition mapping with urgency classifications",
                "type": "structured_knowledge",
                "record_count": 8,
            },
            {
                "id": "drug_interactions",
                "name": "Drug Interaction Database",
                "description": "Known drug-drug interactions with severity levels",
                "type": "structured_knowledge",
                "record_count": 4,
            },
        ],
        "total_resources": 4,
    }


@app.get("/events")
async def sse_events(request: Request):
    """
    Server-Sent Events (SSE) endpoint for MCP streaming transport.
    Enables real-time streaming of tool results to agents.
    """
    async def event_generator():
        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'server': 'mediguide-mcp', 'timestamp': datetime.now().isoformat()})}\n\n"

        # Keep connection alive with periodic heartbeat
        count = 0
        while True:
            if await request.is_disconnected():
                logger.info("SSE client disconnected")
                break

            # Heartbeat every 30 seconds
            await asyncio.sleep(30)
            count += 1
            yield f"data: {json.dumps({'type': 'heartbeat', 'count': count, 'timestamp': datetime.now().isoformat()})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "MediGuide MCP Medical Knowledge Server",
        "description": "Model Context Protocol server for healthcare AI agents",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "tools": "GET /tools",
            "call_tool": "POST /tools/call",
            "resources": "GET /resources",
            "events": "GET /events (SSE)",
            "docs": "GET /docs",
        },
        "project": "MediGuide AI — Kaggle AI Agents Capstone",
        "github": "https://github.com/maruthisaiteja/mediguide-ai",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Server Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", "8080"))
    host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")

    logger.info(f"🚀 Starting MediGuide MCP Server on {host}:{port}")
    logger.info(f"📚 {len(MEDICAL_TOOLS_MANIFEST)} medical tools available")
    logger.info(f"📖 API docs available at http://localhost:{port}/docs")

    uvicorn.run(
        "mcp_server.server:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        log_level="info",
    )
