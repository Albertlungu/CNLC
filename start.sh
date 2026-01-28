#!/bin/bash

# CNLC Application Start Script
# Starts both the Flask backend API and frontend server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Ports (5001 to avoid macOS AirPlay Receiver conflict on 5000)
BACKEND_PORT=5001
FRONTEND_PORT=8080

# PID and log file locations
BACKEND_PID_FILE="$SCRIPT_DIR/.backend.pid"
FRONTEND_PID_FILE="$SCRIPT_DIR/.frontend.pid"
BACKEND_LOG="$SCRIPT_DIR/.backend.log"

cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"

    if [ -f "$BACKEND_PID_FILE" ]; then
        kill $(cat "$BACKEND_PID_FILE") 2>/dev/null || true
        rm -f "$BACKEND_PID_FILE"
    fi

    if [ -f "$FRONTEND_PID_FILE" ]; then
        kill $(cat "$FRONTEND_PID_FILE") 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE"
    fi

    rm -f "$BACKEND_LOG"

    echo -e "${GREEN}Servers stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found.${NC}"
    echo -e "${YELLOW}Run ./setup.sh first to create the virtual environment.${NC}"
    exit 1
fi

# Check if ports are available
if check_port $BACKEND_PORT; then
    echo -e "${RED}Port $BACKEND_PORT is already in use. Stop the existing process first.${NC}"
    exit 1
fi

if check_port $FRONTEND_PORT; then
    echo -e "${RED}Port $FRONTEND_PORT is already in use. Stop the existing process first.${NC}"
    exit 1
fi

echo -e "${GREEN}Starting CNLC Application...${NC}"
echo "========================================"

# Activate virtual environment
# source venv/bin/activate

# Start backend server
echo -e "${YELLOW}Starting backend API server on port $BACKEND_PORT...${NC}"
python run_server.py > "$BACKEND_LOG" 2>&1 &
echo $! > "$BACKEND_PID_FILE"

# Wait for backend to start (give it more time to load)
sleep 4

if check_port $BACKEND_PORT; then
    echo -e "${GREEN}Backend API running at http://127.0.0.1:$BACKEND_PORT${NC}"
else
    echo -e "${RED}Failed to start backend server. Check log below:${NC}"
    cat "$BACKEND_LOG"
    cleanup
    exit 1
fi

# Start frontend server
echo -e "${YELLOW}Starting frontend server on port $FRONTEND_PORT...${NC}"
cd frontend/src
python -m http.server $FRONTEND_PORT > /dev/null 2>&1 &
echo $! > "$FRONTEND_PID_FILE"
cd "$SCRIPT_DIR"

# Wait for frontend to start
sleep 1

if check_port $FRONTEND_PORT; then
    echo -e "${GREEN}Frontend running at http://127.0.0.1:$FRONTEND_PORT${NC}"
else
    echo -e "${RED}Failed to start frontend server.${NC}"
    cleanup
    exit 1
fi

echo ""
echo "========================================"
echo -e "${GREEN}Application started successfully!${NC}"
echo ""
echo "  Backend API:  http://127.0.0.1:$BACKEND_PORT"
echo "  Frontend:     http://127.0.0.1:$FRONTEND_PORT"
echo "  Login:        http://127.0.0.1:$FRONTEND_PORT/auth.html"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo "========================================"

# Open browser (macOS) - open auth page since businesses requires login
if command -v open &> /dev/null; then
    open "http://127.0.0.1:$FRONTEND_PORT/auth.html"
fi

# Keep script running
wait
