#!/bin/bash
# =============================================================================
# SiWorkGroup - Start Development Servers
# Usage: bash scripts/start-dev.sh
# =============================================================================

BREW_PREFIX="$(brew --prefix 2>/dev/null || echo /opt/homebrew)"
export PATH="${BREW_PREFIX}/opt/postgresql@16/bin:${BREW_PREFIX}/opt/node@20/bin:${BREW_PREFIX}/bin:$PATH"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting SiWorkGroup development environment..."
echo ""

# Ensure services are running
echo "→ Ensuring PostgreSQL is running..."
brew services start postgresql@16 2>/dev/null || true

echo "→ Ensuring Redis is running..."
brew services start redis 2>/dev/null || true

sleep 1

echo "→ Starting Backend (FastAPI on :8000)..."
cd "${ROOT_DIR}/backend"
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 2

echo "→ Starting Frontend (Next.js on :3000)..."
cd "${ROOT_DIR}/frontend"
"${BREW_PREFIX}/opt/node@20/bin/npm" run dev &
FRONTEND_PID=$!

echo ""
echo "================================================================"
echo "  SiWorkGroup is starting up"
echo "================================================================"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Frontend:  http://localhost:3000"
echo "================================================================"
echo ""
echo "  Press Ctrl+C to stop all services"
echo ""

# Wait for processes and handle Ctrl+C
trap "echo 'Stopping...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait $BACKEND_PID $FRONTEND_PID