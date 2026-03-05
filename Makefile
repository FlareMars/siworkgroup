# =============================================================================
# SiWorkGroup - Development Makefile
# =============================================================================

.PHONY: help setup up down logs backend frontend db-migrate db-reset \
        test test-backend test-frontend lint format clean

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Environment Setup
# ---------------------------------------------------------------------------
setup: ## Initial project setup: copy .env and install dependencies
	@echo "→ Copying .env.example to .env..."
	@[ -f .env ] || cp .env.example .env
	@echo "→ Installing backend dependencies..."
	cd backend && python -m venv .venv && \
		source .venv/bin/activate && \
		pip install -e ".[dev]"
	@echo "→ Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✓ Setup complete. Edit .env with your configuration."

# ---------------------------------------------------------------------------
# Docker Compose
# ---------------------------------------------------------------------------
up: ## Start all services via Docker Compose (development)
	docker compose up -d

up-build: ## Build and start all services
	docker compose up -d --build

down: ## Stop all Docker Compose services
	docker compose down

down-volumes: ## Stop services and remove volumes (WARNING: deletes data)
	docker compose down -v

logs: ## Tail all service logs
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-frontend: ## Tail frontend logs
	docker compose logs -f frontend

# ---------------------------------------------------------------------------
# Infra-only (for local dev without containers)
# ---------------------------------------------------------------------------
infra-up: ## Start only PostgreSQL and Redis
	docker compose up -d postgres redis

infra-down: ## Stop PostgreSQL and Redis
	docker compose stop postgres redis

# ---------------------------------------------------------------------------
# Backend
# ---------------------------------------------------------------------------
backend: ## Run backend development server locally
	cd backend && source .venv/bin/activate && \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

celery: ## Run Celery worker locally
	cd backend && source .venv/bin/activate && \
		celery -A app.worker worker --loglevel=info

db-migrate: ## Apply database migrations (alembic upgrade head)
	cd backend && source .venv/bin/activate && \
		alembic upgrade head

db-migrate-auto: ## Auto-generate a new migration (usage: make db-migrate-auto MSG="description")
	cd backend && source .venv/bin/activate && \
		alembic revision --autogenerate -m "$(MSG)"

db-reset: ## Drop all tables and re-run migrations (WARNING: deletes data)
	cd backend && source .venv/bin/activate && \
		alembic downgrade base && alembic upgrade head

# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------
frontend: ## Run frontend development server locally
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && source .venv/bin/activate && \
		pytest --cov=app --cov-report=term-missing

test-frontend: ## Run frontend tests
	cd frontend && npm run test

type-check: ## Run TypeScript type checking
	cd frontend && npm run type-check

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------
lint: ## Lint backend and frontend
	cd backend && source .venv/bin/activate && ruff check app tests
	cd frontend && npm run lint

format: ## Format backend and frontend code
	cd backend && source .venv/bin/activate && ruff format app tests
	cd frontend && npm run format

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
clean: ## Remove build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/.next frontend/out 2>/dev/null || true
	@echo "✓ Cleaned up."