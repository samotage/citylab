#!/usr/bin/env bash
# Restart CityLab development server.
# This is the ONLY permitted way to restart the server.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${CITYLAB_PORT:-5099}"

# Kill existing process on port
PID=$(lsof -ti :"$PORT" 2>/dev/null || true)
if [ -n "$PID" ]; then
    echo "Killing existing process on port $PORT (PID: $PID)"
    kill "$PID" 2>/dev/null || true
    sleep 1
fi

echo "Starting CityLab on port $PORT..."
python run.py &
echo "Server started (PID: $!)"
