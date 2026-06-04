#!/bin/bash
# Restart the CityLab Flask server
#
# Uses run_citylab.py (distinctive name to avoid killing other apps' run.py)
# TLS is handled by nginx reverse proxy — Flask listens on 127.0.0.1 without TLS.

cd "$(dirname "$0")"

# Load .env if it exists
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

PORT=$(grep -A2 "^server:" config.yaml 2>/dev/null | grep "port:" | awk '{print $2}' || echo "15099")

# Kill ALL run_citylab.py processes — not just the one on the port.
CITYLAB_PIDS=$(pgrep -f "python.*run_citylab.py" 2>/dev/null)
if [[ -n "$CITYLAB_PIDS" ]]; then
    echo "$CITYLAB_PIDS" | xargs kill 2>/dev/null
    sleep 1
    REMAINING=$(pgrep -f "python.*run_citylab.py" 2>/dev/null)
    if [[ -n "$REMAINING" ]]; then
        echo "$REMAINING" | xargs kill -9 2>/dev/null
        sleep 0.5
    fi
fi

# Also kill anything still listening on our port (safety net)
PORT_PIDS=$(timeout 3 lsof -ti :$PORT -sTCP:LISTEN 2>/dev/null)
if [[ -n "$PORT_PIDS" ]]; then
    echo "$PORT_PIDS" | xargs kill 2>/dev/null
    sleep 0.5
fi

# Activate venv if it exists, otherwise set PYTHONPATH for src layout
if [[ -d "venv" ]]; then
    source venv/bin/activate
elif [[ -d ".venv" ]]; then
    source .venv/bin/activate
else
    export PYTHONPATH="${PWD}/src${PYTHONPATH:+:$PYTHONPATH}"
fi

# Strip Werkzeug reloader env vars so the new server starts fresh
unset WERKZEUG_RUN_MAIN WERKZEUG_SERVER_FD
unset CLAUDECODE

# Start server in background
python3 run_citylab.py > /tmp/citylab.log 2>&1 &

# Wait for startup
sleep 2

# Verify it's running
if curl -sf -o /dev/null --max-time 3 "http://127.0.0.1:$PORT/health"; then
    echo "Server started on http://127.0.0.1:$PORT (behind nginx at https://smac.griffin-blenny.ts.net:5099)"
    timeout 3 lsof -i :$PORT 2>/dev/null | head -3
elif timeout 3 lsof -i :$PORT > /dev/null 2>&1; then
    echo "Server bound to port http://127.0.0.1:$PORT (health check not yet responding)"
    timeout 3 lsof -i :$PORT 2>/dev/null | head -3
else
    echo "Server failed to start. Check /tmp/citylab.log"
    tail -20 /tmp/citylab.log
fi
