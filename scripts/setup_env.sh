#!/bin/bash
# ============================================================
# VoiceGuard — Full Setup Script
# Usage: bash scripts/setup_env.sh
# Run from the project root directory.
# ============================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'   # No Color

info()    { echo -e "${CYAN}==>${NC} $1"; }
success() { echo -e "${GREEN}  ✓${NC}  $1"; }
warn()    { echo -e "${YELLOW}  ⚠${NC}  $1"; }
error()   { echo -e "${RED}  ✗${NC}  $1"; exit 1; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   VoiceGuard Compliance Intelligence Setup   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Check Python ──────────────────────────────────────────────────────
info "Checking Python version..."
python_version=$(python3 --version 2>&1 || python --version 2>&1)
echo "  Found: $python_version"

# ── Step 2: Install Python dependencies ──────────────────────────────────────
info "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt --quiet && success "Dependencies installed"

# ── Step 3: Check .env file ───────────────────────────────────────────────────
info "Checking .env configuration..."
if [ ! -f ".env" ]; then
    warn ".env file not found — creating template..."
    cat > .env << 'EOF'
# VoiceGuard — Environment Configuration
OPENAI_API_KEY=sk-...your-key-here...
# VOICEGUARD_DB_URL=sqlite:///./memory_store/compliance.db
# CHROMA_DIR=./memory_store/chroma_db
EOF
    warn "Please edit .env and add your real OPENAI_API_KEY before starting the server"
else
    if grep -q "sk-...your-key-here..." .env 2>/dev/null; then
        warn ".env exists but OPENAI_API_KEY is still a placeholder — agent will run in fallback mode"
    else
        success ".env file found with API key"
    fi
fi

# ── Step 4: Create required directories ──────────────────────────────────────
info "Creating required directories..."
mkdir -p memory_store reports data/uploads
success "Directories ready (memory_store/, reports/, data/uploads/)"

# ── Step 5: Initialise SQLite + ChromaDB ─────────────────────────────────────
info "Initialising memory (SQLite + ChromaDB)..."
python scripts/init_memory.py && success "Memory initialised"

# ── Step 6: Seed demo data ────────────────────────────────────────────────────
info "Seeding demo data (2 Finance incidents)..."
python scripts/seed_demo_data.py && success "Demo data seeded"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Setup complete! ✅                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo "  Start the server with:"
echo -e "    ${CYAN}uvicorn api.main:app --reload --port 8000${NC}"
echo ""
echo "  Then open:"
echo -e "    ${CYAN}http://localhost:8000/static/dashboard.html${NC}  ← Compliance Dashboard"
echo -e "    ${CYAN}http://localhost:8000/static/index.html${NC}       ← Basic Detector"
echo -e "    ${CYAN}http://localhost:8000/docs${NC}                    ← API Docs (Swagger)"
echo ""
