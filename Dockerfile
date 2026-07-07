# ─────────────────────────────────────────────────────────────────────────────
# MediGuide AI — Docker Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Demonstrates "Deployability" — one of the 6 Kaggle evaluation concepts
#
# Build: docker build -t mediguide-ai .
# Run:   docker run -p 8080:8080 --env-file .env mediguide-ai
#
# Multi-stage build for minimal production image size
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir wheel

# ── Stage 2: Production Image ─────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Security: run as non-root user
RUN groupadd --gid 1000 mediguide \
    && useradd --uid 1000 --gid mediguide --shell /bin/bash --create-home mediguide

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=mediguide:mediguide . .

# Switch to non-root user
USER mediguide

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${MCP_SERVER_PORT:-8080}/health || exit 1

# Expose MCP server port
EXPOSE 8080

# Environment defaults (override with --env-file or -e flags)
ENV MCP_SERVER_PORT=8080 \
    MCP_SERVER_HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    APP_ENV=production \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Entry point: start the MCP server by default
# Override with: docker run mediguide-ai python src/main.py --demo
CMD ["python", "mcp_server/server.py"]

# ─────────────────────────────────────────────────────────────────────────────
# Alternative: Run interactive agent
# CMD ["python", "src/main.py"]
#
# For Google Cloud Run:
# gcloud run deploy mediguide-ai \
#   --image gcr.io/PROJECT_ID/mediguide-ai \
#   --platform managed \
#   --region us-central1 \
#   --allow-unauthenticated
# ─────────────────────────────────────────────────────────────────────────────
