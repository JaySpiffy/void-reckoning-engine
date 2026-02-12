#!/bin/bash
# Quick dev server - skips type checking for faster startup

echo "🚀 Starting dev server (fast mode)..."
cd "$(dirname "$0")/.."

# Kill any existing vite processes
pkill -f "vite" 2>/dev/null

# Start vite dev server directly
npx vite --host &

VITE_PID=$!
echo "✅ Dev server started (PID: $VITE_PID)"
echo "🌐 http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop"

# Wait for process
wait $VITE_PID
