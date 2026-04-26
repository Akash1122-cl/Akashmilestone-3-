FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY templates/ ./templates/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8003

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
