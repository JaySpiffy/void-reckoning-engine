#!/bin/bash
#
# OVERNIGHT SIMULATIONS - Run extended batch with persistence
#
# Usage: ./scripts/overnight-simulations.sh [count] [&]
# 
# Features:
# - Runs in background (survives disconnect)
# - Logs to file
# - Email/notify on completion
# - Resume capability

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
COUNT="${1:-500}"
LOG_FILE="$ROOT/simulation-results/overnight-$(date +%Y%m%d-%H%M%S).log"
PID_FILE="$ROOT/.overnight-sim.pid"

# Colors (disabled when logging to file)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    GRAY='\033[0;90m'
    NC='\033[0m'
else
    GREEN='' YELLOW='' CYAN='' GRAY='' NC=''
fi

function log() {
    echo -e "${GRAY}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Ensure directories exist
mkdir -p "$ROOT/simulation-results"
mkdir -p "$ROOT/reports"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Overnight simulations already running (PID: $OLD_PID)${NC}"
        echo "To stop: kill $OLD_PID"
        echo "To tail log: tail -f $LOG_FILE"
        exit 1
    else
        rm "$PID_FILE"
    fi
fi

# Check dev server
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -q "200"; then
    echo -e "${YELLOW}Dev server not running. Starting it...${NC}"
    npm run dev:quick &
    DEV_PID=$!
    sleep 5
    
    if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 | grep -q "200"; then
        echo -e "${RED}Failed to start dev server${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}         ${YELLOW}OVERNIGHT SIMULATION RUNNER${NC}                     ${CYAN}║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

log "Starting ${COUNT} simulations..."
log "Log file: $LOG_FILE"
log "Results: $ROOT/simulation-results/"

# Save PID
echo $$ > "$PID_FILE"

# Cleanup on exit
trap 'rm -f "$PID_FILE"; log "Stopped."' EXIT

# Record start time
START_TIME=$(date +%s)

# Run the simulations
node "$SCRIPT_DIR/batch-simulator.js" "$COUNT" --export=all 2>&1 | tee -a "$LOG_FILE"

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))

log ""
log "${GREEN}✓ Complete!${NC} Ran ${COUNT} simulations in ${DURATION_MIN} minutes"

# Generate summary
RESULTS_COUNT=$(ls -1 "$ROOT/simulation-results"/batch-*.json 2>/dev/null | wc -l)
log "Results files: $RESULTS_COUNT"

# Optional: Send notification (if notify-send available)
if command -v notify-send &> /dev/null; then
    notify-send "Darwin's Island" "Overnight simulations complete! ${COUNT} runs finished in ${DURATION_MIN}m"
fi

# Optional: Send email (if mail command available)
if command -v mail &> /dev/null && [ -n "$EMAIL" ]; then
    echo "Overnight simulations complete. See attached logs." | mail -s "Simulations Complete" -A "$LOG_FILE" "$EMAIL"
fi

log ""
log "Next steps:"
log "  - Check results: ls -la $ROOT/simulation-results/"
log "  - View summary: cat $ROOT/simulation-results/summary-*.json | tail -20"
log "  - Analyze: npm run sim:analyze"

exit 0
