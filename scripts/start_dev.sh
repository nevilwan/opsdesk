#!/bin/bash
# OpsDesk AI — Development Quick Start
# Run from project root: bash scripts/start_dev.sh
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================="
echo "  OpsDesk AI — Dev Quick Start"
echo "=================================="

# Step 1: Sample data
if [ ! -f "data/raw/all_tickets_processed_improved_v3.csv" ]; then
  echo "[1/5] Generating sample datasets..."
  python3 data/samples/generate_samples.py
else
  echo "[1/5] ✓ Datasets already present"
fi

# Step 2: Data pipeline
if [ ! -f "data/processed/tickets_unified.csv" ]; then
  echo "[2/5] Running data pipeline..."
  python3 ml/data_pipeline.py
else
  echo "[2/5] ✓ Processed data already present"
fi

# Step 3: Train models
if [ ! -f "ml/models/ticket_classifier.pkl" ]; then
  echo "[3/5] Training ML models (takes ~60s)..."
  python3 ml/train.py
else
  echo "[3/5] ✓ ML models already trained"
fi

# Step 4: Backend
echo "[4/5] Starting backend on :8000..."
cd backend
MODELS_DIR=../ml/models DATA_DIR=../data/processed \
  uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 4
echo "       Seeding demo data..."
curl -s -X POST "http://localhost:8000/api/tickets/seed-demo?count=80" > /dev/null 2>&1 || true
echo "       ✓ Demo data seeded"

# Step 5: Frontend
echo "[5/5] Starting frontend on :3000..."
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ OpsDesk AI is running!"
echo "   Frontend : http://localhost:3000"
echo "   Backend  : http://localhost:8000"
echo "   API Docs : http://localhost:8000/api/docs"
echo "   Health   : http://localhost:8000/api/health"
echo ""
echo "Demo login: admin@opsdesk.ai / admin123"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill \$BACKEND_PID \$FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT INT
wait
