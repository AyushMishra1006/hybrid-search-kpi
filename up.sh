#!/usr/bin/env bash
# up.sh — one-command boot for hybrid-search-kpi
# Idempotent: safe to run multiple times. Skips steps already done.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$REPO_ROOT/backend"
FRONTEND="$REPO_ROOT/frontend"
VENV="$REPO_ROOT/.venv"
DATA="$REPO_ROOT/data"

echo "=== hybrid-search-kpi ==="

# 1. Virtual environment
if [ ! -d "$VENV" ]; then
    echo "[1/6] Creating virtual environment..."
    python3 -m venv "$VENV"
else
    echo "[1/6] Virtual environment already exists — skipping"
fi

# 2. Install Python dependencies
echo "[2/6] Installing Python dependencies..."
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$REPO_ROOT/requirements.txt"

# 3. Ingest pipeline (skip if docs.jsonl already exists)
if [ ! -f "$DATA/processed/docs.jsonl" ]; then
    echo "[3/6] Running ingest pipeline..."
    cd "$BACKEND"
    "$VENV/bin/python" -m app.ingest --input "$DATA/raw" --out "$DATA/processed"
    cd "$REPO_ROOT"
else
    echo "[3/6] docs.jsonl already exists — skipping ingest"
fi

# 4. Build search indexes (skip if BM25 index already exists)
if [ ! -f "$DATA/index/bm25/bm25_index.pkl" ]; then
    echo "[4/6] Building BM25 + FAISS indexes..."
    cd "$BACKEND"
    "$VENV/bin/python" -m app.index --input "$DATA/processed/docs.jsonl"
    cd "$REPO_ROOT"
else
    echo "[4/6] Indexes already exist — skipping index build"
fi

# 5. Start FastAPI backend (skip if port 8000 already in use)
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "[5/6] Port 8000 already in use — skipping backend start"
else
    echo "[5/6] Starting FastAPI backend on port 8000..."
    cd "$BACKEND"
    "$VENV/bin/uvicorn" app.api.main:app --host 0.0.0.0 --port 8000 \
        > "$REPO_ROOT/uvicorn.log" 2>&1 &
    cd "$REPO_ROOT"
fi

# 6. Start Vite frontend (skip if port 5173 already in use)
if lsof -ti:5173 > /dev/null 2>&1; then
    echo "[6/6] Port 5173 already in use — skipping frontend start"
else
    echo "[6/6] Starting React frontend on port 5173..."
    cd "$FRONTEND"
    if [ ! -d "node_modules" ]; then
        npm install -q
    fi
    npm run dev > "$REPO_ROOT/vite.log" 2>&1 &
    cd "$REPO_ROOT"
fi

echo ""
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Run ./down.sh to stop both servers."
