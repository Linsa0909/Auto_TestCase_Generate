#!/bin/bash
echo ""
echo "  ========================================"
echo "    Test Case Intelligence v1.0"
echo "  ========================================"
echo ""

cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Install Python dependencies
echo "[1/4] Installing Python dependencies..."
pip3 install -r backend/requirements.txt -q 2>/dev/null

# Install Playwright browsers
echo "[2/4] Installing Playwright browser..."
python3 -m playwright install chromium 2>/dev/null

# Build frontend
echo "[3/4] Building frontend..."
cd frontend && npm install --silent 2>/dev/null && npm run build 2>/dev/null && cd ..

# Create data directory
mkdir -p backend/data/output

# Start server
echo "[4/4] Starting server..."
echo ""
echo "  Frontend: http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Open browser after short delay
(sleep 2 && python3 -m webbrowser http://localhost:8000) &

cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
