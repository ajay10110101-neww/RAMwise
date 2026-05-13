#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :3000 | xargs kill -9 2>/dev/null

echo "Starting RAMWise..."
echo ""

echo "[1/2] Backend  -> http://localhost:8000"
echo "[2/2] Frontend -> http://localhost:3000"
echo "API Docs      -> http://localhost:8000/docs"
echo ""

cd "$PROJECT_DIR/backend"
source venv/bin/activate
uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

cd "$PROJECT_DIR/dashboard"
npm start &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
