# Canvas Learning System - FastAPI Backend
# Story 1.1: Docker environment setup
# Python 3.11-slim for minimal image size

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (curl for healthcheck, build tools for some pip packages)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add src/ to Python path for agentic_rag module
ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"

# Expose FastAPI port
EXPOSE 8001

# Start uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
