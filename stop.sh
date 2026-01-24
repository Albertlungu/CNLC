#!/bin/bash

# CNLC Application Stop Script
# Stops both the Flask backend API and frontend server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"

echo -e "${YELLOW}Stopping CNLC servers...${NC}"

if [ -f "$BACKEND_PID_FILE" ]; then
    kill $(cat "$BACKEND_PID_FILE") 2>/dev/null && echo "Backend server stopped." || echo "Backend server was not running."
    rm -f "$BACKEND_PID_FILE"
else
    echo "No backend PID file found."
fi

if [ -f "$FRONTEND_PID_FILE" ]; then
    kill $(cat "$FRONTEND_PID_FILE") 2>/dev/null && echo "Frontend server stopped." || echo "Frontend server was not running."
    rm -f "$FRONTEND_PID_FILE"
else
    echo "No frontend PID file found."
fi

# Also kill any orphaned processes on the ports
lsof -ti:5000 | xargs kill 2>/dev/null || true
lsof -ti:8080 | xargs kill 2>/dev/null || true

echo -e "${GREEN}All servers stopped.${NC}"
