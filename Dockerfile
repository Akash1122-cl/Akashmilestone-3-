# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from phase 6 (the main backend)
COPY phase6/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Phase 5 and Phase 6 code
# Phase 6 depends on Phase 5's external_mcp_client
COPY phase5/src/ /app/phase5/src/
COPY phase6/src/ /app/phase6/src/

# Set Python path to include /app for module resolution
ENV PYTHONPATH="/app:/app/phase5/src:/app/phase6/src:${PYTHONPATH}"

# Expose the port (Render uses $PORT)
EXPOSE 8006

# Command to run the application
CMD ["sh", "-c", "uvicorn phase6.src.main:app --host 0.0.0.0 --port ${PORT:-8006}"]
