FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install Linux system dependencies:
# - build-essential: compiler for python native packages
# - libpq-dev: PostgreSQL client development headers
# - postgresql-client: provides pg_isready utility
# - curl: used for healthcheck probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root or local
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend codebase
COPY backend/ ./backend/

# Copy and set execution permissions on entrypoint script
COPY backend/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose ASGI application port
EXPOSE 8000

# Container healthcheck probe against system health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
