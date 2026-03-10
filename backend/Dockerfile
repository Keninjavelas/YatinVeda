# YatinVeda Backend Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps: build tools + curl (for healthchecks) + libpq (for psycopg2)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer-cached when code changes but deps don't)
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY backend/ /app/

# Container startup script (wait for DB, migrate, start app)
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# Default command (overridden by docker-compose.yml)
CMD ["/app/entrypoint.sh"]
