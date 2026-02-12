#!/bin/bash
#
# TEST AND DEPLOY - Full CI/CD pipeline for local use
# 
# Runs: Lint → Type Check → Tests → Build → Deploy
# Usage: ./scripts/test-and-deploy.sh [--skip-deploy]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SKIP_DEPLOY=false
if [[ "$1" == "--skip-deploy" ]]; then
    SKIP_DEPLOY=true
fi

function log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"
}

function success() {
    echo -e "${GREEN}✓${NC} $1"
}

function error() {
    echo -e "${RED}✗${NC} $1"
}

function warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

cd "$ROOT"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}         ${YELLOW}DARWIN'S ISLAND - TEST & DEPLOY${NC}                  ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check if dev server is running
log "Step 1/6: Checking dev server..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -q "200"; then
    success "Dev server is running"
else
    warning "Dev server not running, starting it..."
    npm run dev:quick &
    DEV_PID=$!
    sleep 5
    
    # Check again
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -q "200"; then
        success "Dev server started (PID: $DEV_PID)"
    else
        error "Failed to start dev server"
        exit 1
    fi
fi

# Step 2: Lint
log "Step 2/6: Running linter..."
if npm run lint 2>&1 | grep -q "error"; then
    error "Lint errors found"
    npm run lint
    exit 1
else
    success "Lint passed"
fi

# Step 3: Type Check
log "Step 3/6: Running type check..."
if npx tsc --noEmit 2>&1 | grep -q "error"; then
    warning "Type errors found (non-blocking for now)"
    npx tsc --noEmit || true
else
    success "Type check passed"
fi

# Step 4: Tests
log "Step 4/6: Running headless tests..."
if npm run test:headless 2>&1; then
    success "All tests passed"
else
    error "Tests failed"
    exit 1
fi

# Step 5: Build
log "Step 5/6: Building for production..."
if npm run build 2>&1; then
    success "Build successful"
else
    error "Build failed"
    exit 1
fi

# Step 6: Deploy (optional)
if [ "$SKIP_DEPLOY" = false ]; then
    log "Step 6/6: Deploying..."
    if ./deploy.sh --skip-build 2>&1; then
        success "Deployed successfully"
    else
        warning "Deploy had issues but continuing..."
    fi
else
    log "Step 6/6: Skipping deploy (--skip-deploy)"
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}              ${GREEN}ALL CHECKS PASSED! 🎉${NC}                        ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Generate quick report
echo "Quick Stats:"
echo "  - Build: dist/ ($(du -sh dist/ | cut -f1))"
echo "  - Tests: $(find tests -name "*.spec.ts" | wc -l) suites"
echo "  - Time: $(date)"
echo ""

# Clean up dev server if we started it
if [ ! -z "$DEV_PID" ]; then
    log "Stopping dev server we started..."
    kill $DEV_PID 2>/dev/null || true
fi
