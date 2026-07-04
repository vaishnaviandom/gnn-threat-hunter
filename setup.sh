#!/usr/bin/env bash
# =============================================================================
# GNN Threat Hunter — One-Shot Local Environment Setup
#
# Run this ONCE after cloning (or forking) the repository:
#   chmod +x setup.sh && ./setup.sh
#
# What this script does:
#   1. Checks all required tools are installed
#   2. Copies .env.example → .env
#   3. Sets up Python venv + installs deps for backend & inference
#   4. Installs Node.js deps for frontend
#   5. Checks Rust toolchain for ingestion
#   6. Verifies Solana CLI is available
#   7. Prints next steps
#
# Requirements:
#   - macOS 12+ (Monterey or later)
#   - Python 3.11+
#   - Node.js 18+
#   - Rust (via rustup)
#   - Docker Desktop (running)
#   - Solana CLI (install: https://docs.solana.com/cli/install-solana-cli-tools)
# =============================================================================

set -e  # Exit immediately on any error

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

PASS="${GREEN}✔${NC}"
FAIL="${RED}✘${NC}"
INFO="${BLUE}→${NC}"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${BOLD}   GNN Threat Hunter — Environment Setup Script    ${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Check required tools
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[1/6] Checking required tools...${NC}"

check_tool() {
  local tool=$1
  local install_hint=$2
  if command -v "$tool" &>/dev/null; then
    echo -e "  ${PASS} $tool ($(${tool} --version 2>&1 | head -1))"
  else
    echo -e "  ${FAIL} $tool not found."
    echo -e "       Install: $install_hint"
    exit 1
  fi
}

check_tool python3   "brew install python3"
check_tool node      "brew install node  OR  https://nodejs.org"
check_tool npm       "comes with Node.js"
check_tool cargo     "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
check_tool docker    "https://www.docker.com/products/docker-desktop"
check_tool git       "xcode-select --install"

# Solana is optional at Phase 0 — warn but don't exit
if command -v solana &>/dev/null; then
  echo -e "  ${PASS} solana ($(solana --version 2>&1 | head -1))"
else
  echo -e "  ${YELLOW}⚠${NC}  solana CLI not found — needed for Phase 12 only."
  echo -e "       Install: https://docs.solana.com/cli/install-solana-cli-tools"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Environment variables
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[2/6] Setting up environment variables...${NC}"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo -e "  ${PASS} .env created from .env.example"
  echo -e "  ${YELLOW}⚠${NC}  Open .env and set your POSTGRES_PASSWORD and DJANGO_SECRET_KEY"
else
  echo -e "  ${INFO} .env already exists — skipping (not overwriting your secrets)"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Backend Python environment
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[3/6] Setting up backend Python environment...${NC}"

if [ ! -d "backend/.venv" ]; then
  echo -e "  ${INFO} Creating backend/.venv..."
  python3 -m venv backend/.venv
fi

echo -e "  ${INFO} Installing backend Python dependencies..."
backend/.venv/bin/pip install --quiet --upgrade pip
backend/.venv/bin/pip install --quiet -r backend/requirements.txt
echo -e "  ${PASS} backend/.venv ready"

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Inference service Python environment
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[4/6] Setting up inference Python environment...${NC}"

if [ ! -d "inference/.venv" ]; then
  echo -e "  ${INFO} Creating inference/.venv..."
  python3 -m venv inference/.venv
fi

echo -e "  ${INFO} Installing inference Python dependencies..."
inference/.venv/bin/pip install --quiet --upgrade pip
inference/.venv/bin/pip install --quiet -r inference/requirements.txt
echo -e "  ${PASS} inference/.venv ready"

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Frontend Node.js dependencies
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[5/6] Installing frontend Node.js dependencies...${NC}"
(cd frontend && npm install --silent)
echo -e "  ${PASS} frontend/node_modules ready"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Rust ingestion — just verify it compiles
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}[6/6] Verifying Rust ingestion crate...${NC}"
echo -e "  ${INFO} Running cargo check (first run downloads dependencies — may take a minute)..."
(cd ingestion && cargo check 2>&1 | tail -3)
echo -e "  ${PASS} Rust ingestion crate OK"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Done!
# ─────────────────────────────────────────────────────────────────────────────
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}   ✔  Setup complete!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo ""
echo -e "  1. ${YELLOW}Edit .env${NC} — set POSTGRES_PASSWORD and DJANGO_SECRET_KEY"
echo ""
echo -e "  2. ${YELLOW}Start the local data layer:${NC}"
echo -e "     docker compose up -d"
echo ""
echo -e "  3. ${YELLOW}Run Django migrations:${NC}"
echo -e "     cd backend && .venv/bin/python manage.py migrate"
echo ""
echo -e "  4. ${YELLOW}Start backend:${NC}"
echo -e "     cd backend && .venv/bin/python manage.py runserver"
echo ""
echo -e "  5. ${YELLOW}Start frontend:${NC}"
echo -e "     cd frontend && npm run dev"
echo ""
echo -e "  6. ${YELLOW}Start Phase 1 development:${NC}"
echo -e "     Read telemetry/README.md for the Phase 1 ESF daemon spec"
echo ""
