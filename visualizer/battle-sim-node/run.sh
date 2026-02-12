#!/bin/bash

# ============================================
# DARWIN'S ISLAND / LAST HIT BLITZ - LAUNCHER
# ============================================

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   SELECT GAME MODE                            ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║                                                                ║"
echo "║  [1] 🧬 SURVIVAL RPG - Darwin's Island ReHelixed              ║"
echo "║      Evolve DNA, build bases, survive waves                   ║"
echo "║                                                                ║"
echo "║  [2] 🏈 LAST HIT BLITZ - Football Simulation                  ║"
echo "║      FIFA meets Madden, play calling & strategy               ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Read choice
read -p "Enter choice (1 or 2): " choice

# Set environment variable for App.tsx to read
if [ "$choice" == "2" ]; then
    echo ""
    echo "🏈 Starting Last Hit Blitz..."
    echo ""
    echo "Game Tips:"
    echo "  • View Teams to see player cards (click to flip)"
    echo "  • KICKOFF to start a game"
    echo "  • Select play category → Pick 1 of 3 plays"
    echo "  • On 4th down: Punt, FG, or Go For It"
    echo ""
    export VITE_GAME_MODE="football"
else
    echo ""
    echo "🧬 Starting Darwin's Island ReHelixed..."
    echo ""
    echo "Controls:"
    echo "  • WASD - Move"
    echo "  • Mouse - Aim/Shoot"
    echo "  • B - Build Mode"
    echo "  • T - Abilities | Y - DNA Evolution"
    echo "  • F9 - Toggle Autoplay | F10 - Debug Panel"
    echo ""
    export VITE_GAME_MODE="survival"
fi

# Clean environment
if [ "$1" == "--clean" ]; then
    echo "🧹 Cleaning node_modules and dist..."
    rm -rf node_modules dist package-lock.json
fi

# Check for dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🚀 Launching server at http://localhost:5173"
echo ""

# Launch Development Server
npm run dev
