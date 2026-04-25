#!/bin/bash
# Development mode: Vite dev server (hot reload) + FastAPI backend
cd "$(dirname "$0")"

echo "Starting development mode..."
echo "  Vite dev:  http://localhost:5173"
echo "  FastAPI:   http://localhost:8000"
echo ""

# Start FastAPI in background
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Start Vite dev server
cd frontend
npx vite --host 0.0.0.0 --port 5173
VITE_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM
