# =============================================================================
# SiWorkGroup Backend - Multi-stage Dockerfile
# =============================================================================

# ---------------------------------------------------------------------------
# Base stage
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---------------------------------------------------------------------------
# Dependencies stage
# ---------------------------------------------------------------------------
FROM base AS dependencies

COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install hatchling && \
    pip install -e ".[dev]"

# ---------------------------------------------------------------------------
# Development stage
# ---------------------------------------------------------------------------
FROM dependencies AS development

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------------------------
# Production stage
# ---------------------------------------------------------------------------
FROM base AS production

COPY pyproject.toml .
RUN pip install --upgrade pip && \
    pip install hatchling && \
    pip install -e "."

COPY . .

# Create non-root user
RUN groupadd -r siapp && useradd -r -g siapp siapp && \
    chown -R siapp:siapp /app
USER siapp

EXPOSE 8000

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools"]