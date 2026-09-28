#!/usr/bin/env bash
# Launch both servers: backend on :8000, frontend on :5173.
set -e
root="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$root/backend/app/fonts/Amiri-Regular.ttf" ]; then
  echo "[mishkat] fonts missing - fetching..."
  bash "$root/scripts/fetch_fonts.sh"
fi

echo "[mishkat] starting API on http://127.0.0.1:8000"
(cd "$root/backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
API_PID=$!

echo "[mishkat] starting web app on http://localhost:5173"
(cd "$root/frontend" && [ -d node_modules ] || npm install; npx vite --port 5173) &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null' EXIT
echo "[mishkat] ready. Ctrl+C to stop."
wait
