#!/bin/bash
# =============================================================================
# SiWorkGroup - Local Development Setup Script (No Docker)
# Run this once to set up the local development environment
# Usage: bash scripts/local-setup.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERR]${NC}  $1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Homebrew prefix
BREW_PREFIX="$(brew --prefix)"
PG_BIN="${BREW_PREFIX}/opt/postgresql@16/bin"
NODE_BIN="${BREW_PREFIX}/opt/node@20/bin"

# Add to PATH for this session
export PATH="${PG_BIN}:${NODE_BIN}:${BREW_PREFIX}/bin:$PATH"

echo ""
echo "========================================"
echo "  SiWorkGroup Local Dev Setup"
echo "========================================"
echo ""

# =========================================
# 1. Check/Install PostgreSQL 16
# =========================================
log_info "Checking PostgreSQL 16..."
if ! brew list postgresql@16 &>/dev/null; then
    log_info "Installing PostgreSQL 16..."
    brew install postgresql@16
fi
log_success "PostgreSQL 16 installed"

# =========================================
# 2. Check/Install Redis
# =========================================
log_info "Checking Redis..."
if ! brew list redis &>/dev/null; then
    log_info "Installing Redis..."
    brew install redis
fi
log_success "Redis installed"

# =========================================
# 3. Check/Install Node.js 20
# =========================================
log_info "Checking Node.js 20..."
if ! brew list node@20 &>/dev/null; then
    log_info "Installing Node.js 20..."
    brew install node@20
fi
log_success "Node.js 20 installed"

# =========================================
# 4. Add PATH entries to .zshrc (idempotent)
# =========================================
ZSHRC="$HOME/.zshrc"
log_info "Updating PATH in $ZSHRC..."

add_path_entry() {
    local entry="$1"
    if ! grep -qF "$entry" "$ZSHRC" 2>/dev/null; then
        echo "export PATH=\"${entry}:\$PATH\"" >> "$ZSHRC"
        log_info "Added to .zshrc: $entry"
    fi
}

add_path_entry "${PG_BIN}"
add_path_entry "${NODE_BIN}"

log_success "PATH updated"

# =========================================
# 5. Start Services
# =========================================
log_info "Starting PostgreSQL 16..."
brew services start postgresql@16 || brew services restart postgresql@16
log_info "Starting Redis..."
brew services start redis || brew services restart redis

# Wait for PostgreSQL
log_info "Waiting for PostgreSQL to be ready..."
for i in $(seq 1 15); do
    if "${PG_BIN}/pg_isready" -q 2>/dev/null; then
        log_success "PostgreSQL is ready"
        break
    fi
    sleep 1
done

# =========================================
# 6. Setup Database
# =========================================
log_info "Setting up database..."

# Create user (ignore error if exists)
"${PG_BIN}/psql" postgres -tc "SELECT 1 FROM pg_roles WHERE rolname='siuser'" | grep -q 1 || \
    "${PG_BIN}/psql" postgres -c "CREATE USER siuser WITH PASSWORD 'sipass';"

# Create database (ignore error if exists)
"${PG_BIN}/psql" postgres -tc "SELECT 1 FROM pg_database WHERE datname='siworkgroup'" | grep -q 1 || \
    "${PG_BIN}/psql" postgres -c "CREATE DATABASE siworkgroup OWNER siuser;"

"${PG_BIN}/psql" postgres -c "GRANT ALL PRIVILEGES ON DATABASE siworkgroup TO siuser;" 2>/dev/null || true

# Extensions
"${PG_BIN}/psql" siworkgroup -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";' 2>/dev/null || true
"${PG_BIN}/psql" siworkgroup -c 'CREATE EXTENSION IF NOT EXISTS "pg_trgm";' 2>/dev/null || true

log_success "Database ready"

# =========================================
# 7. Backend Python Environment
# =========================================
log_info "Setting up Python backend..."
cd "${ROOT_DIR}/backend"

if [ ! -f ".venv/bin/activate" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv .venv
fi

log_info "Installing Python dependencies..."
.venv/bin/pip install -q -e ".[dev]"
log_success "Python deps installed"

# =========================================
# 8. Run Database Migrations
# =========================================
log_info "Running Alembic migrations..."

# Remove duplicate migration if both exist
if [ -f "alembic/versions/001_initial_schema.py" ] && [ -f "alembic/versions/1d515c75062f_initial_schema.py" ]; then
    log_warn "Duplicate migration files detected - removing auto-generated one"
    rm -f "alembic/versions/1d515c75062f_initial_schema.py"
fi

.venv/bin/alembic upgrade head
log_success "Migrations applied"

# Check tables
TABLES=$("${PG_BIN}/psql" -U siuser -d siworkgroup -c "\dt" 2>&1)
echo "$TABLES"

# =========================================
# 9. Frontend Setup
# =========================================
log_info "Setting up frontend..."
cd "${ROOT_DIR}/frontend"
"${NODE_BIN}/npm" install
log_success "Frontend deps installed"

# =========================================
# 10. Create .env if not exists
# =========================================
cd "${ROOT_DIR}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    log_info "Created .env from .env.example"
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Services running:"
brew services list | grep -E "postgresql|redis"
echo ""
echo "To start development servers:"
echo ""
echo "  Backend:  cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "API docs: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"
echo ""