#!/usr/bin/env bash
# down.sh — stop backend and frontend servers
echo "Stopping hybrid-search-kpi servers..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
echo "Backend (8000) and frontend (5173) stopped."
