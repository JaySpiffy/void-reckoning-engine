#!/bin/bash
# Quick restart dev server

echo "🔄 Restarting dev server..."

# Kill existing vite processes
pkill -f "vite" 2>/dev/null
sleep 1

# Start fresh
cd "$(dirname "$0")/.."
npx vite --host &

VITE_PID=$!
echo "✅ Dev server restarted (PID: $VITE_PID)"
echo "🌐 Refresh http://localhost:5173"
echo ""

wait $VITE_PID
