# AI-Enhanced ThreatIngestor Production Dockerfile
# Updated for Python 3.11+ with AI capabilities and modern dependencies
FROM ubuntu:22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV OLLAMA_HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    sqlite3 \
    tesseract-ocr \
    python3-lxml \
    git \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-hackathon.txt .
COPY requirements.txt .

# Install Python dependencies
RUN python3.11 -m pip install --upgrade pip
RUN python3.11 -m pip install -r requirements-hackathon.txt
RUN python3.11 -m pip install opencv-python pytesseract numpy

# Install Ollama (for AI capabilities)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy application code
COPY app/ ./app/
COPY threatingestor/ ./threatingestor/
COPY simple_dashboard.py .
COPY populate_db.py .
COPY setup-ai.sh .
COPY *.md ./
COPY *.yml ./
COPY *.yaml ./

# Create necessary directories
RUN mkdir -p logs

# Initialize database
RUN python3.11 populate_db.py

# Expose ports
EXPOSE 7862 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7862/ || exit 1

# Start script
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]