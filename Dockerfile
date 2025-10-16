# Use Python 3.11 slim image for security and size optimization
FROM python:3.11-slim

# Security: Create non-root user for running the application
RUN groupadd -r memebot && useradd -r -g memebot memebot

# Set working directory
WORKDIR /app

# Install system dependencies (minimal set for security)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ ./src/
COPY main.py .
COPY .env.example .env.example

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R memebot:memebot /app

# Security: Switch to non-root user
USER memebot

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PAPER_MODE=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose only necessary port (GUI API socket)
EXPOSE 8080

# Default command - run the bot in paper mode
ENTRYPOINT ["python", "main.py", "--paper-mode"]
