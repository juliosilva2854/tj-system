# Backend Dockerfile - Gestao TJ (Railway 2025 Optimized)
# Based on Railway best practices for Python/FastAPI apps

FROM python:3.12-slim

# Railway 2025 recommended environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only essential system dependencies (Railway best practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt1-dev \
    libjpeg-dev zlib1g-dev \
    libfreetype6-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements first (better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || true

# Copy application code
COPY . .

# Railway will inject PORT via environment variable
# No hardcoded port - Railway 2025 requirement
EXPOSE 8001

# Health check endpoint (Railway 2025 best practice)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8001}/api/health || exit 1

# Use exec form to handle signals properly (Docker best practice 2025)
# Railway will use PORT from environment
CMD ["sh", "-c", "python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001} --workers 2"]
